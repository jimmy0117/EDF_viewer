from django.urls import path
from . import views

app_name = 'viewer'  # 確認這行存在

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_edf, name='upload_edf'),
    path('edf/<int:pk>/', views.view_edf, name='view_edf'),
    path('signal/<int:signal_id>/data/', views.signal_data, name='signal_data'),
    path('edf/<int:pk>/hypnogram/', views.hypnogram_data, name='hypnogram_data'),
]
