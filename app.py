# app.py
import requests
from bs4 import BeautifulSoup
import openai
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

NEWS_SOURCES = {
    "CNBC": {
        "url": "https://www.cnbc.com/world/?region=world",
        "tag": "a",
        "attrs": {"class": "Card-title"},
    },
    "Yahoo Finance": {
        "url": "https://finance.yahoo.com/",
        "tag": "h3",
        "attrs": {"class": "Mb(5px)"},
    },
    "Investing.com": {
        "url": "https://www.investing.com/news/stock-market-news",
        "tag": "a",
        "attrs": {"class": "title"},
    }
}

def collect_all_news():
    all_news = {}
    for source, info in NEWS_SOURCES.items():
        try:
            response = requests.get(info["url"], headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all(info["tag"], attrs=info["attrs"])
            titles = [a.get_text(strip=True) for a in articles if a.get_text(strip=True)]
            all_news[source] = titles[:10]
        except Exception as e:
            all_news[source] = []
    return all_news

def ask_gpt_from_news(news_dict):
    if client is None:
        return "GPT 클라이언트 오류"

    today_str = datetime.now().strftime("%Y년 %m월 %d일")

    news_summary = ""
    for source, titles in news_dict.items():
        news_summary += f"📰 {source} 뉴스:\n"
        for title in titles:
            news_summary += f"- {title}\n"
        news_summary += "\n"

    prompt = f"""
오늘은 {today_str}입니다.
다음은 주요 미국 증시 관련 뉴스 제목들입니다:

{news_summary}

이 제목들을 기반으로 아래 항목을 작성해줘:

1. 시장 전반 흐름 요약 (2~3줄)
2. 📌 단기 투자 종목 (1~2일 내 수익 가능성 예상, 종목 코드 포함)
3. 📆 일주일 투자 종목 (업계 이슈 기반으로 주간 상승 기대)
4. 📅 한 달 투자 종목 (중기 상승 가능성 높은 기업)

각 추천 종목마다 이유도 간단하게 써줘. 중복되어도 괜찮고, **오늘 날짜 기준임을 명확히 해줘.**
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 오류: {e}"

def send_email(subject, body):
    if EMAIL_ADDRESS is None or EMAIL_PASSWORD is None:
        return

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ 이메일 발송 완료!")
    except Exception as e:
        print(f"❌ 이메일 전송 오류: {e}")

if __name__ == "__main__":
    if OPENAI_API_KEY and EMAIL_ADDRESS and EMAIL_PASSWORD:
        news_data = collect_all_news()
        analysis = ask_gpt_from_news(news_data)
        send_email("📈 오늘의 미국 주식 리포트", analysis)
    else:
        print("❌ 환경 변수 누락: OPENAI_API_KEY, EMAIL_ADDRESS, EMAIL_PASSWORD가 필요합니다.")
