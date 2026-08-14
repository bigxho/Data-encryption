from django.http import HttpResponseForbidden
from django_ratelimit.exceptions import Ratelimited

class RatelimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            return HttpResponseForbidden("Troppi tentativi di accesso. Riprova tra 5 minuti per la tua sicurezza.")