import requests
import pymysql
import os 
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
from selenium_stealth import stealth

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

# ✅ ScraperAPI 설정
#SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
#proxy = f"http://scraperapi:{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001"

# ✅ CryptoPanic API 설정
API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
API_URL = f"https://cryptopanic.com/api/v1/posts/?auth_token={API_KEY}"

# ✅ Selenium 드라이버 설정
def get_driver():
    options = uc.ChromeOptions()
    #options.add_argument(f"--proxy-server={proxy}")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")	
    options.add_argument("--disable-popup-blocking")
    options.add_argument("user-agent=Mozilla/5.0")
    
    driver = uc.Chrome(
    	options=options,
    	driver_executable_path="/opt/airflow/bin/chromedriver",
    	browser_executable_path="/opt/chrome/chrome"
    )

    stealth(driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
    )

    return driver

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

# ✅ 원본 주소 리디렉션 추적 (JavaScript 강제 클릭 버전)
def get_original_url_by_click(crypto_panic_url):
    driver = get_driver()
    try:
        driver.get(crypto_panic_url)

        # 🔎 아이콘 링크 요소 대기 (외부 링크 버튼)
        icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "h1.post-title > a > .icon-link-external"))
        )
        
        current_tabs = driver.window_handles

        # ✅ 자바스크립트로 강제 클릭
        driver.execute_script("arguments[0].click();", icon)
        print("✅ 외부 링크 아이콘 클릭 (JS 실행 완료)")
        
        # 새 탭이 열릴 때까지 대기
        WebDriverWait(driver, 10).until(
            lambda d: len(d.window_handles) > len(current_tabs)
        )

        # 새 탭으로 전환
        new_tab = [tab for tab in driver.window_handles if tab not in current_tabs][0]
        driver.switch_to.window(new_tab)
        print("✅ 새 탭으로 전환됨")
        print(f"🌐 현재 URL: {driver.current_url}")
        
        original_url = driver.current_url
        print(f"🔗 실제 JS 클릭으로 열린 원문 주소: {original_url}")
        return original_url

    except Exception as e:
        print(f"❌ JS 클릭 원문 링크 추출 실패: {e}")
        return crypto_panic_url

    finally:
        driver.quit()



# ✅ 본문 크롤링 함수 (CryptoPanic 요약용)
def get_news_content_from_cryptopanic(crypto_panic_url):
    driver = get_driver()
    try:
        driver.get(crypto_panic_url)

        time.sleep(6)  # ✅ 렌더링 기다림

        article_text = driver.execute_script(
            "return document.querySelector('.description-body')?.innerText || '';"
        )

        if not article_text or len(article_text.strip()) < 10:
            print("⚠️ 본문 비어 있음 (innerText 부족)")
            return None, None

        translated_text = GoogleTranslator(source="en", target="ko").translate(article_text[:5000])
        return article_text.strip(), translated_text

    except Exception as e:
        print(f"❌ 본문 크롤링 오류: {e}")
        return None, None

    finally:
        driver.quit()

        
# ✅ 트위터/유튜브/레딧 제외
def is_excluded_source(source_domain):
    exclude_list = ["twitter.com", "youtube.com", "youtu.be", "reddit.com"]
    return any(ex in source_domain for ex in exclude_list)
        
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
        source_domain = post.get("domain", "")
        newspaper = post.get("source", {}).get("title", "N/A")

        print("\n🔍 뉴스 검사 시작")
        print(f"📰 제목: {title_en}")
        print(f"🔗 중계 URL: {crypto_panic_url}")
        print(f"🌍 도메인: {source_domain}")
        print(f"🏛️ 신문사: {newspaper}")
        
        # ❌ 제외 도메인 차단
        if is_excluded_source(source_domain):
            print("🚫 제외된 도메인 (트위터/유튜브 등)")
            continue
            
        # 중복뉴스
        original_url = get_original_url_by_click(crypto_panic_url)      
        if original_url in existing_sources:
            print("⚠️ 이미 저장된 뉴스 (중복)")
            duplicate_news += 1
            continue

        # ✅ 본문 크롤링
        content_en, content_ko = get_news_content_from_cryptopanic(crypto_panic_url)
        if not content_en:
            print("⚠️ 본문 없음 or 크롤링 실패")
            continue	    
        else:
            print(f"✅ 본문 크롤링 성공 ({len(content_en)}자)")

        # ✅ 10개 코인만 필터링 & 중복 제거
        related_coins = list(set(get_coin_info(coin["code"]) for coin in post.get("currencies", []) if "code" in coin))
        related_coins = [coin for coin in related_coins if coin is not None]

        related_coin_ids = list(set(coin[0] for coin in related_coins))  # 코인 ID 중복 제거
        related_tickers = list(set(coin[1] for coin in related_coins))  # 코인 티커 중복 제거

        if not related_coin_ids:
            print(f"⚠️ 관련 코인 없음 → 저장 제외됨 (코인 목록: {[coin.get('code') for coin in post.get('currencies', [])]})")
            filtered_articles += 1
            continue
        else:
            print(f"✅ 관련 코인 있음 → IDs: {related_coin_ids}, Tickers: {related_tickers}")
            
        #날짜 파싱
        news_datetime = parse_datetime(post.get("published_at", ""))
        
        # ✅ 뉴스 저장 (중복 업데이트)
        print("✅ 이 뉴스는 DB에 저장됩니다.")        
        insert_news_query = """
        INSERT INTO news (title, title_en, content, content_en, newspaper, source, uploadtime)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title=VALUES(title), content=VALUES(content), uploadtime=VALUES(uploadtime);
        """
        cursor.execute(insert_news_query, (title_ko, title_en, content_ko, content_en, newspaper, original_url, news_datetime))
        conn.commit()

        # ✅ 저장된 뉴스 ID 가져오기
        cursor.execute("SELECT news_id FROM news WHERE source = %s;", (original_url,))
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
        print(f" 🔗 기사 소스: {original_url}")
        print(f" 🕒 업로드 시간 (KST): {news_datetime}")
        print(f" 💰 관련 코인 ID: {related_coin_ids}")
        print(f" 💰 관련 코인 티커: {related_tickers}")
        print(" ====================== \n")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"크롤링 오류: {e}")

print(f"📌 코인이 없는 기사 {filtered_articles}개는 저장되지 않았습니다.") 
print(f"⚠️ 중복된 기사 {duplicate_news}개는 저장되지 않았습니다.")
