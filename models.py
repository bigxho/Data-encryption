import os, uuid
import hashlib
from django.db import models
from django.contrib.auth.models import User
from fernet_fields import EncryptedCharField # Per il CF e dati sensibili
from cryptography.fernet import Fernet
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta


def secure_rename(instance, filename):
    ext = filename.split('.')[-1]
    return f"docs/{timezone.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}.{ext}"


class DocumentoRiservato(models.Model):
    # Relazione con l'utente (chi possiede il file)
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documenti')
    codice_fiscale = EncryptedCharField(max_length=16, help_text="Criptato nel database")
    file_documento = models.FileField(upload_to=secure_rename)
    
    # Metadati per la sicurezza
    file_hash = models.CharField(max_length=64, editable=False) # SHA-256
    caricato_il = models.DateTimeField(auto_now_add=True)
    download_effettuati = models.IntegerField(default=0)
    limite_download = models.IntegerField(default=5)
    
    
    @property
    def download_rimanenti(self):
        """Restituisce il numero di download ancora disponibili"""
        return max(0, self.limite_download - self.download_effettuati)

    @property
    def percentuale_consumata(self):
        """Calcola la percentuale di download effettuati per la barra di progresso"""
        if self.limite_download <= 0:
            return 100
        # Calcoliamo la percentuale e ci assicuriamo che non superi 100
        percent = (self.download_effettuati / self.limite_download) * 100
        return min(100, int(percent))


    class Meta:
        verbose_name = "Documento Riservato"
        verbose_name_plural = "Documenti Riservati"

    def save(self, *args, **kwargs):
        """
        Ciclo di salvataggio blindato: 
        1. Calcola l'hash del file originale.
        2. Cripta il contenuto del file in AES-256 (Fernet).
        3. Salva tutto nel DB e nello Storage.
        """
        if self.file_documento and not self.pk: # Esegui solo al primo caricamento
            # 1. Recupera la chiave Fernet dal tuo .env
            key = os.getenv('FERNET_KEY').encode()
            if not key:
                raise ValueError("FERNET_KEY non trovata nelle variabili d'ambiente!")
            f = Fernet(key)

            # 2. Leggi il contenuto originale
            self.file_documento.open('rb')
            file_content = self.file_documento.read()

            # 3. Calcola l'impronta digitale (SHA-256) dell'originale
            #self.file_hash = hashlib.sha256(file_content).hexdigest()
            self.file_hash = hashlib.sha256(file_content).hexdigest()
            
            # 4. Cripta il contenuto
            encrypted_content = f.encrypt(file_content)

            # 5. Sostituisci il file nel buffer di Django con la versione criptata
            file_name = self.file_documento.name
            self.file_documento.save (file_name, ContentFile(encrypted_content), save=False)
            self.file_documento.close()
        super().save(*args, **kwargs)
        

    def __str__(self):
        return f"Doc_{self.id} - {self.utente.username}"


# models.py

@property
def percentuale_consumata(self):
    """Calcola la percentuale di download effettuati per la barra di progresso"""
    if self.limite_download <= 0:
        return 100
    # Calcoliamo la percentuale e ci assicuriamo che non superi 100
    percent = (self.download_effettuati / self.limite_download) * 100
    return min(100, int(percent))

@property
def download_rimanenti(self):
    """Restituisce il numero di download ancora disponibili"""
    return max(0, self.limite_download - self.download_effettuati)

@property
def width_style(self):
    return f"width: {self.percentuale_consumata}%"


@property
def download_effettuati_neg(self):
    # Usato per il trucco dell'addizione nel template (|add)
    return -self.download_effettuati  

class SecurityLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    utente = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    evento = models.CharField(max_length=50)
    ip = models.GenericIPAddressField()
    doc_id = models.IntegerField(null=True)