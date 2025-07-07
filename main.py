# main.py (Final Advanced Version: Relative Sentiment + Risk Index)
import json
import feedparser
from datetime import datetime, timezone
import time
import numpy as np

# --- بخش دیکشنری RSS و کلیدواژه‌ها بدون تغییر ---
CURRENCY_RSS_FEEDS = {
    'USD': "https://www.investing.com/rss/news_1.rss", 'EUR': "https://www.investing.com/rss/news_4.rss",
    'GBP': "https://www.investing.com/rss/news_6.rss", 'JPY': "https://www.investing.com/rss/news_3.rss",
    'CAD': "https://www.investing.com/rss/news_10.rss", 'AUD': "https://www.investing.com/rss/news_8.rss",
    'CHF': "https://www.investing.com/rss/news_7.rss", 'World': "https://www.investing.com/rss/news_25.rss"
}
# کلیدواژه‌ها بدون تغییر باقی می‌مانند
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
def get_sentiment_for_feed(rss_url):
    """
    برای یک فید RSS، امتیاز وزنی و تعداد کل کلمات کلیدی را برمی‌گرداند.
    """
    try:
        feed = feedparser.parse(rss_url)
        weighted_score, total_keywords = 0.0, 0
        now_utc = datetime.now(timezone.utc)
        for entry in feed.entries[:20]:
            text = (entry.get('title', '') + " " + entry.get('summary', '')).lower()
            pos_count = sum(1 for k in POSITIVE_KEYWORDS if k in text)
            neg_count = sum(1 for k in NEGATIVE_KEYWORDS if k in text)
            
            article_score = pos_count - neg_count
            total_keywords += pos_count + neg_count
            
            if 'published_parsed' in entry:
                article_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                age_hours = (now_utc - article_time).total_seconds() / 3600
                weight = max(0, 1 - (age_hours / 24.0))
                weighted_score += article_score * weight
        return int(round(weighted_score)), total_keywords
    except:
        return 0, 0

def generate_final_analysis():
    """
    تمام تحلیل‌ها را ترکیب کرده و خروجی نهایی شامل امتیازهای نسبی و شاخص ریسک را تولید می‌کند.
    """
    raw_sentiments = {}
    total_keyword_counts = {}
    
    # ۱. محاسبه امتیاز خام برای همه ارزها
    for currency, rss_url in CURRENCY_RSS_FEEDS.items():
        raw_sentiments[currency], total_keyword_counts[currency] = get_sentiment_for_feed(rss_url)

    # ۲. محاسبه میانگین احساسات بازار (به جز اخبار جهانی)
    market_scores = [v for k, v in raw_sentiments.items() if k != 'World']
    average_sentiment = np.mean(market_scores) if market_scores else 0

    # ۳. محاسبه امتیاز نسبی برای هر ارز
    relative_sentiments = {
        currency: round(score - average_sentiment, 2)
        for currency, score in raw_sentiments.items()
    }

    # ۴. محاسبه شاخص ریسک یکپارچه (بر اساس تعداد کل کلمات کلیدی پیدا شده)
    total_chatter = sum(total_keyword_counts.values())
    risk_index = min(10, int(round(total_chatter / 5.0))) # نرمال‌سازی ساده

    # ۵. ساخت خروجی نهایی
    final_output = {
        "risk_index": risk_index,
        "average_sentiment": round(average_sentiment, 2),
        "relative_sentiments": relative_sentiments,
        "raw_sentiments": raw_sentiments,
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return final_output

if __name__ == "__main__":
    analysis = generate_final_analysis()
    with open("sentiment.txt", "w") as f:
        json.dump(analysis, f)
    print(f"Advanced analysis updated: {analysis}")
