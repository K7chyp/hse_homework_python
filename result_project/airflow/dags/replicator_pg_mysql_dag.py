from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.operators.python import PythonOperator
from datetime import datetime

def replicate_data():
    pg_hook = PostgresHook(postgres_conn_id="postgres")
    mysql_hook = MySqlHook(mysql_conn_id="mysql")

    queries = [
        ("SELECT * FROM Users", "Users"),
        ("SELECT * FROM ProductCategories", "ProductCategories"),
        ("SELECT * FROM Products", "Products"),
        ("SELECT * FROM Orders", "Orders"),
        ("SELECT * FROM OrderDetails", "OrderDetails"),
    ]

    for query, table in queries:
        src_records = pg_hook.get_records(query)
        mysql_hook.insert_rows(table, src_records)

with DAG(
    dag_id="replicate_postgres_to_mysql",
    start_date=datetime(2023, 1, 1),
    schedule_interval="@hourly",
    catchup=False
) as dag:

    replicate_task = PythonOperator(
        task_id="replicate_data",
        python_callable=replicate_data
    )
