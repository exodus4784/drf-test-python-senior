from decimal import Decimal
from django.test import Client
from rest_framework import status
import pytest

from app.models import Wallet, Transaction


@pytest.mark.django_db
@pytest.fixture
def client():
    """Creating Django client for API requests"""
    return Client()


@pytest.mark.django_db
@pytest.fixture
def transaction(request):
    wallet = Wallet.objects.create(label='test_wallet')
    return Transaction.objects.create(wallet=wallet, amount=request.param)


@pytest.mark.django_db
@pytest.fixture
def create_transactions():
    wallet = Wallet.objects.create(label='test_wallet')
    for i in range(3):
        Transaction.objects.create(wallet=wallet, amount=Decimal(10.00))


@pytest.mark.django_db
def test_transaction_list_ok(create_transactions, client, django_db_setup):
    response = client.get('/v1/transaction/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['count'] == 3
    assert list(data['results'][0].keys()) == ['id', 'amount', 'txid', 'wallet']


@pytest.mark.django_db
@pytest.mark.parametrize("transaction", (Decimal(100.00),
                                         Decimal(-100.00),
                                         Decimal(50.00)),
                         indirect=True)
def test_transaction_retrieve_ok(client, transaction, django_db_setup):
    response = client.get(f'/v1/transaction/{transaction.txid}')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {
        'amount': str(transaction.amount) + '.00',
        'id': transaction.pk,
        'txid': transaction.txid,
        'wallet': transaction.wallet_id
    }


@pytest.mark.django_db
def test_transaction_retrieve_not_found(client, django_db_setup):
    response = client.get(f'/v1/transaction/{"random_tx_id"}')
    assert response.status_code == status.HTTP_404_NOT_FOUND
