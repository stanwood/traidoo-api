import json

from django.core.management import BaseCommand

from payments.mixins import MangopayMixin


class Command(MangopayMixin, BaseCommand):

    help = "Sets mangopay webhooks handlers"

    def add_arguments(self, parser):
        parser.add_argument('handler_url', type=str)

    def handle(self, *args, **options):
        new_hook = options['handler_url']
        hooks = self.mangopay.get('/hooks')
        for hook in hooks:
            self.stdout.write(json.dumps(hook))
            result = self.mangopay.put(
                '/hooks/{}'.format(hook['Id']),
                params={
                    'Url': new_hook
                },
            )
            self.stdout.write(json.dumps(result))

