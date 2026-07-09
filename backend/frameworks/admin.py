from django.contrib import admin

from .models import Framework, Requirement


class RequirementInline(admin.TabularInline):
    model = Requirement
    extra = 0
    fields = ("identifier", "title", "weight", "category", "control_group")
    readonly_fields = fields
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "version", "requirement_count", "control_count", "is_active", "synced_at")
    list_filter = ("is_active", "category", "publisher")
    search_fields = ("id", "name")
    readonly_fields = ("config_hash", "raw_config", "scoring_config", "synced_at", "requirement_count", "control_count")
    inlines = [RequirementInline]


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ("identifier", "framework", "weight", "category", "control_group")
    list_filter = ("framework", "category", "weight")
    search_fields = ("identifier", "title", "description")
