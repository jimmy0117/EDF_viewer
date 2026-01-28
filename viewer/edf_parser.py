import struct
from datetime import datetime
from django.utils import timezone
from .models import Signal

def parse_edf_file(edf_file_obj):
    """解析 EDF 檔案並儲存元數據和信號信息"""
    file_path = edf_file_obj.file.path
    
    with open(file_path, 'rb') as f:
        # 讀取 EDF 檔案頭（256 bytes）
        header = f.read(256).decode('latin1')
        
        # 解析基本信息
        version = header[0:8].strip()
        patient_info = header[8:88].strip()
        recording_info = header[88:168].strip()
        start_date = header[168:176].strip()
        start_time = header[176:184].strip()
        num_header_bytes = int(header[184:192].strip())
        reserved = header[192:236].strip()
        num_data_records = int(header[236:244].strip())
        try:
            duration_per_record = float(header[244:252].strip())
            if duration_per_record <= 0:
                duration_per_record = 1.0
        except ValueError:
            duration_per_record = 1.0
        num_signals = int(header[252:256].strip())
        
        # 計算總時長（秒）
        total_duration = num_data_records * duration_per_record
        
        # 更新 EDF 物件
        edf_file_obj.patient_name = patient_info[:50]
        edf_file_obj.num_signals = num_signals
        edf_file_obj.duration = total_duration
        
        # 解析開始時間
        try:
            rec_date = datetime.strptime(f"{start_date} {start_time}", "%d.%m.%y %H.%M.%S")
            edf_file_obj.recording_date = timezone.make_aware(rec_date)
        except:
            pass
        
        edf_file_obj.save()
        
        # 讀取信號標籤部分（每個信號 16 bytes）
        signal_labels = []
        f.seek(256)
        for i in range(num_signals):
            label = f.read(16).decode('latin1').strip()
            signal_labels.append(label)
        
        # 讀取轉換器信息
        transducers = []
        for i in range(num_signals):
            transducer = f.read(80).decode('latin1').strip()
            transducers.append(transducer)
        
        # 讀取物理單位
        physical_dims = []
        for i in range(num_signals):
            phys_dim = f.read(8).decode('latin1').strip()
            physical_dims.append(phys_dim)
        
        # 讀取物理最小值
        phys_mins = []
        for i in range(num_signals):
            phys_min = float(f.read(8).decode('latin1').strip())
            phys_mins.append(phys_min)
        
        # 讀取物理最大值
        phys_maxs = []
        for i in range(num_signals):
            phys_max = float(f.read(8).decode('latin1').strip())
            phys_maxs.append(phys_max)
        
        # 讀取數位最小值
        dig_mins = []
        for i in range(num_signals):
            dig_min = int(f.read(8).decode('latin1').strip())
            dig_mins.append(dig_min)
        
        # 讀取數位最大值
        dig_maxs = []
        for i in range(num_signals):
            dig_max = int(f.read(8).decode('latin1').strip())
            dig_maxs.append(dig_max)
        
        # 讀取預濾波信息
        prefilters = []
        for i in range(num_signals):
            prefilter = f.read(80).decode('latin1').strip()
            prefilters.append(prefilter)
        
        # 讀取每筆錄音中的樣本數
        samples_per_record = []
        for i in range(num_signals):
            spr = int(f.read(8).decode('latin1').strip())
            samples_per_record.append(spr)
        
        # 計算採樣率
        for i in range(num_signals):
            sampling_rate = samples_per_record[i] / duration_per_record
            
            Signal.objects.create(
                edf_file=edf_file_obj,
                signal_index=i,  # 新增：保存索引
                signal_label=signal_labels[i],
                transducer=transducers[i],
                units=physical_dims[i],
                physical_min=phys_mins[i],
                physical_max=phys_maxs[i],
                sampling_rate=sampling_rate,
            )
