from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy

import bs.core.user.views as user_views

EXTRA_APPS = settings.INSTALLED_APPS

urlpatterns = [
    path('login',
         LoginView.as_view(
             template_name='user/login.html',
             extra_context={'EXTRA_APPS': EXTRA_APPS},
             redirect_authenticated_user=True),
         name='login'
         ),
]
