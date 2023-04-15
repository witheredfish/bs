from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

import bs.core.portal.views as portal_views

admin.site.site_header = 'HPC中心管理（毕设）'
admin.site.site_title = 'HPC中心管理（毕设）'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain'), name="robots"),
    path('', portal_views.home, name='home'),
    path('center-summary', portal_views.center_summary, name='center-summary'),
    path('allocation-summary', portal_views.allocation_summary,
         name='allocation-summary'),
    path('allocation-by-fos', portal_views.allocation_by_fos,
         name='allocation-by-fos'),
    path('user/', include('bs.core.user.urls')),
    path('project/', include('bs.core.project.urls')),
    path('allocation/', include('bs.core.allocation.urls')),
    path('resource/', include('bs.core.resource.urls')),
    path('grant/', include('bs.core.grant.urls')),
    path('publication/', include('bs.core.publication.urls')),
    path('research-output/', include('bs.core.research_output.urls')),
]

if 'django_su.backends.SuBackend' in settings.AUTHENTICATION_BACKENDS:
    urlpatterns.append(path('su/', include('django_su.urls')))
