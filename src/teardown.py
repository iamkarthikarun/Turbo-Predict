import os

# Define the directories
RAW_DATA_DIR = "./data/raw_data/"
PROCESSED_DATA_DIR = "./data/processed/"
MODEL_DIR = "./models/ml/"
SCALER_DIR = "./models/scalers/"

# Function to delete all files in a directory
def delete_files_in_directory(directory):
    # Iterate over all files in the directory
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        # Check if the file is a regular file (not a directory)
        if os.path.isfile(file_path):
            # Delete the file
            os.unlink(file_path)

def delete_all_files():
    # Delete files in each directory
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODEL_DIR, SCALER_DIR]:
        print(f"Deleting files in directory: {directory}")
        delete_files_in_directory(directory)

    print("All files deleted successfully.")

if __name__ == "__main__":
    delete_all_files()