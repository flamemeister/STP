# /app/core/kafka_producer.py
import json
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

_producer = None

def get_producer(retries=10, delay=5):
    global _producer
    if _producer is not None:
        return _producer

    for attempt in range(retries):
        try:
            _producer = KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=3
            )
            return _producer
        except NoBrokersAvailable:
            print(f"⏳ Попытка {attempt+1}/{retries}: Kafka не готова. Повтор через {delay} сек...")
            time.sleep(delay)
    
    raise NoBrokersAvailable("Kafka не готова после всех попыток")

from datetime import datetime

def send_event(topic, data, user=None):
    if user:
        data["user"] = str(user)

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": data
    }

    try:
        producer = get_producer()
        print(f"📦 Отправка в Kafka ({topic}): {event}")
        producer.send(topic, event)
        producer.flush()
        print("✅ Успешно отправлено в Kafka")
    except Exception as e:
        print(f"❌ Ошибка Kafka: {e}")

