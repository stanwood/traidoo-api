from django.core.management import BaseCommand

from documents.models import Document
from payments.mixins import MangopayMixin


class Command(MangopayMixin, BaseCommand):
    help = "Recreates expired payin for document which was not paid"

    def add_arguments(self, parser):
        parser.add_argument('payins', nargs='+', type=str)

    def handle(self, *args, **options):
        for payin in options.get('payins', []):
            response = self.mangopay.get_pay_in(payin)
            self.stdout.write(response['Tag'] + " " + response['Status'])
            try:
                document = Document.objects.get(mangopay_payin_id=str(payin))
            except Document.DoesNotExist:
                self.stdout.write("No matching document")
                continue
            self.stdout.write("Paid: {}".format(document.paid))
            if document.paid is False:
                new_payin = self.mangopay.post(
                    '/payins/bankwire/direct',
                    {
                        'Tag': response['Tag'],
                        'AuthorId': response['AuthorId'],
                        'WalletId': response['CreditedWalletId'],
                        'CreditedWalletId': response['CreditedWalletId'],
                        'DeclaredDebitedFunds': response['DeclaredDebitedFunds'],
                        "DeclaredFees": response['DeclaredFees']
                    }
                )
                self.stdout.write("Old payin {old_payin[Id]} new payin {payin[Id]} reference {payin[WireReference]}".format(
                    old_payin=response,
                    payin=new_payin)
                )
                document.mangopay_payin_id = new_payin['Id']
                document.payment_reference = new_payin['WireReference']
                document.save()
                self.stdout.write("Document updated")
