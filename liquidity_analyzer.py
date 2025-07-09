# Confluence_Time_AI.py
# Copyright 2025, Gemini AI - The Final Confluence & Time-Based Strategist

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json
import sys

# --- تنظیمات نهایی ---
PRIMARY_SYMBOLS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X"]
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 252 # یک سال معاملاتی
EMA_PERIODS = [50, 200]
FIB_LEVELS = [0.382, 0.5, 0.618]
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
    context = {}
    # ... (کد این تابع مشابه نسخه قبلی است و بدون تغییر باقی می‌ماند)
    return context

def find_confluence_zones(data, context):
    if data is None: return []
    
    # محاسبه اندیکاتورها
    for p in EMA_PERIODS: data[f'ema_{p}'] = data['close'].ewm(span=p, adjust=False).mean()
    main_trend = "Up" if data['close'].iloc[-1] > data['ema_200'].iloc[-1] else "Down"
    
    # یافتن آخرین موج حرکتی بزرگ برای فیبوناچی
    major_swings, _ = find_peaks(data['high'], prominence=data['close'].std())
    major_troughs, _ = find_peaks(-data['low'], prominence=data['close'].std())
    last_major_swing = data.iloc[major_swings[-1]] if len(major_swings) > 0 else None
    last_major_trough = data.iloc[major_troughs[-1]] if len(major_troughs) > 0 else None

    plans = []
    
    # تحلیل سقف‌ها (برای پلن فروش)
    high_indices, _ = find_peaks(data['high'].to_numpy(), prominence=data['close'].std()*0.5, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        score, thesis = 50, f"Sell Plan @ {peak['high']:.5f}: "
        factors = ["Swing High"]
        
        # ۱. بررسی همگرایی با فیبوناچی
        if last_major_trough is not None and peak.name > last_major_trough.name:
            impulse_range = peak['high'] - last_major_trough['low']
            for level in FIB_LEVELS:
                fib_price = peak['high'] - impulse_range * level
                if abs(peak['high'] - fib_price) < data['close'].std() * 0.2:
                    score += 15; factors.append(f"Fib {level*100:.1f}%")
                    break
        
        # ۲. بررسی همگرایی با میانگین متحرک
        for p in EMA_PERIODS:
            if abs(peak['high'] - peak[f'ema_{p}']) < data['close'].std() * 0.2:
                score += 10; factors.append(f"EMA {p} Resist")
                break
                
        # ۳. بررسی همگرایی با زمینه بازار
        if main_trend == "Down": score += 20; factors.append("Pro-Trend")
        if context.get("DXY") == "Bullish": score += 20; factors.append("DXY Confirms")
        
        if score > 70:
            sl = peak['high'] + data['close'].std() * 0.4
            tp = last_major_trough['low'] if last_major_trough is not None else peak['high'] - data['close'].std()*2
            plans.append({"type": "SELL", "price": peak['high'], "sl": sl, "tp": tp, "score": min(score, 100), "thesis": " + ".join(factors)})

    # ... (منطق مشابه برای تحلیل کف‌ها و پلن خرید)
    
    return plans

def main():
    print("--- Starting Confluence & Time-Based AI Analysis ---")
    # ... (کد اصلی برنامه مشابه نسخه چندارزی قبلی است، فقط تابع find_confluence_zones را فراخوانی می‌کند)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    market_context = get_market_context(start_date, end_date)
    all_analyses = {}

    for symbol in PRIMARY_SYMBOLS:
        print(f"\n--- Finding Confluence for {symbol} ---")
        primary_data = yf.download(symbol, start=start_date, end=end_date, progress=False, timeout=20)
        primary_data = validate_data(primary_data, symbol)
        
        all_plans = find_confluence_zones(primary_data, market_context)
        all_plans.sort(key=lambda x: x['score'], reverse=True)
        
        clean_symbol_name = symbol.replace("=X", "")
        all_analyses[clean_symbol_name] = {"trade_plans": all_plans[:2]}

    output_data = {"analysis": all_analyses}
    with open(OUTPUT_FILENAME, 'w') as f:
        json.dump(output_data, f, indent=4)
    print(f"\n--- Confluence analysis complete. Results saved to '{OUTPUT_FILENAME}' ---")

if __name__ == "__main__":
    main()
