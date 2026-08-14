import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import DocumentoRiservato, SecurityLog
from .forms import DocumentoUploadForm
import hashlib
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from cryptography.fernet import Fernet
from django.core.cache import cache
import os



def get_client_ip(request):
    """Utility per estrarre l'IP dell'utente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def upload_view(request):
    if request.method == 'POST':
        form = DocumentoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.utente = request.user
            
            # Calcolo hash prima del salvataggio definitivo
            sha = hashlib.sha256()
            for chunk in request.FILES['file_documento'].chunks():
                sha.update(chunk)
            doc.file_hash = sha.hexdigest()
            
            doc.save()
            return redirect('lista_documenti')
    return render(request, 'patient_encryption/upload_file.html', {'form': DocumentoUploadForm()})

#************************************************************************************

@login_required
def download_sicuro(request, doc_id):
    """
    Versione Debug:
    - Controllo permessi.
    - Controllo limiti su Database (al posto di Redis).
    - Decriptazione Fernet.
    """
    # 1. Recupero documento e controllo proprietà
    doc = get_object_or_404(DocumentoRiservato, id=doc_id, utente=request.user)
    cache_key = f"dl_limit_{request.user.id}_{doc.id}"
    ip = request.META.get('REMOTE_ADDR')

    # 1. Controlli Accesso
    if doc.utente != request.user and not request.user.is_staff:
        SecurityLog.objects.create(utente=request.user, evento="NEGATO", ip=ip, doc_id=doc_id)
        return HttpResponseForbidden("Accesso negato.")


    # 2. Controllo Limiti Download tramite Database
    # In debug usiamo direttamente il campo del modello che abbiamo creato
    if doc.download_effettuati >= doc.limite_download:
        return HttpResponseForbidden(
            f"Limite raggiunto: hai già scaricato questo file {doc.download_effettuati} volte."
        )

    # 3. Decriptazione in Memoria
    try:
        # Recupera la chiave dal tuo settings o .env
        fernet_key = os.getenv('FERNET_KEY')
        if not fernet_key:
            return HttpResponseForbidden("Configurazione Errata: Chiave FERNET_KEY non trovata.")
        
        f = Fernet(fernet_key.encode())

        # Legge il file (che nel modello abbiamo salvato criptato nel metodo save)
        encrypted_content = doc.file_documento.read()
        decrypted_content = f.decrypt(encrypted_content)

    except Exception as e:
        # Se la chiave è cambiata o il file non è criptato, darà errore qui
        return HttpResponseForbidden(f"Errore di decriptazione: {str(e)}")

    # 4. Aggiornamento Contatore (Database)
    doc.download_effettuati += 1
    doc.save()

    # 5. Risposta HTTP
    response = HttpResponse(decrypted_content, content_type='application/octet-stream')
    
    # Puliamo il nome del file per l'utente
    original_name = os.path.basename(doc.file_documento.name)
    response['Content-Disposition'] = f'attachment; filename="{original_name}"'
    
    return response
#************************************************************************************

class SafeLoginView(LoginView):
    template_name = 'registration/login.html'

    # 'ip' usa l'indirizzo del client
    # '5/5m' significa 5 richieste ogni 5 minuti
    # 'block=True' lancia un'eccezione Ratelimited se superato
    @method_decorator(ratelimit(key='ip', rate='5/5m', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
def download_file(request, doc_id):
    doc = get_object_or_404(DocumentoRiservato, id=doc_id, utente=request.user)
    
    # Verifica limite download
    if doc.download_effettuati >= doc.limite_download:
        return HttpResponseForbidden("Limite raggiunto.")

    # Decriptazione al volo
    f = Fernet(os.getenv('FERNET_KEY').encode())
    encrypted_data = doc.file_documento.read()
    decrypted_data = f.decrypt(encrypted_data)

    # Incrementa contatore
    doc.download_effettuati += 1
    doc.save()

    response = HttpResponse(decrypted_data, content_type='application/pdf') # o il tipo corretto
    response['Content-Disposition'] = f'attachment; filename="documento_sicuro.pdf"'
    return response


@login_required
def lista_view(request):
    # Vediamo solo i documenti dell'utente loggato
    documenti = DocumentoRiservato.objects.filter(utente=request.user)
    return render(request, 'patient_encryption/list_file.html', {'documenti': documenti})




@login_required
def decripta_cf(request, doc_id):
    # Recuperiamo il documento assicurandoci che appartenga all'utente
    doc = get_object_or_404(DocumentoRiservato, id=doc_id, utente=request.user)
    
    # Restituiamo semplicemente il campo. Django-fernet-fields 
    # si occupa della decriptazione automatica quando accediamo alla proprietà.
    return HttpResponse(doc.codice_fiscale)

    
"""
from mfa.models import UserKeys

@login_required
def dashboard_sicurezza(request):
    # Recuperiamo tutte le chiavi WebAuthn registrate dall'utente
    chiavi_biometriche = UserKeys.objects.filter(username=request.user.username, key_type="WebAuthn")
    
    context = {
        'chiavi': chiavi_biometriche,
        'documenti_recenti': DocumentoRiservato.objects.filter(utente=request.user).order_by('-caricato_il')[:5]
    }
    return render(request, 'dashboard_sicurezza.html', context)

"""


