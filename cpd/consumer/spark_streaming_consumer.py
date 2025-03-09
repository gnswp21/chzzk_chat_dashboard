from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, lit, coalesce
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import datetime
import pymysql
from pymongo import MongoClient
from dbutils.pooled_db import PooledDB  # pip install DBUtils

spark = SparkSession.builder.appName("KafkaStreamingWithForeachBatch").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# MySQL 커넥션 풀 생성 (최대 5개의 연결)
mysql_pool = PooledDB(
    creator=pymysql,
    host="mysql",
    user="user",
    password="password",
    database="mydb",
    autocommit=True,
    blocking=True,
    maxconnections=5
)

# MongoDB 글로벌 클라이언트 (내부적으로 커넥션 풀 사용)
mongo_client = MongoClient("mongodb://user:password@mongo:27017/mydatabase?authSource=mydatabase")

def foreach_batch_function(batch_df, batch_id):
    rows = batch_df.collect()
    batch_df.show(truncate=False)
    if not rows:
        return

    # MySQL 저장 (커넥션 풀 사용)
    try:
        conn = mysql_pool.connection()
        cursor = conn.cursor()
        # 테이블 생성 (없으면) - 각 필드를 별도 컬럼으로 저장
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                channelName VARCHAR(255),
                timestamp DATETIME,
                chat_type VARCHAR(255),
                nickname VARCHAR(255),
                msg TEXT
            )
        """)
        for row in rows:
            channelName = row['channelName']
            ts = row['timestamp']
            chat_type = row['chat_type']
            nickname = row['nickname']
            msg = row['msg']
            query = "INSERT INTO chat_messages (channelName, timestamp, chat_type, nickname, msg) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (channelName, ts, chat_type, nickname, msg))
        conn.commit()
        cursor.close()
        conn.close()  # 반납됨
        print(f"MySQL에 {len(rows)} 건 저장 완료")
    except Exception as e:
        print("MySQL 저장 에러:", e)

    # MongoDB 저장 (글로벌 클라이언트 재사용)
    try:
        db = mongo_client["mydatabase"]
        collection = db["chat_messages"]
        docs = [{
            "channelName": row['channelName'],
            "timestamp": row['timestamp'],
            "chat_type": row['chat_type'],
            "nickname": row['nickname'],
            "msg": row['msg']
        } for row in rows]
        if docs:
            collection.insert_many(docs)
        print(f"MongoDB에 {len(docs)} 건 저장 완료")
    except Exception as e:
        print("MongoDB 저장 에러:", e)


# JSON 메시지 스키마 정의
schema = StructType([
    StructField("channelName", StringType(), True),
    StructField("chat_type", StringType(), True),
    StructField("nickname", StringType(), True),
    StructField("msg", StringType(), True)
])

# ✅ Kafka 메시지 읽기
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "chzzk") \
    .load()

# ✅ Kafka 메시지 JSON 변환 및 Kafka 타임스탬프 활용
df_parsed = df.select(
    col("timestamp").alias("timestamp"),  # Kafka 타임스탬프
    from_json(col("value").cast("string"), schema).alias("data")
).select(
    col("timestamp"),  # Kafka 타임스탬프 사용
    col("data.*")  # JSON 파싱된 필드
)

query = df_parsed.writeStream \
    .outputMode("append") \
    .foreachBatch(foreach_batch_function) \
    .start()

query.awaitTermination()
