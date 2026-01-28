from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import EDFFile, Signal
from .forms import EDFUploadForm
from .edf_parser import parse_edf_file
import os

def index(request):
    """首頁 - 顯示已上傳的 EDF 檔案列表"""
    edf_files = EDFFile.objects.all()
    context = {
        'edf_files': edf_files,
    }
    return render(request, 'viewer/index.html', context)


@require_http_methods(["GET", "POST"])
def upload_edf(request):
    """上傳 EDF 檔案"""
    if request.method == 'POST':
        form = EDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            edf_file = form.save()
            
            # 解析 EDF 檔案
            try:
                parse_edf_file(edf_file)
                messages.success(request, f'檔案 {edf_file.title} 上傳成功！')
                return redirect('viewer:view_edf', pk=edf_file.pk)  # 加上 app_name
            except Exception as e:
                edf_file.delete()
                messages.error(request, f'解析檔案失敗：{str(e)}')
    else:
        form = EDFUploadForm()
    
    context = {'form': form}
    return render(request, 'viewer/upload.html', context)


def view_edf(request, pk):
    """檢視 EDF 檔案的信號數據"""
    edf_file = get_object_or_404(EDFFile, pk=pk)
    signals = edf_file.signals.all()
    
    context = {
        'edf_file': edf_file,
        'signals': signals,
    }
    return render(request, 'viewer/view_edf.html', context)


def signal_data(request, signal_id):
    """獲取信號數據（JSON 格式用於圖表）"""
    from django.http import JsonResponse
    signal = get_object_or_404(Signal, id=signal_id)

    start = request.GET.get('start')
    end = request.GET.get('end')

    try:
        start_time = float(start) if start is not None else None
        end_time = float(end) if end is not None else None
    except ValueError:
        start_time, end_time = None, None

    try:
        from .edf_reader import read_signal_data
        data, sampling_rate = read_signal_data(
            signal.edf_file.file.path,
            signal.signal_index,
            start_time=start_time,
            end_time=end_time,
            return_rate=True
        )
        return JsonResponse({
            'signal_label': signal.signal_label,
            'units': signal.units,
            'sampling_rate': sampling_rate,
            'data': data,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def hypnogram_data(request, pk):
    """讀取睡眠週期 annotation（onset, duration, stage）"""
    from django.http import JsonResponse
    import mne
    
    edf_file = get_object_or_404(EDFFile, pk=pk)

    if not edf_file.hypnogram_file:
        return JsonResponse({'error': 'no hypnogram file'}, status=404)

    try:
        annotations = mne.read_annotations(edf_file.hypnogram_file.path)
        
        # 睡眠階段名稱映射
        stage_mapping = {
            'Sleep stage W': 'W',
            'Sleep stage 1': 'N1',
            'Sleep stage 2': 'N2',
            'Sleep stage 3': 'N3',
            'Sleep stage 4': 'N3',
            'Sleep stage R': 'REM',
            'Sleep stage ?': 'unknown',
            'W': 'W',
            'N1': 'N1',
            'N2': 'N2',
            'N3': 'N3',
            'REM': 'REM',
            '1': 'N1',
            '2': 'N2',
            '3': 'N3',
            'R': 'REM',
        }
        
        hypnogram_data = []
        unique_stages = set()
        
        for onset, duration, description in zip(annotations.onset, annotations.duration, annotations.description):
            stage = stage_mapping.get(description, description.split()[-1] if 'Sleep stage' in description else description)
            unique_stages.add(description)
            hypnogram_data.append({
                'onset': float(onset),
                'duration': float(duration),
                'stage': stage
            })
        
        print(f"Unique stage descriptions found: {unique_stages}")
        print(f"Sample mapped stages: {[s['stage'] for s in hypnogram_data[:10]]}")
        
        main_edf = edf_file
        total_duration = main_edf.duration
        
        return JsonResponse({
            'data': hypnogram_data,
            'total_duration': float(total_duration),
            'num_segments': len(hypnogram_data),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'{type(e).__name__}: {str(e)}'}, status=400)
