# main.py (The Ultimate Comprehensive Version: V2 with NLP and Advanced Indicators)
import json
import feedparser
from datetime import datetime, timezone, timedelta
import time
import yfinance as yf
import pandas as pd
# --- کتابخانه جدید برای تحلیل احساسات با NLP ---
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- فایل‌های حافظه و کنترل ---
MEMORY_FILE = "strategy_data.json"
CONTROL_FILE = "control.json"
OUTPUT_FILE = "sentiment.txt"
DASHBOARD_FILE = "dashboard.html"

# --- دیکشنری فیدهای RSS و جفت ارزها ---
CURRENCY_RSS_FEEDS = {'USD':"https://www.investing.com/rss/news_1.rss",'EUR':"https://www.investing.com/rss/news_4.rss",'GBP':"https://www.investing.com/rss/news_6.rss",'JPY':"https://www.investing.com/rss/news_3.rss",'CAD':"https://www.investing.com/rss/news_10.rss",'AUD':"https://www.investing.com/rss/news_8.rss",'CHF':"https://www.investing.com/rss/news_7.rss",'World':"https://www.investing.com/rss/news_25.rss"}
CURRENCY_PAIRS_YF = {"EURUSD":"EURUSD=X", "GBPUSD":"GBPUSD=X", "USDJPY":"USDJPY=X", "AUDUSD":"AUDUSD=X", "USDCAD":"USDCAD=X"}

# --- بخش جدید: وزن‌دهی به هر ماژول تحلیلی ---
# شما می‌توانید این وزن‌ها را برای تنظیم استراتژی تغییر دهید
ANALYSIS_WEIGHTS = {
    "news_sentiment": 0.5,      # تحلیل اخبار بیشترین وزن را دارد
    "leading_indicators": 0.3,  # شاخص‌های پیشرو وزن متوسط
    "market_regime": 0.2        # رژیم بازار وزن کمتری دارد
}

# --- آبجکت تحلیلگر NLP ---
nlp_analyzer = SentimentIntensityAnalyzer()

# --- توابع اصلی تحلیل ---

def get_nlp_sentiment_for_feed(rss_url):
    """
    نسخه جدید: تحلیل احساسات با استفاده از NLP (VADER) به جای کلمات کلیدی.
    این تابع زمینه و شدت احساسات را بهتر درک می‌کند.
    """
    try:
        feed = feedparser.parse(rss_url)
        total_compound_score = 0.0
        now_utc = datetime.now(timezone.utc)
        
        for entry in feed.entries[:25]:
            text = entry.get('title', '')
            # استفاده از VADER برای گرفتن امتیاز احساسات
            # امتیاز compound یک نمره نرمال‌شده بین -۱ (بسیار منفی) و +۱ (بسیار مثبت) است
            sentiment_score = nlp_analyzer.polarity_scores(text)['compound']
            
            if 'published_parsed' in entry:
                age_hours = (now_utc - datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)).total_seconds() / 3600
                time_weight = max(0, 1 - (age_hours / 24.0)) # وزن‌دهی زمانی مانند قبل
                total_compound_score += sentiment_score * time_weight
                
        # تبدیل امتیاز VADER به مقیاس خودمان (مثلا -۱۰ تا +۱۰)
        return int(round(total_compound_score * 10))
    except:
        return 0

def get_robust_market_regime():
    """
    نسخه جدید: تحلیل رژیم بازار با استفاده از میانگین متحرک و سطح VIX.
    این روش پایدارتر از بررسی تغییرات روزانه است.
    """
    try:
        sp500_data = yf.Ticker("^GSPC").history(period="1mo")
        vix_data = yf.Ticker("^VIX").history(period="1mo")
        
        sp500_price = sp500_data['Close'].iloc[-1]
        sp500_ma20 = sp500_data['Close'].rolling(window=20).mean().iloc[-1]
        
        vix_level = vix_data['Close'].iloc[-1]
        
        if sp500_price > sp500_ma20 and vix_level < 20:
            return "Risk-On"
        elif sp500_price < sp500_ma20 and vix_level > 25:
            return "Risk-Off"
        return "Neutral"
    except:
        return "Neutral"

