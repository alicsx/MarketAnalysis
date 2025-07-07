# main.py
import os
import requests
import random
import json
from datetime import datetime, timedelta
import feedparser

# آدرس فید RSS را می‌توانید از گزینه‌های قبلی انتخاب کنید
NEWS_RSS_URL = "https://www.investing.com/rss/news_25.rss"

# --- کلیدواژه‌های نهایی و بسیار گسترده ---
POSITIVE_KEYWORDS = [
    # سیاسی و دیپلماتیک
    "agreement", "deal", "peace", "truce", "accord", "resolution", "talks", "summit", 
    "cooperation", "ceasefire", "negotiation", "successful", "stability", "détente",
    
    # اقتصادی مثبت
    "growth", "recover", "rebound", "expansion", "boom", "strong", "upbeat", "beats estimates", 
    "better-than-expected", "stimulus", "easing", "dovish", "rate cut", "surplus", 
    "employment", "hiring", "manufacturing", "pmi", "gdp", "upward revision",

    # احساسات بازار مثبت
    "optimism", "confidence", "rally", "surge", "gains", "bullish", "risk-on", "record high",
    "breakthrough", "innovation", "outperform", "risk appetite"
]

NEGATIVE_KEYWORDS = [
    # سیاسی و ژئوپلیتیک
    "conflict", "sanction", "crisis", "war", "uncertainty", "dispute", "tension", 
    "protest", "deadlock", "veto", "threat", "escalation", "unrest", "instability", "geopolitical",

    # اقتصادی منفی
    "recession", "downturn", "slowdown", "contraction", "inflation", "fears", "deficit", "debt",
    "worse-than-expected", "disappointing", "misses estimates", "rate hike", "tightening", 
    "hawkish", "jobless", "unemployment", "layoffs", "bankruptcy", "default", "bubble",

    # احساسات بازار منفی
    "panic", "sell-off", "crash", "slump", "tumble", "losses", "bearish", "risk-off", 
    "volatile", "fear", "contagion", "vix", "correction", "headwinds"
]


def get_political_sentiment():
    try:
        feed = feedparser.parse(NEWS_RSS_URL)
        sentiment_score = 0
        for entry in feed.entries[:30]: # بررسی 30 تیتر آخر
            full_text = entry.title.lower() + " " + entry.summary.lower()
            for keyword in POSITIVE_KEYWORDS:
                if keyword in full_text: sentiment_score += 1
            for keyword in NEGATIVE_KEYWORDS:
                if keyword in full_text: sentiment_score -= 1
        return sentiment_score
    except:
        return 0

# ... (بقیه توابع get_news_impact و get_ai_recommendation را از پاسخ قبلی کپی کنید) ...
# در اینجا برای کامل بودن، مجدداً آورده شده‌اند

def get_news_impact():
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key: return 0
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        r = requests.get(f'https://finnhub.io/api/v1/calendar/economic?from={today}&to={today}&token={api_key}')
        news_events = r.json().get('economicCalendar', [])
        if not news_events: return 0
        highest_impact = 0; now = datetime.now()
        for event in news_events:
            event_time = datetime.fromisoformat(event.get('time', '').replace('Z', '+00:00')).replace(tzinfo=None)
            if now < event_time < (now + timedelta(hours=2)):
                if int(event.get('impact', 0)) > highest_impact:
                    highest_impact = int(event.get('impact', 0))
        return highest_impact
    except:
        return 0

def get_ai_recommendation():
    technical_score = random.randint(-100, 100)
    news_impact = get_news_impact()
    political_score = get_political_sentiment()
    final_score = technical_score + (political_score * 10)
    recommendation = "HOLD"

    if news_impact >= 3: recommendation = "AVOID_NEWS"
    elif political_score <= -5: recommendation = "AVOID_POLITICAL_RISK"
    elif final_score > 80: recommendation = "STRONG_BUY"
    elif final_score > 40: recommendation = "BUY"
    elif final_score < -80: recommendation = "STRONG_SELL"
    elif final_score < -40: recommendation = "SELL"
        
    output = {"final_score": final_score, "news_impact": news_impact, "political_score": political_score, "recommendation": recommendation}
    return output

if __name__ == "__main__":
    final_analysis = get_ai_recommendation()
    with open("sentiment.txt", "w") as f:
        json.dump(final_analysis, f)
    print(f"Analysis updated: {final_analysis}")
