# Проект: Интеграция MySQL, Kafka и Spark с использованием Apache Airflow

## Описание проекта

Данный проект демонстрирует процесс ETL (Extract, Transform, Load) с использованием следующих технологий:
- **MySQL**: источник данных (таблицы `users`, `products`, `orders`).
- **Apache Kafka**: брокер сообщений для передачи данных между системами.
- **Apache Spark**: обработка и трансформация данных, поступающих из Kafka.
- **Apache Airflow**: управление рабочими процессами и автоматизация выполнения задач.
- **MongoDB**: NoSQL база данных (включена для расширения возможностей хранения).
- **Grafana**: визуализация метрик и мониторинг процессов.
- **Jupyter Notebook**: интерактивная среда для анализа данных и прототипирования.

Процесс включает:
1. Извлечение данных из MySQL.
2. Публикацию данных в Kafka.
3. Обработку данных с помощью Spark.
4. Автоматизацию всего процесса через DAG в Airflow.

---

## Стек технологий

- **Docker Compose**: для контейнеризации всех сервисов.
- **MySQL**: база данных с таблицами `users`, `products`, `orders`.
- **Apache Kafka**: распределенный брокер сообщений.
- **Apache Spark**: распределенная обработка данных.
- **Apache Airflow**: оркестрация процессов.
- **Kafdrop**: веб-интерфейс для мониторинга Kafka.
- **PostgreSQL**: база данных для метаданных Airflow.
- **MongoDB**: для хранения дополнительных данных (но я не придумал как ее заиспользовать, просто поднял) 
- **Grafana**: мониторинг и визуализация.
- **Jupyter Notebook**: анализ и прототипирование.

---

## Установка и запуск

### 1. Клонирование репозитория
Склонируйте проект на локальный компьютер:
```bash
git clone <URL репозитория>
cd <папка проекта>
```

### 2. Настройка окружения
Убедитесь, что на вашей машине установлены:
- **Docker** (v20.10+)
- **Docker Compose** (v1.29+)

### 3. Запуск контейнеров
Для запуска всех сервисов выполните:
```bash
docker-compose up -d
```

Это запустит следующие контейнеры:
- `mysql`: база данных с таблицами `users`, `products`, `orders`.
- `kafka`, `zookeeper`: инфраструктура Apache Kafka.
- `kafdrop`: UI для мониторинга Kafka.
- `spark-master`, `spark-worker`: Spark-кластер для обработки данных.
- `airflow-webserver`, `airflow-scheduler`, `postgres`: инфраструктура Airflow.
- `spark-history-server`: сервер истории для Spark.
- `grafana`: для мониторинга и визуализации.
- `mongo`: NoSQL база данных.
- `jupyter`: Jupyter Notebook для анализа данных.

### 4. Настройка Airflow
Перейдите в веб-интерфейс Airflow: [http://localhost:8080](http://localhost:8080).
1. Войдите с учётными данными:
   - Логин: `airflow`
   - Пароль: `airflow`
2. Добавьте подключения:
   - **MySQL**: для подключения к базе данных MySQL.
     ```
     Conn Id: mysql
     Conn Type: MySQL
     Host: mysql
     Login: test_user
     Password: test_password
     Schema: test_db
     ```
   - **Spark**: для подключения к Spark.
     ```
     Conn Id: spark_default
     Conn Type: Spark
     Host: spark://spark-master:7077
     ```

### 5. Запуск DAG
1. Активируйте DAG `mysql_to_kafka_dag` в веб-интерфейсе Airflow.
2. Запустите DAG вручную или дождитесь автоматического запуска по расписанию.

---

## Реализация DAG

Файл `mysql_kafka_dag.py` содержит следующие задачи:

1. **`extract_from_mysql_and_publish_to_kafka`**: 
   - Извлекает данные из таблиц `users`, `products`, `orders` в MySQL.
   - Форматирует данные в JSON.
   - Публикует данные в Kafka (топик `mysql_data_topic`).

2. **`process_kafka_data_with_spark`**: 
   - Обрабатывает данные из Kafka с помощью Spark-приложения `/opt/spark-apps/process_kafka_data.py`.
   - Результаты сохраняются в файл (или другой источник, в зависимости от настройки).

3. **Задачи зависимости**: 
   DAG обеспечивает выполнение задач последовательно.

---

## Обработка данных в Spark

Скрипт `/spark-apps/process_kafka_data.py` выполняет:
1. Подключение к Kafka.
2. Чтение данных из топика `mysql_data_topic`.
3. Преобразование данных (например, фильтрация, агрегация).
4. Сохранение результата (в файл или базу данных).

Пример запуска Spark-приложения:
```bash
spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.executor.memory=1g \
  --conf spark.driver.memory=1g \
  /opt/spark-apps/process_kafka_data.py
```

---

## Просмотр данных Kafka

1. Откройте Kafdrop: [http://localhost:9000](http://localhost:9000).
2. Выберите топик `mysql_data_topic`.
3. Посмотрите опубликованные сообщения.

---

## Полезные команды

### Остановка всех сервисов
```bash
docker-compose down
```

### Пересборка образов
```bash
docker-compose build
```

### Логи контейнеров
```bash
docker-compose logs -f <имя_контейнера>
```

---

## Дальнейшие улучшения

1. **Расширить обработку данных в Spark**: Например, добавить больше табличек и обработчиков
2. **Добавить тесты**: Проверка DAG и интеграционных процессов.
3. **Использовать как нибудь mongodb**

