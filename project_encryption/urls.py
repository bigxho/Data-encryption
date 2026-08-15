from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from paz_enc.views import SafeLoginView # La nostra vista con Rate Limit

urlpatterns = [
    # Area Amministrativa
    path('admin/', admin.site.urls, name='admin'),

    # Autenticazione Avanzata
    path('login/', SafeLoginView.as_view(), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Modulo MFA (WebAuthn / Biometria)
    # Gestisce automaticamente: /mfa/register, /mfa/authenticate, ecc.
    #path('mfa/', include('mfa.urls')),
    # Rotte dell'Applicazione Documenti
    path('', include('patient_encryption.urls')),
]
