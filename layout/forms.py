from django import forms
from django.forms import PasswordInput

from .models import TextStyle, Layout, Section


class StartForm(forms.Form):
    layout = forms.CharField(label="Sheet Name:", max_length=80)


class CreateLayoutForm(forms.Form):
    layout = forms.CharField(label="Sheet Name:", max_length=80)
    unlock_key = forms.CharField(label="Unlock Code:", max_length=80, widget=PasswordInput)


class LayoutNameForm(forms.ModelForm):
    class Meta:
        model = Layout
        fields = ['name']


class LayoutForm(forms.ModelForm):
    class Meta:
        model = Layout
        fields = ['width', 'height', 'margin', 'padding']


class TextStyleForm(forms.ModelForm):
    class Meta:
        model = TextStyle
        fields = ['font', 'size', 'color', 'align', 'suffix']


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['title', 'location', 'order', 'columns',
                  'fill_color', 'border_color',
                  'text_style', 'key_style', 'line_spacing', 'content',
                  'image'
                  ]
