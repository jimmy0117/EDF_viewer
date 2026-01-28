import struct
import math

def read_signal_data(file_path, signal_index, start_time=None, end_time=None, max_samples=50000, return_rate=False):
    """
    讀取 EDF 檔案中的信號數據
    """
    with open(file_path, 'rb') as f:
        # 讀取檔案頭
        header = f.read(256).decode('latin1')
        
        try:
            num_signals = int(header[252:256].strip())
            num_header_bytes = int(header[184:192].strip()) or (256 + num_signals * 256)
            num_data_records = int(header[236:244].strip())
            duration_per_record = float(header[244:252].strip())
        except (ValueError, IndexError) as e:
            raise ValueError(f"EDF header parse error: {e}")
        
        if duration_per_record <= 0:
            duration_per_record = 1.0
        
        if signal_index < 0 or signal_index >= num_signals:
            raise ValueError(f"signal_index {signal_index} out of range [0, {num_signals-1}]")
        
        header_size = num_header_bytes
        
        # 讀取每個信號的樣本數
        f.seek(256 + num_signals * (16 + 80 + 8 + 8 + 8 + 8 + 8 + 80))
        samples_per_record = []
        for i in range(num_signals):
            try:
                spr = int(f.read(8).decode('latin1').strip())
            except ValueError:
                spr = 0
            samples_per_record.append(spr)
        
        sampling_rate = samples_per_record[signal_index] / duration_per_record if duration_per_record > 0 else 1
        
        # 讀取物理最小值和最大值
        f.seek(256 + num_signals * (16 + 80 + 8))
        phys_mins = []
        for i in range(num_signals):
            try:
                pm = float(f.read(8).decode('latin1').strip())
            except ValueError:
                pm = 0.0
            phys_mins.append(pm)
        
        phys_maxs = []
        for i in range(num_signals):
            try:
                pm = float(f.read(8).decode('latin1').strip())
            except ValueError:
                pm = 0.0
            phys_maxs.append(pm)
        
        # 讀取數位最小值和最大值
        dig_mins = []
        for i in range(num_signals):
            try:
                dm = int(f.read(8).decode('latin1').strip())
            except ValueError:
                dm = 0
            dig_mins.append(dm)
        
        dig_maxs = []
        for i in range(num_signals):
            try:
                dm = int(f.read(8).decode('latin1').strip())
            except ValueError:
                dm = 0
            dig_maxs.append(dm)
        
        # 計算縮放因子
        if dig_maxs[signal_index] == dig_mins[signal_index]:
            gain = 1.0
            offset = 0.0
        else:
            gain = (phys_maxs[signal_index] - phys_mins[signal_index]) / (dig_maxs[signal_index] - dig_mins[signal_index])
            offset = phys_mins[signal_index] - gain * dig_mins[signal_index]
        
        bytes_per_record = sum(samples_per_record) * 2
        total_duration = num_data_records * duration_per_record
        
        start_time = max(0.0, start_time or 0.0)
        end_time = min(total_duration, end_time) if end_time is not None else total_duration
        
        start_record = int(start_time // duration_per_record)
        end_record = int(math.ceil(end_time / duration_per_record))
        end_record = min(end_record, num_data_records)
        
        f.seek(header_size + start_record * bytes_per_record)
        
        all_data = []
        
        # 讀取所有數據記錄
        for record in range(start_record, end_record):
            for sig in range(num_signals):
                num_samples = samples_per_record[sig]
                if sig == signal_index:
                    # 讀取目標信號數據
                    for _ in range(num_samples):
                        raw_value = struct.unpack('<h', f.read(2))[0]
                        # 轉換為物理值
                        physical_value = raw_value * gain + offset
                        all_data.append(physical_value)
                else:
                    # 跳過其他信號
                    f.seek(num_samples * 2, 1)
        
        # 下採樣
        if len(all_data) > max_samples:
            step = max(1, len(all_data) // max_samples)
            all_data = all_data[::step]
        
        if return_rate:
            return all_data, sampling_rate
        return all_data
