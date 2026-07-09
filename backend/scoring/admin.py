from django.contrib import admin

from .models import AssessmentScore


@admin.register(AssessmentScore)
class AssessmentScoreAdmin(admin.ModelAdmin):
    list_display = ("assessment", "level", "requirement_identifier", "control_id", "status", "normalized_score", "is_human_overridden")
    list_filter = ("level", "status", "is_human_overridden")
    search_fields = ("requirement_identifier", "control_id", "label")
