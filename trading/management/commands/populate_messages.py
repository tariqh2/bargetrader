from django.core.management.base import BaseCommand
from trading.models import Message

class Command(BaseCommand):
    help = 'Populates the database with sample messages.'
    
    def handle(self, *args, **kwargs):
        Message.objects.create(content="Oil terminal strike announced", impact_type="bearish", impact_value=5.00)
        Message.objects.create(content="New oil reserves discovered", impact_type="bullish", impact_value=3.50)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated messages.'))
