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


class ProjectStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


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
