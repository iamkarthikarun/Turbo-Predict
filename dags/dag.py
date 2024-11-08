from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.models import Variable
import requests
from datetime import datetime
import pendulum

RAW_DATA_DIR = "./data/raw_data/"
PROCESSED_DATA_DIR = "./data/processed/"
MODEL_DIR = "./models/ml/"

engine_class_param = Variable.get("engine_class_param", default_var=None)

def run_query():
    url = "http://host.docker.internal:9027/api/v1/query"
    response = requests.post(url)
    print(response.status_code)

def fetch_model():
    url = "http://host.docker.internal:9027/api/v1/fetch_model?engine={}"
    response = requests.post(url.format(engine_class_param))
    print(response.status_code)

def preprocess_data():
    url = "http://host.docker.internal:9027/api/v1/preprocess?engine={}"
    response = requests.post(url.format(engine_class_param))
    print(response.status_code)

def do_prediction():
    url = "http://host.docker.internal:9027/api/v1/predict?engine={}"
    response = requests.post(url.format(engine_class_param))
    print(response.status_code)

def teardown():
    url = "http://host.docker.internal:9027/api/v1/teardown"
    response = requests.post(url)
    print(response.status_code)

with DAG(
    "RULPredictionDAG",
    default_args={"retries": 2},
    description="PBDA Data Pipeline",
    schedule=None,
    start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Singapore"),
    catchup=False,
    tags=["PBDA"],
) as dag:
    
    call_run_query_api = PythonOperator(
        task_id='Run_Query',
        python_callable=run_query,
    )
    
    call_fetch_model_api = PythonOperator(
        task_id='Fetch_Model',
        python_callable=fetch_model,
    )

    call_preprocessor_api = PythonOperator(
        task_id='Preprocess_Data',
        python_callable=preprocess_data,
    )

    predictor_api = PythonOperator(
        task_id='Prediction',
        python_callable=do_prediction,
    )

    teardown_api = PythonOperator(
        task_id = 'Teardown',
        python_callable = teardown
    )
    
    call_run_query_api >> call_fetch_model_api >> call_preprocessor_api >> predictor_api >> teardown_api
    