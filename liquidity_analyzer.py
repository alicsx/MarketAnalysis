# AI_Strategist_Complete.py
# Copyright 2025, Gemini AI - Final Corrected & Complete Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json
import sys

# --- تنظیمات ---
PRIMARY_SYMBOLS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDJPY=X", "USDCAD=X", "NZDUSD=X"]
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 252
EMA_PERIOD = 50
TOP_N_PLANS_TO_REPORT = 5
OUTPUT_FILENAME = "multi_currency_analysis.json"

def validate_data(data, symbol_name):
    if data is None or data.empty: return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = [col.lower() for col in data.columns]
    required = ['open', 'high', 'low', 'close']
    if not all(col in data.columns for col in required): return None
    data.dropna(subset=required, inplace=True)
    if len(data) < EMA_PERIOD: return None
    return data

def get_market_context(start, end):
    context = {}
    print("Analyzing market context...")
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=20)
            data = validate_data(data, name)
            if data is not None:
                data['ema'] = data['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
                context[name] = "Bullish" if data['close'].iloc[-1] > data['ema'].iloc[-1] else "Bearish"
        except Exception:
            context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

def find_complete_plans(data, context, symbol_name):
    """
    نسخه کامل و تصحیح شده: تمام فرصت‌های بالقوه را با امتیازشان پیدا می‌کند
    """
    if data is None: return []
    
    data['trend_ema'] = data['close'].ewm(span=200, adjust=False).mean()
    main_trend = "Up" if data['close'].iloc[-1] > data['trend_ema'].iloc[-1] else "Down"
    prominence_threshold = data['close'].std() * 0.5 # کمی آستانه را منعطف‌تر می‌کنیم
    plans = []

    # *** بخش تصحیح شده: افزودن حلقه‌های پردازش ***
    # تحلیل سقف‌ها
    swing_highs, _ = find_peaks(data['high'], prominence=prominence_threshold, distance=5)
    for idx in swing_highs:
        peak_price = data['high'].iloc[idx]
        score = 50
        factors = ["Swing High"]
        
        # بررسی زمینه بازار
        if main_trend == "Down": score += 25; factors.append("Pro-Trend")
        if context.get("DXY") == "Bullish": score += 25; factors.append("DXY Confirms")
        
        plans.append({"symbol": symbol_name, "type": "SELL", "price": peak_price, "score": min(score, 100), "thesis": " + ".join(factors)})

    # تحلیل کف‌ها
    swing_lows, _ = find_peaks(-data['low'], prominence=prominence_threshold, distance=5)
    for idx in swing_lows:
        peak_price = data['low'].iloc[idx]
        score = 50
        factors = ["Swing Low"]

        if main_trend == "Up": score += 25; factors.append("Pro-Trend")
        if context.get("DXY") == "Bearish": score += 25; factors.append("DXY Confirms")
        
        plans.append({"symbol": symbol_name, "type": "BUY", "price": peak_price, "score": min(score, 100), "thesis": " + ".join(factors)})
        
    return plans

def main():
    print("--- Starting Corrected AI Analysis ---")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    market_context = get_market_context(start_date, end_date)
    
    master_plan_list = []

    # مرحله ۱: جمع‌آوری تمام پلن‌ها
    for symbol in PRIMARY_SYMBOLS:
        print(f"--- Scanning {symbol} for opportunities ---")
        primary_data = yf.download(symbol, start=start_date, end=end_date, progress=False, timeout=20)
        primary_data = validate_data(primary_data, symbol)
        if primary_data is None: continue
        
        clean_symbol_name = symbol.replace("=X", "")
        potential_plans = find_complete_plans(primary_data, market_context, clean_symbol_name)
        master_plan_list.extend(potential_plans)

    # مرحله ۲: رتبه‌بندی تمام پلن‌ها
    master_plan_list.sort(key=lambda x: x['score'], reverse=True)
    
    # مرحله ۳: انتخاب بهترین‌ها
    top_plans = master_plan_list[:TOP_N_PLANS_TO_REPORT]
    
    # مرحله ۴: ساختار نهایی JSON
    final_analysis = {}
    for plan in top_plans:
        symbol = plan.pop('symbol')
        if symbol not in final_analysis:
            final_analysis[symbol] = {"trade_plans": []}
        final_analysis[symbol]["trade_plans"].append(plan)

    output_data = {"analysis": final_analysis}
    with open(OUTPUT_FILENAME, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\n--- Corrected analysis complete. Top {len(top_plans)} plans saved to '{OUTPUT_FILENAME}' ---")

if __name__ == "__main__":
    main()
