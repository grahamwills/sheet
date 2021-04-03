from django.shortcuts import render

from layout.forms import StartForm


def index(request):
    default_name = request.session.get('last_layout', 'DEFAULT')
    form = StartForm(initial={'layout': default_name})
    return render(request, 'view/index.html', {'form': form})
