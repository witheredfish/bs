import datetime
import textwrap
from enum import Enum

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from ast import literal_eval
from bs.core.utils.validate import AttributeValidator
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords
from bs.core.utils.common import import_from_settings
from bs.core.field_of_science.models import FieldOfScience

PROJECT_ENABLE_PROJECT_REVIEW = import_from_settings(
    'PROJECT_ENABLE_PROJECT_REVIEW', False)


class ProjectPermission(Enum):
    USER = 'user'
    MANAGER = 'manager'
    PI = 'pi'
    UPDATE = 'update'


class ProjectStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = "项目状态"
        verbose_name_plural = "项目状态"


class Project(TimeStampedModel):

    DEFAULT_DESCRIPTION = "我们没有关于您的研究信息。请提供工作的详细描述并更新您的学科领域。谢谢！"

    title = models.CharField(max_length=255, verbose_name="项目标题")
    pi = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="项目负责人")
    description = models.TextField(
        default=DEFAULT_DESCRIPTION,
        validators=[
            MinLengthValidator(10, "项目描述必须多于10个字。")
        ],
        verbose_name="项目描述"
    )

    field_of_science = models.ForeignKey(
        FieldOfScience, on_delete=models.CASCADE, default=000, verbose_name="学科领域")
    status = models.ForeignKey(
        ProjectStatusChoice, on_delete=models.CASCADE, verbose_name="项目状态")
    force_review = models.BooleanField(default=False, verbose_name="强制审核")
    requires_review = models.BooleanField(default=True, verbose_name="需求审核")
    history = HistoricalRecords()

    def clean(self):
        if "添加项目标题" in self.title:
            raise ValidationError('请输入项目标题')

        if "我们没有关于您的研究信息。请提供工作的详细描述并更新您的学科领域。谢谢！" in self.description:
            raise ValidationError('请输入项目描述')

    @property
    def last_project_review(self):
        if self.projectreview_set.exists():
            return self.projectreview_set.order_by('-created')[0]
        else:
            return None

    @property
    def latest_grant(self):
        if self.grant_set.exists():
            return self.grant_set.order_by('-modified')[0]
        else:
            return None

    @property
    def latest_publication(self):
        if self.publication_set.exists():
            return self.publication_set.order_by('-created')[0]
        else:
            return None

    @property
    def needs_review(self):

        if self.status.name == 'Archived':
            return False

        now = datetime.datetime.now(datetime.timezone.utc)

        if self.force_review is True:
            return True

        if not PROJECT_ENABLE_PROJECT_REVIEW:
            return False

        if self.requires_review is False:
            return False

        if self.projectreview_set.exists():
            last_review = self.projectreview_set.order_by('-created')[0]
            last_review_over_365_days = (now - last_review.created).days > 365
        else:
            last_review = None

        days_since_creation = (now - self.created).days

        if days_since_creation > 365 and last_review is None:
            return True

        if last_review and last_review_over_365_days:
            return True

        return False

    # 返回用户权限
    def user_permissions(self, user):
        if user.is_superuser:
            return list(ProjectPermission)

        user_conditions = (models.Q(status__name__in=(
            'Active', 'New')) & models.Q(user=user))
        if not self.projectuser_set.filter(user_conditions).exists():
            return []

        permissions = [ProjectPermission.USER]

        if self.projectuser_set.filter(user_conditions & models.Q(role__name='Manager')).exists():
            permissions.append(ProjectPermission.MANAGER)

        if self.projectuser_set.filter(user_conditions & models.Q(project__pi_id=user.id)).exists():
            permissions.append(ProjectPermission.PI)

        if ProjectPermission.MANAGER in permissions or ProjectPermission.MANAGER in permissions:
            permissions.append(ProjectPermission.UPDATE)

        return permissions

    def has_perm(self, user, perm):
        perms = self.user_permissions(user)
        return perm in perms

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

        permissions = (
            ("can_view_all_projects", "可以查看所有项目"),
            ("can_review_pending_project_reviews",
             "可以审核所有待审核项目"),
        )

        verbose_name = "项目"
        verbose_name_plural = "项目管理"


class ProjectAdminComment(TimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="发表者")
    comment = models.TextField(verbose_name="评论")

    def __str__(self):
        return self.comment

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论管理"


