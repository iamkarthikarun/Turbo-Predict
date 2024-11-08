import argparse
import boto3
from botocore.exceptions import ClientError
import pandas as pd
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
import pickle
import joblib
import torch
import os
from torch import nn
import numpy as np
from lstm_model import LSTMRegressor
import json
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name ="us-east-2"
# Initialize AWS clients
session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=region_name)
s3_client = session.client('s3')


def preprocess_dataframe(df):
    # Remove engine_class and unit_nr columns for preprocessing
    processed_df = df.drop(columns=['unit_nr'])
    return processed_df


def make_prediction(model_path, input_file_path):
    model = None

    file_name = os.path.basename(model_path)
    if file_name.startswith('xgb'):
        model = XGBRegressor()
        model.load_model(model_path)
    elif file_name.startswith('rf'):
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
            print(type(model))
    elif model_path.endswith('.pth'):
        model = LSTMRegressor()
        model.load_state_dict(torch.load(model_path))
        model.eval()
    else:
        raise ValueError("Unsupported model format. Only '.pth' and '.h5' formats are supported.")
    print(model)
    df = pd.read_csv(input_file_path)

    # Get unique unit numbers
    unit_numbers = df['unit_nr'].unique()

    # Initialize a dictionary to store predictions for each unit
    predictions = {}

    for unit_nr in unit_numbers:
        # Filter dataframe for the current unit number
        unit_df = df[df['unit_nr'] == unit_nr]

        # Preprocess data without engine_class and unit_nr columns
        unit_df_processed = preprocess_dataframe(unit_df)
        print(unit_df_processed.columns)

        if isinstance(model, XGBRegressor):
            print("XGBRegressor model detected.")
            prediction = np.round(model.predict(unit_df_processed)).astype(int)
        elif isinstance(model, RandomForestRegressor):
            print("RandomForestRegressor model detected.")
            prediction = np.round(model.predict(unit_df_processed)).astype(int)
        elif isinstance(model, nn.Module):
            print("Neural network model detected.")
            inputs = torch.tensor(unit_df_processed, dtype=torch.float32)
            with torch.no_grad():
                prediction = model(inputs).numpy()
        else:
            raise ValueError("Unsupported model type.")

        # Store prediction for the current unit
        predictions[unit_nr] = prediction[-1]

    return predictions


def update_rul_s3(engine_class, predictions):
    try:
        file_name = f'EngineClass{engine_class}RUL.json'
        path_to_ruls = "RULs/"
        response = s3_client.get_object(Bucket='bda-nus', Key=path_to_ruls + file_name)
        rul_data = json.load(response['Body'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            rul_data = {}

    # Update RUL data for each unit
    for unit_nr, prediction in predictions.items():
        unit_nr_int = int(float(unit_nr))  # Convert string key to int
        rul_data[str(unit_nr_int)] = int(prediction)

    # Save updated RUL data to S3
    s3_client.put_object(Bucket='bda-nus', Key=path_to_ruls + file_name, Body=json.dumps(rul_data))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Make predictions and update RUL data in S3.')
    parser.add_argument('--model_path', type=str, help='Path to the ML model (.pth or .pkl)')
    parser.add_argument('--input_file_path', type=str, help='Path to the input data CSV file')
    parser.add_argument('--engine_class', type=int, help='Engine class')
    args = parser.parse_args()

    predictions = make_prediction(args.model_path, args.input_file_path)
    print("Predictions:", predictions)

    if args.engine_class is not None:
        update_rul_s3(args.engine_class, predictions)
