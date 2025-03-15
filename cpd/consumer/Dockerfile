FROM bitnami/spark:3.5

# 빌드 시에는 root로 실행
USER root

WORKDIR /app

# 시스템 전역에 설치하도록 --no-cache-dir 옵션과 함께 설치
RUN pip install --no-cache-dir pymysql pymongo cryptography DBUtils

ENV HOME=/opt/bitnami/spark

# Spark Streaming 애플리케이션 코드 복사
COPY spark_streaming_consumer.py /app/spark_streaming_consumer.py

# Ivy 캐시 디렉토리 생성 및 권한 부여
RUN mkdir -p /opt/bitnami/spark/.ivy2/cache /opt/bitnami/spark/.ivy2/jars \
    && chmod -R 777 /opt/bitnami/spark/.ivy2

RUN chmod -R 777 /app

RUN adduser --disabled-password --gecos '' --uid 1001 sparkuser

USER sparkuser

# CMD ["/opt/bitnami/spark/bin/spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1", "/app/spark_streaming_consumer.py"]
