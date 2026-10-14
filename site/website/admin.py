from django.contrib import admin

from .models import ConsultRequest


@admin.register(ConsultRequest)
class ConsultRequestAdmin(admin.ModelAdmin):
    list_display = ["email", "created_at", "handled"]
    list_filter = ["handled"]
    search_fields = ["email"]
    readonly_fields = ["email", "created_at", "remote_addr", "user_agent"]
    list_editable = ["handled"]
