from django.contrib import admin
from .models import APILog

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'direction', 'endpoint', 'method', 'status_code', 'user']
    list_filter = ['direction', 'method', 'status_code']
    search_fields = ['endpoint', 'error_message']
    readonly_fields = [f.name for f in APILog._meta.fields]
