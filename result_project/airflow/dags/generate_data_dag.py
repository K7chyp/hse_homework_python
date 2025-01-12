from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker()


def generate_data_in_postgres():
    pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    for _ in range(100):
        cur.execute("""
        INSERT INTO Users (first_name, last_name, email, phone, registration_date, loyalty_status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            fake.first_name(),
            fake.last_name(),
            fake.unique.email(),
            fake.phone_number(),
            fake.date_time_between(start_date="-1y", end_date="now"),
            random.choice(["Gold", "Silver", "Bronze"])
        ))

    categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Toys"]
    for category in categories:
        cur.execute(
            "INSERT INTO ProductCategories (name) VALUES (%s)", (category,))

    for _ in range(50):
        cur.execute("""
        INSERT INTO Products (name, description, category_id, price, stock_quantity, creation_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            fake.word(),
            fake.sentence(),
            random.randint(1, len(categories)),
            round(random.uniform(10, 1000), 2),
            random.randint(1, 100),
            fake.date_time_between(start_date="-1y", end_date="now")
        ))

    for _ in range(200):
        user_id = random.randint(1, 100)
        order_date = fake.date_time_between(start_date="-1y", end_date="now")
        status = random.choice(["Pending", "Completed", "Cancelled"])
        delivery_date = order_date + timedelta(days=random.randint(1, 7))
        total_amount = round(random.uniform(50, 500), 2)

        cur.execute("""
        INSERT INTO Orders (user_id, order_date, total_amount, status, delivery_date)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING order_id
        """, (user_id, order_date, total_amount, status, delivery_date))

        order_id = cur.fetchone()[0]

        for _ in range(random.randint(1, 5)):
            product_id = random.randint(1, 50)
            quantity = random.randint(1, 10)
            price_per_unit = round(random.uniform(10, 100), 2)
            total_price = quantity * price_per_unit

            cur.execute("""
            INSERT INTO OrderDetails (order_id, product_id, quantity, price_per_unit, total_price)
            VALUES (%s, %s, %s, %s, %s)
            """, (order_id, product_id, quantity, price_per_unit, total_price))

    conn.commit()
    cur.close()
    conn.close()


with DAG(
    dag_id="generate_data_in_postgres",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="DAG для генерации данных в PostgreSQL",
    schedule_interval='*/25 * * * *',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["data_generation"],
) as dag:

    generate_data_task = PythonOperator(
        task_id="generate_data",
        python_callable=generate_data_in_postgres,
        dag=dag,
    )

    generate_data_task
