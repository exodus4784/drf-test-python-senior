from decimal import Decimal
from django.db.models import Sum
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
def create_wallets():
    for i in range(3):
        Wallet.objects.create(label=f'test_wallet_{i}')


@pytest.mark.django_db
def test_wallets_list_ok(client, django_db_setup, create_wallets):
    response = client.get('/v1/wallet/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['count'] == 3
    assert list(data['results'][0].keys()) == ['id', 'label', 'balance']


@pytest.mark.django_db
def test_wallet_create_has_wallet_w_same_label(client, django_db_setup, create_wallets):
    response = client.post('/v1/wallet/', data={'label': Wallet.objects.last().label})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data == {'label': {'label': 'Wallet with that label already exists'}}


@pytest.mark.django_db
def test_wallet_create_ok(client, django_db_setup, create_wallets):
    response = client.post('/v1/wallet/', data={'label': 'new_test_label'})
    assert response.status_code == status.HTTP_201_CREATED
    assert Wallet.objects.filter(label='new_test_label').exists()


@pytest.mark.django_db
def test_wallet_retrieve_ok(client, django_db_setup, create_wallets):
    wallet = Wallet.objects.last()
    response = client.get(f'/v1/wallet/{wallet.pk}/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {'balance': str(wallet.balance), 'id': wallet.pk, 'label': wallet.label}


@pytest.mark.django_db
def test_wallet_retrieve_not_found(client, django_db_setup, create_wallets):
    response = client.get(f'/v1/wallet/{666}/')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_wallet_update_label_ok(client, django_db_setup, create_wallets):
    wallet = Wallet.objects.last()
    response = client.patch(
        f'/v1/wallet/{wallet.pk}/',
        data={'label': 'new test label'},
        content_type='application/json',
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {'balance': str(wallet.balance), 'id': wallet.pk, 'label': 'new test label'}


@pytest.mark.django_db
def test_wallet_update_label_not_found(client, django_db_setup, create_wallets):
    response = client.patch(
        f'/v1/wallet/{666}/',
        data={'label': 'new test label'},
        content_type='application/json',
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_wallet_deposit_ok(client, django_db_setup, create_wallets):
    wallet = Wallet.objects.last()
    old_balance = wallet.balance
    response = client.post(
        f'/v1/wallet/deposit/',
        data={'amount': Decimal('100'), 'wallet_id': wallet.pk},
    )
    assert response.status_code == status.HTTP_201_CREATED
    wallet.refresh_from_db()
    assert wallet.balance == old_balance + Decimal('100')


@pytest.mark.django_db
def test_wallet_deposit_no_wallet(client, django_db_setup, create_wallets):
    response = client.post(
        f'/v1/wallet/deposit/',
        data={'amount': Decimal('100'), 'wallet_id': 666},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data == {'wallet_id': ['Such wallet does not exist']}


@pytest.mark.django_db
def test_wallet_withdraw_ok(client, django_db_setup, create_wallets):
    wallet = Wallet.objects.last()
    old_balance = Decimal('1000')
    wallet.balance = old_balance
    wallet.save(update_fields=['balance', ])
    response = client.post(
        f'/v1/wallet/withdraw/',
        data={'amount': Decimal('10'), 'wallet_id': wallet.pk},
    )
    assert response.status_code == status.HTTP_201_CREATED
    wallet.refresh_from_db()
    assert wallet.balance == old_balance - Decimal('10')


@pytest.mark.django_db
def test_wallet_withdraw_no_funds(client, django_db_setup, create_wallets):
    wallet = Wallet.objects.last()
    old_balance = Decimal('0')
    wallet.balance = old_balance
    wallet.save(update_fields=['balance', ])
    response = client.post(
        f'/v1/wallet/withdraw/',
        data={'amount': Decimal('90'), 'wallet_id': wallet.pk},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data == {'amount': 'Not enough funds to make withdrawal'}


@pytest.mark.django_db
def test_wallet_withdraw_no_wallet(client, django_db_setup, create_wallets):
    response = client.post(
        f'/v1/wallet/withdraw/',
        data={'amount': Decimal('50'), 'wallet_id': 777},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data == {'wallet_id': ['Such wallet does not exist']}


@pytest.mark.django_db
def test_balance_transaction_amount(client, django_db_setup, create_wallets):
    wallet = Wallet.objects.first()
    client.post(f'/v1/wallet/deposit/', data={'amount': Decimal('1000'), 'wallet_id': wallet.pk})
    client.post(f'/v1/wallet/deposit/', data={'amount': Decimal('99'), 'wallet_id': wallet.pk})
    client.post(f'/v1/wallet/deposit/', data={'amount': Decimal('40'), 'wallet_id': wallet.pk})
    client.post(f'/v1/wallet/withdraw/', data={'amount': Decimal('14'), 'wallet_id': wallet.pk})
    client.post(f'/v1/wallet/withdraw/', data={'amount': Decimal('2000'), 'wallet_id': wallet.pk})
    wallet.refresh_from_db()
    transactions_sum_amount = Transaction.objects.filter(wallet=wallet).aggregate(Sum('amount'))
    assert wallet.balance == transactions_sum_amount['amount__sum']
