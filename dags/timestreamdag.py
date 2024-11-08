from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import requests

def read_from_kafka_and_write_to_timestream():
    url = "http://host.docker.internal:9678/api/v1/timestreamwrite"
    response = requests.post(url)
    print(response.status_code)

with DAG(
    "KafkaToTimeStream",
    default_args={
        "retries": 0,
    },
    description="Read data from Kafka based on timestamp and write to AWS TimeStream",
    schedule_interval="*/20 * * * *",  # Every 20 minutes
    start_date=days_ago(0),
    catchup=False,
) as dag:

    # Define the task
    read_kafka_task = PythonOperator(
        task_id="read_kafka_and_write_to_timestream",
        python_callable=read_from_kafka_and_write_to_timestream,
    )

    # Set task dependencies
    read_kafka_task
