#!/bin/bash

# ✅ Airflow 환경 설정
export PATH="/opt/airflow/venv/bin:$PATH" 
export AIRFLOW_HOME=/opt/airflow

# ✅ MySQL RDS가 완전히 실행될 때까지 대기
echo "Waiting for MySQL to be ready..."
until mysqladmin ping -h "$DB_HOST" --silent; do
    echo "MySQL is unavailable - sleeping"
    sleep 5
done

# ✅ MySQL 테이블 자동 생성
echo "Creating tables in MySQL RDS..."
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD --default-character-set=utf8mb4 < /opt/airflow/init.sql
echo "init.sql execution finished!"

# ✅ Airflow DB 초기화 (최초 실행 시에만)
if [ ! -f /opt/airflow/initialized ]; then
    airflow db init
    touch /opt/airflow/initialized  # 초기화 완료 표시
fi

# ✅ **관리자 계정이 없으면 자동 생성**
echo "Checking if Airflow admin user exists..."
airflow users list | grep "${_AIRFLOW_WWW_USER_USERNAME:-admin}"
if [ $? -ne 0 ]; then
    echo "Creating Airflow admin user..."
    airflow users create \
        --username "${_AIRFLOW_WWW_USER_USERNAME:-admin}" \
        --firstname "Admin" \
        --lastname "User" \
        --role "Admin" \
        --email "admin@example.com" \
        --password "${_AIRFLOW_WWW_USER_PASSWORD:-admin}"
else
    echo "Admin user already exists, skipping creation."
fi

# ✅ DAG가 완전히 로드될 때까지 대기 후 DAG 실행
echo "Waiting for DAGs to be available..."
MAX_RETRIES=30  # 최대 30번(5분)까지 체크
RETRY_INTERVAL=10  # 10초마다 확인

DAG_LIST=(
    "crypto_news_crawler"
    "crypto_news_sentiment_analysis"
    "coin_sentiment_dag"
    "update_coin_prospects"
)

for DAG in "${DAG_LIST[@]}"; do
    for ((i=1; i<=MAX_RETRIES; i++)); do
        if airflow dags list | grep -q "$DAG"; then
            echo "DAG $DAG is now available!"
            break
        fi
        echo "DAG $DAG is not available yet - sleeping ($i/$MAX_RETRIES)..."
        sleep $RETRY_INTERVAL
    done
done

# ✅ 최초 실행 시에만 DAG 활성화 & 실행
if [ ! -f /opt/airflow/dags_initialized ]; then
    echo "Activating and triggering DAGs..."
    
    for DAG in "${DAG_LIST[@]}"; do
        echo "Unpausing DAG: $DAG"
        airflow dags unpause "$DAG"
        sleep 3
        echo "Triggering DAG: $DAG"
        airflow dags trigger "$DAG"
    done

    touch /opt/airflow/dags_initialized  # ✅ DAG 초기화 완료 표시
fi

# ✅ Airflow 웹 서버 실행
exec airflow webserver -p 8080
