import requests
import pymysql
import os 
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta


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

# ✅ 허용된 10개 코인 리스트 (MySQL의 coin_id와 매칭)
ALLOWED_TICKERS = {
    "KRW-XRP": (1, "XRP"),
    "KRW-BTC": (2, "BTC"),
    "KRW-ETH": (3, "ETH"),
    "KRW-QTUM": (4, "QTUM"),
    "KRW-WAVES": (5, "WAVES"),
    "KRW-XEM": (6, "XEM"),
    "KRW-ETC": (7, "ETC"),
    "KRW-NEO": (8, "NEO"),
    "KRW-SNT": (9, "SNT"),
    "KRW-MTL": (10, "MTL")
}

# ✅ CryptoPanic API 설정
API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
API_URL = f"https://cryptopanic.com/api/v1/posts/?auth_token={API_KEY}"

# ✅ ChromeDriver 실행 (Selenium 사용)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# ✅ 날짜 변환 함수 (UTC → KST)
def parse_datetime(time_str):
    try:
        if not time_str:
            return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if "T" in time_str and "Z" in time_str:
            dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=9)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"❌ 날짜 변환 오류: {e}")
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# ✅ 티커 변환 & 10개 코인 필터링
def get_coin_info(ticker):
    if not ticker.startswith("KRW-"):
        ticker = f"KRW-{ticker}"
    return ALLOWED_TICKERS.get(ticker, None)

# ✅ 뉴스 본문 가져오기 (Selenium 크롤링)
def get_news_content(news_url):
    try:
        driver.get(news_url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        content_element = soup.select_one("div.description-body, div.article-content, div.entry-content, div.post-content, article")
        if content_element:
            article_text = "\n".join([p.get_text().strip() for p in content_element.find_all("p") if p.get_text().strip()])
        else:
            paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 10]
            article_text = "\n".join(paragraphs) if paragraphs else "본문 없음"

        if not article_text.strip() or len(article_text) < 10:
            return None, None

        translated_text = GoogleTranslator(source="en", target="ko").translate(article_text[:5000])
        return article_text, translated_text
    except Exception as e:
        print(f"❌ 본문 크롤링 오류: {e}")
        return None, None
        
# ✅ 특정 뉴스 제외하는 필터링 함수 추가
def should_exclude_news(content_en):
    """ 특정 뉴스 필터링 (트위터 뉴스, 유튜브 뉴스, 쿠키 메시지) """
    # ✅ 2️⃣ 쿠키 관련 메시지 필터링
    if any(keyword in content_en.lower() for keyword in ["cookie", "accept", "privacy policy", "terms of service"]):
        return True
        
# ✅ 뉴스 크롤링 & 저장
news_data = []
news_coin_relations = []
filtered_articles = 0  
duplicate_news = 0  

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    response = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    data = response.json()

    if "results" not in data:
        print(f"API 응답에 'results' 키가 없음: {data}")
        exit()

    cursor.execute("SELECT source FROM news;")
    existing_sources = {row["source"] for row in cursor.fetchall()}

    for post in data["results"]:
        title_en = post["title"]
        title_ko = GoogleTranslator(source="en", target="ko").translate(title_en)
        crypto_panic_url = post["url"]

        if crypto_panic_url in existing_sources:
            duplicate_news += 1
            continue

        newspaper = post.get("source", {}).get("title", "N/A")

        content_en, content_ko = get_news_content(crypto_panic_url)
        if not content_en:
            continue
        
        #트위터, 유튜브 필터링   
        if should_exclude_news(content_en):
		        continue

        news_datetime = parse_datetime(post.get("published_at", ""))

        # ✅ 10개 코인만 필터링 & 중복 제거
        related_coins = list(set(get_coin_info(coin["code"]) for coin in post.get("currencies", []) if "code" in coin))
        related_coins = [coin for coin in related_coins if coin is not None]

        related_coin_ids = list(set(coin[0] for coin in related_coins))  # 코인 ID 중복 제거
        related_tickers = list(set(coin[1] for coin in related_coins))  # 코인 티커 중복 제거

        if not related_coin_ids:
            filtered_articles += 1
            continue

        # ✅ 뉴스 저장 (중복 업데이트)
        insert_news_query = """
        INSERT INTO news (title, title_en, content, content_en, newspaper, source, uploadtime)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title=VALUES(title), content=VALUES(content), uploadtime=VALUES(uploadtime);
        """
        cursor.execute(insert_news_query, (title_ko, title_en, content_ko, content_en, newspaper, crypto_panic_url, news_datetime))
        conn.commit()

        # ✅ 저장된 뉴스 ID 가져오기
        cursor.execute("SELECT news_id FROM news WHERE source = %s;", (crypto_panic_url,))
        news_row = cursor.fetchone()
        news_id = news_row["news_id"] if news_row else None

        if news_id:
            insert_relation_query = "INSERT IGNORE INTO news_coin_relation (news_id, coin_id) VALUES (%s, %s)"
            cursor.executemany(insert_relation_query, [(news_id, coin_id) for coin_id in related_coin_ids])
            conn.commit()

        print("\n ====================== ")
        print(f" 📰 뉴스 제목 (한글): {title_ko}")
        print(f" 📰 뉴스 제목 (영어): {title_en}")
        print(f" 📄 뉴스 본문 (한글 번역):\n{content_ko[:500]}...")
        print(f" 📄 뉴스 본문 (원본 영어):\n{content_en[:500]}...")
        print(f" 🏛️ 신문사: {newspaper}")
        print(f" 🔗 기사 소스: {crypto_panic_url}")
        print(f" 🕒 업로드 시간 (KST): {news_datetime}")
        print(f" 💰 관련 코인 ID: {related_coin_ids}")
        print(f" 💰 관련 코인 티커: {related_tickers}")
        print(" ====================== \n")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"크롤링 오류: {e}")

finally:
    driver.quit()

print(f"📌 코인이 없는 기사 {filtered_articles}개는 저장되지 않았습니다.") 
print(f"⚠️ 중복된 기사 {duplicate_news}개는 저장되지 않았습니다.")
