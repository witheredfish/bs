import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import BooleanField, Prefetch
from django.db.models.expressions import ExpressionWrapper, F, Q
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, TemplateView

from bs.core.utils.common import import_from_settings
from bs.core.utils.mail import send_email_template
from bs.core.user.forms import UserSearchForm
from bs.core.user.utils import CombinedUserSearch
from bs.core.project.models import Project, ProjectUser

logger = logging.getLogger(__name__)
EMAIL_ENABLED = import_from_settings('EMAIL_ENABLED', False)
if EMAIL_ENABLED:
    EMAIL_TICKET_SYSTEM_ADDRESS = import_from_settings(
        'EMAIL_TICKET_SYSTEM_ADDRESS')


@method_decorator(login_required, name='dispatch')
class UserProfile(TemplateView):
    template_name = 'user/user_profile.html'

    def dispatch(self, request, *args, viewed_username=None, **kwargs):
        if viewed_username:
            if request.user.is_superuser or request.user.is_staff:
                pass
            else:
                if not request.user.username == viewed_username:
                    messages.error(request, "你没有权限查看他人个人中心！！！")

                return HttpResponseRedirect(reverse('user-profile'))

        return super().dispatch(request, *args, viewed_username=viewed_username, ** kwargs)

    def get_context_data(self, viewed_username=None, **kwargs):
        context = super().get_context_data(**kwargs)

        if viewed_username:
            viewed_user = get_object_or_404(User, username=viewed_username)
        else:
            viewed_user = self.request.user

        group_list = ','.join(
            [group.name for group in viewed_user.groups.all()])
        context['group_list'] = group_list
        context['viewed_user'] = viewed_user
        return context


@method_decorator(login_required, name='dispatch')
class UserUpgradeAccount(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            messages.error(request, '你已为超级用户，不需要升级。')
            return HttpResponseRedirect(reverse('user-profile'))

        if request.user.userprofile.is_pi:
            messages.error(request, '你已为项目管理员，不需要升级。')
            return HttpResponseRedirect(reverse('user-profile'))

        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        if EMAIL_ENABLED:
            send_email_template(
                '账户升级请求',
                'email/upgrade_account_request.text',
                {'user': request.user},
                request.user.email,
                [EMAIL_TICKET_SYSTEM_ADDRESS]
            )

        messages.success(request, '请求发送成功')
        return HttpResponseRedirect(reverse('user-profile'))


class UserSearchHome(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'user/user_search_home.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['user_search_form'] = UserSearchForm()
        return context


class UserSearchResults(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'user/user_search_results.html'
    raise_exception = True

    def post(self, request):
        user_search_string = request.POST.get('q')

        search_by = request.POST.get('search_by')

        search_result = CombinedUserSearch(user_search_string, search_by)
        context = search_result.search()

        return render(request, self.template_name, context)

    def test_func(self):
        return self.request.user.is_staff


@method_decorator(login_required, name='dispatch')
class UserProjectsManagersView(ListView):
    template_name = 'user/user_projects_managers.html'

    def dispatch(self, request, *args, viewed_username=None, **kwargs):
        if viewed_username:
            if request.user.is_superuser or request.user.is_staff:
                pass
            else:

                if not request.user.username == viewed_username:
                    messages.error(
                        request, "你不能查看其他用户的项目！")

                return HttpResponseRedirect(reverse('user-projects-managers'))

        if viewed_username:
            self.viewed_user = get_object_or_404(
                User, username=viewed_username)
        else:
            self.viewed_user = self.request.user

        return super().dispatch(request, *args, viewed_username=viewed_username, **kwargs)

    def get_queryset(self, *args, **kwargs):
        viewed_user = self.viewed_user

        ongoing_projectuser_statuses = (
            'Active',
            'Pending - Add',
            'Pending - Remove',
        )
        ongoing_project_statuses = (
            'New',
            'Active',
        )

        qs = ProjectUser.objects.filter(
            user=viewed_user,
            status__name__in=ongoing_projectuser_statuses,
            project__status__name__in=ongoing_project_statuses,
        ).select_related(
            'status',
            'role',
            'project',
            'project__status',
            'project__field_of_science',
            'project__pi',
        ).only(
            'status__name',
            'role__name',
            'project__title',
            'project__status__name',
            'project__field_of_science__description',
            'project__pi__username',
            'project__pi__first_name',
            'project__pi__last_name',
            'project__pi__email',
        ).annotate(
            is_project_pi=ExpressionWrapper(
                Q(user=F('project__pi')),
                output_field=BooleanField(),
            ),
            is_project_manager=ExpressionWrapper(
                Q(role__name='Manager'),
                output_field=BooleanField(),
            ),
        ).order_by(
            '-is_project_pi',
            '-is_project_manager',
            Lower('project__pi__username').asc(),
            Lower('project__title').asc(),
            '-project__pk',
        ).prefetch_related(
            Prefetch(
                lookup='project__projectuser_set',
                queryset=ProjectUser.objects.filter(
                    role__name='Manager',
                    status__name__in=ongoing_projectuser_statuses,
                ).exclude(
                    user__pk__in=[
                        F('project__pi__pk'),
                        viewed_user.pk,
                    ],
                ).select_related(
                    'status',
                    'user',
                ).only(
                    'status__name',
                    'user__username',
                    'user__first_name',
                    'user__last_name',
                    'user__email',
                ).order_by(
                    'user__username',
                ),
                to_attr='project_managers',
            ),
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['viewed_user'] = self.viewed_user

        if self.request.user == self.viewed_user:
            context['user_pronounish'] = 'You'
            context['user_verbform_be'] = 'are'
        else:
            context['user_pronounish'] = 'This user'
            context['user_verbform_be'] = 'is'

        return context


class UserListAllocations(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'user/user_list_allocations.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.userprofile.is_pi

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        user_dict = {}

        for project in Project.objects.filter(pi=self.request.user):
            for allocation in project.allocation_set.filter(status__name='Active'):
                for allocation_user in allocation.allocationuser_set.filter(status__name='Active').order_by('user__username'):
                    if allocation_user.user not in user_dict:
                        user_dict[allocation_user.user] = []

                    user_dict[allocation_user.user].append(allocation)

        context['user_dict'] = user_dict

        return context
