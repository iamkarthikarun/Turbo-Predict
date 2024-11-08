import streamlit as st
import plotly.graph_objects as go
import boto3
import json
import os
from dotenv import load_dotenv
from src.aws.Query import TimestreamQuery 

load_dotenv()

st.set_page_config(
    page_title="Aircraft Engine RUL Prediction Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        background-color: #1B1B1B;
    }
    .stMetric {
        background-color: #2F3742 !important;
        border-radius: 4px !important;
        padding: 1rem !important;
        box-shadow: none !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #B0B0B0 !important;
    }
    div[data-testid="stMetricDelta"] {
        color: #00CA4E !important;
    }
    .stTextInput > div > div {
        background-color: #2F3742;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def create_gauge(rul, max_rul=150):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rul,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, max_rul], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "green"},
            'bgcolor': "darkgray",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': 'red'},
                {'range': [30, 50], 'color': 'orange'},
                {'range': [50, 125], 'color': 'lightgreen'},
                {'range': [125, 150], 'color': 'green'}
            ],
        },
        title={'text': "RUL (cycles)", 'font': {'color': "white", 'size': 24}},
        number={'font': {'color': "white", 'size': 50}}
    ))
    
    fig.update_layout(
        paper_bgcolor='#1B1B1B',
        plot_bgcolor='#1B1B1B',
        height=400,
        margin=dict(t=80, b=40)
    )
    return fig

def get_rul(engine_class, engine_number):
    try:
        region_name = "us-east-2"
        session = boto3.Session(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=region_name
        )
        s3_client = session.client('s3')
        file_name = f'EngineClass{engine_class}RUL.json'
        path_to_ruls = "RULs/"
        response = s3_client.get_object(Bucket='bda-nus', Key=path_to_ruls+file_name)
        rul_data = json.load(response['Body'])
        return float(rul_data[str(engine_number)])
    except Exception as e:
        st.error(f"Error fetching RUL: {e}")
        return None

def get_sensor_readings(engine_class, engine_number):
    try:
        timestream_query = TimestreamQuery()
        query = f"""
        SELECT *
        FROM RawSensorData.SensorTableFD
        WHERE engine_class = {engine_class} 
        AND unit_nr = '{engine_number}'
        ORDER BY time DESC
        LIMIT 1
        """
        df = timestream_query.run_query(query)
        if df is not None and not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Error fetching sensor readings: {e}")
        return None

with st.sidebar:
    st.header("Engine Selection")
    engine_class = st.selectbox("Engine Class", [1, 2, 3, 4])
    engine_number = st.text_input("Engine Number", "1")

st.title("Aircraft Engine RUL Prediction Dashboard")

try:
    engine_num = int(engine_number)
    rul = get_rul(engine_class, engine_num)
    sensor_data = get_sensor_readings(engine_class, engine_num)
    
    if rul and sensor_data:
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.subheader("Engine Health Status")
            fig = create_gauge(rul)
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Remaining Useful Life", 
                     f"{int(rul)} cycles", 
                     delta="Normal" if rul > 50 else "Critical")
        
        with col2:
            st.subheader("Sensor Readings")
            sensor_col1, sensor_col2 = st.columns(2)
            
            # Left column sensors
            with sensor_col1:
                st.metric("Setting 1 (°C)", f"{sensor_data['setting_1']:.2f}")
                st.metric("Setting 2 (psi)", f"{sensor_data['setting_2']:.2f}")
                st.metric("Setting 3 (rpm)", f"{sensor_data['setting_3']:.2f}")
                st.metric("Temperature T2 (°C)", f"{sensor_data['T2']:.2f}")
                st.metric("Temperature T24 (°C)", f"{sensor_data['T24']:.2f}")
                st.metric("Temperature T30 (°C)", f"{sensor_data['T30']:.2f}")
            
            # Right column sensors
            with sensor_col2:
                st.metric("Temperature T50 (°C)", f"{sensor_data['T50']:.2f}")
                st.metric("Pressure P2 (psi)", f"{sensor_data['P2']:.2f}")
                st.metric("Pressure P15 (psi)", f"{sensor_data['P15']:.2f}")
                st.metric("Pressure P30 (psi)", f"{sensor_data['P30']:.2f}")
                st.metric("Speed Nf (rpm)", f"{sensor_data['Nf']:.2f}")
                st.metric("Speed Nc (rpm)", f"{sensor_data['Nc']:.2f}")

except ValueError:
    st.error("Please enter a valid engine number")

st.markdown("---")
st.markdown("*Dashboard showing real-time engine health monitoring*")
