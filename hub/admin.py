
from django.contrib import admin
from .models import (
    UploadedFile, 
    AnalysisResult,
    RetailFile,
    ChatMessage
)

# Register your models here.
admin.site.register(UploadedFile)
admin.site.register(AnalysisResult)
admin.site.register(RetailFile)
admin.site.register(ChatMessage)