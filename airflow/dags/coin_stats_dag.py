from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from coin_sentiment_stats import calculate_coin_sentiment  # ✅ 감성 분석 점수 계산 함수 불러오기

# ✅ DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 16),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),  # ✅ DAG 실행 주기와 동일하게 설정 (5분)
}

# ✅ DAG 정의
dag = DAG(
    'coin_sentiment_dag',
    default_args=default_args,
    description='코인별 감성 분석 점수 계산 DAG',
    schedule_interval=timedelta(minutes=5),  # ✅ 5분마다 실행
    catchup=False  # ✅ 과거 데이터 반영 X (필요하면 True로 변경)
)

# ✅ PythonOperator로 감성 분석 함수 실행
def run_sentiment_task(**kwargs):
    """✅ 코인 감성 분석 점수 실행 함수"""
    result = calculate_coin_sentiment()
    kwargs['task_instance'].xcom_push(key='sentiment_result', value=result)  # ✅ 실행 결과 저장

run_coin_sentiment_task = PythonOperator(
    task_id='run_coin_sentiment_analysis',
    python_callable=run_sentiment_task,
    provide_context=True,
    dag=dag,
)

run_coin_sentiment_task

