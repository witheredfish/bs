from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from bs.core.project.models import Project


class ResearchOutput(TimeStampedModel):
    Project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    title = models.CharField(max_length=128, blank=True, verbose_name="标题")
    description = models.TextField(
        validators=[MinLengthValidator(3)],
        verbose_name="描述"
    )

    created_by = models.ForeignKey(
        User,
        editable=False,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="创建人"
    )

    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="时间")
    history = HistoricalRecords(verbose_name="历史")

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.created_by:
                raise ValueError('必须设定一个创建人')

        self.title = self.title.strip()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "研究成果"
        verbose_name_plural = "研究成果"