def get_leading_indicator_bias():
    """
    نسخه جدید: اضافه شدن نرخ بهره اوراق قرضه ۱۰ ساله آمریکا (^TNX)
    به عنوان یک شاخص کلیدی برای قدرت دلار و سلامت اقتصاد.
    """
    bias = {"AUD": 0, "CAD": 0, "JPY": 0, "CHF": 0, "USD": 0, "EUR": 0, "GBP": 0}
    try:
        # ۱. تحلیل مس (Dr. Copper) - سلامت صنعتی
        copper = yf.Ticker("HG=F").history(period="1mo")
        copper_trend = copper['Close'].rolling(window=5).mean().iloc[-1] > copper['Close'].rolling(window=20).mean().iloc[-1]
        if copper_trend:
            bias["AUD"] += 4 # امتیاز بیشتر برای ارزهای کالایی
            bias["CAD"] += 4

        # ۲. تحلیل طلا (Gold) - پناهگاه امن
        gold = yf.Ticker("GC=F").history(period="1mo")
        gold_trend = gold['Close'].rolling(window=5).mean().iloc[-1] > gold['Close'].rolling(window=20).mean().iloc[-1]
        if gold_trend:
            bias["JPY"] += 5 # امتیاز بیشتر برای ارزهای امن
            bias["CHF"] += 5
            bias["USD"] -= 2 # همبستگی معکوس قوی‌تر با دلار

        # ۳. تحلیل نرخ بهره ۱۰ ساله آمریکا (^TNX) - چشم‌انداز اقتصادی و سیاست پولی
        tnx = yf.Ticker("^TNX").history(period="1mo")
        tnx_trend = tnx['Close'].rolling(window=5).mean().iloc[-1] > tnx['Close'].rolling(window=20).mean().iloc[-1]
        if tnx_trend:
            bias["USD"] += 6 # روند صعودی نرخ بهره به شدت برای دلار مثبت است
            
        print(f"Leading Indicators -> Copper Bullish: {copper_trend}, Gold Bullish: {gold_trend}, 10Y-Yield Bullish: {tnx_trend}")
        return bias
    except Exception as e:
        print(f"Error fetching leading indicators: {e}")
        return bias

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f: return json.load(f)
    except FileNotFoundError:
        return {"weights": {'USD':1.0,'EUR':1.0,'GBP':1.0,'JPY':1.0,'CAD':1.0,'AUD':1.0,'CHF':1.0}, "last_prediction": {}}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f: json.dump(data, f, indent=2)

# تابع review_past_predictions و generate_dashboard_html بدون تغییر باقی می‌مانند
# ... (کدهای آن توابع را اینجا کپی کنید) ...
def review_past_predictions(memory):
    last_pred = memory.get("last_prediction", {})
    if not last_pred: return memory
    pred_time = datetime.fromisoformat(last_pred["timestamp"])
    if not (timedelta(hours=4) < datetime.now() - pred_time < timedelta(hours=8)): return memory
    print("Reviewing past prediction to update weights...")
    pair, predicted_move = last_pred["pair"], last_pred["predicted_move"]
    try:
        ticker = yf.Ticker(CURRENCY_PAIRS_YF.get(pair)).history(period="1d", interval="1h")
        start_price = ticker.loc[ticker.index.hour == pred_time.hour]['Close'].iloc[0]
        end_price = ticker['Close'].iloc[-1]
        actual_move = 1 if end_price > start_price else -1
        base_curr, quote_curr = pair[:3], pair[3:]
        if predicted_move == actual_move:
            memory["weights"][base_curr] = min(1.5, memory["weights"][base_curr] * 1.02)
            memory["weights"][quote_curr] = max(0.5, memory["weights"][quote_curr] * 0.98)
        else:
            memory["weights"][base_curr] = max(0.5, memory["weights"][base_curr] * 0.98)
            memory["weights"][quote_curr] = min(1.5, memory["weights"][quote_curr] * 1.02)
        memory["last_prediction"] = {}
        return memory
    except Exception as e:
        print(f"Could not verify prediction for {pair}: {e}")
        return memory
def generate_dashboard_html(data):
    regime_color = {"Risk-On": "#4CAF50", "Risk-Off": "#F44336", "Neutral": "#777"}.get(data['market_regime'], "#777")
    html = f"""
    <html><head><title>AI Dashboard V2</title><meta http-equiv="refresh" content="300">
    <style>body{{font-family: Consolas, monospace; background: #1e1e1e; color: #d4d4d4;}} table{{width: 600px; margin: auto; border-collapse: collapse;}} td, th{{border: 1px solid #444; padding: 10px; text-align: center;}} th{{background: #2a2d2e;}} .status{{font-size: 1.2em;}} .buy{{color: #50fa7b; font-weight: bold;}} .sell{{color: #ff5555; font-weight: bold;}}</style></head>
    <body><h1 style="text-align:center;">Comprehensive AI Trading Dashboard V2</h1>
    <p style="text-align:center;">Last Updated (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}</p>
    <table class="status"><tr><th>Master Control</th><th>Market Regime</th></tr>
    <tr><td><b>{data['master_control']}</b></td><td style="color:{regime_color};"><b>{data['market_regime']}</b></td></tr></table>
    <h2 style="text-align:center; margin-top: 40px;">Final Combined Currency Score</h2><table>
    <tr><th>Currency</th><th>Final Score</th></tr>"""
    for currency, score in sorted(data['final_sentiments'].items()):
        if currency == 'World': continue
        css_class = 'buy' if score > 5 else 'sell' if score < -5 else ''
        html += f"<tr><td>{currency}</td><td class='{css_class}'>{score}</td></tr>"
    html += "</table></body></html>"
    return html
