from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

import bs.core.portal.views as portal_views

admin.site.site_header = 'HPC中心管理（毕设）'
admin.site.site_title = 'HPC中心管理（毕设）'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('bs.core.user.urls')),
    path('', portal_views.home, name='home'),
]

if 'django_su.backends.SuBackend' in settings.AUTHENTICATION_BACKENDS:
    urlpatterns.append(path('su/', include('django_su.urls')))
