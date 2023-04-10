from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from bs.core.project.models import Project


class PublicationSource(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="名称")
    url = models.URLField(null=True, blank=True, verbose_name="网址")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "出版物资源"
        verbose_name_plural = "出版物资源"


class Publication(TimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    title = models.CharField(max_length=1024, verbose_name="标题")
    author = models.CharField(max_length=1024, verbose_name="作者")
    year = models.PositiveIntegerField(verbose_name="年份")
    journal = models.CharField(max_length=1024, verbose_name="期刊")
    unique_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="独立ID")
    source = models.ForeignKey(
        PublicationSource, on_delete=models.CASCADE, verbose_name="资源地址")
    STATUS_CHOICES = (
        ('Active', '活跃'),
        ('Archived', '封存'),
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default='Active', verbose_name="状态")
    history = HistoricalRecords(verbose_name="历史")

    class Meta:
        unique_together = ('project', 'unique_id')
        verbose_name = "出版物"
        verbose_name_plural = "出版物"

    def __str__(self):
        return self.title

    def display_uid(self):
        return self.unique_id
