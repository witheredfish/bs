from django.forms import ModelForm

from bs.core.research_output.models import ResearchOutput


class ResearchOutputForm(ModelForm):
    class Meta:
        model = ResearchOutput
        exclude = ['project', ]
