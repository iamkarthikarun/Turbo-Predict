import os
from dotenv import load_dotenv
import boto3
import argparse

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
MODEL_FILENAMES = {
    "1": "xgb-fd001.h5",
    "2": "xgb-fd002.h5",
    "3": "xgb-fd003.h5",
    "4": "rf-fd004.h5",
}
SCALER_FILENAMES = {
    "1": "FD001.gz",
    "2": "FD002.gz",
    "3": "FD003.gz",
    "4": "FD004.gz",
}

region_name ="us-east-2"


def download_model_by_engine_class(engine_class, model_output_filepath):
    """
    Downloads the model corresponding to the specified engine class from S3 and saves it locally.

    Args:
        engine_class (str): The engine class (e.g., "EngineClass1").
        output_filepath (str): The path to save the downloaded model file.
    """

    try:
        if engine_class not in MODEL_FILENAMES:
            raise ValueError(f"Engine class '{engine_class}' does not have a corresponding model.")

        model_filename = MODEL_FILENAMES[engine_class]
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=region_name)
        s3_client = session.client('s3')

        bucket_name = "bda-nus"
        path_to_modelfile = "models/ml/"
        s3_client.download_file(Bucket = bucket_name, Key = path_to_modelfile+ model_filename, Filename = model_output_filepath+f"/{model_filename}")

        print(f"Model for engine class '{engine_class}' downloaded successfully and saved to: {model_output_filepath}")

    except Exception as e:
        print(f"Error downloading model: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download model by engine class")
    parser.add_argument("--engine_class", type=str, help="Engine class for model selection")
    parser.add_argument("--model_output_filepath", type=str, help="Path to save the downloaded model")
    args = parser.parse_args()
    download_model_by_engine_class(args.engine_class, args.model_output_filepath)
