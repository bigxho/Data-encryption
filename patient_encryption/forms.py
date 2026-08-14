from django import forms
from .models import DocumentoRiservato

class DocumentoUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentoRiservato
        # Esponiamo solo i campi che l'utente deve compilare
        fields = ['codice_fiscale', 'file_documento']
        widgets = {
            'codice_fiscale': forms.TextInput(attrs={'placeholder': 'Inserisci CF', 'class': 'form-control'}),
            'file_documento': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_file_documento(self):
        file = self.cleaned_data.get('file_documento')
        if file:
            # Limite dimensione file (es. 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Il file è troppo grande! Massimo 5MB.")
            # Controllo estensioni consentite
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'jpg', 'png']:
                raise forms.ValidationError("Sono ammessi solo PDF, JPG e PNG.")
        return file
    
