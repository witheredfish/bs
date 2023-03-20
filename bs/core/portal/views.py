from django.shortcuts import render


def home(request):

    context = {}
    if request.user.is_authenticated:
        template_name = 'portal/authorized_home.html'
