import time
import os
import json
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
import boto3
from boto3 import client
from botocore.config import Config
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name="us-east-2")
client = session.client('timestream-write',region_name="us-east-2")
s3_client = session.client('s3')

def save_timestamp_to_storage(timestamp):
    """
    Writes a timestamp (Unix epoch) to a local text file and uploads it to S3.

    Args:
        timestamp (int): The timestamp to be stored in the file.
    """
    try:
        file_name = 'last_timestamp.txt'
        path_to_ts = "Timestamp/"
        # Write the timestamp to the file
        with open(file_name, 'w') as file:
            json.dump(timestamp, file)
        # Upload the file to S3
        with open(file_name, 'rb') as data:
            s3_client.put_object(Bucket='bda-nus', Key=path_to_ts + file_name, Body=data)
        print("Timestamp written to file and uploaded to S3 successfully.")
    except Exception as e:
        print("Error:", e)

def get_last_timestamp_from_storage():
    """
    Retrieves the last timestamp (Unix epoch) from a local text file.

    Returns:
        int: The last timestamp stored in the file as an integer, or None if not found.
    """
    try:
        file_name = f'last_timestamp.txt'
        path_to_ts = "Timestamp/"
        response = s3_client.get_object(Bucket='bda-nus', Key=path_to_ts+file_name)
        timestamp = json.load(response['Body'])
        return timestamp
    except ClientError as e:
        print("Error: ",e)
    return None

DATABASE_NAME = "RawSensorData"
TABLE_NAME = "SensorTableFD"

INTERVAL = 1 # Seconds


def prepare_record(message_dict):
    record = {
        'Dimensions': [
            {'Name': 'unit_nr', 'Value': str(message_dict['unit_nr'])},
            {'Name': 'engine_class', 'Value': str(message_dict['engine_class'])}
        ],
        'Time': str(message_dict['timestamp']),
        'MeasureName': 'Sensor Data',
        'MeasureValueType': 'MULTI',
        'MeasureValues': [
            {'Name': 'time_cycles', 'Value': str(message_dict['time_cycles']), 'Type': 'DOUBLE'},
            {'Name': 'setting_1', 'Value': str(message_dict['setting_1']), 'Type': 'DOUBLE'},
            {'Name': 'setting_2', 'Value': str(message_dict['setting_2']), 'Type': 'DOUBLE'},
            {'Name': 'setting_3', 'Value': str(message_dict['setting_3']), 'Type': 'DOUBLE'},
            {'Name': 'T2', 'Value': str(message_dict['T2']), 'Type': 'DOUBLE'},
            {'Name': 'T24', 'Value': str(message_dict['T24']), 'Type': 'DOUBLE'},
            {'Name': 'T30', 'Value': str(message_dict['T30']), 'Type': 'DOUBLE'},
            {'Name': 'T50', 'Value': str(message_dict['T50']), 'Type': 'DOUBLE'},
            {'Name': 'P2', 'Value': str(message_dict['P2']), 'Type': 'DOUBLE'},
            {'Name': 'P15', 'Value': str(message_dict['P15']), 'Type': 'DOUBLE'},
            {'Name': 'P30', 'Value': str(message_dict['P30']), 'Type': 'DOUBLE'},
            {'Name': 'Nf', 'Value': str(message_dict['Nf']), 'Type': 'DOUBLE'},
            {'Name': 'Nc', 'Value': str(message_dict['Nc']), 'Type': 'DOUBLE'},
            {'Name': 'epr', 'Value': str(message_dict['epr']), 'Type': 'DOUBLE'},
            {'Name': 'Ps30', 'Value': str(message_dict['Ps30']), 'Type': 'DOUBLE'},
            {'Name': 'phi', 'Value': str(message_dict['phi']), 'Type': 'DOUBLE'},
            {'Name': 'NRf', 'Value': str(message_dict['NRf']), 'Type': 'DOUBLE'},
            {'Name': 'NRc', 'Value': str(message_dict['NRc']), 'Type': 'DOUBLE'},
            {'Name': 'BPR', 'Value': str(message_dict['BPR']), 'Type': 'DOUBLE'},
            {'Name': 'farB', 'Value': str(message_dict['farB']), 'Type': 'DOUBLE'},
            {'Name': 'htBleed', 'Value': str(message_dict['htBleed']), 'Type': 'DOUBLE'},
            {'Name': 'Nf_dmd', 'Value': str(message_dict['Nf_dmd']), 'Type': 'DOUBLE'},
            {'Name': 'PCNfR_dmd', 'Value': str(message_dict['PCNfR_dmd']), 'Type': 'DOUBLE'},
            {'Name': 'W31', 'Value': str(message_dict['W31']), 'Type': 'DOUBLE'},
            {'Name': 'W32', 'Value': str(message_dict['W32']), 'Type': 'DOUBLE'}
        ]
    }
    return record

@staticmethod
def _print_rejected_records_exceptions(err):
    print("RejectedRecords: ", err)
    for rr in err.response["RejectedRecords"]:
        print("Rejected Index " + str(rr["RecordIndex"]) + ": " + rr["Reason"])
        if "ExistingVersion" in rr:
            print("Rejected record existing version: ", rr["ExistingVersion"])

def write_records(records):
    try:
        result = client.write_records(DatabaseName=DATABASE_NAME,
                                      TableName=TABLE_NAME,
                                      Records=records)
        status = result['ResponseMetadata']['HTTPStatusCode']
        print("Processed %d records. WriteRecords HTTPStatusCode: %s" %
              (len(records), status))
    except client.exceptions.RejectedRecordsException as err:
        _print_rejected_records_exceptions(err)
    except Exception as err:
        print("Error:", err)


def write_to_AWS_TS():

    print("writing data to database {} table {}".format(
        DATABASE_NAME, TABLE_NAME))

    KAFKA_BROKER_ADDRESS = "localhost:9092"

    consumer = KafkaConsumer("RawSensorData",
                             auto_offset_reset="earliest",
                             value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                             bootstrap_servers=[KAFKA_BROKER_ADDRESS],
                             consumer_timeout_ms=1000,
                             max_poll_records=25)

    consumer.subscribe('RawSensorData')
    partition = TopicPartition('RawSensorData', 0)

    last_timestamp = get_last_timestamp_from_storage()
    print(last_timestamp)
    if last_timestamp:
        rec_in = consumer.offsets_for_times({partition: last_timestamp})
        print(rec_in[partition].offset)
        consumer.seek(partition, rec_in[partition].offset + 1)
    records = []

    try:
        for msg in consumer:
            try:
                # Check if message is a dictionary
                if isinstance(msg.value, dict):
                    message_dict = msg.value
                else:
                    message_dict = json.loads(msg.value.decode("utf-8"))
                print(message_dict)
                if last_timestamp and (float(last_timestamp) >= float(message_dict['timestamp'])):
                    break
                print(f"Received message: {message_dict}")
                record = prepare_record(message_dict)
                records.append(record)
                last_timestamp = message_dict['timestamp']  # Update last timestamp
                save_timestamp_to_storage(last_timestamp)  # Save for future consumption

            except json.JSONDecodeError:
                print(f"Error: Message is not valid JSON. Skipping message.")
            except Exception as e:
                print(f"Error processing message: {e}")
        if records:
            write_records(records=records)
            records = []
            print("Data processed and written to TimeStream")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Exiting program...")
        consumer.close()

if __name__ == "__main__":
    write_to_AWS_TS()
