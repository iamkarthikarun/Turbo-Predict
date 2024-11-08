import os
from dotenv import load_dotenv
import boto3
import argparse

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# Define model filenames based on engine classes (replace with actual names)
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
        # Check if engine class has a corresponding model filename
        if engine_class not in MODEL_FILENAMES:
            raise ValueError(f"Engine class '{engine_class}' does not have a corresponding model.")

        # Get the model filename
        model_filename = MODEL_FILENAMES[engine_class]
        #scaler_filename = SCALER_FILENAMES[engine_class]

        # Initialize S3 client (replace with your credentials)
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=region_name)
        s3_client = session.client('s3')

        # Replace with your S3 bucket name
        bucket_name = "bda-nus"
        path_to_modelfile = "models/ml/"
        #path_to_scalerfile = "models/scalers/"
        # Download the model from S3
        s3_client.download_file(Bucket = bucket_name, Key = path_to_modelfile+ model_filename, Filename = model_output_filepath+f"/{model_filename}")
        #s3_client.download_file(Bucket = bucket_name, Key = path_to_scalerfile+ scaler_filename, Filename = scaler_output_filepath+f"/{scaler_filename}")

        print(f"Model for engine class '{engine_class}' downloaded successfully and saved to: {model_output_filepath}")
        #print(f"Scaler for engine class '{engine_class}' downloaded successfully and saved to: {scaler_output_filepath}")

    except Exception as e:
        print(f"Error downloading model: {e}")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Download model by engine class")
    parser.add_argument("--engine_class", type=str, help="Engine class for model selection")
    parser.add_argument("--model_output_filepath", type=str, help="Path to save the downloaded model")
    args = parser.parse_args()

    # Call the function with parsed arguments
    download_model_by_engine_class(args.engine_class, args.model_output_filepath)
