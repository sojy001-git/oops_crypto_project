import pymysql
import openai
import os
import json  # ✅ JSON 변환을 위해 추가
from datetime import datetime
from dotenv import load_dotenv  

# ✅ .env 파일 로드 (API 키 보안 처리)
load_dotenv("/opt/airflow/.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 환경 변수에서 API 키 로드

if not OPENAI_API_KEY:
    raise ValueError("❌ OpenAI API 키가 설정되지 않았습니다! .env 파일을 확인하세요.")

openai_client = openai.Client(api_key=OPENAI_API_KEY)  # ✅ 최신 버전 호환 OpenAI 클라이언트 생성

# ✅ MySQL 연결 설정
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT")),
    "cursorclass": pymysql.cursors.DictCursor
}

def analyze_sentiment_with_gpt(text):
    """ ✅ 최신 OpenAI API 방식으로 감성 분석 수행 """
    try:
        prompt = f"""
You are an expert in cryptocurrency sentiment analysis.
Analyze the sentiment of the following news article and return ONLY a JSON response.

The JSON response format must be:
{{
    "sentiment_label": "Positive", "Negative", or "Neutral",
    "sentiment_score": a float number between -1.0 and 1.0
}}

News Content:
{text}

Now, generate the JSON response:
"""
        
        response = openai_client.chat.completions.create(  # ✅ 최신 API 방식으로 변경
            model="gpt-4o-mini",  # ✅ 최신 모델 사용
            messages=[{"role": "system", "content": "You are a cryptocurrency sentiment analysis expert."},
                      {"role": "user", "content": prompt}],
            temperature=0.3,  # ✅ 응답의 일관성을 유지하면서 비용 절약
            max_tokens=200  # ✅ 응답 길이 제한 (비용 절감)
        )
        
        # ✅ GPT 응답 확인 (디버깅)
        gpt_output = response.choices[0].message.content.strip()
        print(f"🧐 GPT 응답 원본: {gpt_output}")  # 🔥 GPT 응답을 그대로 출력하여 확인

        # ✅ GPT 응답을 JSON 변환
        try:
            gpt_output = json.loads(gpt_output)  # ✅ JSON 변환 (eval() 대신 사용)
        except json.JSONDecodeError:
            print(f"⚠️ GPT 응답 JSON 변환 오류: {gpt_output}")
            return 0, "Neutral"

        sentiment_label = gpt_output.get("sentiment_label", "Neutral")
        sentiment_score = float(gpt_output.get("sentiment_score", 0))

        return sentiment_score, sentiment_label

    except openai.OpenAIError as e:
        print(f"⚠️ GPT 감성 분석 오류: {e}")
        return 0, "Neutral"

def update_news_sentiment():
    """ ✅ 뉴스 본문을 가져와 감성 분석 후 MySQL `news_sentiment` 테이블에 업데이트 """
    try:
        print("✅ MySQL 연결 중...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("✅ 감성 분석할 뉴스 조회 중...")
        query = """
        SELECT news_id, title_en, content_en 
        FROM news 
        WHERE news_id NOT IN (SELECT news_id FROM news_sentiment);
        """
        cursor.execute(query)
        news_data = cursor.fetchall()

        if not news_data:
            print("✅ 감성 분석할 뉴스가 없음")
            return

        print(f"✅ 감성 분석할 뉴스 {len(news_data)}개 찾음!")

        insert_query = """
        INSERT INTO news_sentiment (news_id, sentiment_score, sentiment_label)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE sentiment_score = VALUES(sentiment_score), sentiment_label = VALUES(sentiment_label);
        """

        processed_count = 0  

        for news in news_data:
            news_id, title_en, content_en = news["news_id"], news["title_en"] or "", news["content_en"] or ""

            # 🔥 제목과 본문을 결합하여 감성 분석
            full_text = f"{title_en}. {content_en}".strip()

            # 🔥 본문이 짧아도 감성 분석 수행
            sentiment_score, sentiment_label = analyze_sentiment_with_gpt(full_text)

            # ✅ 감성 분석 결과 즉시 프린트 출력
            print("\n=======================")
            print(f" 📰 뉴스 ID: {news_id}")
            print(f" 📰 뉴스 제목 (영어): {title_en}")
            print(f" 📄 뉴스 본문 (영어 200자 미리보기): {content_en[:200]}...")
            print(f" ✅ 감성 분석 결과: {sentiment_label} ({sentiment_score})")
            print("=======================\n")

            try:
                cursor.execute(insert_query, (news_id, sentiment_score, sentiment_label))
                processed_count += 1
            except pymysql.MySQLError as e:
                print(f"❌ MySQL 저장 오류 (news_id {news_id}): {e}")

        conn.commit()
        print(f"✅ {processed_count} 개의 뉴스 감성 분석 완료 및 저장됨!")

    except pymysql.MySQLError as e:
        print(f"❌ MySQL 오류: {e}")

    except Exception as e:
        print(f"❌ 기타 오류 발생: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("🔹 MySQL 연결 종료")

print("🔹 감성 분석 DAG 실행 준비 완료")
update_news_sentiment()
