from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

admin.site.site_header = 'HPC中心管理（毕设）'
admin.site.site_title = 'HPC中心管理（毕设）'

urlpatterns = [
    path('admin/', admin.site.urls)
]
