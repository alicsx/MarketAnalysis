# multi_currency_analyzer.py
# Copyright 2025, Gemini AI - Final Multi-Currency Production Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json
import sys

# --- تنظیمات نهایی ---
# لیستی از جفت ارزهای اصلی برای تحلیل
PRIMARY_SYMBOLS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDJPY=X", "USDCAD=X"]
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 120
EMA_PERIOD = 50
OUTPUT_FILENAME = "multi_currency_analysis.json" # نام فایل خروجی جدید

# (تابع validate_and_standardize_data بدون تغییر باقی می‌ماند)
def validate_and_standardize_data(data, symbol_name):
    if data is None or data.empty:
        print(f"ERROR: No data downloaded for {symbol_name}. Skipping.")
        return None
    data.columns = [col.lower() for col in data.columns] if not isinstance(data.columns, pd.MultiIndex) else [col[0].lower() for col in data.columns]
    required_columns = ['high', 'low', 'close']
    if not all(col in data.columns for col in required_columns):
        print(f"ERROR: Data for {symbol_name} is missing required columns. Skipping.")
        return None
    data.dropna(subset=required_columns, inplace=True)
    if len(data) < EMA_PERIOD:
        print(f"ERROR: Not enough data for {symbol_name}. Skipping.")
        return None
    return data

# (تابع get_market_context بدون تغییر باقی می‌ماند)
def get_market_context(start, end):
    context = {}
    print("Analyzing market context...")
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=20)
            data = validate_and_standardize_data(data, name)
            if data is None: 
                context[name] = "Unknown"
                continue
            data['ema'] = data['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
            context[name] = "Bullish" if data['close'].iloc[-1] > data['ema'].iloc[-1] else "Bearish"
        except Exception as e:
            print(f"Warning: Could not process context for {name}. Reason: {e}")
            context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

# (تابع generate_analysis بدون تغییر باقی می‌ماند)
def generate_analysis(data, context):
    data['trend_ema'] = data['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
    prominence_threshold = data['close'].std() * 0.6
    plans = []
    # ... (بقیه کد این تابع دقیقاً مثل قبل است و نیازی به تغییر ندارد)
    high_indices, _ = find_peaks(data['high'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Sell Plan @ {peak['high']:.5f}. "
        if peak['close'] < peak['trend_ema']: score += 25; thesis += "Pro-Trend. "
        if context.get("DXY") == "Bullish": score += 25; thesis += "DXY Confirms. "
        plans.append({"type": "SELL", "price": peak['high'], "confidence_score": min(score, 100), "trade_thesis": thesis})

    low_indices, _ = find_peaks(-data['low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in low_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Buy Plan @ {peak['low']:.5f}. "
        if peak['close'] > peak['trend_ema']: score += 25; thesis += "Pro-Trend. "
        if context.get("DXY") == "Bearish": score += 25; thesis += "DXY Confirms. "
        plans.append({"type": "BUY", "price": peak['low'], "confidence_score": min(score, 100), "trade_thesis": thesis})
    return plans

def main():
    print("--- Starting Multi-Currency Analysis ---")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    # ۱. تحلیل زمینه بازار یک بار برای همه انجام می‌شود
    market_context = get_market_context(start_date, end_date)
    
    # ۲. ایجاد یک دیکشنری برای نگهداری تمام تحلیل‌ها
    all_analyses = {}

    # ۳. حلقه بر روی تمام نمادهای اصلی
    for symbol in PRIMARY_SYMBOLS:
        print(f"\n--- Analyzing {symbol} ---")
        try:
            primary_data = yf.download(symbol, start=start_date, end=end_date, progress=False, timeout=20)
            primary_data = validate_and_standardize_data(primary_data, symbol)
            
            if primary_data is None:
                continue # اگر داده برای این نماد مشکل داشت، به سراغ بعدی برو

            # نام نماد را برای استفاده به عنوان کلید در JSON استاندارد می‌کنیم
            clean_symbol_name = symbol.replace("=X", "")
            
            all_plans = generate_analysis(primary_data, market_context)
            all_plans.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            all_analyses[clean_symbol_name] = {"trade_plans": all_plans[:4]}
            print(f"Analysis for {clean_symbol_name} complete. Found {len(all_plans)} potential plans.")

        except Exception as e:
            print(f"FATAL ERROR while processing {symbol}: {e}")

    # ۴. ساخت فایل نهایی JSON
    output_data = {
        "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "analysis": all_analyses
    }

    with open(OUTPUT_FILENAME, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\n--- Multi-currency analysis complete. Results saved to '{OUTPUT_FILENAME}' ---")

if __name__ == "__main__":
    main()
