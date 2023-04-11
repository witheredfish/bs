from django.db import models
from django.core.validators import (
    MaxLengthValidator, MaxValueValidator, MinLengthValidator)
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from bs.core.project.models import Project


class GrantFundingAgency(TimeStampedModel):
    name = models.CharField(max_length=255, verbose_name="名称")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = "资助机构"
        verbose_name_plural = "资助机构"


class GrantStatusChoice(TimeStampedModel):
    name = models.CharField(max_length=64, verbose_name="资助状态")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = "资助状态"
        verbose_name_plural = "资助状态"


class Grant(TimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name="项目")
    title = models.CharField(
        validators=[MinLengthValidator(3), MaxLengthValidator(255)],
        max_length=255,
        verbose_name="标题"
    )
    grant_number = models.CharField(
        verbose_name='资助机构的授权编号',
        validators=[MinLengthValidator(3), MaxLengthValidator(255)],
        max_length=255,
    )
    ROLE_CHOICES = (
        ('PI', '项目负责人'),
        ('CoPI', '联合负责人'),
        ('SP', '高级人员'),
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name="角色"
    )
    grant_pi_full_name = models.CharField(
        max_length=255, blank=True, verbose_name="资助项目负责人名称")
    funding_agency = models.ForeignKey(
        GrantFundingAgency, on_delete=models.CASCADE, verbose_name="资助机构")
    other_funding_agency = models.CharField(
        max_length=255, blank=True, verbose_name="其他资助机构")
    other_award_number = models.CharField(
        max_length=255, blank=True, verbose_name="其他奖励")
    grant_start = models.DateField(verbose_name="资助开始时间")
    grant_end = models.DateField(verbose_name="资助结束时间")
    percent_credit = models.FloatField(
        validators=[MaxValueValidator(100)], verbose_name="占比")
    direct_funding = models.FloatField(verbose_name="直接资助")
    total_amount_awarded = models.FloatField(verbose_name="资助总和")
    status = models.ForeignKey(
        GrantStatusChoice, on_delete=models.CASCADE, verbose_name="状态")
    history = HistoricalRecords(verbose_name="历史")

    @property
    def grant_pi(self):
        if self.role == 'PI':
            return '{}'.format(self.project.pi.first_name)
        else:
            return self.grant_pi_full_name

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Grants"

        permissions = (
            ("can_view_all_grants", "可以查看所有资助"),
        )
        verbose_name = "资助"
        verbose_name_plural = "资助"
