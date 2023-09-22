import csv
from django.core.management.base import BaseCommand
from trading.models import Message

class Command(BaseCommand):
    help = 'Populates the database with messages from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file containing the messages.')
    
    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        messages_to_add = []

        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                message = Message(
                    content=row['Content'],
                    impact_type=row['Impact_Type'],
                    impact_value=float(row['Impact_Value'])
                )
                messages_to_add.append(message)
        
        # Bulk add messages to the database
        Message.objects.bulk_create(messages_to_add)
        self.stdout.write(self.style.SUCCESS('Successfully populated messages.'))
