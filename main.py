import requests
import pandas as pd
import json
import io
import time
from datetime import datetime
from minio import Minio
from sqlalchemy import create_engine

# ================= ⚙️ CONFIGURATION =================
# ⚠️ ใส่ API Key ของคุณตรงนี้
WEATHER_API_KEY = "61f6ee2618206ca8b67e01c302e39e82"
AQI_API_KEY = "cb49737b12de2dde0afd81d25b5131044a49bda9"

# พิกัดกรุงเทพฯ (Bangkok)
LAT = "13.7563"
LON = "100.5018"
CITY_NAME = "Bangkok"

# ตั้งค่า MinIO & Database
MINIO_CONF = {
    "endpoint": "localhost:9000",
    "access_key": "admin",
    "secret_key": "password123",
    "secure": False
}
BUCKET_NAME = "raw-data-lake"
DB_URL = "postgresql://admin:password123@localhost:5432/air_quality_db"

# ================= 1. SETUP INFRA =================
def setup_minio():
    client = Minio(**MINIO_CONF)
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
    return client

# ================= 2. EXTRACT (ดึง API) =================
def fetch_data():
    try:
        w_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={WEATHER_API_KEY}&units=metric"
        weather_data = requests.get(w_url).json()

        a_url = f"https://api.waqi.info/feed/geo:{LAT};{LON}/?token={AQI_API_KEY}"
        aqi_data = requests.get(a_url).json()
        
        return weather_data, aqi_data
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None, None

# ================= 3. LOAD RAW TO LAKE (MinIO) =================
def save_raw_to_minio(client, weather_data, aqi_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    w_filename = f"weather/{CITY_NAME}_{timestamp}_weather.json"
    a_filename = f"aqi/{CITY_NAME}_{timestamp}_aqi.json"

    def upload(data, filename):
        data_bytes = json.dumps(data).encode('utf-8')
        data_stream = io.BytesIO(data_bytes)
        client.put_object(BUCKET_NAME, filename, data_stream, len(data_bytes), content_type='application/json')

    upload(weather_data, w_filename)
    upload(aqi_data, a_filename)
    return w_filename, a_filename

# ================= 4. TRANSFORM & LOAD TO DB =================
def process_data(client, w_filename, a_filename):
    """อ่านจาก Lake -> Clean -> Save DB"""
    try:
        # 4.1 Read from MinIO
        w_obj = client.get_object(BUCKET_NAME, w_filename)
        a_obj = client.get_object(BUCKET_NAME, a_filename)
        w_data = json.load(w_obj)
        a_data = json.load(a_obj)
        
        # 4.2 Extract Fields (ดึงเฉพาะค่าที่จำเป็น)
        raw_data = {
            'timestamp': datetime.now(),
            'city': CITY_NAME,
            'temp': w_data.get('main', {}).get('temp'),
            'humidity': w_data.get('main', {}).get('humidity'),
            'wind_speed': w_data.get('wind', {}).get('speed'),
            'pm25': a_data.get('data', {}).get('iaqi', {}).get('pm25', {}).get('v'),
            'aqi': a_data.get('data', {}).get('aqi')
        }
        
        df = pd.DataFrame([raw_data])

        # 4.3 Data Cleaning (กรองค่า Error)
        if df['temp'].isnull().any() or df['pm25'].isnull().any():
            print("⚠️ Skipping batch: Missing Data")
            return

        df['temp'] = df['temp'].astype(float)
        df['pm25'] = df['pm25'].astype(float)
        df = df[(df['temp'] < 60) & (df['pm25'] >= 0)] # Remove Outliers
        
        if df.empty: return

        # 4.4 Feature Engineering (เหลือแค่ Basic Risk Level)
        # จำเป็นต้องเก็บไว้ เพื่อให้ Dashboard แสดงสีสถานะได้ถูกต้อง
        def get_risk(aqi):
            if aqi is None: return "Unknown"
            if aqi <= 50: return "Good"
            elif aqi <= 100: return "Moderate"
            elif aqi <= 150: return "Unhealthy"
            else: return "Hazardous"
            
        df['risk_level'] = df['aqi'].apply(get_risk)

        # 4.5 Load to Warehouse
        engine = create_engine(DB_URL)
        df.to_sql('bangkok_air_quality', engine, if_exists='append', index=False)
        
        print(f"✅ [{raw_data['timestamp'].strftime('%H:%M:%S')}] Data Saved: PM2.5={raw_data['pm25']} | Temp={raw_data['temp']}")

    except Exception as e:
        print(f"❌ Process Error: {e}")

# ================= 🚀 MAIN LOOP =================
if __name__ == "__main__":
    print("🚀 Starting Pipeline (Simple Version)...")
    print("   (Press Ctrl+C to stop)")
    
    minio_client = setup_minio()
    
    while True:
        # 1. Run Pipeline
        w_data, a_data = fetch_data()
        
        if w_data and a_data:
            f_w, f_a = save_raw_to_minio(minio_client, w_data, a_data)
            process_data(minio_client, f_w, f_a)
        
        # 2. Wait
        print("⏳ Waiting every 30 minutes...")
        time.sleep(1800)