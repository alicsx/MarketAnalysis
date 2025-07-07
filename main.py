# main.py (Final Self-Correcting AI)
import json
import feedparser
from datetime import datetime, timezone, timedelta
import time
import yfinance as yf # کتابخانه جدید برای دریافت قیمت واقعی بازار

# --- دیکشنری فیدها و کلیدواژه‌ها بدون تغییر ---
CURRENCY_RSS_FEEDS = {'USD':"https://www.investing.com/rss/news_1.rss",'EUR':"https://www.investing.com/rss/news_4.rss",'GBP':"https://www.investing.com/rss/news_6.rss",'JPY':"https://www.investing.com/rss/news_3.rss",'CAD':"https://www.investing.com/rss/news_10.rss",'AUD':"https://www.investing.com/rss/news_8.rss",'CHF':"https://www.investing.com/rss/news_7.rss",'World':"https://www.investing.com/rss/news_25.rss"}

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

CURRENCY_PAIRS_YF = {"EURUSD":"EURUSD=X", "GBPUSD":"GBPUSD=X", "USDJPY":"USDJPY=X", "AUDUSD":"AUDUSD=X", "USDCAD":"USDCAD=X"}

# فایل حافظه برای ذخیره وزن‌ها و پیش‌بینی‌های قبلی
MEMORY_FILE = "strategy_data.json"

def get_sentiment_for_feed(rss_url):
    # ... این تابع دقیقاً مانند پاسخ قبلی است و تغییری نکرده ...
    try:
        feed = feedparser.parse(rss_url)
        weighted_score = 0.0
        now_utc = datetime.now(timezone.utc)
        for entry in feed.entries[:20]:
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
    except: return 0

def load_memory():
    """حافظه AI (وزن‌ها و پیش‌بینی قبلی) را بارگذاری می‌کند"""
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # اگر حافظه وجود نداشت، یک حافظه پیش‌فرض بساز
        return {
            "weights": {'USD':1.0,'EUR':1.0,'GBP':1.0,'JPY':1.0,'CAD':1.0,'AUD':1.0,'CHF':1.0,'World':0.5},
            "last_prediction": {}
        }

def save_memory(data):
    """حافظه AI را ذخیره می‌کند"""
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def review_past_predictions(memory):
    """پیش‌بینی‌های قبلی را با واقعیت بازار مقایسه کرده و وزن‌ها را اصلاح می‌کند"""
    last_pred = memory.get("last_prediction", {})
    if not last_pred: return memory["weights"] # اگر پیش‌بینی قبلی نبود، کاری نکن

    pred_time = datetime.fromisoformat(last_pred["timestamp"])
    # فقط اگر پیش‌بینی بین 4 تا 8 ساعت پیش بوده، آن را بررسی کن
    if not (timedelta(hours=4) < datetime.now() - pred_time < timedelta(hours=8)):
        return memory["weights"]

    print("Reviewing past prediction...")
    pair = last_pred["pair"]
    predicted_move = last_pred["predicted_move"] # 1 for buy, -1 for sell
    
    # دریافت قیمت واقعی بازار از Yahoo Finance
    ticker = CURRENCY_PAIRS_YF.get(pair)
    if not ticker: return memory["weights"]
    
    hist = yf.Ticker(ticker).history(period="1d", interval="1h")
    start_price = hist.loc[hist.index.hour == pred_time.hour]['Close'].iloc[0]
    end_price = hist['Close'].iloc[-1]
    actual_move = 1 if end_price > start_price else -1

    # یادگیری: اگر پیش‌بینی درست بود، وزن‌ها را تقویت کن و اگر غلط بود، تضعیف
    base_curr, quote_curr = pair[:3], pair[3:]
    if predicted_move == actual_move:
        print(f"Correct prediction for {pair}. Increasing weights.")
        memory["weights"][base_curr] *= 1.02 # 2% تقویت
        memory["weights"][quote_curr] *= 0.98 # 2% تضعیف (نسبی)
    else:
        print(f"Incorrect prediction for {pair}. Decreasing weights.")
        memory["weights"][base_curr] *= 0.98
        memory["weights"][quote_curr] *= 1.02
    
    return memory["weights"]

def generate_new_analysis():
    """تحلیل جدید را بر اساس آخرین وزن‌ها تولید می‌کند"""
    memory = load_memory()
    weights = review_past_predictions(memory)
    
    all_sentiments = {}
    for currency, rss_url in CURRENCY_RSS_FEEDS.items():
        raw_score = get_sentiment_for_feed(rss_url)
        all_sentiments[currency] = raw_score * weights.get(currency, 1.0)
    
    # پیدا کردن بهترین سیگنال واگرایی
    best_pair, best_divergence = None, 0
    for pair in CURRENCY_PAIRS_YF.keys():
        base_curr, quote_curr = pair[:3], pair[3:]
        divergence = all_sentiments[base_curr] - all_sentiments[quote_curr]
        if abs(divergence) > abs(best_divergence):
            best_divergence = divergence
            best_pair = pair
    
    # ذخیره پیش‌بینی جدید برای بررسی در آینده
    if best_divergence > 5:
        memory["last_prediction"] = {"pair": best_pair, "predicted_move": 1, "timestamp": datetime.now().isoformat()}
    elif best_divergence < -5:
        memory["last_prediction"] = {"pair": best_pair, "predicted_move": -1, "timestamp": datetime.now().isoformat()}

    save_memory(memory)
    
    # خروجی برای ربات
    all_sentiments["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return all_sentiments


if __name__ == "__main__":
    final_analysis = generate_new_analysis()
    with open("sentiment.txt", "w") as f:
        json.dump(final_analysis, f)
    print(f"Self-Correcting analysis updated: {final_analysis}")
