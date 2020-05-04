# API

## Environment

```
pipenv --python 3.7.1
pipenv shell
docker-compose up
```

## Mangopay integration

We will attempt to create bank account during daily payouts for accounts which balance is above 10 EUR. However we are going to check if user's `iban` property is set and has correct format of iban account number. The reason for that is that we after migration from noSQL we have many users with `-` as iban number. Attempts to create bank account in mangopay fail and trigger error notifications on daily basis.

## HTML2PDF backend

API depends on external html2pdf service which runs on shared instance of Google Run service.

## Mangopay admin commands

### Recreate payin

Mangopay pains may expire. Then new one should be created. Following admin command creates new payin if related order has not been paid yet:

`python manage.py recreate_payin old_payin_id`

### List transactions from user's wallet

We assume user has one wallet. This command takes user first wallet and saves all transactions to csv file:

`python manage.py list_transactions mangopay_user_id`

### Update mangopay webhooks

This command updates mangopay settings with new webhook handler, for example:

`python manage.py mangopay_webhooks https://api.example.com/mangopay/webhook`
