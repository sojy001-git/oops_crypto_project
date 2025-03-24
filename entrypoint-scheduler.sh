#!/bin/bash

# ✅ Airflow 환경 설정
export PATH="/opt/airflow/venv/bin:$PATH"
export AIRFLOW_HOME=/opt/airflow

# ✅ DB가 초기화 안 됐으면 init 실행
if [ ! -f /opt/airflow/initialized ]; then
    echo "Initializing Airflow DB..."
    airflow db init
    touch /opt/airflow/initialized
else
    echo "Airflow DB already initialized."
fi

# ✅ Airflow 스케줄러 실행
exec airflow scheduler
