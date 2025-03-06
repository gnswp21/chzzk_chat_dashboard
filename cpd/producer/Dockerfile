FROM python:3.9-slim

WORKDIR /app

COPY kafka_producer.py /app/kafka_producer.py
COPY cookies.json /app/cookies.json
COPY temp.py /app/temp.py
COPY ChzzkChatAPI /app/ChzzkChatAPI

RUN pip install requests==2.31.0 websocket-client==1.7.0 kafka-python==2.0.3 cryptography

CMD ["python", "kafka_producer.py"]