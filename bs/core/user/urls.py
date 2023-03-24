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
    path('logout', LogoutView.as_view(), name='logout'),
    path('user-profile/', user_views.UserProfile.as_view(), name='user-profile'),
    path('user-profile/<str:viewed_username>',
         user_views.UserProfile.as_view(), name='user-profile'),
    path('user-upgrade/', user_views.UserUpgradeAccount.as_view(), name='user-upgrade'),
    path('user-search-home/', user_views.UserSearchHome.as_view(),
         name='user-search-home'),
    path('user-search-results/', user_views.UserSearchResults.as_view(),
         name='user-search-results')
]
