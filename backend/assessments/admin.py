from django.contrib import admin

from .models import Assessment, Evidence


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("id", "framework", "status", "overall_score", "risk_level", "created_by", "created_at")
    list_filter = ("status", "framework", "risk_level")
    search_fields = ("id", "name")
    readonly_fields = ("config_snapshot", "summary", "created_at", "updated_at", "started_at", "completed_at")
    filter_horizontal = ("documents",)


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("requirement_identifier", "assessment", "page", "verified", "confidence")
    list_filter = ("verified", "verification_method")
    search_fields = ("requirement_identifier", "quote")
