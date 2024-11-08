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
        padding: 0.5rem !important;
        margin: 0.2rem !important;
        box-shadow: none !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 12px !important;
        color: #B0B0B0 !important;
    }
    div[data-testid="stMetricDelta"] {
        color: #00CA4E !important;
        font-size: 12px !important;
    }
    .stTextInput > div > div {
        background-color: #2F3742;
        color: white;
    }
    [data-testid="stHeader"] {
        background-color: #1B1B1B;
    }
    .stMarkdown {
        color: #B0B0B0;
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
            for i in range(5):
                cols = st.columns(5)
                for j in range(5):
                    idx = i * 5 + j
                    if idx < 24:
                        with cols[j]:
                            if idx == 0:
                                st.metric("Setting 1 (°C)", f"{sensor_data['setting_1']:.2f}")
                            elif idx == 1:
                                st.metric("Setting 2 (psi)", f"{sensor_data['setting_2']:.2f}")
                            elif idx == 2:
                                st.metric("Setting 3 (rpm)", f"{sensor_data['setting_3']:.2f}")
                            elif idx == 3:
                                st.metric("T2 (°C)", f"{sensor_data['T2']:.2f}")
                            elif idx == 4:
                                st.metric("T24 (°C)", f"{sensor_data['T24']:.2f}")
                            elif idx == 5:
                                st.metric("T30 (°C)", f"{sensor_data['T30']:.2f}")
                            elif idx == 6:
                                st.metric("T50 (°C)", f"{sensor_data['T50']:.2f}")
                            elif idx == 7:
                                st.metric("P2 (psi)", f"{sensor_data['P2']:.2f}")
                            elif idx == 8:
                                st.metric("P15 (psi)", f"{sensor_data['P15']:.2f}")
                            elif idx == 9:
                                st.metric("P30 (psi)", f"{sensor_data['P30']:.2f}")
                            elif idx == 10:
                                st.metric("Nf (rpm)", f"{sensor_data['Nf']:.2f}")
                            elif idx == 11:
                                st.metric("Nc (rpm)", f"{sensor_data['Nc']:.2f}")
                            elif idx == 12:
                                st.metric("EPR", f"{sensor_data['epr']:.2f}")
                            elif idx == 13:
                                st.metric("Ps30 (psi)", f"{sensor_data['Ps30']:.2f}")
                            elif idx == 14:
                                st.metric("φ (deg)", f"{sensor_data['phi']:.2f}")
                            elif idx == 15:
                                st.metric("NRf", f"{sensor_data['NRf']:.2f}")
                            elif idx == 16:
                                st.metric("NRc", f"{sensor_data['NRc']:.2f}")
                            elif idx == 17:
                                st.metric("BPR", f"{sensor_data['BPR']:.2f}")
                            elif idx == 18:
                                st.metric("farB", f"{sensor_data['farB']:.3f}")
                            elif idx == 19:
                                st.metric("htBleed", f"{sensor_data['htBleed']:.2f}")
                            elif idx == 20:
                                st.metric("Nf_dmd", f"{sensor_data['Nf_dmd']:.2f}")
                            elif idx == 21:
                                st.metric("PCNfR_dmd", f"{sensor_data['PCNfR_dmd']:.2f}")
                            elif idx == 22:
                                st.metric("W31", f"{sensor_data['W31']:.2f}")
                            elif idx == 23:
                                st.metric("W32", f"{sensor_data['W32']:.2f}")

except ValueError:
    st.error("Please enter a valid engine number")

st.markdown("---")
st.markdown("*Dashboard showing real-time engine health monitoring*")
