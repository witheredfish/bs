from django.shortcuts import render, get_object_or_404
import datetime
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms import formset_factory
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html, mark_safe
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from bs.core.allocation.forms import (AllocationAccountForm,
                                      AllocationAddUserForm,
                                      AllocationAttributeCreateForm,
                                      AllocationAttributeDeleteForm,
                                      AllocationChangeForm,
                                      AllocationChangeNoteForm,
                                      AllocationAttributeChangeForm,
                                      AllocationAttributeUpdateForm,
                                      AllocationForm,
                                      AllocationInvoiceNoteDeleteForm,
                                      AllocationInvoiceUpdateForm,
                                      AllocationRemoveUserForm,
                                      AllocationReviewUserForm,
                                      AllocationSearchForm,
                                      AllocationUpdateForm)
from bs.core.allocation.models import (Allocation,
                                       AllocationPermission,
                                       AllocationAccount,
                                       AllocationAttribute,
                                       AllocationAttributeType,
                                       AllocationChangeRequest,
                                       AllocationChangeStatusChoice,
                                       AllocationAttributeChangeRequest,
                                       AllocationStatusChoice,
                                       AllocationUser,
                                       AllocationUserNote,
                                       AllocationUserStatusChoice)
from bs.core.allocation.signals import (allocation_activate,
                                        allocation_activate_user,
                                        allocation_disable,
                                        allocation_remove_user,
                                        allocation_change_approved)
from bs.core.allocation.utils import (generate_guauge_data_from_usage,
                                      get_user_resources)
from bs.core.project.models import (Project,
                                    ProjectUser,
                                    ProjectPermission,
                                    ProjectUserStatusChoice)
from bs.core.resource.models import Resource
from bs.core.utils.common import (get_domain_url,
                                  import_from_settings)
from bs.core.utils.mail import (send_allocation_admin_email,
                                send_allocation_customer_email)

ALLOCATION_ENABLE_ALLOCATION_RENEWAL = import_from_settings(
    'ALLOCATION_ENABLE_ALLOCATION_RENEWAL', True)
ALLOCATION_DEFAULT_ALLOCATION_LENGTH = import_from_settings(
    'ALLOCATION_DEFAULT_ALLOCATION_LENGTH', 365)
ALLOCATION_ENABLE_CHANGE_REQUESTS_BY_DEFAULT = import_from_settings(
    'ALLOCATION_ENABLE_CHANGE_REQUESTS_BY_DEFAULT', True)

PROJECT_ENABLE_PROJECT_REVIEW = import_from_settings(
    'PROJECT_ENABLE_PROJECT_REVIEW', False)
INVOICE_ENABLED = import_from_settings('INVOICE_ENABLED', False)
if INVOICE_ENABLED:
    INVOICE_DEFAULT_STATUS = import_from_settings(
        'INVOICE_DEFAULT_STATUS', 'Pending Payment')

ALLOCATION_ACCOUNT_ENABLED = import_from_settings(
    'ALLOCATION_ACCOUNT_ENABLED', False)
ALLOCATION_ACCOUNT_MAPPING = import_from_settings(
    'ALLOCATION_ACCOUNT_MAPPING', {})


logger = logging.getLogger(__name__)


class AllocationDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    model = Allocation
    template_name = 'allocation/allocation_detail.html'
    context_object_name = 'allocation'

    def test_func(self):
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)

        if self.request.user.has_perm('allocation.can_view_all_allocations'):
            return True

        return allocation_obj.has_perm(self.request.user, AllocationPermission.USER)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)
        allocation_users = allocation_obj.allocationuser_set.exclude(
            status__name__in=['Removed']).order_by('user__username')

        alloc_attr_set = allocation_obj.get_attribute_set(self.request.user)
        attributes_with_usage = [
            a for a in alloc_attr_set if hasattr(a, 'allocationattributeusage')]
        attributes = alloc_attr_set

        allocation_changes = allocation_obj.allocationchangerequest_set.all().order_by('-pk')

        guage_data = []
        invalid_attributes = []
        for attribute in attributes_with_usage:
            try:
                guage_data.append(generate_guauge_data_from_usage(
                    attribute.allocation_attribute_type.name,
                    float(attribute.value),
                    float(attribute.allocationattributeusage.value)
                ))
            except ValueError:
                logger.error("属性 '%s' 不为int但是有用法",
                             attribute.allocation_attribute_type.name)
                invalid_attributes.append(attribute)

        for a in invalid_attributes:
            attributes_with_usage.remove(a)

        context['allocation_users'] = allocation_users
        context['guage_data'] = guage_data
        context['attributes_with_usage'] = attributes_with_usage
        context['attributes'] = attributes
        context['allocation_changes'] = allocation_changes

        context['is_allowed_to_update_project'] = allocation_obj.project.has_perm(
            self.request.user, ProjectPermission.UPDATE)

        noteset = allocation_obj.allocationusernote_set
        notes = noteset.all() if self.request.user.is_superuser else noteset.filter(
            is_private=False)

        context['notes'] = notes
        context['ALLOCATION_ENABLE_ALLOCATION_RENEWAL'] = ALLOCATION_ENABLE_ALLOCATION_RENEWAL
        return context

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)

        initial_data = {
            'status': allocation_obj.status,
            'end_date': allocation_obj.end_date,
            'start_date': allocation_obj.start_date,
            'description': allocation_obj.description,
            'is_locked': allocation_obj.is_locked,
            'is_changeable': allocation_obj.is_changeable,
        }

        form = AllocationUpdateForm(initial=initial_data)
        if not self.request.user.is_superuser:
            form.fields['is_locked'].disabled = True
            form.fields['is_changeable'].disabled = True

        context = self.get_context_data()
        context['form'] = form
        context['allocation'] = allocation_obj
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)
        if not self.request.user.is_superuser:
            messages.success(
                request, '你没有权限更新分配')
            return HttpResponseRedirect(reverse('allocation-detail', kwargs={'pk': pk}))

        initial_data = {
            'status': allocation_obj.status,
            'end_date': allocation_obj.end_date,
            'start_date': allocation_obj.start_date,
            'description': allocation_obj.description,
            'is_locked': allocation_obj.is_locked,
            'is_changeable': allocation_obj.is_changeable,
        }
        form = AllocationUpdateForm(request.POST, initial=initial_data)

        if not form.is_valid():
            context = self.get_context_data()
            context['form'] = form
            context['allocation'] = allocation_obj
            return render(request, self.template_name, context)

        action = request.POST.get('action')
        if action not in ['update', 'approve', 'auto-approve', 'deny']:
            return HttpResponseBadRequest("无效请求")

        form_data = form.cleaned_data

        old_status = allocation_obj.status.name

        if action in ['update', 'approve', 'deny']:
            allocation_obj.end_date = form_data.get('end_date')
            allocation_obj.start_date = form_data.get('start_date')
            allocation_obj.description = form_data.get('description')
            allocation_obj.is_locked = form_data.get('is_locked')
            allocation_obj.is_changeable = form_data.get('is_changeable')
            allocation_obj.status = form_data.get('status')

        if 'approve' in action:
            allocation_obj.status = AllocationStatusChoice.objects.get(
                name='Active')
        elif action == 'deny':
            allocation_obj.status = AllocationStatusChoice.objects.get(
                name='Denied')

        if old_status != 'Active' == allocation_obj.status.name:
            if not allocation_obj.start_date:
                allocation_obj.start_date = datetime.datetime.now()
            if 'approve' in action or not allocation_obj.end_date:
                allocation_obj.end_date = datetime.datetime.now(
                ) + relativedelta(days=ALLOCATION_DEFAULT_ALLOCATION_LENGTH)

            allocation_obj.save()

            allocation_activate.send(
                sender=self.__class__, allocation_pk=allocation_obj.pk)
            allocation_users = allocation_obj.allocationuser_set.exclude(
                status__name__in=['Removed', 'Error'])
            for allocation_user in allocation_users:
                allocation_activate_user.send(
                    sender=self.__class__, allocation_user_pk=allocation_user.pk)

            send_allocation_customer_email(allocation_obj, '分配已激活',
                                           'email/allocation_activated.txt', domain_url=get_domain_url(self.request))
            if action != 'auto-approve':
                messages.success(request, '分配已激活')

        elif old_status != allocation_obj.status.name in ['Denied', 'New', 'Revoked']:
            allocation_obj.start_date = None
            allocation_obj.end_date = None
            allocation_obj.save()

            if allocation_obj.status.name == ['Denied', 'Revoked']:
                allocation_disable.send(
                    sender=self.__class__, allocation_pk=allocation_obj.pk)
                allocation_users = allocation_obj.allocationuser_set.exclude(
                    status__name__in=['Removed', 'Error'])
                for allocation_user in allocation_users:
                    allocation_remove_user.send(
                        sender=self.__class__, allocation_user_pk=allocation_user.pk)
            if allocation_obj.status.name == 'Denied':
                send_allocation_customer_email(
                    allocation_obj, '分配已拒绝', 'email/allocation_denied.txt', domain_url=get_domain_url(self.request))
                messages.success(request, '分配已拒绝!')
            elif allocation_obj.status.name == 'Revoked':
                send_allocation_customer_email(
                    allocation_obj, '分配已撤销', 'email/allocation_revoked.txt', domain_url=get_domain_url(self.request))
                messages.success(request, '分配已撤销!')
            else:
                messages.success(request, '分配已更新!')
        else:
            messages.success(request, '分配已更新!')
            allocation_obj.save()

        if action == 'auto-approve':
            messages.success(request, '{}的分配已对{}({})激活'.format(
                allocation_obj.get_parent_resource,
                allocation_obj.project.pi.first_name,
                allocation_obj.project.pi.username)
            )
            return HttpResponseRedirect(reverse('allocation-request-list'))

        return HttpResponseRedirect(reverse('allocation-detail', kwargs={'pk': pk}))


