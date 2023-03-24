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
