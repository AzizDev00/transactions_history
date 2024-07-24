from django.http import HttpResponseRedirect


class CurrencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'currency' in request.GET:
            request.session['currency'] = request.GET['currency']
            next_url = request.GET.get('next', request.path)
            return HttpResponseRedirect(next_url)
        
        request.currency = request.session.get('currency', 'UZS')
        response = self.get_response(request)
        return response
