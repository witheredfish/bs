from django.db import models
from model_utils.models import TimeStampedModel


class FieldOfScience(TimeStampedModel):
    DEFAULT_PK = 149
    parent_id = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, verbose_name="父学科ID")
    is_selectable = models.BooleanField(default=True, verbose_name="可选性")
    description = models.CharField(max_length=255, verbose_name="学科描述")
    fos_nsf_id = models.IntegerField(
        null=True, blank=True, verbose_name="NSF编号")
    fos_nsf_abbrev = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="NSF缩写")
    directorate_fos_id = models.IntegerField(
        null=True, blank=True, verbose_name="管理机构ID")

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "学科领域"
        verbose_name_plural = "学科领域"
        ordering = ['description']
