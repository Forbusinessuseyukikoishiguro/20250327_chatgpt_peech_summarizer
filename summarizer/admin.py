from django.contrib import admin
from .models import Summary


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "input_type", "created_at")
    list_filter = ("input_type", "created_at")
    search_fields = ("title", "original_text", "summary_text")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("基本情報", {"fields": ("title", "input_type", "created_at")}),
        ("入力情報", {"fields": ("url", "uploaded_file", "original_text")}),
        ("処理結果", {"fields": ("summary_text", "audio_file")}),
    )
