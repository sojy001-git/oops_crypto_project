import pymysql
from datetime import datetime
import os
from dotenv import load_dotenv  

# ✅ .env 파일 로드 (API 키 보안 처리)
load_dotenv("/opt/airflow/.env")

# ✅ MySQL 연결 설정
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT")),
    "cursorclass": pymysql.cursors.DictCursor
}

def update_coin_prospects():
    """ ✅ 최신 coin_score 값을 coin 테이블의 prospects 컬럼으로 업데이트 """
    try:
        print("✅ MySQL 연결 중...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("✅ coin 테이블의 prospects 값 업데이트 중...")
        query = """
            UPDATE coin c
            JOIN (
                SELECT css.coin_id, css.coin_score
                FROM coin_sentiment_stats css
                WHERE css.time = (SELECT MAX(time) FROM coin_sentiment_stats WHERE coin_id = css.coin_id)
            ) latest_scores
            ON c.coin_id = latest_scores.coin_id
            SET c.prospects = latest_scores.coin_score;
        """
        cursor.execute(query)
        conn.commit()

        print("✅ coin 테이블 업데이트 완료!")
    except pymysql.MySQLError as e:
        print(f"❌ MySQL 오류: {e}")
    finally:
        cursor.close()
        conn.close()
        print("🔹 MySQL 연결 종료")

update_coin_prospects()
