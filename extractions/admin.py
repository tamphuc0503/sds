from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import SdsFile

@admin.register(SdsFile)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("md5", "file_path", "version_date")
    search_fields = ("md5", "file_path")