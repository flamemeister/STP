from django.core.management.base import BaseCommand
from core.kafka_consumer import start_consumer  

class Command(BaseCommand):
    help = 'Run Kafka consumer to process events'

    def handle(self, *args, **kwargs):
        print("🟢 run_consumer запущен!")  
        self.stdout.write(self.style.SUCCESS("▶️ Запуск Kafka consumer..."))
        start_consumer()
