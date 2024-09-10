from decimal import Decimal
from django.db.transaction import atomic

from app.exceptions import InsufficientFundsException
from app.models import Wallet


@atomic
def deposit_process(wallet_id: int, amount: Decimal):
    wallet = Wallet.objects.select_for_update().get(pk=wallet_id)
    wallet.balance_plus(amount=amount)


@atomic
def withdraw_process(wallet_id: int, amount: Decimal):
    wallet = Wallet.objects.select_for_update().get(pk=wallet_id)
    if wallet.balance - amount < 0:
        raise InsufficientFundsException()
    wallet.balance_minus(amount=amount)
