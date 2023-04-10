from datetime import datetime

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords
import bs.core.attribute_expansion as attribute_expansion


class AttributeType(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True, verbose_name="属性类型")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "属性类型"
        verbose_name_plural = "属性类型"


class ResourceType(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True, verbose_name="资源类型")
    description = models.CharField(max_length=255, verbose_name="描述")
    history = HistoricalRecords(verbose_name="历史")

    @property
    def active_count(self):
        return ResourceAttribute.objects.filter(
            resource__resource_type__name=self.name, value="Active").count()

    @property
    def inactive_count(self):
        return ResourceAttribute.objects.filter(
            resource__resource_type__name=self.name, value="Inactive").count()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "资源类型"
        verbose_name_plural = "资源类型"


class ResourceAttributeType(TimeStampedModel):
    attribute_type = models.ForeignKey(
        AttributeType, on_delete=models.CASCADE, verbose_name="属性类型")
    name = models.CharField(max_length=128, verbose_name="名称")
    is_required = models.BooleanField(default=False, verbose_name="是否可用")
    is_unique_per_resource = models.BooleanField(
        default=False, verbose_name="是否独立")
    is_value_unique = models.BooleanField(default=False, verbose_name="金额独立")
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "资源属性类型"
        verbose_name_plural = "资源属性类型"


class Resource(TimeStampedModel):
    parent_resource = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True, verbose_name="主资源")
    resource_type = models.ForeignKey(
        ResourceType, on_delete=models.CASCADE, verbose_name="资源类型")
    name = models.CharField(max_length=128, unique=True, verbose_name="名称")
    description = models.TextField(verbose_name="描述")
    is_available = models.BooleanField(default=True, verbose_name="是否可获得")
    is_public = models.BooleanField(default=True, verbose_name="是否公共")
    is_allocatable = models.BooleanField(default=True, verbose_name="是否可分配")
    requires_payment = models.BooleanField(default=False, verbose_name="价格")
    allowed_groups = models.ManyToManyField(
        Group, blank=True, verbose_name="分配的小组")
    allowed_users = models.ManyToManyField(
        User, blank=True, verbose_name="分配的成员")
    linked_resources = models.ManyToManyField(
        'self', blank=True, verbose_name="关联资源")
    history = HistoricalRecords(verbose_name="历史")

    def get_missing_resource_attributes(self, required=False):
        if required:
            resource_attributes = ResourceAttributeType.objects.filter(
                resource_type=self.resource_type, required=True)
        else:
            resource_attributes = ResourceAttributeType.objects.filter(
                resource_type=self.resource_type)

        missing_resource_attributes = []

        for attribute in resource_attributes:
            if not ResourceAttribute.objects.filter(resource=self, resource_attribute_type=attribute).exists():
                missing_resource_attributes.append(attribute)
        return missing_resource_attributes

    @property
    def status(self):
        return ResourceAttribute.objects.get(resource=self, resource_attribute_type__attribute="Status").value

    def get_attribute(self, name, expand=True, typed=True,
                      extra_allocations=[]):
        attr = self.resourceattribute_set.filter(
            resource_attribute_type__name=name).first()
        if attr:
            if expand:
                return attr.expanded_value(
                    typed=typed, extra_allocations=extra_allocations)
            else:
                if typed:
                    return attr.typed_value()
                else:
                    return attr.value
        return None

    def get_attribute_list(self, name, expand=True, typed=True,
                           extra_allocations=[]):
        attr = self.resourceattribute_set.filter(
            resource_attribute_type__name=name).all()
        if expand:
            return [a.expanded_value(extra_allocations=extra_allocations,
                                     typed=typed) for a in attr]
        else:
            if typed:
                return [a.typed_value() for a in attr]
            else:
                return [a.value for a in attr]

    def get_ondemand_status(self):
        ondemand = self.resourceattribute_set.filter(
            resource_attribute_type__name='OnDemand').first()
        if ondemand:
            return ondemand.value
        return None

    def __str__(self):
        return '%s (%s)' % (self.name, self.resource_type.name)

    class Meta:
        ordering = ['name', ]
        verbose_name = "资源"
        verbose_name_plural = "资源"


class ResourceAttribute(TimeStampedModel):
    resource_attribute_type = models.ForeignKey(
        ResourceAttributeType, on_delete=models.CASCADE, verbose_name="资源属性类型")
    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, verbose_name="资源")
    value = models.TextField(verbose_name="值")
    history = HistoricalRecords(verbose_name="历史")

    def clean(self):

        expected_value_type = self.resource_attribute_type.attribute_type.name.strip()

        if expected_value_type == "Int" and not self.value.isdigit():
            raise ValidationError(
                '"%s". 值必须为int类型.' % (self.value))
        elif expected_value_type == "Active/Inactive" and self.value not in ["Active", "Inactive"]:
            raise ValidationError(
                '"%s". 值为"Active" 或 "Inactive".' % (self.value))
        elif expected_value_type == "Public/Private" and self.value not in ["Public", "Private"]:
            raise ValidationError(
                '"%s". 值为"Public" 或 "Private".' % (self.value))
        elif expected_value_type == "Date":
            try:
                datetime.strptime(self.value.strip(), "%m/%d/%Y")
            except ValueError:
                raise ValidationError(
                    '"%s". 日期格式为 MM/DD/YYYY' % (self.value))

    def __str__(self):
        return '%s: %s (%s)' % (self.resource_attribute_type, self.value, self.resource)

    def typed_value(self):
        raw_value = self.value
        atype_name = self.resource_attribute_type.attribute_type.name
        return attribute_expansion.convert_type(
            value=raw_value, type_name=atype_name)

    def expanded_value(self, typed=True, extra_allocations=[]):
        raw_value = self.value
        if typed:
            raw_value = self.typed_value()

        if not attribute_expansion.is_expandable_type(
                self.resource_attribute_type.attribute_type):
            return raw_value

        allocs = extra_allocations
        resources = [self.resource]
        attrib_name = self.resource_attribute_type.name

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
        unique_together = ('resource_attribute_type', 'resource')
        verbose_name = "资源属性"
        verbose_name_plural = "资源属性"
