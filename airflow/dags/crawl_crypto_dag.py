from airflow import DAG
from airflow.operators.python import PythonOperator
import subprocess
from datetime import datetime, timedelta

# DAG 기본 설정
default_args = {
    "owner": "airflow",
    "depends_on_past": True,
    "start_date": datetime(2024, 2, 16),  # DAG 시작 날짜
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# 크롤링 실행 함수 (crypto_crawler.py 실행)
def run_crypto_crawler():
    subprocess.run(["python3", "/opt/airflow/dags/crypto_crawler.py"], check=True)

# DAG 생성 (5분마다 실행)
dag = DAG(
    "crypto_news_crawler",
    default_args=default_args,
    description="CryptoPanic 뉴스 크롤러 DAG",
    schedule_interval="*/5 * * * *",  # 매 5분마다 실행
    catchup=False,
    max_active_runs=1,
    concurrency=1,
)

# PythonOperator를 사용해 크롤링 코드 실행
run_crawler = PythonOperator(
    task_id="run_crypto_crawler",
    python_callable=run_crypto_crawler,
    dag=dag,
)

run_crawler
