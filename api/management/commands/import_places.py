import csv
from django.core.management.base import BaseCommand
from api.models import Place  # Update to match your app name

class Command(BaseCommand):
    help = 'Imports places from a CSV file into the Place model'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file']
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0

            for row in reader:
                Place.objects.create(
                    name=row.get('Name', ''),
                    city=row.get('City', ''),
                    state=row.get('State', ''),
                    zone=row.get('Zone', ''),
                    type=row.get('Type', ''),
                    rating=float(row.get('Google review rating', 0) or 0),
                    entrance_fee=float(row.get('Entrance Fee in INR', 0) or 0),
                    best_time_to_visit=row.get('Best Time to visit', ''),
                    significance=row.get('Significance', ''),
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} places'))
