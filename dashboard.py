import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time
import plotly.express as px # ถ้าไม่มีให้ pip install plotly ด้วย (ถ้าไม่ลง ใช้กราฟธรรมดาของ streamlit ได้)

# ================= CONFIGURATION =================
# เชื่อมต่อ Database เดียวกับที่เราสร้างใน Docker
DB_URL = "postgresql://admin:password123@localhost:5432/air_quality_db"
engine = create_engine(DB_URL)

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="PM2.5 Live Monitor",
    page_icon="🌪️",
    layout="wide"
)

# ================= FUNCTION: ดึงข้อมูล =================
def load_data():
    try:
        # ดึง 100 แถวล่าสุด (เพื่อให้กราฟไม่รกเกินไป)
        query = "SELECT * FROM bangkok_air_quality ORDER BY timestamp DESC LIMIT 100"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        return pd.DataFrame() # ส่งค่าว่างกลับไปถ้า Error

# ================= MAIN DASHBOARD UI =================
st.title("🌪️ Real-time Air Quality Pipeline")
st.markdown("### Monitoring System: MinIO (Lake) ➡️ Pandas (Transform) ➡️ PostgreSQL (Warehouse)")

# สร้าง Placeholder เพื่อให้ข้อมูลอัปเดตในจุดเดิม (ไม่กระพริบทั้งหน้า)
placeholder = st.empty()

# Loop ตลอดไปเพื่อทำ Auto-Refresh
while True:
    df = load_data()
    
    with placeholder.container():
        if not df.empty:
            # เตรียมข้อมูลล่าสุด (แถวบนสุด เพราะ order desc)
            latest = df.iloc[0]
            
            # --- ส่วนที่ 1: KPI Metrics (ตัวเลขใหญ่ๆ) ---
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(label="📍 Location", value=latest['city'])
            
            with col2:
                # คำนวณความเปลี่ยนแปลงจากข้อมูลก่อนหน้า (Delta)
                prev_pm25 = df.iloc[1]['pm25'] if len(df) > 1 else latest['pm25']
                delta = latest['pm25'] - prev_pm25
                st.metric(label="PM2.5 (µg/m³)", value=f"{latest['pm25']}", delta=f"{delta:.1f}", delta_color="inverse")
            
            with col3:
                st.metric(label="🌡️ Temperature", value=f"{latest['temp']} °C")
                
            with col4:
                # แสดงสถานะความเสี่ยงแบบมีสี
                risk = latest.get('risk_level', 'Unknown')
                if risk == "Good":
                    st.success(f"Status: {risk}")
                elif risk in ["Moderate", "Unhealthy for Sensitive"]:
                    st.warning(f"Status: {risk}")
                else:
                    st.error(f"Status: {risk}")

            st.markdown("---") # เส้นขีดคั่น

            # --- ส่วนที่ 2: Charts (กราฟ) ---
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.subheader("📉 PM2.5 & Wind Speed Trend")
                # กราฟเส้น PM2.5
                st.line_chart(df.set_index('timestamp')[['pm25', 'wind_speed']])
            
            with chart_col2:
                st.subheader("📊 Temperature vs Humidity")
                st.line_chart(df.set_index('timestamp')[['temp', 'humidity']])

            # --- ส่วนที่ 3: Raw Data (ตาราง) ---
            with st.expander("🔎 View Recent Raw Data (From PostgreSQL)"):
                st.dataframe(df)
                
            # แสดงเวลาที่อัปเดตล่าสุด
            st.caption(f"Last updated: {time.strftime('%H:%M:%S')}")

        else:
            st.warning("⚠️ No data found in Database. Please run the Pipeline script (main.py) first.")
    
    # รอ 5 วินาทีแล้วโหลดใหม่ (Auto-Refresh)
    time.sleep(5)