import csv
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import formset_factory
from django.http import HttpResponseRedirect, StreamingHttpResponse
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.edit import UpdateView

from bs.core.utils.common import Echo
from bs.core.grant.forms import GrantDeleteForm, GrantDownloadForm, GrantForm
from bs.core.grant.models import Grant
from bs.core.project.models import Project


class GrantCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = GrantForm
    template_name = 'grant/grant_create.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

        messages.error(
            self.request, '没有权限添加资助。')

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))
        if project_obj.status.name not in ['Active', 'New', ]:
            messages.error(
                request, '封存项目不能添加资助。')
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form_data = form.cleaned_data
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))
        grant_obj = Grant.objects.create(
            project=project_obj,
            title=form_data.get('title'),
            grant_number=form_data.get('grant_number'),
            role=form_data.get('role'),
            grant_pi_full_name=form_data.get('grant_pi_full_name'),
            funding_agency=form_data.get('funding_agency'),
            other_funding_agency=form_data.get('other_funding_agency'),
            other_award_number=form_data.get('other_award_number'),
            grant_start=form_data.get('grant_start'),
            grant_end=form_data.get('grant_end'),
            percent_credit=form_data.get('percent_credit'),
            direct_funding=form_data.get('direct_funding'),
            total_amount_awarded=form_data.get('total_amount_awarded'),
            status=form_data.get('status'),
        )

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['project'] = Project.objects.get(
            pk=self.kwargs.get('project_pk'))
        return context

    def get_success_url(self):
        messages.success(self.request, '添加成功。')
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('project_pk')})


class GrantUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    def test_func(self):
        if self.request.user.is_superuser:
            return True

        grant_obj = get_object_or_404(Grant, pk=self.kwargs.get('pk'))

        if grant_obj.project.pi == self.request.user:
            return True

        if grant_obj.project.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

        messages.error(
            self.request, '你没有权限更新项目资助')

    model = Grant
    template_name_suffix = '_update_form'
    fields = ['title', 'grant_number', 'role', 'grant_pi_full_name', 'funding_agency', 'other_funding_agency',
              'other_award_number', 'grant_start', 'grant_end', 'percent_credit', 'direct_funding', 'total_amount_awarded', 'status', ]

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.object.project.id})


class GrantDeleteGrantsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'grant/grant_delete_grants.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True

        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        if project_obj.pi == self.request.user:
            return True

        if project_obj.projectuser_set.filter(user=self.request.user, role__name='Manager', status__name='Active').exists():
            return True

        messages.error(
            self.request, '你没有权限删除项目资助')

    def get_grants_to_delete(self, project_obj):

        grants_to_delete = [

            {'title': grant.title,
             'grant_number': grant.grant_number,
             'grant_end': grant.grant_end}

            for grant in project_obj.grant_set.all()
        ]

        return grants_to_delete

    def get(self, request, *args, **kwargs):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        grants_to_delete = self.get_grants_to_delete(project_obj)
        context = {}

        if grants_to_delete:
            formset = formset_factory(
                GrantDeleteForm, max_num=len(grants_to_delete))
            formset = formset(initial=grants_to_delete, prefix='grantform')
            context['formset'] = formset

        context['project'] = project_obj
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        grants_to_delete = self.get_grants_to_delete(project_obj)
        context = {}

        formset = formset_factory(
            GrantDeleteForm, max_num=len(grants_to_delete))
        formset = formset(
            request.POST, initial=grants_to_delete, prefix='grantform')

        grants_deleted_count = 0

        if formset.is_valid():
            for form in formset:
                grant_form_data = form.cleaned_data
                if grant_form_data['selected']:

                    grant_obj = Grant.objects.get(
                        project=project_obj,
                        title=grant_form_data.get('title'),
                        grant_number=grant_form_data.get('grant_number')
                    )
                    grant_obj.delete()
                    grants_deleted_count += 1

            messages.success(
                request, '删除{}个资助'.format(grants_deleted_count))
        else:
            for error in formset.errors:
                messages.error(request, error)

        return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.object.project.id})


