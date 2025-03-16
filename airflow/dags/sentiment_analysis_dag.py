from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 16),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "crypto_news_sentiment_analysis",
    default_args=default_args,
    description="Perform sentiment analysis on crypto news and update DB",
    schedule_interval="*/5 * * * *",  # 🔥 5분마다 실행
    catchup=False,
)

def run_sentiment_analysis():
    subprocess.run(["python3", "/opt/airflow/dags/news_sentiment.py"], check=True)

sentiment_task = PythonOperator(
    task_id="update_news_sentiment",
    python_callable=run_sentiment_analysis,
    dag=dag,
)

sentiment_task