def run_main_analysis():
    # ۱. خواندن کنترل دستی
    try:
        with open(CONTROL_FILE, "r") as f: master_control = json.load(f).get("master_override", "ACTIVE")
    except: master_control = "ACTIVE"
    
    # ۲. بارگذاری حافظه و یادگیری از گذشته
    memory = load_memory()
    memory = review_past_predictions(memory)
    
    # ۳. اجرای تحلیل‌های جدید و قوی‌تر
    weights = memory["weights"]
    news_sentiments = {currency: get_nlp_sentiment_for_feed(rss_url) * weights.get(currency, 1.0) for currency, rss_url in CURRENCY_RSS_FEEDS.items()}
    market_regime = get_robust_market_regime()
    leading_bias = get_leading_indicator_bias()

    # ۴. **بخش جدید: ترکیب هوشمندانه تحلیل‌ها با سیستم وزن‌دهی**
    final_sentiments = {c: 0 for c in CURRENCY_RSS_FEEDS.keys()}
    
    # اعمال بایاس رژیم بازار
    regime_bias = {c: 0 for c in CURRENCY_RSS_FEEDS.keys()}
    safe_havens, commodity_currencies = ["JPY","CHF","USD"], ["AUD","CAD"]
    if market_regime == "Risk-On":
        for c in commodity_currencies: regime_bias[c] = 5
        for c in safe_havens: regime_bias[c] = -5
    elif market_regime == "Risk-Off":
        for c in commodity_currencies: regime_bias[c] = -5
        for c in safe_havens: regime_bias[c] = 5

    # محاسبه امتیاز نهایی هر ارز با ترکیب وزن‌دار
    for currency in final_sentiments.keys():
        news_score = news_sentiments.get(currency, 0)
        leading_score = leading_bias.get(currency, 0)
        regime_score = regime_bias.get(currency, 0)
        
        # فرمول ترکیب نهایی
        combined_score = (news_score * ANALYSIS_WEIGHTS["news_sentiment"]) + \
                         (leading_score * ANALYSIS_WEIGHTS["leading_indicators"]) + \
                         (regime_score * ANALYSIS_WEIGHTS["market_regime"])
                         
        final_sentiments[currency] = int(round(combined_score))
    
    # ۵. اعمال کنترل دستی و ذخیره پیش‌بینی
    if master_control == "PAUSE_TRADING":
        for k in final_sentiments: final_sentiments[k] = 0
    else:
        # منطق پیدا کردن بهترین جفت ارز و ذخیره پیش‌بینی مانند قبل
        best_pair, best_divergence = None, 0
        for pair in CURRENCY_PAIRS_YF.keys():
            base, quote = pair[:3], pair[3:]
            divergence = final_sentiments.get(base,0) - final_sentiments.get(quote,0)
            if abs(divergence) > abs(best_divergence):
                best_divergence, best_pair = divergence, pair
        
        # آستانه را کمی بالاتر می‌بریم چون سیستم قوی‌تر شده
        if abs(best_divergence) > 8:
            memory["last_prediction"] = {
                "pair": best_pair, 
                "predicted_move": 1 if best_divergence > 0 else -1, 
                "timestamp": datetime.now().isoformat()
            }
            
    save_memory(memory)
    
    # ۶. ساخت و ذخیره خروجی‌ها
    output_for_robot = {"market_regime": market_regime, "sentiments": final_sentiments}
    with open(OUTPUT_FILE, "w") as f: json.dump(output_for_robot, f)
    
    dashboard_data = {"master_control":master_control, "market_regime":market_regime, "final_sentiments":final_sentiments}
    with open(DASHBOARD_FILE, "w") as f: f.write(generate_dashboard_html(dashboard_data))
    
    print(f"V2 analysis complete. Control: {master_control}, Regime: {market_regime}")
    print(f"Final Combined Scores: {final_sentiments}")

if __name__ == "__main__":
    run_main_analysis()
