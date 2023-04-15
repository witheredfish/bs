from django import forms

from bs.core.publication.models import PublicationSource


class PublicationAddForm(forms.Form):
    title = forms.CharField(max_length=1024, required=True, label="标题")
    author = forms.CharField(max_length=1024, required=True, label="作者")
    year = forms.IntegerField(
        min_value=1500, max_value=2090, required=True, label="年份")
    journal = forms.CharField(max_length=1024, required=True, label="期刊")
    source = forms.CharField(widget=forms.HiddenInput(), label="来源")


class PublicationSearchForm(forms.Form):
    search_id = forms.CharField(
        label='搜索ID', widget=forms.Textarea, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['search_id'].help_text = '<br/>输入ID，例如 DOI 或书目代码进行搜索。'


class PublicationResultForm(forms.Form):
    title = forms.CharField(max_length=1024, disabled=True)
    author = forms.CharField(disabled=True)
    year = forms.CharField(max_length=4, disabled=True)
    journal = forms.CharField(max_length=1024, disabled=True)
    unique_id = forms.CharField(max_length=255, disabled=True)
    source_pk = forms.IntegerField(widget=forms.HiddenInput(), disabled=True)
    selected = forms.BooleanField(initial=False, required=False)


class PublicationDeleteForm(forms.Form):
    title = forms.CharField(max_length=255, disabled=True)
    year = forms.CharField(max_length=30, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)


class PublicationExportForm(forms.Form):
    title = forms.CharField(max_length=255, disabled=True)
    year = forms.CharField(max_length=30, disabled=True)
    unique_id = forms.CharField(max_length=255, disabled=True)
    selected = forms.BooleanField(initial=False, required=False)