class GrantReportView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'grant/grant_report_list.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('grant.can_view_all_grants'):
            return True

        messages.error(
            self.request, '你没有权限查看所有资助')

    def get_grants(self):
        grants = Grant.objects.prefetch_related(
            'project', 'project__pi').all().order_by('-total_amount_awarded')
        grants = [

            {'pk': grant.pk,
             'title': grant.title,
             'project_pk': grant.project.pk,
             'pi_first_name': grant.project.pi.first_name,
             'role': grant.role,
             'grant_pi': grant.grant_pi,
             'total_amount_awarded': grant.total_amount_awarded,
             'funding_agency': grant.funding_agency,
             'grant_number': grant.grant_number,
             'grant_start': grant.grant_start,
             'grant_end': grant.grant_end,
             'percent_credit': grant.percent_credit,
             'direct_funding': grant.direct_funding,
             }
            for grant in grants
        ]

        return grants

    def get(self, request, *args, **kwargs):
        context = {}
        grants = self.get_grants()

        if grants:
            formset = formset_factory(GrantDownloadForm, max_num=len(grants))
            formset = formset(initial=grants, prefix='grantdownloadform')
            context['formset'] = formset
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        grants = self.get_grants()

        formset = formset_factory(GrantDownloadForm, max_num=len(grants))
        formset = formset(request.POST, initial=grants,
                          prefix='grantdownloadform')

        header = [
            '资助标题',
            '项目负责人',
            '角色',
            '资助负责人',
            '资助总和',
            '资助机构',
            '资助机构的授权编号',
            '开始日期',
            '结束日期',
            '信用百分比',
            '资助使用情况',
        ]
        rows = []
        grants_selected_count = 0

        if formset.is_valid():
            for form in formset:
                form_data = form.cleaned_data
                if form_data['selected']:
                    grant = get_object_or_404(Grant, pk=form_data['pk'])

                    row = [
                        grant.title,
                        grant.project.pi.first_name,
                        grant.role,
                        grant.grant_pi_full_name,
                        grant.total_amount_awarded,
                        grant.funding_agency,
                        grant.grant_number,
                        grant.grant_start,
                        grant.grant_end,
                        grant.percent_credit,
                        grant.direct_funding,
                    ]

                    rows.append(row)
                    grants_selected_count += 1

            if grants_selected_count == 0:
                grants = Grant.objects.prefetch_related(
                    'project', 'project__pi').all().order_by('-total_amount_awarded')
                for grant in grants:
                    row = [
                        grant.title,
                        grant.project.pi.first_name,
                        grant.role,
                        grant.grant_pi_full_name,
                        grant.total_amount_awarded,
                        grant.funding_agency,
                        grant.grant_number,
                        grant.grant_start,
                        grant.grant_end,
                        grant.percent_credit,
                        grant.direct_funding,
                    ]
                    rows.append(row)

            rows.insert(0, header)
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                             content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename="资助表.csv"'
            return response
        else:
            for error in formset.errors:
                messages.error(request, error)
            return HttpResponseRedirect(reverse('grant-report'))


class GrantDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = "/"

    def test_func(self):
        if self.request.user.is_superuser:
            return True

        if self.request.user.has_perm('grant.can_view_all_grants'):
            return True

        messages.error(
            self.request, '你没有权限下载所有资助')

    def get(self, request):

        header = [
            '资助标题',
            '项目负责人',
            '角色',
            '资助负责人',
            '资助总和',
            '资助机构',
            '资助机构的授权编号',
            '开始日期',
            '结束日期',
            '信用百分比',
            '资助使用情况',
        ]

        rows = []
        grants = Grant.objects.prefetch_related(
            'project', 'project__pi').all().order_by('-total_amount_awarded')
        for grant in grants:
            row = [
                grant.title,
                grant.project.pi.first_name,
                grant.role,
                grant.grant_pi_full_name,
                grant.total_amount_awarded,
                grant.funding_agency,
                grant.grant_number,
                grant.grant_start,
                grant.grant_end,
                grant.percent_credit,
                grant.direct_funding,
            ]

            rows.append(row)
        rows.insert(0, header)
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                         content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="资助表.csv"'
        return response
