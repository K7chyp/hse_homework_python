from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.operators.python import PythonOperator
from kafka import KafkaProducer
from datetime import datetime, timedelta
import json
from decimal import Decimal


def custom_json_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {
                    obj.__class__.__name__} is not JSON serializable")


def publish_mysql_data_to_kafka():
    mysql_hook = MySqlHook(mysql_conn_id="mysql")
    tables_queries = {
        "users": "SELECT * FROM MartUserOrderSummary",
        "products": "SELECT  * FROM MartProductSales",
        "sales": "SELECT * FROM MartCategorySales",
    }

    producer = KafkaProducer(
        bootstrap_servers=["kafka:9092"],
        value_serializer=lambda v: json.dumps(
            v, default=custom_json_serializer).encode("utf-8"),
    )

    for table, query in tables_queries.items():
        records = mysql_hook.get_records(query)
        for record in records:
            message = {"table": table, "data": record}
            producer.send("mysql_data_topic", value=message)

    producer.flush()
    producer.close()


with DAG(
    dag_id="mysql_to_kafka_dag",
    start_date=datetime(2023, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:

    publish_task = PythonOperator(
        task_id="publish_mysql_data_to_kafka",
        python_callable=publish_mysql_data_to_kafka,
    )

    spark_processing_task = SparkSubmitOperator(
        task_id="process_kafka_data_with_spark",
        application="/opt/spark-apps/process_kafka_data.py",
        conn_id="spark",
        verbose=True,
        conf={
            "spark.master": "spark://spark-master:7077",
            "spark.executor.memory": "1g",
            "spark.driver.memory": "1g"
        },
        name="arrow-spark"
    )

    publish_task >> spark_processing_task
