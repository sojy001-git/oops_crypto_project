#!/bin/bash

# ✅ Airflow 환경 설정
export PATH="/opt/airflow/venv/bin:$PATH"
export AIRFLOW_HOME=/opt/airflow

# ✅ Airflow 스케줄러 실행
exec airflow scheduler
