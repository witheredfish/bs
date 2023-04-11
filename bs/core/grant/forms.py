from django import forms
from django.forms import ModelForm
from django.shortcuts import get_object_or_404

from bs.core.grant.models import Grant
from bs.core.utils.common import import_from_settings

CENTER_NAME = import_from_settings('CENTER_NAME')


class GrantForm(ModelForm):
    class Meta:
        model = Grant
        exclude = ['project', ]
        labels = {
            'percent_credit': '{}的信用分百分比'.format(CENTER_NAME),
            'direct_funding': '{}的资助使用情况'.format(CENTER_NAME)
        }
        help_texts = {
            'percent_credit': '按照拨款申请表中填写的百分比信用作为财务信用分配给部门/单位',
            'direct_funding': '资助会用于{}的服务、硬件、软件或人员'.format(CENTER_NAME)
        }

    def __init__(self, *args, **kwargs):
        super(GrantForm, self).__init__(*args, **kwargs)
        self.fields['funding_agency'].queryset = self.fields['funding_agency'].queryset.order_by(
            'name')


class GrantDeleteForm(forms.Form):
    title = forms.CharField(max_length=255, disabled=True)
    grant_number = forms.CharField(
        max_length=30, required=False, disabled=True)
    grant_end = forms.CharField(max_length=150, required=False, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)


class GrantDownloadForm(forms.Form):
    pk = forms.IntegerField(required=False, disabled=True)
    title = forms.CharField(required=False, disabled=True)
    project_pk = forms.IntegerField(required=False, disabled=True)
    pi_first_name = forms.CharField(required=False, disabled=True)
    role = forms.CharField(required=False, disabled=True)
    grant_pi = forms.CharField(required=False, disabled=True)
    total_amount_awarded = forms.FloatField(required=False, disabled=True)
    funding_agency = forms.CharField(required=False, disabled=True)
    grant_number = forms.CharField(required=False, disabled=True)
    grant_start = forms.DateField(required=False, disabled=True)
    grant_end = forms.DateField(required=False, disabled=True)
    percent_credit = forms.FloatField(required=False, disabled=True)
    direct_funding = forms.FloatField(required=False, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pk'].widget = forms.HiddenInput()
