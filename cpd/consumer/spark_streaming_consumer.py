from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, lit, coalesce
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import datetime

spark = SparkSession.builder.appName("KafkaStreamingWithForeachBatch").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

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

# ✅ 10초 윈도우 집계 (Watermark를 30초로 늘려 데이터 손실 방지)
agg_df = df_parsed.withWatermark("timestamp", "30 seconds") \
    .groupBy("channelName", window(col("timestamp"), "10 seconds")) \
    .count() \
    .withColumnRenamed("count", "msg_count")

# ✅ 윈도우 정보 추출
agg_df_flat = agg_df.select(
    "channelName",
    col("window.start").alias("win_start"),
    col("window.end").alias("win_end"),
    "msg_count"
)

# ✅ 정적 채널 리스트
static_channels = ["녹두로", "B", "C"]

# ✅ `foreachBatch` 내부에서 빈 배치에서도 0 카운트 보장하는 함수
def fill_missing_channels(batch_df, epoch_id):
    # 현재 시간 기준으로 가장 가까운 10초 윈도우 정렬
    now = datetime.datetime.utcnow()
    aligned_win_start = now.replace(second=(now.second // 10) * 10, microsecond=0)
    aligned_win_end = aligned_win_start + datetime.timedelta(seconds=10)

    if batch_df.isEmpty():
        # ✅ 배치가 비어 있을 경우, 기본 윈도우 생성하여 각 채널에 0 카운트 추가
        empty_data = [(c, aligned_win_start, aligned_win_end, 0) for c in static_channels]
        empty_df = spark.createDataFrame(empty_data, ["channelName", "win_start", "win_end", "msg_count"])
        empty_df.show(truncate=False)
        return
    
    # ✅ 정적 채널 리스트를 Spark DataFrame으로 변환
    static_df = spark.createDataFrame([(c,) for c in static_channels], ["channelName"])

    # ✅ 현재 배치에서 생성된 윈도우 리스트 추출
    windows_df = batch_df.select("win_start", "win_end").distinct()

    # ✅ 모든 윈도우에 대해 정적 채널 추가
    full_df = windows_df.crossJoin(static_df) \
        .join(batch_df, on=["channelName", "win_start", "win_end"], how="left") \
        .select(
            "channelName",
            "win_start",
            "win_end",
            coalesce(col("msg_count"), lit(0)).alias("msg_count")  # NULL이면 0으로 변경
        )

    # ✅ 결과 출력 (또는 데이터 저장)
    full_df.show(truncate=False)

# ✅ 배치마다 `fill_missing_channels` 적용
query = agg_df_flat.writeStream \
    .outputMode("append") \
    .foreachBatch(fill_missing_channels) \
    .option("checkpointLocation", "/tmp/kafka_checkpoint") \
    .trigger(processingTime="10 seconds") \
    .start()

query.awaitTermination()
