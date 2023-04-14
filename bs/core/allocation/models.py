import datetime
import logging
from ast import literal_eval
from enum import Enum
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import mark_safe
from django.utils.module_loading import import_string
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords
from bs.core.project.models import Project, ProjectPermission
from bs.core.resource.models import Resource
from bs.core.utils.common import import_from_settings
import bs.core.attribute_expansion as attribute_expansion

logger = logging.getLogger(__name__)

ALLOCATION_ATTRIBUTE_VIEW_LIST = import_from_settings(
    'ALLOCATION_ATTRIBUTE_VIEW_LIST', [])
ALLOCATION_FUNCS_ON_EXPIRE = import_from_settings(
    'ALLOCATION_FUNCS_ON_EXPIRE', [])
ALLOCATION_RESOURCE_ORDERING = import_from_settings(
    'ALLOCATION_RESOURCE_ORDERING',
    ['-is_allocatable', 'name'])


class AllocationPermission(Enum):
    USER = 'USER'
    MANAGER = 'MANAGER'


class AllocationStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="名称")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "分配状态"
        verbose_name_plural = "分配状态"


class Allocation(TimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    resources = models.ManyToManyField(Resource, verbose_name="资源")
    status = models.ForeignKey(
        AllocationStatusChoice, on_delete=models.CASCADE, verbose_name='状态')
    quantity = models.IntegerField(default=1, verbose_name="数量")
    start_date = models.DateField(blank=True, null=True, verbose_name="开始日期")
    end_date = models.DateField(blank=True, null=True, verbose_name="结束日期")
    justification = models.TextField(verbose_name="理由")
    description = models.CharField(
        max_length=512, blank=True, null=True, verbose_name="描述")
    is_locked = models.BooleanField(default=False, verbose_name="是否锁定")
    is_changeable = models.BooleanField(default=False, verbose_name="是否可变")
    history = HistoricalRecords(verbose_name="历史")

    class Meta:
        ordering = ['end_date', ]
        verbose_name = "分配资源"
        verbose_name_plural = "分配资源"

        permissions = (
            ('can_view_all_allocations', '可以查看分配'),
            ('can_review_allocation_requests',
             '可以审核所有分配请求'),
            ('can_manage_invoice', '可以管理账单'),
        )

    def clean(self):
        if self.status.name == 'Expired':
            if not self.end_date:
                raise ValidationError('必须填写结束日期')

            if self.end_date > datetime.datetime.now().date():
                raise ValidationError(
                    '结束日期不能大于今天')

            if self.start_date > self.end_date:
                raise ValidationError(
                    '开始日期不能大于结束日期')

        elif self.status.name == 'Active':
            if not self.start_date:
                raise ValidationError('你必须设置开始日期')

            if not self.end_date:
                raise ValidationError('你必须设置结束日期')

            if self.start_date > self.end_date:
                raise ValidationError(
                    '开始日期不能大于结束日期')

    def save(self, *args, **kwargs):
        if self.pk:
            old_obj = Allocation.objects.get(pk=self.pk)
            if old_obj.status.name != self.status.name and self.status.name == 'Expired':
                for func_string in ALLOCATION_FUNCS_ON_EXPIRE:
                    func_to_run = import_string(func_string)
                    func_to_run(self.pk)

        super().save(*args, **kwargs)

    @property
    def expires_in(self):
        return (self.end_date - datetime.date.today()).days

    @property
    def get_information(self):
        html_string = ''
        for attribute in self.allocationattribute_set.all():
            if attribute.allocation_attribute_type.name in ALLOCATION_ATTRIBUTE_VIEW_LIST:
                html_string += '%s: %s <br>' % (
                    attribute.allocation_attribute_type.name, attribute.value)

            if hasattr(attribute, 'allocationattributeusage'):
                try:
                    percent = round(float(attribute.allocationattributeusage.value) /
                                    float(attribute.value) * 10000) / 100
                except ValueError:
                    percent = '无效值'
                    logger.error(" '%s' 不是int类型",
                                 attribute.allocation_attribute_type.name)
                except ZeroDivisionError:
                    percent = 100
                    logger.error(" '%s' 等于0但是又用法",
                                 attribute.allocation_attribute_type.name)

                string = '{}: {}/{} ({} %) <br>'.format(
                    attribute.allocation_attribute_type.name,
                    attribute.allocationattributeusage.value,
                    attribute.value,
                    percent
                )
                html_string += string

        return mark_safe(html_string)

    @property
    def get_resources_as_string(self):
        return ', '.join([ele.name for ele in self.resources.all().order_by(
            *ALLOCATION_RESOURCE_ORDERING)])

    @property
    def get_resources_as_list(self):
        return [ele for ele in self.resources.all().order_by('-is_allocatable')]

    @property
    def get_parent_resource(self):
        if self.resources.count() == 1:
            return self.resources.first()
        else:
            parent = self.resources.order_by(
                *ALLOCATION_RESOURCE_ORDERING).first()
            if parent:
                return parent
            return self.resources.first()

    def get_attribute(self, name, expand=True, typed=True,
                      extra_allocations=[]):
        attr = self.allocationattribute_set.filter(
            allocation_attribute_type__name=name).first()
        if attr:
            if expand:
                return attr.expanded_value(
                    extra_allocations=extra_allocations, typed=typed)
            else:
                if typed:
                    return attr.typed_value()
                else:
                    return attr.value
        return None

    def set_usage(self, name, value):
        attr = self.allocationattribute_set.filter(
            allocation_attribute_type__name=name).first()
        if not attr:
            return

        if not attr.allocation_attribute_type.has_usage:
            return

        if not AllocationAttributeUsage.objects.filter(allocation_attribute=attr).exists():
            usage = AllocationAttributeUsage.objects.create(
                allocation_attribute=attr)
        else:
            usage = attr.allocationattributeusage

        usage.value = value
        usage.save()

    def get_attribute_list(self, name, expand=True, typed=True,
                           extra_allocations=[]):
        attr = self.allocationattribute_set.filter(
            allocation_attribute_type__name=name).all()
        if expand:
            return [a.expanded_value(typed=typed,
                                     extra_allocations=extra_allocations) for a in attr]
        else:
            if typed:
                return [a.typed_value() for a in attr]
            else:
                return [a.value for a in attr]

    def get_attribute_set(self, user):
        if user.is_superuser:
            return self.allocationattribute_set.all().order_by('allocation_attribute_type__name')

        return self.allocationattribute_set.filter(allocation_attribute_type__is_private=False).order_by('allocation_attribute_type__name')

    def user_permissions(self, user):
        if user.is_superuser:
            return list(AllocationPermission)

        project_perms = self.project.user_permissions(user)

        if ProjectPermission.USER not in project_perms:
            return []

        if ProjectPermission.PI in project_perms or ProjectPermission.MANAGER in project_perms:
            return [AllocationPermission.USER, AllocationPermission.MANAGER]

        if self.allocationuser_set.filter(user=user, status__name__in=['Active', 'New', ]).exists():
            return [AllocationPermission.USER]

        return []

    def has_perm(self, user, perm):
        perms = self.user_permissions(user)
        return perm in perms

    def __str__(self):
        return "%s (%s)" % (self.get_parent_resource.name, self.project.pi)


class AllocationAdminNote(TimeStampedModel):
    allocation = models.ForeignKey(
        Allocation, on_delete=models.CASCADE, verbose_name="分配")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="管理员")
    note = models.TextField(verbose_name="描述")

    def __str__(self):
        return self.note

    class Meta:
        verbose_name = "分配管理员描述"
        verbose_name_plural = "分配管理员描述"


