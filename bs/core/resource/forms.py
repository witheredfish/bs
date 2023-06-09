from django import forms

from bs.core.resource.models import ResourceAttribute
from django.db.models.functions import Lower


class ResourceSearchForm(forms.Form):
    model = forms.CharField(
        label='类型', max_length=100, required=False)
    serialNumber = forms.CharField(
        label='序号', max_length=100, required=False)
    vendor = forms.CharField(
        label='供应商', max_length=100, required=False)
    installDate = forms.DateField(
        label='安装日期',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    serviceStart = forms.DateField(
        label='开始日期',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    serviceEnd = forms.DateField(
        label='结束日期',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    warrantyExpirationDate = forms.DateField(
        label='保修日期',
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False)
    show_allocatable_resources = forms.BooleanField(
        initial=False, required=False, label="显示所有可分配资源")


class ResourceAttributeDeleteForm(forms.Form):
    pk = forms.IntegerField(required=False, disabled=True)
    name = forms.CharField(max_length=150, required=False, disabled=True)
    value = forms.CharField(max_length=150, required=False, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pk'].widget = forms.HiddenInput()


class ResourceAttributeCreateForm(forms.ModelForm):
    class Meta:
        model = ResourceAttribute
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ResourceAttributeCreateForm, self).__init__(*args, **kwargs)
        self.fields['resource_attribute_type'].queryset = self.fields['resource_attribute_type'].queryset.order_by(
            Lower('name'))
