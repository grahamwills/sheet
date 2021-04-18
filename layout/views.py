from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils.http import urlencode

from pdf.main import create_pdf
from .forms import CreateLayoutForm, LayoutForm, SectionForm, TextStyleForm
from .models import Layout, Section, TextStyle, add_layout


def show(request):
    layout = get_object_or_404(Layout, name=(request.GET['layout']))
    request.session['last_layout'] = layout.name
    context = create_layout_context(layout, request)

    try:
        name = request.GET['style']
        return show_style(name, layout, context, request)
    except:
        pass

    try:
        name = request.GET['section']
        return show_section(name, layout, context, request)
    except:
        pass

    return show_layout(layout, context, request)


def create_layout(request):
    context = {'form': CreateLayoutForm(request.POST or None)}
    if not 'layout' in request.POST:
        return render(request, 'layout/create_layout.html',context)

    layout_name = request.POST['layout']
    unlock_key = request.POST['unlock_key']
    base_layout = request.POST['base']

    try:
        Layout.objects.get(name=layout_name)
        msg = "Character Sheet '%s' already exists, please choose another name" % layout_name
        context['error'] = msg
        return render(request, 'layout/create_layout.html', context)
    except Layout.DoesNotExist:
        add_layout(layout_name, unlock_key, base_layout)
        request.session['last_layout'] = layout_name
        base_url = reverse('show')
        query_string = urlencode({'layout': layout_name})
        url = '{}?{}'.format(base_url, query_string)
        return redirect(url)


def show_style(name, layout, context, request):
    target = get_object_or_404(TextStyle, owner=layout, name=name)
    context['style_name'] = TextStyle.Name(name).label
    form = TextStyleForm(request.POST or None, instance=target)
    if form.is_valid():
        form.save()
    context['form'] = form
    return render(request, 'layout/show_style.html', context)


def show_section(name, layout, context, request):
    target = get_object_or_404(Section, owner=layout, title=name)
    context['section_name'] = request.GET['section']
    form = SectionForm(request.POST or None, instance=target)
    if form.is_valid():
        form.save()
    context['form'] = form
    return render(request, 'layout/show_section.html', context)


def show_layout(layout, context, request):
    form = LayoutForm(request.POST or None, instance=layout)
    if form.is_valid():
        form.save()
    context['form'] = form
    return render(request, 'layout/show_layout.html', context)


def build(request):
    layout = get_object_or_404(Layout, name=request.GET['layout'])
    sections = Section.objects.filter(owner=layout)
    styles = TextStyle.objects.filter(owner=layout)

    layout_dict = model_to_dict(layout)
    del (layout_dict['unlock_key'])

    complete = {
        'layout':   to_dict(layout),
        'sections': [to_dict(o) for o in sections],
        'styles':   [to_dict(o) for o in styles]
    }

    # TODO: Fill in default styles from 'DEFAULT'

    pdf = create_pdf(complete)
    response = HttpResponse(pdf, content_type='application/pdf')
    return response


def create_layout_context(layout, request):
    owned_sections = Section.objects.filter(owner=layout)
    section_list = [{
        'name':    o.title,
        'label':   Section.Location(o.location).label,
        'content': o.content_trimmed()
    } for o in owned_sections]
    owned_styles = TextStyle.objects.filter(owner=layout)
    style_list = [{'name': o.name, 'label': TextStyle.Name(o.name).label} for o in owned_styles]
    return {'layout_name': layout.name, 'sections': section_list, 'styles': style_list}


def to_dict(obj):
    return model_to_dict(obj, exclude=['unlock_key', 'id', 'owner'])
