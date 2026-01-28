from viewer.models import EDFFile
# 刪除所有舊數據
EDFFile.objects.all().delete()
exit()