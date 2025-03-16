from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from coin_update import update_coin_prospects  # ✅ Python 파일에서 함수 가져오기

# ✅ DAG 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 16),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'update_coin_prospects',  # DAG 이름
    default_args=default_args,
    description='Update coin prospects from latest coin_score',
    schedule_interval=timedelta(minutes=5),  # 5분마다 실행
    catchup=False  # 과거 실행은 무시
)

# ✅ PythonOperator 사용 (MySqlOperator 대신)
update_prospects_task = PythonOperator(
    task_id='update_prospects',
    python_callable=update_coin_prospects,  # ✅ Python 파일에서 가져온 함수 실행
    dag=dag
)

update_prospects_task

