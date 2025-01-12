import logging
from airflow import DAG
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def replicate_data():
    try:
        logger.info("Начало процесса репликации данных.")

        mysql_hook = MySqlHook(mysql_conn_id="mysql")
        logger.info("Успешно подключились к MySQL.")

        views = [
            ("MartUserOrderSummary", "SELECT * FROM test_db.UserOrderSummary"),
            ("MartProductSales", "SELECT * FROM test_db.ProductSales"),
            ("MartCategorySales", "SELECT * FROM test_db.CategorySales")
        ]

        for table_name, query in views:
            logger.info(f"Начало репликации для таблицы {
                        table_name}. Выполнение запроса: {query}")

            records = mysql_hook.get_records(query)
            logger.info(f"Извлечено {len(records)
                                     } записей из представления {table_name}.")

            if records:

                mysql_hook.insert_rows(table_name, records)
                logger.info(f"Успешно вставлено {
                            len(records)} записей в таблицу {table_name}.")
            else:
                logger.warning(f"Данные для таблицы {table_name} отсутствуют.")

        last_run_time = datetime.now()
        update_last_run_time(last_run_time)
        logger.info(f"Процесс репликации завершен. Время последнего запуска обновлено: {
                    last_run_time}.")

    except Exception as e:
        logger.error(f"Ошибка при репликации данных: {e}", exc_info=True)
        raise


def get_last_run_time():

    last_run_time = datetime.now() - timedelta(days=1)
    logger.info(f"Получено время последнего запуска: {last_run_time}.")
    return last_run_time


def update_last_run_time(last_run_time: datetime):

    logger.info(f"Обновление времени последнего запуска: {last_run_time}.")


with DAG(
    dag_id="analytical_mart",
    start_date=datetime(2023, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    default_args={
        'retries': 3,
        'retry_delay': timedelta(minutes=5)
    }
) as dag:

    replicate_task = PythonOperator(
        task_id="mart_updater",
        python_callable=replicate_data
    )
