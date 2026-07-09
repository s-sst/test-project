from django.contrib import admin

from .models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ("id", "assessment", "report_format", "status", "generated_at")
    list_filter = ("report_format", "status")
    search_fields = ("assessment__id",)
