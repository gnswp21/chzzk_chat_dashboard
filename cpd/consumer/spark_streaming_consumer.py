from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window
from pyspark.sql.types import StructType, StructField, StringType
import pymysql
from pymongo import MongoClient

# Spark 세션 생성
spark = SparkSession.builder.appName(
    "KafkaSparkStreamingConsumer").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# 메시지 JSON 스키마 (메시지 형식: {"name": "xxx", "chat": "내용"})
schema = StructType([
    StructField("name", StringType(), True),
    StructField("chat", StringType(), True)
])

# Kafka에서 스트림으로 데이터 읽기 (Kafka 기본 제공 timestamp 포함)
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "tst") \
    .option("startingOffsets", "earliest") \
    .load()

# Kafka 메시지의 value를 문자열로 변환하고, timestamp 컬럼도 선택
df_string = df.selectExpr("CAST(value AS STRING) as json_str", "timestamp")

# JSON 파싱 후 컬럼 분리 및 timestamp 포함
df_parsed = df_string.select(from_json(col("json_str"), schema).alias("data"), "timestamp") \
    .select("data.*", "timestamp")

# 각 배치마다 원본 메시지를 MySQL과 MongoDB에 저장하는 함수


def foreach_batch_function(batch_df, batch_id):
    rows = batch_df.collect()
    if not rows:
        return

    # MySQL 저장
    try:
        conn = pymysql.connect(host="mysql", user="user",
                               password="password", database="mydb")
        cursor = conn.cursor()
        # 테이블 생성 (없으면)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                chat TEXT
            )
        """)
        for row in rows:
            name = row['name']
            chat = row['chat']
            query = "INSERT INTO chat_messages (name, chat) VALUES (%s, %s)"
            cursor.execute(query, (name, chat))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"MySQL에 {len(rows)} 건 저장 완료")
    except Exception as e:
        print("MySQL 저장 에러:", e)

    # MongoDB 저장
    try:
        client = MongoClient(
            "mongodb://user:password@mongo:27017/mydatabase?authSource=mydatabase")
        db = client["mydatabase"]
        collection = db["chat_messages"]
        docs = [{"name": row['name'], "chat": row['chat']} for row in rows]
        if docs:
            collection.insert_many(docs)
        client.close()
        print(f"MongoDB에 {len(docs)} 건 저장 완료")
    except Exception as e:
        print("MongoDB 저장 에러:", e)


# foreachBatch를 사용해 배치 단위로 원본 메시지 저장
query_raw = df_parsed.writeStream \
    .foreachBatch(foreach_batch_function) \
    .outputMode("append") \
    .start()

# ------------------ 추가 로직: 10초 윈도우 집계 ------------------

# 10초 간격의 윈도우로 메시지 수 집계
df_agg = df_parsed.groupBy(window(col("timestamp"), "10 seconds")) \
    .count() \
    .selectExpr("window.start as window_start", "window.end as window_end", "count")


def foreach_batch_agg(batch_df, batch_id):
    rows = batch_df.collect()
    if not rows:
        return

    try:
        conn = pymysql.connect(host="mysql", user="user",
                               password="password", database="mydb")
        cursor = conn.cursor()
        # 집계 결과를 저장할 테이블 생성 (없으면)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages_agg (
                id INT AUTO_INCREMENT PRIMARY KEY,
                window_start DATETIME,
                window_end DATETIME,
                message_count INT
            )
        """)
        for row in rows:
            window_start = row['window_start']
            window_end = row['window_end']
            count_val = row['count']
            query = "INSERT INTO chat_messages_agg (window_start, window_end, message_count) VALUES (%s, %s, %s)"
            cursor.execute(query, (window_start, window_end, count_val))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"MySQL에 집계 데이터 {len(rows)} 건 저장 완료")
    except Exception as e:
        print("MySQL 집계 데이터 저장 에러:", e)


# foreachBatch를 사용해 10초 집계 데이터를 MySQL에 저장
query_agg = df_agg.writeStream \
    .foreachBatch(foreach_batch_agg) \
    .outputMode("update") \
    .start()

# 두 스트리밍 쿼리가 모두 종료될 때까지 대기
query_raw.awaitTermination()
