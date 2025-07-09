# Intelligent_Confluence_AI.py
# Copyright 2025, Gemini AI - Final Flexible Confluence Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json
import sys

# --- تنظیمات نهایی ---
PRIMARY_SYMBOLS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDJPY=X", "USDCAD=X", "NZDUSD=X"]
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 252
EMA_PERIODS = [50, 200]
FIB_LEVELS = [0.5, 0.618]
OUTPUT_FILENAME = "multi_currency_analysis.json"

def validate_data(data, symbol_name):
    if data is None or data.empty: return None
    data.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in data.columns]
    required = ['open', 'high', 'low', 'close']
    if not all(col in data.columns for col in required): return None
    data.dropna(subset=required, inplace=True)
    if len(data) < max(EMA_PERIODS): return None
    return data

def get_market_context(start, end):
    # این تابع بدون تغییر باقی می‌ماند
    context = {}
    print("Analyzing market context...")
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=20)
            data = validate_data(data, name)
            if data is not None:
                data['ema'] = data['close'].ewm(span=50, adjust=False).mean()
                context[name] = "Bullish" if data['close'].iloc[-1] > data['ema'].iloc[-1] else "Bearish"
        except Exception: context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

def find_intelligent_confluence(data, context):
    if data is None: return []
    
    # محاسبه اندیکاتورها
    for p in EMA_PERIODS: data[f'ema_{p}'] = data['close'].ewm(span=p, adjust=False).mean()
    main_trend = "Up" if data['close'].iloc[-1] > data['ema_200'].iloc[-1] else "Down"
    
    # یافتن آخرین موج حرکتی بزرگ برای فیبوناچی
    lows, _ = find_peaks(-data['low'], prominence=data['close'].std()*0.8)
    highs, _ = find_peaks(data['high'], prominence=data['close'].std()*0.8)
    
    last_low_price = data['low'].iloc[lows[-1]] if len(lows) > 0 else None
    last_high_price = data['high'].iloc[highs[-1]] if len(highs) > 0 else None

    plans = []
    
    # پیدا کردن تمام سطوح نقدینگی (قله‌ها و دره‌ها)
    swing_highs, _ = find_peaks(data['high'], prominence=data['close'].std()*0.4, distance=5)
    swing_lows, _ = find_peaks(-data['low'], prominence=data['close'].std()*0.4, distance=5)

    # امتیازدهی به هر سطح بر اساس همگرایی
    for idx in swing_highs:
        peak_price = data['high'].iloc[idx]
        score, factors = 50, ["Swing High"]
        # بررسی فیبوناچی
        if last_low_price and last_high_price and last_high_price > peak_price:
            for level in FIB_LEVELS:
                fib_price = last_high_price - (last_high_price - last_low_price) * level
                if abs(peak_price - fib_price) < data['close'].std() * 0.25:
                    score += 20; factors.append(f"Fib {level*100:.0f}%"); break
        # بررسی EMA
        for p in EMA_PERIODS:
            if abs(peak_price - data[f'ema_{p}'].iloc[idx]) < data['close'].std() * 0.25:
                score += 15; factors.append(f"EMA{p} Resist"); break
        # بررسی زمینه بازار
        if main_trend == "Down": score += 15
        if context.get("DXY") == "Bullish": score += 15
        
        plans.append({"type": "SELL", "price": peak_price, "score": min(score, 100), "thesis": " + ".join(factors)})

    for idx in swing_lows:
        peak_price = data['low'].iloc[idx]
        score, factors = 50, ["Swing Low"]
        if last_high_price and last_low_price and last_low_price < peak_price:
            for level in FIB_LEVELS:
                fib_price = last_low_price + (last_high_price - last_low_price) * level
                if abs(peak_price - fib_price) < data['close'].std() * 0.25:
                    score += 20; factors.append(f"Fib {level*100:.0f}%"); break
        for p in EMA_PERIODS:
            if abs(peak_price - data[f'ema_{p}'].iloc[idx]) < data['close'].std() * 0.25:
                score += 15; factors.append(f"EMA{p} Support"); break
        if main_trend == "Up": score += 15
        if context.get("DXY") == "Bearish": score += 15
        
        plans.append({"type": "BUY", "price": peak_price, "score": min(score, 100), "thesis": " + ".join(factors)})

    return plans

def main():
    print("--- Starting Intelligent Confluence AI ---")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    market_context = get_market_context(start_date, end_date)
    all_analyses = {}

    for symbol in PRIMARY_SYMBOLS:
        print(f"\n--- Finding Confluence for {symbol} ---")
        primary_data = yf.download(symbol, start=start_date, end=end_date, progress=False, timeout=20)
        primary_data = validate_data(primary_data, symbol)
        
        if primary_data is None: continue

        all_plans = find_intelligent_confluence(primary_data, market_context)
        all_plans.sort(key=lambda x: x['score'], reverse=True)
        
        clean_symbol_name = symbol.replace("=X", "")
        # فقط پلن‌هایی با امتیاز بالاتر از یک حد مشخص را ذخیره می‌کنیم
        final_plans = [p for p in all_plans if p['score'] >= 65][:2]
        all_analyses[clean_symbol_name] = {"trade_plans": final_plans}

    output_data = {"analysis": all_analyses}
    with open(OUTPUT_FILENAME, 'w') as f:
        json.dump(output_data, f, indent=4)
    print(f"\n--- Confluence analysis complete. Results saved to '{OUTPUT_FILENAME}' ---")

if __name__ == "__main__":
    main()
