# myapp/management/commands/audit_files.py
from django.core.management.base import BaseCommand
import hashlib
from patient_encryption.models import DocumentoRiservato, SecurityLog

class Command(BaseCommand):
    help = 'Esegue un controllo di integrità su tutti i file nel sistema'

    def handle(self, *args, **options):
        documenti = DocumentoRiservato.objects.all()
        self.stdout.write(f"Inizio audit su {documenti.count()} file...")

        for doc in documenti:
            sha256_hash = hashlib.sha256()
            try:
                with doc.file_documento.open() as f:
                    for chunk in f.chunks():
                        sha256_hash.update(chunk)
                
                if sha256_hash.hexdigest() != doc.file_hash:
                    self.stdout.write(self.style.ERROR(f"CRITICO: File ID {doc.id} corrotto!"))
                    # Registriamo l'evento nei log di sicurezza
                    SecurityLog.objects.create(evento="INTEGRITA_FALLITA_AUDIT", doc_id=doc.id, ip="127.0.0.1")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"ERRORE: Impossibile leggere file ID {doc.id}: {e}"))

        self.stdout.write(self.style.SUCCESS("Audit terminato."))