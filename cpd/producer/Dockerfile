FROM python:3.9-slim

WORKDIR /app

COPY kafka_producer.py /app/kafka_producer.py

RUN pip install kafka-python cryptography

CMD ["python", "kafka_producer.py"]