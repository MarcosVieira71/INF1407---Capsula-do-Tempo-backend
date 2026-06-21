from django.contrib import admin

from .models import Capsula, Usuario, ItemTexto

admin.site.register(Usuario)
admin.site.register(Capsula)
admin.site.register(ItemTexto)
