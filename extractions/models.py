from django.db import models

# Create your models here.

class SdsFile(models.Model):
    class Language(models.TextChoices):
        # Languages supported by langdetect library (55 languages)
        AFRIKAANS = 'af', 'Afrikaans'
        ARABIC = 'ar', 'Arabic'
        BULGARIAN = 'bg', 'Bulgarian'
        BENGALI = 'bn', 'Bengali'
        CATALAN = 'ca', 'Catalan'
        CZECH = 'cs', 'Czech'
        WELSH = 'cy', 'Welsh'
        DANISH = 'da', 'Danish'
        GERMAN = 'de', 'German'
        GREEK = 'el', 'Greek'
        ENGLISH = 'en', 'English'
        ESPERANTO = 'eo', 'Esperanto'
        SPANISH = 'es', 'Spanish'
        ESTONIAN = 'et', 'Estonian'
        PERSIAN = 'fa', 'Persian'
        FINNISH = 'fi', 'Finnish'
        FRENCH = 'fr', 'French'
        GUJARATI = 'gu', 'Gujarati'
        HEBREW = 'he', 'Hebrew'
        HINDI = 'hi', 'Hindi'
        CROATIAN = 'hr', 'Croatian'
        HUNGARIAN = 'hu', 'Hungarian'
        INDONESIAN = 'id', 'Indonesian'
        ITALIAN = 'it', 'Italian'
        JAPANESE = 'ja', 'Japanese'
        KANNADA = 'kn', 'Kannada'
        KOREAN = 'ko', 'Korean'
        LITHUANIAN = 'lt', 'Lithuanian'
        LATVIAN = 'lv', 'Latvian'
        MACEDONIAN = 'mk', 'Macedonian'
        MALAYALAM = 'ml', 'Malayalam'
        MARATHI = 'mr', 'Marathi'
        NEPALI = 'ne', 'Nepali'
        DUTCH = 'nl', 'Dutch'
        NORWEGIAN = 'no', 'Norwegian'
        PUNJABI = 'pa', 'Punjabi'
        POLISH = 'pl', 'Polish'
        PORTUGUESE = 'pt', 'Portuguese'
        ROMANIAN = 'ro', 'Romanian'
        RUSSIAN = 'ru', 'Russian'
        SLOVAK = 'sk', 'Slovak'
        SLOVENIAN = 'sl', 'Slovenian'
        SOMALI = 'so', 'Somali'
        ALBANIAN = 'sq', 'Albanian'
        SWEDISH = 'sv', 'Swedish'
        SWAHILI = 'sw', 'Swahili'
        TAMIL = 'ta', 'Tamil'
        TELUGU = 'te', 'Telugu'
        THAI = 'th', 'Thai'
        TAGALOG = 'tl', 'Tagalog'
        TURKISH = 'tr', 'Turkish'
        UKRAINIAN = 'uk', 'Ukrainian'
        URDU = 'ur', 'Urdu'
        VIETNAMESE = 'vi', 'Vietnamese'
        CHINESE_SIMPLIFIED = 'zh-cn', 'Chinese (Simplified)'
        CHINESE_TRADITIONAL = 'zh-tw', 'Chinese (Traditional)'
    
    md5 = models.CharField(max_length=32)
    file_path = models.CharField(max_length=500)
    md5_content = models.CharField(max_length=32, null=True)
    content = models.TextField(null=True)
    language = models.CharField(max_length=5, choices=Language.choices, null=True, blank=True)
    revision_date = models.DateField(null=True)
    revision_str = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sds_files'

    def __str__(self):
        return f"{self.md5} - {self.md5_content}"