from django.views.generic import FormView, TemplateView
from django.http import (HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpResponseBadRequest,
    QueryDict, JsonResponse)
from django.contrib.auth.models import User
from plaid_app.models import Account, Transaction, Item_table
from .palid_task import update_account, update_transaction
# from celery import app as celery_app
from plaid_app.plaid_setting import get_exchange_token, get_link_token



def format_error(e):
  return {'error': {'display_message': e.display_message, 'error_code': e.code, 'error_type': e.type, 'error_message': e.message } }


class Bmplaid(TemplateView):
    
    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse('Unauthorized', status=401)
        # user = User.find(...)
        client_user_id = request.user.id    #user.id
        # Create a link_token for the given user
        response = get_link_token(client_user_id)
        print(response)
        link_token = response['link_token']
        return  HttpResponse(link_token) #JsonResponse(response)


    

class link_page(TemplateView):
    
    template_name = 'plaid_form.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")
        return super().get(request)
    
    def post(self, request):
        public_token = request.POST['public_token']
        exchange_response, is_err = get_exchange_token(public_token)
        if is_err:
            return JsonResponse(exchange_response)
        # pretty_print_response(exchange_response)
        print(exchange_response)
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']
        request.session['access_token'] = access_token
        request.session['item_id'] = item_id
        acc_user = Item_table(user_id=request.user.id, item_id= item_id, access_token=access_token)
        acc_user.save()
        update_account.delay(request.user.id, item_id, access_token)
        update_transaction.delay(request.user.id, item_id, access_token)
        return JsonResponse(exchange_response)
    

class AccountHandler(TemplateView):
    
    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponseBadRequest()
        # import ipdb; ipdb.set_trace()

        data = Account.objects.filter(user_id=request.user.id)
        return JsonResponse(data)

class TransactionHandler(TemplateView):
    
    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponseBadRequest()
        # import ipdb; ipdb.set_trace()
        
        data = Transaction.objects.filter(user_id=request.user.id)
        return JsonResponse(data)
    

    
