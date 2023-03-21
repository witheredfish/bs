import operator

from django.conf import settings
from django.shortcuts import render


def home(request):

    context = {}
    if request.user.is_authenticated:
        template_name = 'portal/authorized_home.html'

        try:
            context['ondemand_url'] = settings.ONDEMAND_URL
        except AttributeError:
            pass
    else:
        template_name = 'portal/nonauthorized_home.html'

    context['EXTRA_APPS'] = settings.INSTALLED_APPS

    return render(request, template_name, context)
