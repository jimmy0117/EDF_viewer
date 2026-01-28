from django import forms
from .models import EDFFile

class EDFUploadForm(forms.ModelForm):
    class Meta:
        model = EDFFile
        fields = ['title', 'file', 'hypnogram_file']  # 新增
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '輸入檔案標題'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.edf'
            }),
            'hypnogram_file': forms.FileInput(attrs={  # 新增
                'class': 'form-control',
                'accept': '.edf'
            }),
        }
