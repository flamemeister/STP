from kafka import KafkaProducer
import json
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    retries=3
)

def send_event(topic, data):
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": data
    }
    try:
        print(f"📦 Отправка в Kafka ({topic}): {event}")
        producer.send(topic, event)
        producer.flush()
        print("✅ Успешно отправлено в Kafka")
    except Exception as e:
        print(f"❌ Ошибка Kafka: {e}")
