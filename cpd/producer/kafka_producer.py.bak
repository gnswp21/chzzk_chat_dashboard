import json
import time
from kafka import KafkaProducer

# KafkaProducer는 docker-compose 상에서 kafka 컨테이너의 호스트명("kafka")를 사용합니다.
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_message(name, chat):
    message = {"name": name, "chat": chat}
    producer.send('tst', value=message)
    producer.flush()
    print(f"Sent: {message}")

if __name__ == "__main__":
    counter = 0
    while True:
        counter += 1
        # 예시 메시지: 이름과 채팅 내용을 변경할 수 있습니다.
        name = f"User{counter}"
        chat = f"Hello, this is message {counter}"
        send_message(name, chat)
        time.sleep(2)  # 2초 간격으로 메시지 전송
