import feedparser
import openai
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime

# ✅ 환경변수에서 보안 정보 가져오기
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# ✅ OpenAI 클라이언트 초기화
if OPENAI_API_KEY is None:
    print("❌ 오류: OPENAI_API_KEY가 환경변수에 없습니다.")
    client = None
else:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ 1. 실시간 뉴스 가져오기
def get_stock_news():
    url = 'https://www.investing.com/rss/news_301.rss'
    feed = feedparser.parse(url)
    news_items = feed.entries[:5]
    news_text = ""
    for item in news_items:
        title = getattr(item, 'title', '제목 없음')
        summary = getattr(item, 'summary', getattr(item, 'description', ''))
        news_text += f"제목: {title}\n"
        if summary:
            news_text += f"요약: {summary}\n"
        news_text += "\n"
    return news_text.strip()

# ✅ 2. GPT 분석 요청
def ask_gpt(news_text):
    if client is None:
        return "❌ 오류: GPT 클라이언트 초기화 실패"

    today = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"""
오늘은 {today}입니다.

미국 주식 뉴스 요약:

{news_text}

아래 내용을 작성해줘:

1. 시장 전반 흐름 요약 (2~3줄)
2. 📌 단기 투자 종목 (1~2일 수익 가능, 이유 포함)
3. 📆 일주일 투자 종목 (업계 이슈 기반, 이유 포함)
4. 📅 한 달 투자 종목 (중기 상승 기대, 이유 포함)

실제 상장된 미국 종목만 추천하고, 뉴스 기반으로 종목 추천해줘.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 호출 오류: {e}"

# ✅ 3. 이메일 전송 함수
def send_email(subject, body):
    if EMAIL_ADDRESS is None or EMAIL_PASSWORD is None:
        print("❌ 오류: 이메일 주소 또는 비밀번호 환경변수 누락")
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
        print(f"❌ 이메일 전송 실패: {e}")

# ✅ 실행
if __name__ == "__main__":
    if OPENAI_API_KEY and EMAIL_ADDRESS and EMAIL_PASSWORD:
        print("🔍 뉴스 수집 중...")
        news = get_stock_news()

        if news:
            print("🧠 GPT 분석 중...")
            result = ask_gpt(news)

            print("📧 이메일 전송 중...")
            if "GPT 호출 오류:" in result or "초기화 실패" in result:
                print(result)
            else:
                send_email("📈 오늘의 미국 주식 추천 리포트", result)
        else:
            print("❌ 뉴스 없음. 종료")
    else:
        print("❌ 환경변수 설정 누락. 실행 불가")
