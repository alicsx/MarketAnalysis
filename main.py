# main.py
import os, requests, random, json, feedparser, joblib, numpy as np
from datetime import datetime, timedelta

NEWS_RSS_URL = "https://www.investing.com/rss/news_25.rss"
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
        score = 0
        for entry in feed.entries[:30]:
            text = (entry.title + " " + entry.summary).lower()
            score += sum(1 for k in POSITIVE_KEYWORDS if k in text)
            score -= sum(1 for k in NEGATIVE_KEYWORDS if k in text)
        return score
    except: return 0

def get_news_impact():
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key: return 0
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        r = requests.get(f'https://finnhub.io/api/v1/calendar/economic?from={today}&to={today}&token={api_key}')
        events = r.json().get('economicCalendar', [])
        impact = 0
        now = datetime.now()
        for event in events:
            event_time = datetime.fromisoformat(event.get('time', '').replace('Z', '+00:00')).replace(tzinfo=None)
            if now < event_time < (now + timedelta(hours=2)) and int(event.get('impact', 0)) > impact:
                impact = int(event.get('impact', 0))
        return impact
    except: return 0

def get_ai_recommendation():
    try:
        model = joblib.load('market_model.joblib')
        political_score = get_political_sentiment()
        news_impact = get_news_impact()
        features = np.array([[political_score, news_impact]])
        prediction = model.predict(features)[0]
        probability = max(model.predict_proba(features)[0])
        recommendation_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
        return {
            "prediction": int(prediction),
            "recommendation": recommendation_map.get(prediction, "HOLD"),
            "confidence": round(probability, 2),
            "political_score": political_score,
            "news_impact": news_impact
        }
    except Exception as e:
        return {"recommendation": "ERROR", "confidence": 0, "error": str(e)}

if __name__ == "__main__":
    analysis = get_ai_recommendation()
    with open("sentiment.txt", "w") as f: json.dump(analysis, f)
    print(f"Analysis updated: {analysis}")