class ProjectUserMessage(TimeStampedModel):
    Project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="发表者")
    is_private = models.BooleanField(default=True, verbose_name="可见性")
    message = models.TextField(verbose_name="留言")

    def __str__(self):
        return self.message

    class Meta:
        verbose_name = "留言"
        verbose_name_plural = "留言管理"


class ProjectReviewStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="名称")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "审核状态"
        verbose_name_plural = "审核状态管理"


class ProjectReview(TimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    status = models.ForeignKey(
        ProjectReviewStatusChoice, on_delete=models.CASCADE, verbose_name='状态')
    reason_for_not_updating_project = models.TextField(
        blank=True, null=True, verbose_name="未升级原因")
    history = HistoricalRecords(verbose_name="历史")

    class Meta:
        verbose_name = "项目审核"
        verbose_name_plural = "项目审核"


class ProjectUserRoleChoice(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="角色选择")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "人员角色"
        verbose_name_plural = "人员角色"


class ProjectUserStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="状态选择")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "人员状态"
        verbose_name_plural = "人员状态"


class ProjectUser(TimeStampedModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    role = models.ForeignKey(ProjectUserRoleChoice,
                             on_delete=models.CASCADE, verbose_name="角色")
    status = models.ForeignKey(
        ProjectUserStatusChoice, on_delete=models.CASCADE, verbose_name='状态')
    enable_notifications = models.BooleanField(
        default=True, verbose_name="启用通知")
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return '%s %s (%s)' % (self.user.first_name, self.user.last_name, self.user.username)

    class Meta:
        unique_together = ('user', 'project')
        verbose_name = "项目人员状态"
        verbose_name_plural = "项目人员状态"


class AttributeType(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="属性类型")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "属性类型"
        verbose_name_plural = "属性类型"


class ProjectAttributeType(TimeStampedModel):
    attribute_type = models.ForeignKey(
        AttributeType, on_delete=models.CASCADE, verbose_name="属性类型")
    name = models.CharField(max_length=50, verbose_name="名称")
    has_usage = models.BooleanField(default=False, verbose_name="可用性")
    is_required = models.BooleanField(default=False, verbose_name="是否需要")
    is_unique = models.BooleanField(default=False, verbose_name="是否独立")
    is_private = models.BooleanField(default=True, verbose_name="是否私有")
    is_changeable = models.BooleanField(default=False, verbose_name="是否可变")
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return '%s (%s)' % (self.name, self.attribute_type.name)

    def __repr__(self) -> str:
        return str(self)

    class Meta:
        ordering = ['name', ]
        verbose_name = "项目属性类型"
        verbose_name_plural = "项目属性类型"


class ProjectAttribute(TimeStampedModel):
    proj_attr_type = models.ForeignKey(
        ProjectAttributeType, on_delete=models.CASCADE, verbose_name="项目属性")
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")

    value = models.CharField(max_length=128, verbose_name="金额")
    history = HistoricalRecords(verbose_name="历史")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.proj_attr_type.has_usage and not ProjectAttributeUsage.objects.filter(project_attribute=self).exists():
            ProjectAttributeUsage.objects.create(
                project_attribute=self)

    def clean(self):
        if self.proj_attr_type.is_unique and self.project.projectattribute_set.filter(proj_attr_type=self.proj_attr_type).exists():
            raise ValidationError("'{}' 已经出现在项目中".format(
                self.proj_attr_type))

        expected_value_type = self.proj_attr_type.attribute_type.name.strip()

        validator = AttributeValidator(self.value)

        if expected_value_type == "Int":
            validator.validate_int()
        elif expected_value_type == "Float":
            validator.validate_float()
        elif expected_value_type == "Yes/No":
            validator.validate_yes_no()
        elif expected_value_type == "Date":
            validator.validate_date()

    def __str__(self):
        return '%s' % (self.proj_attr_type.name)

    class Meta:
        verbose_name = "项目属性"
        verbose_name_plural = "项目属性"


class ProjectAttributeUsage(TimeStampedModel):
    project_attribute = models.OneToOneField(
        ProjectAttribute, on_delete=models.CASCADE, primary_key=True, verbose_name="项目属性")
    value = models.FloatField(default=0, verbose_name="金额")
    history = HistoricalRecords(verbose_name="历史")

    def __str__(self):
        return '{}: {}'.format(self.project_attribute.proj_attr_type.name, self.value)

    class Meta:
        verbose_name = "项目属性可用性"
        verbose_name_plural = "项目属性可用性"
