# main.py (Final Currency Divergence Version)
import json
import feedparser
from datetime import datetime, timezone
import time

# دیکشنری فیدهای RSS برای هر ارز اصلی
CURRENCY_RSS_FEEDS = {
    'USD': "https://www.investing.com/rss/news_1.rss",      # اخبار بازار آمریکا
    'EUR': "https://www.investing.com/rss/news_4.rss",      # اخبار بازار اروپا
    'GBP': "https://www.investing.com/rss/news_6.rss",      # اخبار بازار بریتانیا
    'JPY': "https://www.investing.com/rss/news_3.rss",      # اخبار بازار ژاپن
    'CAD': "https://www.investing.com/rss/news_10.rss",     # اخبار بازار کانادا
    'AUD': "https://www.investing.com/rss/news_8.rss",      # اخبار بازار استرالیا
    'CHF': "https://www.investing.com/rss/news_7.rss",      # اخبار بازار سوئیس
    'World': "https://www.investing.com/rss/news_25.rss"    # اخبار عمومی جهان
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
    برای یک فید RSS مشخص، امتیاز احساسات زمانی-وزنی را محاسبه می‌کند.
    """
    try:
        feed = feedparser.parse(rss_url)
        weighted_score = 0.0
        now_utc = datetime.now(timezone.utc)
        for entry in feed.entries[:15]:
            article_score = 0
            text = (entry.get('title', '') + " " + entry.get('summary', '')).lower()
            article_score += sum(1 for k in POSITIVE_KEYWORDS if k in text)
            article_score -= sum(1 for k in NEGATIVE_KEYWORDS if k in text)
            
            if 'published_parsed' in entry:
                article_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                age_hours = (now_utc - article_time).total_seconds() / 3600
                weight = max(0, 1 - (age_hours / 24.0))
                weighted_score += article_score * weight
        return int(round(weighted_score))
    except:
        return 0

def get_all_currency_sentiments():
    """
    امتیاز احساسات را برای همه ارزهای تعریف شده محاسبه می‌کند.
    """
    all_sentiments = {}
    for currency, rss_url in CURRENCY_RSS_FEEDS.items():
        all_sentiments[currency] = get_sentiment_for_feed(rss_url)
    
    all_sentiments["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return all_sentiments

if __name__ == "__main__":
    final_analysis = get_all_currency_sentiments()
    with open("sentiment.txt", "w") as f:
        json.dump(final_analysis, f)
    print(f"Currency sentiments updated: {final_analysis}")
