from decimal import Decimal

import pytest

from app.exceptions import InsufficientFundsException
from app.models import Wallet, Transaction
from app.utils import deposit_process, withdraw_process


@pytest.mark.django_db
@pytest.fixture
def wallet():
    return Wallet.objects.create(label='test_wallet')


@pytest.mark.django_db
def test_deposit_process_ok(django_db_setup, wallet):
    deposit_process(
        wallet_id=wallet.pk,
        amount=Decimal('100'),
    )
    wallet.refresh_from_db()
    assert wallet.balance == Decimal('100')
    assert Transaction.objects.filter(wallet=wallet, amount=Decimal('100')).exists()


@pytest.mark.django_db
def test_withdraw_process_ok(wallet, django_db_setup):
    deposit_process(
        wallet_id=wallet.pk,
        amount=Decimal('100'),
    )
    wallet.refresh_from_db()
    assert wallet.balance == Decimal('100')
    withdraw_process(
        wallet_id=wallet.pk,
        amount=Decimal('50'),
    )
    wallet.refresh_from_db()
    assert wallet.balance == Decimal('50')
    assert Transaction.objects.filter(wallet=wallet, amount=Decimal('100')).exists()
    assert Transaction.objects.filter(wallet=wallet, amount=Decimal('-50')).exists()


@pytest.mark.django_db
def test_withdraw_insufficient_funds(wallet, django_db_setup):
    with pytest.raises(InsufficientFundsException):
        withdraw_process(
            wallet_id=wallet.pk,
            amount=Decimal('50'),
        )