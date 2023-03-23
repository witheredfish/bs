from django.contrib import admin
from django.contrib.auth.models import User
from bs.core.user.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'is_pi')
    list_filter = ('is_pi',)
    search_fields = ['user__username', 'user__first_name',]

    def username(self, obj):
        return obj.user.username
    username.short_description = '用户名'

    def first_name(self, obj):
        return obj.user.first_name
    first_name.short_description = '姓名'