class AllocationUserNote(TimeStampedModel):
    allocation = models.ForeignKey(
        Allocation, on_delete=models.CASCADE, verbose_name="分配")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="用户")
    is_private = models.BooleanField(default=True, verbose_name="是否私人")
    note = models.TextField(verbose_name="描述")

    def __str__(self):
        return self.note

    class Meta:
        verbose_name = "分配人员描述"
        verbose_name_plural = "分配人员描述"


class AttributeType(TimeStampedModel):

    name = models.CharField(max_length=64, verbose_name="名称")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "分配属性"
        verbose_name_plural = "分配属性"


class AllocationAttributeType(TimeStampedModel):
    attribute_type = models.ForeignKey(
        AttributeType, on_delete=models.CASCADE, verbose_name="属性类型")
    name = models.CharField(max_length=50, verbose_name="名称")
    has_usage = models.BooleanField(default=False, verbose_name="是否有用")
    is_required = models.BooleanField(default=False, verbose_name="是否被需要")
    is_unique = models.BooleanField(default=False, verbose_name="是否独立")
    is_private = models.BooleanField(default=True, verbose_name="是否私有")
    is_changeable = models.BooleanField(default=False, verbose_name="是否可变")
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        ordering = ['name', ]
        verbose_name = "分配属性类型"
        verbose_name_plural = "分配属性类型"


