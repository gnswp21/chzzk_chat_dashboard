FROM bitnami/spark:latest

WORKDIR /app

# 복사할 Spark Streaming 애플리케이션 코드
COPY spark_streaming_consumer.py /app/spark_streaming_consumer.py

# 필요한 Python 라이브러리 설치: pymysql, pymongo
RUN pip install pymysql pymongo cryptography

# spark-submit 실행 시 Kafka 커넥터 패키지를 포함합니다.
CMD ["/opt/bitnami/spark/bin/spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1", "/app/spark_streaming_consumer.py"]
