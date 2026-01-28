from django.contrib import admin
from .models import EDFFile, Signal


@admin.register(EDFFile)
class EDFFileAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient_name', 'uploaded_at', 'num_signals', 'duration']
    search_fields = ['title', 'patient_name']
    list_filter = ['uploaded_at']


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ['signal_label', 'edf_file', 'units', 'sampling_rate']
    search_fields = ['signal_label', 'edf_file__title']
    list_filter = ['edf_file']
