from django import forms
from django.utils.html import mark_safe


class UserSearchForm(forms.Form):
    CHOICES = [
        ('username_only', '用户名查找'),
        ('all_fields', mark_safe(
            '所有字段查找<span class="text-secondary">（如果使用多个用户名进行查找，这项参数将会被忽略。）</span>'))
    ]
    q = forms.CharField(label='搜索内容', min_length=2,
                        widget=forms.Textarea(attrs={'rows': 4}), help_text='输入多个用户名并以空格间隔，可以搜索多个用户名。')

    search_by = forms.ChoiceField(
        choices=CHOICES, widget=forms.RadioSelect(), initial='username_only', label='搜索方式')
