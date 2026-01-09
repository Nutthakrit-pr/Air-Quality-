# 🌪️ End-to-End Air Quality Data Pipeline

## 📖 Overview
This project is an automated **ETL (Extract, Transform, Load) pipeline** designed to monitor and analyze real-time PM2.5 air quality and weather conditions in **Bangkok**. 

The system utilizes a **Modern Data Stack** approach, leveraging **Docker** to containerize a Data Lake (MinIO) and a Data Warehouse (PostgreSQL). It fetches data from external APIs, processes it using Python/Pandas to ensure data integrity, and visualizes actionable insights via an interactive **Streamlit** dashboard.

## 🏗️ Architecture
The pipeline follows a robust flow from raw data ingestion to analytical serving:

1.  **Ingestion:** Python scripts fetch data from OpenWeatherMap & AQICN APIs.
2.  **Data Lake (Raw):** Raw JSON responses are stored in **MinIO** for auditability.
3.  **Transformation:** Data is cleaned, validated, and enriched (e.g., Risk Level calculation) using **Pandas**.
4.  **Data Warehouse (Serving):** Structured data is loaded into **PostgreSQL**.
5.  **Visualization:** **Streamlit** queries the warehouse to display real-time trends.

![System Architecture](./final_project_architecture.png)
*(Note: Upload the diagram image generated earlier to your repo and reference it here)*

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Containerization:** Docker & Docker Compose
* **Storage:**
    * **Data Lake:** MinIO (S3 Compatible)
    * **Data Warehouse:** PostgreSQL
* **Processing:** Pandas, SQLAlchemy
* **Visualization:** Streamlit, Plotly
* **APIs:** OpenWeatherMap, AQICN (World Air Quality Index)

## 🚀 Features
* ✅ **Automated Data Collection:** Runs continuously to fetch real-time environmental data.
* ✅ **Data Quality Checks:** Automatically handles missing values and filters outliers (e.g., temp > 60°C).
* ✅ **Hybrid Storage:** Implements the "Lakehouse" concept by separating raw logs from structured SQL tables.
* ✅ **Interactive Dashboard:** Live monitoring of PM2.5, Temperature, and Health Risk Levels.
