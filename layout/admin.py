from django.contrib import admin

from .models import Layout, Section, TextStyle

admin.site.register(Layout)
admin.site.register(TextStyle)
admin.site.register(Section)