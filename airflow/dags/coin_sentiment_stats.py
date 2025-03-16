import pymysql
from datetime import datetime
from dotenv import load_dotenv  
import os 

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

def calculate_coin_sentiment():
    """ ✅ 코인별 감성 분석 점수 계산 & 변경된 경우에만 MySQL 저장 """
    try:
        print("✅ MySQL 연결 중...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("✅ 코인별 감성 분석 점수 계산 중...")

        # ✅ 1️⃣ 코인별 감성 분석 점수 계산 (-1 ~ 1 범위로 변환)
        query = """
        WITH SentimentStats AS (
            SELECT 
                c.coin_id,
                COUNT(n.news_id) AS total_news,
                SUM(CASE WHEN ns.sentiment_label = 'Positive' THEN 1 ELSE 0 END) AS positive_news,
                SUM(CASE WHEN ns.sentiment_label = 'Negative' THEN 1 ELSE 0 END) AS negative_news,
                SUM(CASE WHEN ns.sentiment_label = 'Neutral' THEN 1 ELSE 0 END) AS neutral_news,
                SUM(
                    (CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, n.uploadtime, NOW()) < 30 THEN 1.5  
                        WHEN TIMESTAMPDIFF(HOUR, n.uploadtime, NOW()) < 6 THEN 1.2  
                        ELSE 1.0  
                    END) 
                    * ns.sentiment_score
                ) / SUM(
                    CASE 
                        WHEN TIMESTAMPDIFF(MINUTE, n.uploadtime, NOW()) < 30 THEN 1.5
                        WHEN TIMESTAMPDIFF(HOUR, n.uploadtime, NOW()) < 6 THEN 1.2
                        ELSE 1.0
                    END
                ) AS coin_score
            FROM news_sentiment ns
            JOIN news n ON ns.news_id = n.news_id
            JOIN news_coin_relation ncr ON n.news_id = ncr.news_id
            JOIN coin c ON ncr.coin_id = c.coin_id
            WHERE n.uploadtime >= NOW() - INTERVAL 24 HOUR
            GROUP BY c.coin_id
        )
        SELECT 
            coin_id,
            ROUND(coin_score, 2) AS normalized_coin_score
        FROM SentimentStats;
        """
        cursor.execute(query)
        coin_sentiment_data = cursor.fetchall()

        if not coin_sentiment_data:
            print("✅ 저장할 감성 분석 데이터 없음")
            return

        # ✅ 2️⃣ 기존 감성 분석 점수 가져오기
        cursor.execute("SELECT coin_id, coin_score FROM coin_sentiment_stats")
        existing_scores = {row["coin_id"]: row["coin_score"] for row in cursor.fetchall()}

        # ✅ 3️⃣ `coin_sentiment_stats` 테이블에 저장하는 SQL (점수가 변한 경우만 저장)
        insert_query = """
        INSERT INTO coin_sentiment_stats (coin_id, time, coin_score)
        VALUES (%s, NOW(), %s)
        """

        updated_count = 0
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ✅ 현재 시간 저장

        for row in coin_sentiment_data:
            coin_id = row["coin_id"]
            new_coin_score = row["normalized_coin_score"]
            prev_coin_score = existing_scores.get(coin_id, None)  # 기존 점수 가져오기

            # ✅ 기존 점수와 비교하여 변경 여부 확인
            if prev_coin_score is None:
                cursor.execute(insert_query, (coin_id, new_coin_score))
                updated_count += 1
                print(f"✅ 코인 ID {coin_id} - 감성 점수 **처음 저장됨**: {new_coin_score} (저장 시간: {current_time})")
            elif prev_coin_score != new_coin_score:
                cursor.execute(insert_query, (coin_id, new_coin_score))
                updated_count += 1
                print(f"✅ 코인 ID {coin_id} - 감성 점수 **변경됨**: {prev_coin_score} → {new_coin_score} (저장 시간: {current_time})")
            else:
                print(f"🔹 코인 ID {coin_id} - 감성 점수 변경 없음: {new_coin_score} (기존 점수: {prev_coin_score})")

        conn.commit()

        if updated_count > 0:
            print(f"\n✅ {updated_count}개의 코인 감성 분석 점수 업데이트 완료! (저장 시간: {current_time})")
        else:
            print("\n✅ 모든 코인의 감성 분석 점수가 동일하여 저장하지 않음.")

    except pymysql.MySQLError as e:
        print(f"❌ MySQL 오류: {e}")

    finally:
        cursor.close()
        conn.close()
        print("🔹 MySQL 연결 종료")

print("🔹 코인 감성 분석 DAG 실행 준비 완료")
calculate_coin_sentiment()

