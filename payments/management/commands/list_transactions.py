import csv
import datetime

from django.core.management import BaseCommand

from payments.mixins import MangopayMixin


class Command(MangopayMixin, BaseCommand):
    help = "Dumps transactions from payments"

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        if not user_id:
            return

        user_wallet = self.get_user_wallet(user_id)
        wallet_id = user_wallet['Id']
        output_file_name = f'transactions_{user_id}_{wallet_id}.csv'
        with open(output_file_name, 'w') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(
                ('id', 'tag', 'created', 'author', 'credited_user', 'debited', 'credited', 'status', 'executed', 'type')
            )
            for count, transaction in enumerate(self.mangopay.wallet_transactions(wallet_id), start=1):
                try:
                    execution_date = datetime.datetime.fromtimestamp(transaction['ExecutionDate']).strftime('%Y-%m-%d')
                except TypeError:
                    execution_date = 'None'

                row = [
                        transaction['Id'],
                        transaction['Tag'],
                        datetime.datetime.fromtimestamp(transaction['CreationDate']).strftime('%Y-%m-%d'),
                        transaction['AuthorId'],
                        transaction['CreditedUserId'],
                        str(transaction['DebitedFunds']['Amount']),
                        str(transaction['CreditedFunds']['Amount']),
                        transaction['Status'],
                        execution_date,
                        transaction['Type'],
                    ]
                writer.writerow(row)

        print(f'{count} transactions written to {output_file_name}')
