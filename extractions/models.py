from django.db import models

# Create your models here.

class SdsFile(models.Model):
    md5 = models.CharField(max_length=32)
    file_path = models.CharField(max_length=500)
    md5_content = models.CharField(max_length=32, null=True)
    content = models.TextField(null=True)
    revision_date = models.DateField(null=True)
    revision_str = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sds_files'

    def __str__(self):
        return f"{self.md5} - {self.md5_content}"