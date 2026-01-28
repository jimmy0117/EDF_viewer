from django.db import models
from django.core.validators import FileExtensionValidator

class EDFFile(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='edf_files/',
        validators=[FileExtensionValidator(allowed_extensions=['edf'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # EDF 元數據
    patient_name = models.CharField(max_length=255, blank=True)
    recording_date = models.DateTimeField(null=True, blank=True)
    num_signals = models.IntegerField(default=0)
    duration = models.FloatField(default=0)  # 秒數

    # 新增：睡眠週期 EDF
    hypnogram_file = models.FileField(
        upload_to='edf_hypnogram/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['edf'])]
    )
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title


class Signal(models.Model):
    edf_file = models.ForeignKey(EDFFile, on_delete=models.CASCADE, related_name='signals')
    signal_index = models.IntegerField(default=0)  # 新增：在 EDF 檔案中的索引
    signal_label = models.CharField(max_length=255)
    transducer = models.CharField(max_length=255, blank=True)
    units = models.CharField(max_length=50, blank=True)
    physical_min = models.FloatField()
    physical_max = models.FloatField()
    sampling_rate = models.FloatField()
    
    class Meta:
        ordering = ['signal_index']  # 改用 signal_index 排序
    
    def __str__(self):
        return f"{self.edf_file.title} - {self.signal_label}"
