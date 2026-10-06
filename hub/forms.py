from django import forms
# Import all the models we need for our forms
from .models import UploadedFile, RetailFile 
from django.core.validators import FileExtensionValidator

# This is the form for the Feedback Analyzer
class FileUploadForm(forms.ModelForm):
    file = forms.FileField(
        label='File',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'csv', 'xlsx'])
        ],
        widget=forms.ClearableFileInput(attrs={
            'accept': '.pdf, .csv, .xlsx',
            'class': 'form-control'
        })
    )

    class Meta:
        model = UploadedFile
        fields = ['file']

# This is the new form for the Retail Insight Engine
class RetailFileUploadForm(forms.ModelForm):
    file = forms.FileField(
        label='Upload Retail Data',
        validators=[
            FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])
        ],
        widget=forms.ClearableFileInput(attrs={
            'accept': '.csv, .xlsx',
            'class': 'form-control'
        })
    )

    class Meta:
        model = RetailFile # This will now work because of the import
        fields = ['file']
        