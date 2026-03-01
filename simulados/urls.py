# simulados/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('responder/<int:questao_id>/', views.responder_questao, name='responder_questao'),
]