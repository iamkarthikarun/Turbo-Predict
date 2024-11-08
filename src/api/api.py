import flask
from flask import request, Response
import json
import os
import subprocess
import glob

# Define temporary storage locations (replace with preferred persistence solutions)
RAW_DATA_DIR = "./data/raw_data/"
PROCESSED_DATA_DIR = "./data/processed/"
MODEL_DIR = "./models/ml/"
SCALER_DIR = "./models/scalers/"

app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "RUL Prediction APIs"

@app.route('/api/v1/query', methods=['POST'])
def query():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    data_file = f"{RAW_DATA_DIR}raw_data.csv"
    proc = f"python src/Query.py --filepath {data_file}"
    try:
        subprocess.run(proc, check=True)
    except subprocess.CalledProcessError as e:
        return Response(status=500)
    return Response(status=200)

@app.route('/api/v1/preprocess', methods=['POST'])
def preprocess():
    engine_number = request.args['engine']
    data_file = f"{RAW_DATA_DIR}raw_data.csv"
    if not os.path.exists(data_file):
        return Response(status=400)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    processed_file = f"{PROCESSED_DATA_DIR}processed_data.csv"
    proc = f"python src/new-processor.py --ipfilepath {data_file} --opfilepath {processed_file} --engine_class {engine_number}"
    try:
        subprocess.run(proc, check=True)
    except subprocess.CalledProcessError as e:
        return Response(status=500)
    return Response(status=200)

@app.route('/api/v1/fetch_model', methods=['POST'])
def fetch_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    #os.makedirs(SCALER_DIR, exist_ok=True)
    engine_number = request.args['engine']
    proc = f"python src/model_fetcher.py --engine_class {engine_number} --model_output_filepath {MODEL_DIR}"
    try:
        subprocess.run(proc, check=True)
    except subprocess.CalledProcessError as e:
        return Response(status=500)
    return Response(status=200)

@app.route('/api/v1/predict', methods=['POST'])
def predict():
    processed_file = f"{PROCESSED_DATA_DIR}processed_data.csv"
    model_path = glob.glob(MODEL_DIR + '*.h5')[0]
    if not os.path.exists(processed_file):
        print("Processed Data doesn't exist")
        return Response(status=400)
    if not os.path.exists(model_path):
        print("Model doesn't exist")
        return Response(status=400)

    engine_number = request.args['engine']

    try:
        proc = f"python src/new-predictor.py --model_path {model_path} --input_file_path {processed_file} --engine_class {engine_number}"
        #proc = f"pip freeze | grep scikit-learn"
        subprocess.run(proc, check=True)
    except subprocess.CalledProcessError as e:
        return Response(status=500)

    return Response(status=200)

@app.route('/api/v1/teardown', methods=['POST'])
def teardown():
    proc = f"python src/teardown.py"
    try:
        subprocess.run(proc, check=True)
    except subprocess.CalledProcessError as e:
        return Response(status=500)
    return Response(status=200)

if __name__ == '__main__':
    app.run(host="localhost", port=9027, debug=True)
