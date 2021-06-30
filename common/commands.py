import csv
from abc import abstractmethod

from django.core.management import BaseCommand
from progress.bar import Bar


class ExportCommand(BaseCommand):
    @abstractmethod
    def get_queryset(self, **options):
        pass

    @abstractmethod
    def write_header(self, writer):
        pass

    @abstractmethod
    def write_row(self, obj, writer):
        pass

    @abstractmethod
    def get_output_file_name(self):
        pass

    def get_writer(self, output_file):
        return csv.writer(output_file)

    def handle(self, *args, **options):
        output_file_name = self.get_output_file_name()

        with open(output_file_name, "w") as output_file:
            writer = self.get_writer(output_file)
            self.write_header(writer)
            queryset = self.get_queryset()
            bar = Bar("Exporting", max=queryset.count())
            for count, user in enumerate(queryset, start=1):
                self.write_row(user, writer)
                bar.next()

        self.stdout.write(f"Saved in {output_file_name}")
