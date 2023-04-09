from django.urls import path

import bs.core.project.views as project_views

urlpatterns = [
    path('<int:pk>/', project_views.ProjectDetailView.as_view(),
         name='project-detail'),
]
