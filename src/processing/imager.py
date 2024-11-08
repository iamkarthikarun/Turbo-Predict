import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib import cm
import io
import json
import base64
import boto3

load_dotenv()

app = Flask(__name__)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
engine_image_path = "C:/Users/Karthik Arun/Downloads/Real-Time-Data-Pipeline-Using-Kafka-and-Spark-master/Application/turbofan.png" # Define the engine image path

def generate_color_overlay(rul):
    if rul > 125 or rul < 30:
        alpha = 0.85  # Set transparency to higher value for very good or dangerous condition
    elif 30 <= rul < 50:
        alpha = 0.5  # Set transparency to medium value for slightly dangerous condition
    elif 50 <= rul <= 125:
        alpha = 0.3  # Set transparency to a bit higher than medium for okayish condition
    else:
        alpha = 0.2  # Set transparency to lower value for other conditions

    cmap = cm.get_cmap('RdYlGn')
    norm = plt.Normalize(0, 100)  # Assuming RUL is a percentage between 0 and 100
    color = cmap(norm(rul))
    color = tuple(int(c * 255) for c in color[:3])  # Extract RGB values
    overlay_img = Image.new('RGBA', (200, 150), color)  # Adjust dimensions if needed
    overlay_img.putalpha(int(255 * alpha))

    return overlay_img

def generate_colored_engine_image(rul):
    # Load the engine image
    engine_img = Image.open(engine_image_path)

    # Resize the engine image if necessary
    engine_img = engine_img.resize((200, 150))  # Adjust dimensions if needed
    engine_img = engine_img.convert('RGBA')

    if rul > 125:
        engine_img.putalpha(int(255 * 0.1))  # Set transparency to lower value for very good condition
    elif rul < 30:
        engine_img.putalpha(int(255 * 1))  # Set transparency to higher value for dangerous condition
    elif 30 <= rul < 50:
        engine_img.putalpha(int(255 * 0.5))  # Set transparency to medium value for slightly dangerous condition
    elif 50 <= rul <= 125:
        engine_img.putalpha(int(255 * 0.3))

    color_overlay = generate_color_overlay(rul)

    merged_img = Image.alpha_composite(engine_img, color_overlay)

    img_byte_array = merged_img.tobytes()
    img_mode = merged_img.mode
    img_size = merged_img.size

    return img_byte_array, img_mode, img_size

def get_rul(engine_class, engine_number):
    try:
        # Initialize AWS S3 client
        #print(f"Engine Class {engine_class} Type {type(engine_class)}")
        #print(f"Engine Number {engine_number} Type {type(engine_number)}")
        region_name ="us-east-2"
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                region_name=region_name)
        s3_client = session.client('s3')
        file_name = f'EngineClass{engine_class}RUL.json'
        path_to_ruls = "RULs/"
        response = s3_client.get_object(Bucket='bda-nus', Key=path_to_ruls+file_name)
        rul_data = json.load(response['Body'])
        #print(f"RUL DATA {rul_data}")
        rul = rul_data[str(engine_number)]
        #print(f"RUL {rul}")
        return rul
    except Exception as e:
        print(f"Error fetching RUL: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        engine_class = int(request.form['engine_class'])
        engine_number = int(request.form['engine_number'])
        #sensor_readings = newquery.fetch_last_point(engine_class, engine_number)
        sensor_readings = {"unit_nr": 176.0, "time_cycles": 46.0, "setting_1": 20.0012, "setting_2": 0.7, "setting_3": 100.0, "T2": 491.19, "T24": 606.82, "T30": 1480.53, "T50": 1247.48, "P2": 9.35, "P15": 13.65, "P30": 334.91, "Nf": 2323.97, "Nc": 8727.51, "epr": 1.08, "Ps30": 44.19, "phi": 315.53, "NRf": 2388.06, "NRc": 8069.3, "BPR": 9.1756, "farB": 0.02, "htBleed": 364.0, "Nf_dmd": 2324.0, "PCNfR_dmd": 100.0, "W31": 24.69, "W32": 14.7645, "engine_class": 4.0}
        rul = get_rul(engine_class, engine_number)
        print("RUL",rul)
        if rul and sensor_readings:
            print("here")
            img_data, _, _ = generate_colored_engine_image(rul)
            img = Image.frombytes('RGBA', (200, 150), img_data)
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            img_byte_array = img_byte_array.getvalue()
            encoded_img_data = base64.b64encode(img_byte_array).decode('utf-8')
            key_list = ['setting_1', 'setting_2', 'setting_3', 'T2', 'T24', 'T30', 'T50', 'P2', 'P15', 'P30', 'Nf', 'Nc', 'epr', 'Ps30', 'phi', 'NRf', 'NRc', 'BPR', 'farB', 'htBleed', 'Nf_dmd', 'PCNfR_dmd', 'W31', 'W32']
            sensor_readings_filtered = {key: value for key, value in sensor_readings.items() if key in key_list}
            half_len = len(sensor_readings_filtered) // 2
            sensor_readings_left = {k: v for i, (k, v) in enumerate(sensor_readings_filtered.items()) if i < half_len}
            print(len(sensor_readings_left))
            sensor_readings_right = {k: v for i, (k, v) in enumerate(sensor_readings_filtered.items()) if i >= half_len}
            print(len(sensor_readings_right))

            return jsonify({'success': True, 'engine_image': encoded_img_data,
                    'rul_prediction': rul,
                    'sensor_readings_left': sensor_readings_left,
                    'sensor_readings_right': sensor_readings_right})
        else:
            return jsonify({'success': False, 'error': 'Invalid engine number'})
    return render_template('index3.html')

if __name__ == '__main__':
    app.run(debug=True, port=9192)
