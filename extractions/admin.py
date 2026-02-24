from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import SdsFile

@admin.register(SdsFile)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("md5", "file_path", "revision_date", "revision_str", "content", "md5_content")
    search_fields = ("md5", "file_path")