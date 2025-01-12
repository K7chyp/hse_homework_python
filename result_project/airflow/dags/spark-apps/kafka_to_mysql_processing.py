from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, IntegerType, DoubleType


schema = StructType([
    col("table", StringType()),
    col("data", StructType([
        col("id", IntegerType()),
        col("user_id", IntegerType()),
        col("product_id", IntegerType()),
        col("quantity", IntegerType()),
        col("total_price", DoubleType()),
    ]))
])


def main():
    spark = SparkSession.builder \
        .appName("KafkaToMySQLProcessing") \
        .getOrCreate()

    kafka_data = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "mysql_data_topic") \
        .load()

    parsed_data = kafka_data.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    aggregated_data = parsed_data.filter(col("table") == "orders") \
        .groupBy("user_id") \
        .sum("data.total_price") \
        .withColumnRenamed("sum(total_price)", "total_spent")

    aggregated_data.writeStream \
        .outputMode("update") \
        .foreachBatch(write_to_mysql) \
        .start() \
        .awaitTermination()


def write_to_mysql(batch_df, batch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:mysql://mysql:3306/test_db") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("dbtable", "aggregated_data") \
        .option("user", "test_user") \
        .option("password", "test_password") \
        .mode("append") \
        .save()


if __name__ == "__main__":
    main()
