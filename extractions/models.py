from django.db import models

# Create your models here.

class SdsFile(models.Model):
    md5 = models.CharField(max_length=32, unique=True)
    file_path = models.CharField(max_length=500)
    md5_content = models.CharField(max_length=32)
    content = models.TextField()
    version_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.md5} - {self.file_path}"