from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from bs.core.research_output.models import ResearchOutput

_research_output_fields_for_end = [
    'created_by', 'project', 'created', 'modified']


@admin.register(ResearchOutput)
class ResearchOutputAdmin(SimpleHistoryAdmin):
    list_display = [
        field.name for field in ResearchOutput._meta.get_fields()
        if field.name not in _research_output_fields_for_end
    ] + _research_output_fields_for_end
    list_filter = (
        'project',
        'created_by',
    )
    ordering = (
        'project',
        '-created',
    )

    readonly_fields = [
        field.name for field in ResearchOutput._meta.get_fields()
        if not field.editable
    ]

    def has_add_permission(self, request):
        return False
