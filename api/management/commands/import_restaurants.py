# import_restaurants.py
import csv
from django.core.management.base import BaseCommand
from api.models import Restaurant

class Command(BaseCommand):
    help = 'Import restaurants from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file']
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0

            for row in reader:
                Restaurant.objects.create(
                    name=row.get('res', ''),
                    location=row.get('Location', ''),
                    locality=row.get('Locality', ''),
                    city=row.get('City', ''),
                    cuisine=row.get('Cuisine', ''),
                    rating=float(row.get('Rating') or 0),
                    votes=int(row.get('Votes') or 0),
                    cost=float(row.get('Cost') or 0)
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} restaurants'))
