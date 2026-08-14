from django.urls import path, include
from . import views

urlpatterns = [
    path('upload/', views.upload_view, name='upload_documento'),
    path('', views.lista_view, name='lista_documenti'),
    path('download/<int:doc_id>/', views.download_sicuro, name='download_sicuro'),
    path('decripta-cf/<int:doc_id>/', views.decripta_cf, name='decripta_cf'),
    #path('mfa/', include('mfa.urls')),
    
]