class AllocationListView(LoginRequiredMixin, ListView):

    model = Allocation
    template_name = 'allocation/allocation_list.html'
    context_object_name = 'allocation_list'
    paginate_by = 25

    def get_queryset(self):

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            dir_dict = {'asc': '', 'des': '-'}
            order_by = dir_dict[direction] + order_by
        else:
            order_by = 'id'

        allocation_search_form = AllocationSearchForm(self.request.GET)

        if allocation_search_form.is_valid():
            data = allocation_search_form.cleaned_data

            if data.get('show_all_allocations') and (self.request.user.is_superuser or self.request.user.has_perm('allocation.can_view_all_allocations')):
                allocations = Allocation.objects.prefetch_related(
                    'project', 'project__pi', 'status',).all().order_by(order_by)
            else:
                allocations = Allocation.objects.prefetch_related('project', 'project__pi', 'status',).filter(
                    Q(project__status__name__in=['New', 'Active', ]) &
                    Q(project__projectuser__status__name='Active') &
                    Q(project__projectuser__user=self.request.user) &

                    (Q(project__projectuser__role__name='Manager') |
                     Q(allocationuser__user=self.request.user) &
                     Q(allocationuser__status__name='Active'))
                ).distinct().order_by(order_by)

            if data.get('project'):
                allocations = allocations.filter(
                    project__title__icontains=data.get('project'))

            if data.get('username'):
                allocations = allocations.filter(
                    Q(project__pi__username__icontains=data.get('username')) |
                    Q(allocationuser__user__username__icontains=data.get('username')) &
                    Q(allocationuser__status__name='Active')
                )

            if data.get('resource_type'):
                allocations = allocations.filter(
                    resources__resource_type=data.get('resource_type'))

            if data.get('resource_name'):
                allocations = allocations.filter(
                    resources__in=data.get('resource_name'))

            if data.get('allocation_attribute_name') and data.get('allocation_attribute_value'):
                allocations = allocations.filter(
                    Q(allocationattribute__allocation_attribute_type=data.get('allocation_attribute_name')) &
                    Q(allocationattribute__value=data.get(
                        'allocation_attribute_value'))
                )

            if data.get('end_date'):
                allocations = allocations.filter(end_date__lt=data.get(
                    'end_date'), status__name='Active').order_by('end_date')

            if data.get('active_from_now_until_date'):
                allocations = allocations.filter(
                    end_date__gte=date.today())
                allocations = allocations.filter(end_date__lt=data.get(
                    'active_from_now_until_date'), status__name='Active').order_by('end_date')

            if data.get('status'):
                allocations = allocations.filter(
                    status__in=data.get('status'))

        else:
            allocations = Allocation.objects.prefetch_related('project', 'project__pi', 'status',).filter(
                Q(allocationuser__user=self.request.user) &
                Q(allocationuser__status__name='Active')
            ).order_by(order_by)

        return allocations.distinct()

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        allocations_count = self.get_queryset().count()
        context['allocations_count'] = allocations_count

        allocation_search_form = AllocationSearchForm(self.request.GET)

        if allocation_search_form.is_valid():
            data = allocation_search_form.cleaned_data
            filter_parameters = ''
            for key, value in data.items():
                if value:
                    if isinstance(value, QuerySet):
                        filter_parameters += ''.join(
                            [f'{key}={ele.pk}&' for ele in value])
                    elif hasattr(value, 'pk'):
                        filter_parameters += f'{key}={value.pk}&'
                    else:
                        filter_parameters += f'{key}={value}&'
            context['allocation_search_form'] = allocation_search_form
        else:
            filter_parameters = None
            context['allocation_search_form'] = AllocationSearchForm()

        order_by = self.request.GET.get('order_by')
        if order_by:
            direction = self.request.GET.get('direction')
            filter_parameters_with_order_by = filter_parameters + \
                'order_by=%s&direction=%s&' % (order_by, direction)
        else:
            filter_parameters_with_order_by = filter_parameters

        if filter_parameters:
            context['expand_accordion'] = 'show'
        context['filter_parameters'] = filter_parameters
        context['filter_parameters_with_order_by'] = filter_parameters_with_order_by

        allocation_list = context.get('allocation_list')
        paginator = Paginator(allocation_list, self.paginate_by)

        page = self.request.GET.get('page')

        try:
            allocation_list = paginator.page(page)
        except PageNotAnInteger:
            allocation_list = paginator.page(1)
        except EmptyPage:
            allocation_list = paginator.page(paginator.num_pages)

        return context


class AllocationCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = AllocationForm
    template_name = 'allocation/allocation_create.html'

    def test_func(self):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))
        if project_obj.has_perm(self.request.user, ProjectPermission.UPDATE):
            return True

        messages.error(
            self.request, '没有权限请求新分配')
        return False

    def dispatch(self, request, *args, **kwargs):
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))

        if project_obj.needs_review:
            messages.error(
                request, '不能请求新的分配，因为你必须先审查你的项目。')
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))

        if project_obj.status.name not in ['Active', 'New', ]:
            messages.error(
                request, '不能给封存项目请求新分配')
            return HttpResponseRedirect(reverse('project-detail', kwargs={'pk': project_obj.pk}))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))
        context['project'] = project_obj

        user_resources = get_user_resources(self.request.user)
        resources_form_default_quantities = {}
        resources_form_label_texts = {}
        resources_with_eula = {}
        attr_names = ('quantity_default_value', 'quantity_label', 'eula')
        for resource in user_resources:
            for attr_name in attr_names:
                query = Q(resource_attribute_type__name=attr_name)
                if resource.resourceattribute_set.filter(query).exists():
                    value = resource.resourceattribute_set.get(query).value
                    if attr_name == 'quantity_default_value':
                        resources_form_default_quantities[resource.id] = int(
                            value)
                    if attr_name == 'quantity_label':
                        resources_form_label_texts[resource.id] = mark_safe(
                            f'<strong>{value}*</strong>')
                    if attr_name == 'eula':
                        resources_with_eula[resource.id] = value

        context['resources_form_default_quantities'] = resources_form_default_quantities
        context['resources_form_label_texts'] = resources_form_label_texts
        context['resources_with_eula'] = resources_with_eula
        context['resources_with_accounts'] = list(Resource.objects.filter(
            name__in=list(ALLOCATION_ACCOUNT_MAPPING.keys())).values_list('id', flat=True))

        return context

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.user, self.kwargs.get('project_pk'), **self.get_form_kwargs())

    def form_valid(self, form):
        form_data = form.cleaned_data
        project_obj = get_object_or_404(
            Project, pk=self.kwargs.get('project_pk'))
        resource_obj = form_data.get('resource')
        justification = form_data.get('justification')
        quantity = form_data.get('quantity', 1)
        allocation_account = form_data.get('allocation_account', None)
        if ALLOCATION_ACCOUNT_ENABLED and resource_obj.name in ALLOCATION_ACCOUNT_MAPPING and AllocationAttributeType.objects.filter(
                name=ALLOCATION_ACCOUNT_MAPPING[resource_obj.name]).exists() and not allocation_account:
            form.add_error(None, format_html(
                '您需要创建一个帐户。点击链接来创建它。'))
            return self.form_invalid(form)

        usernames = form_data.get('users')
        usernames.append(project_obj.pi.username)
        usernames = list(set(usernames))

        users = [get_user_model().objects.get(username=username)
                 for username in usernames]
        if project_obj.pi not in users:
            users.append(project_obj.pi)

        if INVOICE_ENABLED and resource_obj.requires_payment:
            allocation_status_obj = AllocationStatusChoice.objects.get(
                name=INVOICE_DEFAULT_STATUS)
        else:
            allocation_status_obj = AllocationStatusChoice.objects.get(
                name='New')

        allocation_obj = Allocation.objects.create(
            project=project_obj,
            justification=justification,
            quantity=quantity,
            status=allocation_status_obj
        )

        if ALLOCATION_ENABLE_CHANGE_REQUESTS_BY_DEFAULT:
            allocation_obj.is_changeable = True
            allocation_obj.save()

        allocation_obj.resources.add(resource_obj)

        if ALLOCATION_ACCOUNT_ENABLED and allocation_account and resource_obj.name in ALLOCATION_ACCOUNT_MAPPING:

            allocation_attribute_type_obj = AllocationAttributeType.objects.get(
                name=ALLOCATION_ACCOUNT_MAPPING[resource_obj.name])
            AllocationAttribute.objects.create(
                allocation_attribute_type=allocation_attribute_type_obj,
                allocation=allocation_obj,
                value=allocation_account
            )

        for linked_resource in resource_obj.linked_resources.all():
            allocation_obj.resources.add(linked_resource)

        allocation_user_active_status = AllocationUserStatusChoice.objects.get(
            name='Active')
        for user in users:
            AllocationUser.objects.create(allocation=allocation_obj, user=user,
                                          status=allocation_user_active_status)

        send_allocation_admin_email(allocation_obj, '新的分配请求',
                                    'email/new_allocation_request.txt', domain_url=get_domain_url(self.request))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('project_pk')})


class AllocationAddUsersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'allocation/allocation_add_users.html'

    def test_func(self):
        allocation_obj = get_object_or_404(
            Allocation, pk=self.kwargs.get('pk'))
        if allocation_obj.has_perm(self.request.user, AllocationPermission.MANAGER):
            return True

        messages.error(
            self.request, '没有权限给该分配添加人员')
        return False

    def dispatch(self, request, *args, **kwargs):
        allocation_obj = get_object_or_404(
            Allocation, pk=self.kwargs.get('pk'))

        message = None
        if allocation_obj.is_locked and not self.request.user.is_superuser:
            message = '您无法修改已锁定的分配！'
        elif allocation_obj.status.name not in ['Active', 'New', 'Renewal Requested', 'Payment Pending', 'Payment Requested', 'Paid']:
            message = f'不能以 {allocation_obj.status.name} 添加人员'
        if message:
            messages.error(request, message)
            return HttpResponseRedirect(reverse('allocation-detail', kwargs={'pk': allocation_obj.pk}))
        return super().dispatch(request, *args, **kwargs)

    def get_users_to_add(self, allocation_obj):
        active_users_in_project = list(allocation_obj.project.projectuser_set.filter(
            status__name='Active').values_list('user__username', flat=True))
        users_already_in_allocation = list(allocation_obj.allocationuser_set.exclude(
            status__name__in=['Removed']).values_list('user__username', flat=True))

        missing_users = list(set(active_users_in_project) -
                             set(users_already_in_allocation))
        missing_users = get_user_model().objects.filter(username__in=missing_users).exclude(
            pk=allocation_obj.project.pi.pk)

        users_to_add = [

            {'username': user.username,
             'first_name': user.first_name,
             'email': user.email, }

            for user in missing_users
        ]

        return users_to_add

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)

        users_to_add = self.get_users_to_add(allocation_obj)
        context = {}

        if users_to_add:
            formset = formset_factory(
                AllocationAddUserForm, max_num=len(users_to_add))
            formset = formset(initial=users_to_add, prefix='userform')
            context['formset'] = formset

        context['allocation'] = allocation_obj
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)

        users_to_add = self.get_users_to_add(allocation_obj)

        formset = formset_factory(
            AllocationAddUserForm, max_num=len(users_to_add))
        formset = formset(request.POST, initial=users_to_add,
                          prefix='userform')

        users_added_count = 0

        if formset.is_valid():

            allocation_user_active_status_choice = AllocationUserStatusChoice.objects.get(
                name='Active')

            for form in formset:
                user_form_data = form.cleaned_data
                if user_form_data['selected']:

                    users_added_count += 1

                    user_obj = get_user_model().objects.get(
                        username=user_form_data.get('username'))

                    if allocation_obj.allocationuser_set.filter(user=user_obj).exists():
                        allocation_user_obj = allocation_obj.allocationuser_set.get(
                            user=user_obj)
                        allocation_user_obj.status = allocation_user_active_status_choice
                        allocation_user_obj.save()
                    else:
                        allocation_user_obj = AllocationUser.objects.create(
                            allocation=allocation_obj, user=user_obj, status=allocation_user_active_status_choice)

                    allocation_activate_user.send(sender=self.__class__,
                                                  allocation_user_pk=allocation_user_obj.pk)

            messages.success(
                request, f'添加{users_added_count}个用户')
        else:
            for error in formset.errors:
                messages.error(request, error)

        return HttpResponseRedirect(reverse('allocation-detail', kwargs={'pk': pk}))


class AllocationRemoveUsersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'allocation/allocation_remove_users.html'

    def test_func(self):
        """ UserPassesTestMixin Tests"""
        allocation_obj = get_object_or_404(
            Allocation, pk=self.kwargs.get('pk'))
        if allocation_obj.has_perm(self.request.user, AllocationPermission.MANAGER):
            return True

        messages.error(
            self.request, 'You do not have permission to remove users from allocation.')
        return False

    def dispatch(self, request, *args, **kwargs):
        allocation_obj = get_object_or_404(
            Allocation, pk=self.kwargs.get('pk'))

        message = None
        if allocation_obj.is_locked and not self.request.user.is_superuser:
            message = 'You cannot modify this allocation because it is locked! Contact support for details.'
        elif allocation_obj.status.name not in ['Active', 'New', 'Renewal Requested', ]:
            message = f'You cannot remove users from a allocation with status {allocation_obj.status.name}.'
        if message:
            messages.error(request, message)
            return HttpResponseRedirect(reverse('allocation-detail', kwargs={'pk': allocation_obj.pk}))
        return super().dispatch(request, *args, **kwargs)

    def get_users_to_remove(self, allocation_obj):
        users_to_remove = list(allocation_obj.allocationuser_set.exclude(
            status__name__in=['Removed', 'Error', ]).values_list('user__username', flat=True))

        users_to_remove = get_user_model().objects.filter(username__in=users_to_remove).exclude(
            pk__in=[allocation_obj.project.pi.pk, self.request.user.pk])
        users_to_remove = [

            {'username': user.username,
             'first_name': user.first_name,
             'last_name': user.last_name,
             'email': user.email, }

            for user in users_to_remove
        ]

        return users_to_remove

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)

        users_to_remove = self.get_users_to_remove(allocation_obj)
        context = {}

        if users_to_remove:
            formset = formset_factory(
                AllocationRemoveUserForm, max_num=len(users_to_remove))
            formset = formset(initial=users_to_remove, prefix='userform')
            context['formset'] = formset

        context['allocation'] = allocation_obj
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        allocation_obj = get_object_or_404(Allocation, pk=pk)

        users_to_remove = self.get_users_to_remove(allocation_obj)

        formset = formset_factory(
            AllocationRemoveUserForm, max_num=len(users_to_remove))
        formset = formset(
            request.POST, initial=users_to_remove, prefix='userform')

        remove_users_count = 0

        if formset.is_valid():
            allocation_user_removed_status_choice = AllocationUserStatusChoice.objects.get(
                name='Removed')
            for form in formset:
                user_form_data = form.cleaned_data
                if user_form_data['selected']:

                    remove_users_count += 1

                    user_obj = get_user_model().objects.get(
                        username=user_form_data.get('username'))
                    if allocation_obj.project.pi == user_obj:
                        continue

                    allocation_user_obj = allocation_obj.allocationuser_set.get(
                        user=user_obj)
                    allocation_user_obj.status = allocation_user_removed_status_choice
                    allocation_user_obj.save()
                    allocation_remove_user.send(sender=self.__class__,
                                                allocation_user_pk=allocation_user_obj.pk)

            user_plural = "user" if remove_users_count == 1 else "users"
            messages.success(
                request, f'Removed {remove_users_count} {user_plural} from allocation.')
        else:
            for error in formset.errors:
                messages.error(request, error)

        return HttpResponseRedirect(reverse('allocation-detail', kwargs={'pk': pk}))
