from kafka import KafkaProducer
from kafka.errors import KafkaError

import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka 브로커 및 토픽 설정
BROKER = "my-cluster-kafka-brokers.kafka.svc.cluster.local:9092"
TOPIC = "debug-topic"
MESSAGE = "debug-msg"

# Kafka 프로듀서 생성
producer = KafkaProducer(bootstrap_servers=[BROKER])

def on_success(metadata):
    logging.info(f"메시지 전송 성공: topic={metadata.topic}, partition={metadata.partition}, offset={metadata.offset}")

def on_error(ex):
    logging.error(f"메시지 전송 실패: {ex}")

# 메시지 전송 및 결과 확인
future = producer.send(TOPIC, MESSAGE.encode('utf-8'))
future.add_callback(on_success)
future.add_errback(on_error)

# 메시지 플러시 및 종료
producer.flush()
producer.close()