class AllocationAttribute(TimeStampedModel):
    allocation_attribute_type = models.ForeignKey(
        AllocationAttributeType, on_delete=models.CASCADE, verbose_name="分配属性类型")
    allocation = models.ForeignKey(
        Allocation, on_delete=models.CASCADE, verbose_name="分配")
    value = models.CharField(max_length=128, verbose_name="值")
    history = HistoricalRecords(verbose_name="历史")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.allocation_attribute_type.has_usage and not AllocationAttributeUsage.objects.filter(allocation_attribute=self).exists():
            AllocationAttributeUsage.objects.create(
                allocation_attribute=self)

    def clean(self):
        if self.allocation_attribute_type.is_unique and self.allocation.allocationattribute_set.filter(allocation_attribute_type=self.allocation_attribute_type).exclude(id=self.pk).exists():
            raise ValidationError("'{}' 这个属性已经出现在分配中".format(
                self.allocation_attribute_type))

        expected_value_type = self.allocation_attribute_type.attribute_type.name.strip()

        if expected_value_type == "Int" and not isinstance(literal_eval(self.value), int):
            raise ValidationError(
                '值 "%s" . 必须为int类型' % (self.value))
        elif expected_value_type == "Float" and not (isinstance(literal_eval(self.value), float) or isinstance(literal_eval(self.value), int)):
            raise ValidationError(
                '值 "%s" . 必须为float类型' % (self.value))
        elif expected_value_type == "Yes/No" and self.value not in ["Yes", "No"]:
            raise ValidationError(
                '值 "%s" . 必须为 "Yes" 或 "No".' % (self.values))
        elif expected_value_type == "Date":
            try:
                datetime.datetime.strptime(self.value.strip(), "%Y-%m-%d")
            except ValueError:
                raise ValidationError(
                    '值 "%s" .日期格式必须为YYYY-MM-DD' % (self.value))

    def __str__(self):
        return '%s' % (self.allocation_attribute_type.name)

    def typed_value(self):
        raw_value = self.value
        atype_name = self.allocation_attribute_type.attribute_type.name
        return attribute_expansion.convert_type(
            value=raw_value, type_name=atype_name)

    def expanded_value(self, extra_allocations=[], typed=True):
        raw_value = self.value
        if typed:
            raw_value = self.typed_value()

        if not attribute_expansion.is_expandable_type(
                self.allocation_attribute_type.attribute_type):
            return raw_value

        allocs = [self.allocation] + extra_allocations
        resources = list(self.allocation.resources.all())
        attrib_name = self.allocation_attribute_type.name

        attriblist = attribute_expansion.get_attriblist_str(
            attribute_name=attrib_name,
            resources=resources,
            allocations=allocs)

        if not attriblist:
            return raw_value

        expanded = attribute_expansion.expand_attribute(
            raw_value=raw_value,
            attribute_name=attrib_name,
            attriblist_string=attriblist,
            resources=resources,
            allocations=allocs)
        return expanded

    class Meta:
        verbose_name = "分配属性"
        verbose_name_plural = "分配属性"


class AllocationAttributeUsage(TimeStampedModel):
    allocation_attribute = models.OneToOneField(
        AllocationAttribute, on_delete=models.CASCADE, primary_key=True, verbose_name="分配属性")
    value = models.FloatField(default=0, verbose_name="值")
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return '{}: {}'.format(self.allocation_attribute.allocation_attribute_type.name, self.value)

    class Meta:
        verbose_name = "分配属性用法"
        verbose_name_plural = "分配属性用法"


class AllocationUserStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="名称")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "分配用户状态"
        verbose_name_plural = "分配用户状态"


class AllocationUser(TimeStampedModel):
    allocation = models.ForeignKey(
        Allocation, on_delete=models.CASCADE, verbose_name="分配")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    status = models.ForeignKey(AllocationUserStatusChoice, on_delete=models.CASCADE,
                               verbose_name='用户状态')
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return '%s' % (self.user)

    class Meta:
        unique_together = ('user', 'allocation')
        verbose_name = "分配用户"
        verbose_name_plural = "分配用户"


class AllocationAccount(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    name = models.CharField(max_length=64, unique=True, verbose_name="名称")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "分配账户"
        verbose_name_plural = "分配账户"


class AllocationChangeStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="名称")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "分配更改状态"
        verbose_name_plural = "分配更改状态"


class AllocationChangeRequest(TimeStampedModel):
    allocation = models.ForeignKey(
        Allocation, on_delete=models.CASCADE, verbose_name="分配")
    status = models.ForeignKey(
        AllocationChangeStatusChoice, on_delete=models.CASCADE, verbose_name='状态')
    end_date_extension = models.IntegerField(
        blank=True, null=True, verbose_name="延期日期")
    justification = models.TextField(verbose_name="理由")
    notes = models.CharField(max_length=512, blank=True,
                             null=True, verbose_name="描述")
    history = HistoricalRecords(verbose_name="历史")

    @property
    def get_parent_resource(self):
        if self.allocation.resources.count() == 1:
            return self.allocation.resources.first()
        else:
            return self.allocation.resources.filter(is_allocatable=True).first()

    def __str__(self):
        return "%s (%s)" % (self.get_parent_resource.name, self.allocation.project.pi)

    class Meta:
        verbose_name = "分配更改请求"
        verbose_name_plural = "分配更改请求"


class AllocationAttributeChangeRequest(TimeStampedModel):
    allocation_change_request = models.ForeignKey(
        AllocationChangeRequest, on_delete=models.CASCADE, verbose_name="分配更改请求")
    allocation_attribute = models.ForeignKey(
        AllocationAttribute, on_delete=models.CASCADE, verbose_name="分配属性")
    new_value = models.CharField(max_length=128, verbose_name="新属性")
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return '%s' % (self.allocation_attribute.allocation_attribute_type.name)

    class Meta:
        verbose_name = "分配属性更改请求"
        verbose_name_plural = "分配属性更改请求"
