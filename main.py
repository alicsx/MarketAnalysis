# main.py (The Ultimate Comprehensive Version: All Features Included)
import json
import feedparser
from datetime import datetime, timezone, timedelta
import time
import yfinance as yf
import pandas as pd

# --- فایل‌های حافظه و کنترل ---
MEMORY_FILE = "strategy_data.json"
CONTROL_FILE = "control.json"

# --- دیکشنری فیدهای RSS ---
CURRENCY_RSS_FEEDS = {'USD':"https://www.investing.com/rss/news_1.rss",'EUR':"https://www.investing.com/rss/news_4.rss",'GBP':"https://www.investing.com/rss/news_6.rss",'JPY':"https://www.investing.com/rss/news_3.rss",'CAD':"https://www.investing.com/rss/news_10.rss",'AUD':"https://www.investing.com/rss/news_8.rss",'CHF':"https://www.investing.com/rss/news_7.rss",'World':"https://www.investing.com/rss/news_25.rss"}
CURRENCY_PAIRS_YF = {"EURUSD":"EURUSD=X", "GBPUSD":"GBPUSD=X", "USDJPY":"USDJPY=X", "AUDUSD":"AUDUSD=X", "USDCAD":"USDCAD=X"}

# --- دیکشنری کلیدواژه‌های جامع با وزن‌دهی معنایی ---
KEYWORDS = {
    "breakthrough":5,"landmark deal":5,"historic agreement":5,"bull market":5,"record high":4,"surge":4,"boom":4,
    "strong growth":3,"beats estimates":3,"rally":3,"optimism":3,"peace":3,"stimulus":3,"dovish":3,"outperform":3,
    "agreement":2,"recover":2,"rebound":2,"upbeat":2,"easing":2,"expansion":2,"confidence":2,"hiring":2,"better-than-expected":2,
    "talks":1,"stable":1,"negotiation":1,"potential":1,"improving":1,"rate cut":1,"upward revision":1,"risk-on":1,
    "war":-5,"crash":-5,"panic":-5,"default":-5,"collapse":-5,"bear market":-5,"turmoil":-5,
    "crisis":-4,"recession":-4,"lockdown":-4,"sell-off":-3,"fears":-3,"sanction":-3,"sharp drop":-3,
    "inflation":-2,"rate hike":-2,"uncertainty":-2,"dispute":-2,"tightening":-2,"hawkish":-2,"bearish":-2,"deficit":-2,
    "tension":-1,"volatile":-1,"worse-than-expected":-1,"slowdown":-1,"risk-off":-1,"headwinds":-1,"concerns":-1,"jobless":-1
}

# --- توابع اصلی ---

def get_sentiment_for_feed(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        weighted_score = 0.0
        now_utc = datetime.now(timezone.utc)
        for entry in feed.entries[:25]:
            article_score = 0
            text = (entry.get('title', '') + " " + entry.get('summary', '')).lower()
            for keyword, weight in KEYWORDS.items():
                if keyword in text:
                    article_score += weight
            if 'published_parsed' in entry:
                age_hours = (now_utc - datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)).total_seconds() / 3600
                time_weight = max(0, 1 - (age_hours / 24.0))
                weighted_score += article_score * time_weight
        return int(round(weighted_score))
    except: return 0

def get_market_regime():
    try:
        sp500 = yf.Ticker("^GSPC").history(period="2d")['Close'].pct_change().iloc[-1]
        vix = yf.Ticker("^VIX").history(period="2d")['Close'].pct_change().iloc[-1]
        if sp500 > 0.002 and vix < -0.01: return "Risk-On"
        elif sp500 < -0.002 and vix > 0.01: return "Risk-Off"
        return "Neutral"
    except: return "Neutral"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f: return json.load(f)
    except FileNotFoundError:
        return {"weights": {'USD':1.0,'EUR':1.0,'GBP':1.0,'JPY':1.0,'CAD':1.0,'AUD':1.0,'CHF':1.0}, "last_prediction": {}}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f: json.dump(data, f, indent=2)

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
    <html><head><title>AI Dashboard</title><meta http-equiv="refresh" content="300">
    <style>body{{font-family: Consolas, monospace; background: #1e1e1e; color: #d4d4d4;}} table{{width: 600px; margin: auto; border-collapse: collapse;}} td, th{{border: 1px solid #444; padding: 10px; text-align: center;}} th{{background: #2a2d2e;}} .status{{font-size: 1.2em;}} .buy{{color: #50fa7b;}} .sell{{color: #ff5555;}}</style></head>
    <body><h1 style="text-align:center;">Comprehensive AI Trading Dashboard</h1>
    <p style="text-align:center;">Last Updated (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}</p>
    <table class="status"><tr><th>Master Control</th><th>Market Regime</th></tr>
    <tr><td><b>{data['master_control']}</b></td><td style="color:{regime_color};"><b>{data['market_regime']}</b></td></tr></table>
    <h2 style="text-align:center; margin-top: 40px;">Currency Sentiment Scores (Weighted)</h2><table>
    <tr><th>Currency</th><th>Final Sentiment Score</th></tr>"""
    for currency, score in sorted(data['final_sentiments'].items()):
        if currency == 'World': continue
        css_class = 'buy' if score > 0 else 'sell' if score < 0 else ''
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
    
    # ۳. تحلیل جدید
    weights = memory["weights"]
    sentiments = {currency: get_sentiment_for_feed(rss_url) * weights.get(currency, 1.0) for currency, rss_url in CURRENCY_RSS_FEEDS.items()}
    market_regime = get_market_regime()

    # ۴. اعمال بایاس رژیم بازار
    safe, risky = ["JPY","CHF","USD"], ["AUD","CAD","GBP","EUR"]
    if market_regime == "Risk-On":
        for c in risky: sentiments[c] *= 1.5
        for c in safe: sentiments[c] *= 0.5
    elif market_regime == "Risk-Off":
        for c in risky: sentiments[c] *= 0.5
        for c in safe: sentiments[c] *= 1.5

    final_sentiments = {k: int(round(v)) for k, v in sentiments.items()}
    
    # ۵. اعمال کنترل دستی
    if master_control == "PAUSE_TRADING":
        for k in final_sentiments: final_sentiments[k] = 0

    # ۶. ذخیره پیش‌بینی جدید (فقط اگر معامله‌ای محتمل است)
    else:
        best_pair, best_divergence = None, 0
        for pair in CURRENCY_PAIRS_YF.keys():
            base, quote = pair[:3], pair[3:]
            divergence = final_sentiments.get(base,0) - final_sentiments.get(quote,0)
            if abs(divergence) > abs(best_divergence): best_divergence, best_pair = divergence, pair
        if abs(best_divergence) > 5:
            memory["last_prediction"] = {"pair": best_pair, "predicted_move": 1 if best_divergence > 0 else -1, "timestamp": datetime.now().isoformat()}

    save_memory(memory)
    
    # ۷. ساخت و ذخیره خروجی‌ها
    output_for_robot = {"market_regime": market_regime, "sentiments": final_sentiments}
    with open("sentiment.txt", "w") as f: json.dump(output_for_robot, f)
    
    dashboard_data = {"master_control":master_control, "market_regime":market_regime, "final_sentiments":final_sentiments}
    with open("dashboard.html", "w") as f: f.write(generate_dashboard_html(dashboard_data))
    
    print(f"Comprehensive analysis complete. Control: {master_control}, Regime: {market_regime}")

if __name__ == "__main__":
    run_main_analysis()
