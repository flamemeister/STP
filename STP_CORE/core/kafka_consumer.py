from confluent_kafka import Consumer, KafkaException
import json
import os
import time

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
GROUP_ID = "django-consumer-group"

def start_consumer(retries=10, delay=5):
    for attempt in range(retries):
        try:
            consumer = Consumer({
                'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
                'group.id': GROUP_ID,
                'auto.offset.reset': 'earliest'
            })

            consumer.subscribe(["eta_predictions", "proxy_calls"])
            print("✅ Kafka Consumer подключён и слушает топики.")
            break

        except KafkaException as e:
            print(f"❌ Попытка {attempt + 1}/{retries}: Kafka недоступна: {e}")
            time.sleep(delay)
    else:
        raise RuntimeError("Kafka не доступна после всех попыток подключения")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"❌ Consumer error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode('utf-8'))
                print(f"📨 Получено сообщение из {msg.topic()}: {data}")

            except Exception as e:
                print(f"❌ Ошибка обработки сообщения: {e}")

    except KeyboardInterrupt:
        print("⛔ Consumer остановлен пользователем")
    finally:
        consumer.close()
