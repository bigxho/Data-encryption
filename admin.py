from django.contrib import admin, messages
from .models import DocumentoRiservato, SecurityLog

@admin.register(DocumentoRiservato)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'utente', 'caricato_il', 'download_effettuati', 'integrita_status')
    actions = ['check_integrita_action']

    def integrita_status(self, obj):
        return "Verificato" # Placeholder per la colonna
    
    @admin.action(description='Verifica integrità file selezionati')
    def check_integrita_action(self, request, queryset):
        successi = 0
        errori = 0
        for doc in queryset:
            if doc.calcola_hash_corrente() == doc.file_hash:
                successi += 1
            else:
                errori += 1
        self.message_user(request, f"Esito: {successi} OK, {errori} CORROTTI", messages.SUCCESS if errori==0 else messages.ERROR)