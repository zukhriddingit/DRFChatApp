from django.contrib import admin
from .models import *
# Registering models Message and Chat to access through django admin panel in browser
admin.site.register(Message)
admin.site.register(Chat)