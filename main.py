# main.py (Debugging Version)
import os
import requests
import random
import json
from datetime import datetime, timedelta
import feedparser
import joblib
import numpy as np

# --- بخش کلیدواژه‌ها بدون تغییر ---
NEWS_RSS_URL = "https://www.investing.com/rss/news_25.rss"
POSITIVE_KEYWORDS = ["agreement","deal","peace","truce","accord","resolution","talks","summit","cooperation","ceasefire","negotiation","successful","stability","détente","growth","recover","rebound","expansion","boom","strong","upbeat","beats estimates","better-than-expected","stimulus","easing","dovish","rate cut","surplus","employment","hiring","manufacturing","pmi","gdp","upward revision","optimism","confidence","rally","surge","gains","bullish","risk-on","record high","breakthrough","innovation","outperform","risk appetite"]
NEGATIVE_KEYWORDS = ["conflict","sanction","crisis","war","uncertainty","dispute","tension","protest","deadlock","veto","threat","escalation","unrest","instability","geopolitical","recession","downturn","slowdown","contraction","inflation","fears","deficit","debt","worse-than-expected","disappointing","misses estimates","rate hike","tightening","hawkish","jobless","unemployment","layoffs","bankruptcy","default","bubble","panic","sell-off","crash","slump","tumble","losses","bearish","risk-off","volatile","fear","contagion","vix","correction","headwinds"]

def get_political_sentiment():
    print("Step 1: Fetching political news from RSS...")
    try:
        feed = feedparser.parse(NEWS_RSS_URL)
        if not feed.entries:
            print("RSS feed is empty or could not be fetched.")
            return 0
        sentiment_score = 0
        for entry in feed.entries[:30]:
            text = (entry.title + " " + entry.summary).lower()
            score_change = sum(1 for k in POSITIVE_KEYWORDS if k in text) - sum(1 for k in NEGATIVE_KEYWORDS if k in text)
            sentiment_score += score_change
        print(f"Political sentiment analysis complete. Score: {sentiment_score}")
        return sentiment_score
    except Exception as e:
        print(f"!!! ERROR in get_political_sentiment: {e}")
        return 0

def get_news_impact():
    print("Step 2: Fetching economic calendar from Finnhub...")
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("!!! ERROR: FINNHUB_API_KEY not found in secrets!")
        return 0
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        r = requests.get(f'https://finnhub.io/api/v1/calendar/economic?from={today}&to={today}&token={api_key}')
        r.raise_for_status() # این خط اگر خطای HTTP رخ دهد، آن را نمایش می‌دهد
        data = r.json()
        news_events = data.get('economicCalendar', [])
        if not news_events:
            print("No major economic events found for today.")
            return 0
        highest_impact = 0
        now = datetime.now()
        for event in news_events:
            event_time_str = event.get('time', '')
            if event_time_str:
                event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
                if now < event_time < (now + timedelta(hours=2)):
                    impact = int(event.get('impact', 0))
                    if impact > highest_impact:
                        highest_impact = impact
        print(f"Economic news analysis complete. Highest impact: {highest_impact}")
        return highest_impact
    except Exception as e:
        print(f"!!! ERROR in get_news_impact: {e}")
        return 0

def get_ai_recommendation():
    print("Step 3: Loading ML model...")
    try:
        model = joblib.load('market_model.joblib')
        print("ML model loaded successfully.")
        
        political_score = get_political_sentiment()
        news_impact = get_news_impact()
        
        print(f"Inputs for model: political_score={political_score}, news_impact={news_impact}")
        
        features = np.array([[political_score, news_impact]])
        prediction = model.predict(features)[0]
        probability = max(model.predict_proba(features)[0])
        recommendation_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
        
        output = {
            "prediction": int(prediction),
            "recommendation": recommendation_map.get(prediction, "HOLD"),
            "confidence": round(probability, 2),
            "political_score": political_score,
            "news_impact": news_impact
        }
        print(f"Final recommendation generated: {output}")
        return output
    except Exception as e:
        print(f"!!! ERROR in get_ai_recommendation (maybe 'market_model.joblib' is missing?): {e}")
        return {"recommendation": "ERROR", "confidence": 0}

if __name__ == "__main__":
    print("--- Starting AI Analysis ---")
    final_analysis = get_ai_recommendation()
    
    if final_analysis.get("recommendation") != "ERROR":
        with open("sentiment.txt", "w") as f:
            json.dump(final_analysis, f)
        print("--- Analysis complete. sentiment.txt file created. ---")
    else:
        print("--- Analysis failed. sentiment.txt was NOT created. ---")
