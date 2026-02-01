import struct
import math
from functools import lru_cache

# 文件快取：避免重複打開同一個文件
_file_cache = {}

def read_signal_data(file_path, signal_index, start_time=None, end_time=None, max_samples=10000, return_rate=False):
    """
    讀取 EDF 檔案中的信號數據（優化版本）
    使用增量讀取，避免一次性載入大量數據
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
        
        # 讀取樣本數配置
        samples_per_record = _read_samples_per_record(f, num_signals, num_header_bytes)
        
        if samples_per_record[signal_index] == 0:
            raise ValueError(f"Signal {signal_index} has no samples")
        
        sampling_rate = samples_per_record[signal_index] / duration_per_record
        
        # 讀取縮放參數
        phys_mins = _read_physical_mins(f, num_signals, num_header_bytes)
        phys_maxs = _read_physical_maxs(f, num_signals, num_header_bytes)
        dig_mins = _read_digital_mins(f, num_signals, num_header_bytes)
        dig_maxs = _read_digital_maxs(f, num_signals, num_header_bytes)
        
        # 計算縮放因子
        if dig_maxs[signal_index] == dig_mins[signal_index]:
            gain = 1.0
            offset = 0.0
        else:
            gain = (phys_maxs[signal_index] - phys_mins[signal_index]) / (dig_maxs[signal_index] - dig_mins[signal_index])
            offset = phys_mins[signal_index] - gain * dig_mins[signal_index]
        
        bytes_per_record = sum(samples_per_record) * 2
        total_duration = num_data_records * duration_per_record
        
        # 限制請求範圍
        start_time = max(0.0, start_time or 0.0)
        end_time = min(total_duration, end_time) if end_time is not None else total_duration
        
        # 計算記錄範圍
        start_record = int(start_time // duration_per_record)
        end_record = int(math.ceil(end_time / duration_per_record))
        end_record = min(end_record, num_data_records)
        
        # 計算每條記錄內的樣本偏移
        samples_before_target = sum(samples_per_record[:signal_index])
        target_samples = samples_per_record[signal_index]
        
        # 讀取數據（優化版本）
        all_data = []
        try:
            for record in range(start_record, end_record):
                f.seek(num_header_bytes + record * bytes_per_record + samples_before_target * 2)
                
                for _ in range(target_samples):
                    try:
                        raw_value = struct.unpack('<h', f.read(2))[0]
                        physical_value = raw_value * gain + offset
                        all_data.append(physical_value)
                    except struct.error:
                        break
        except Exception as e:
            print(f"Error reading signal data: {e}")
        
        # 下採樣 - 只在必要時進行
        if len(all_data) > max_samples:
            step = max(1, len(all_data) // max_samples)
            all_data = all_data[::step]
        
        if return_rate:
            return all_data, sampling_rate
        return all_data


def _read_samples_per_record(f, num_signals, num_header_bytes):
    """讀取每筆錄音中的樣本數"""
    offset = 256 + num_signals * (16 + 80 + 8 + 8 + 8 + 8 + 8 + 80)
    f.seek(offset)
    samples = []
    for i in range(num_signals):
        try:
            spr = int(f.read(8).decode('latin1').strip())
        except ValueError:
            spr = 0
        samples.append(spr)
    return samples


def _read_physical_mins(f, num_signals, num_header_bytes):
    """讀取物理最小值"""
    offset = 256 + num_signals * (16 + 80 + 8)
    f.seek(offset)
    values = []
    for i in range(num_signals):
        try:
            val = float(f.read(8).decode('latin1').strip())
        except ValueError:
            val = 0.0
        values.append(val)
    return values


def _read_physical_maxs(f, num_signals, num_header_bytes):
    """讀取物理最大值"""
    offset = 256 + num_signals * (16 + 80 + 8 + 8)
    f.seek(offset)
    values = []
    for i in range(num_signals):
        try:
            val = float(f.read(8).decode('latin1').strip())
        except ValueError:
            val = 0.0
        values.append(val)
    return values


def _read_digital_mins(f, num_signals, num_header_bytes):
    """讀取數位最小值"""
    offset = 256 + num_signals * (16 + 80 + 8 + 8 + 8)
    f.seek(offset)
    values = []
    for i in range(num_signals):
        try:
            val = int(f.read(8).decode('latin1').strip())
        except ValueError:
            val = 0
        values.append(val)
    return values


def _read_digital_maxs(f, num_signals, num_header_bytes):
    """讀取數位最大值"""
    offset = 256 + num_signals * (16 + 80 + 8 + 8 + 8 + 8)
    f.seek(offset)
    values = []
    for i in range(num_signals):
        try:
            val = int(f.read(8).decode('latin1').strip())
        except ValueError:
            val = 0
        values.append(val)
    return values
