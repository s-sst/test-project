from django.contrib import admin

from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("title", "assessment", "priority", "priority_rank", "status", "requirement_identifier")
    list_filter = ("priority", "status", "category")
    search_fields = ("title", "description", "requirement_identifier")
