from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, ListView

from bs.core.project.models import Project
from bs.core.research_output.forms import ResearchOutputForm
from bs.core.research_output.models import ResearchOutput
from bs.core.utils.mixins.views import (UserActiveManagerOrHigherMixin,
                                        ChangesOnlyOnActiveProjectMixin,
                                        ProjectInContextMixin,
                                        SnakeCaseTemplateNameMixin,)


class ResearchOutputCreateView(UserActiveManagerOrHigherMixin,
                               ChangesOnlyOnActiveProjectMixin,
                               SuccessMessageMixin,
                               SnakeCaseTemplateNameMixin,
                               ProjectInContextMixin,
                               CreateView):

    form_class = ResearchOutputForm

    model = ResearchOutput
    template_name_suffix = '_create'

    success_message = '研究成果添加成功'

    def form_valid(self, form):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.project = project_obj

        self.object = obj

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('project_pk')})


class ResearchOutputDeleteResearchOutputsView(UserActiveManagerOrHigherMixin,
                                              ChangesOnlyOnActiveProjectMixin,
                                              SnakeCaseTemplateNameMixin,
                                              ProjectInContextMixin,
                                              ListView
                                              ):

    model = ResearchOutput
    template_name_suffix = '_delete_research_outputs'

    def get_queryset(self):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        return ResearchOutput.objects.filter(project=project_obj).order_by('-created')

    def post(self, request, *args, **kwargs):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        def get_normalized_posted_pks():
            posted_pks = set(request.POST.keys())
            posted_pks.remove('csrfmiddlewaretoken')
            return {int(x) for x in posted_pks}

        project_research_outputs = self.get_queryset()

        project_research_output_pks = set(
            project_research_outputs.values_list('pk', flat=True))
        posted_research_output_pks = get_normalized_posted_pks()

        if not posted_research_output_pks:
            messages.error(request, '请选择研究成果')
            return HttpResponseRedirect(request.path_info)

        if not project_research_output_pks >= posted_research_output_pks:
            raise PermissionDenied("尝试删除其他研究成果")

        num_deletions, _ = project_research_outputs.filter(
            pk__in=posted_research_output_pks).delete()

        msg = '删除 {} 个研究成果'.format(
            num_deletions,)
        messages.success(request, msg)

        return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
