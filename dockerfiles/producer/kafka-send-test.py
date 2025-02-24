from kafka import KafkaProducer

kafka_broker = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=[kafka_broker])
topic = 'debug-topic'
msg = 'debug-msg'

producer.send(topic, msg.encode('utf-8'))
producer.flush()
