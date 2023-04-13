import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from bs.core.project.models import Project


class SnakeCaseTemplateNameMixin:

    def get_template_names(self):
        def to_snake(string):

            return string[0].lower() + re.sub('([A-Z])', r'_\1', string[1:]).lower()

        app_label = self.model._meta.app_label
        model_name = self.model.__name__

        return ['{}/{}{}.html'.format(app_label, to_snake(model_name), self.template_name_suffix)]


class ProjectInContextMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['project'] = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        return context


class ChangesOnlyOnActiveProjectMixin:
    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))
        if project_obj.status.name not in ['Active', 'New', ]:
            messages.error(
                request, '不能修改存档项目')
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            return super().dispatch(request, *args, **kwargs)


class UserActiveManagerOrHigherMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True
