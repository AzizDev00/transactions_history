from .models import AccountBalance

def account_balance(request):
    if request.user.is_authenticated:
        account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
        return {'balance': account_balance.balance}
    return {}
