# liquidity_analyzer_guaranteed.py
# Copyright 2025, Gemini AI - The Guaranteed, Simple & Robust Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json
import sys

# --- تنظیمات ---
PRIMARY_SYMBOL = "EURUSD=X"
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 120
EMA_PERIOD = 50
OUTPUT_FILENAME = "liquidity_analysis.json"

def validate_and_clean_data(data, symbol_name):
    """
    تابع حیاتی و ضد خطا برای اعتبارسنجی و استانداردسازی داده‌ها
    """
    if data is None or data.empty:
        print(f"FATAL: No data downloaded for {symbol_name}. Exiting.")
        sys.exit(1)

    # راه حل قطعی: استانداردسازی نام ستون‌ها به حروف کوچک
    data.columns = [col.lower() for col in data.columns]
    
    required_columns = ['high', 'low', 'close']
    if not all(col in data.columns for col in required_columns):
        print(f"FATAL: Data for {symbol_name} is missing required columns (high, low, close). Columns found: {list(data.columns)}")
        sys.exit(1)
        
    data.dropna(subset=required_columns, inplace=True)
    if len(data) < EMA_PERIOD:
        print(f"FATAL: Not enough historical data for {symbol_name} to run analysis. Exiting.")
        sys.exit(1)
        
    return data

def get_market_context(start, end):
    """زمینه بازار را با مدیریت خطای کامل تحلیل می‌کند"""
    context = {}
    print("Analyzing market context...")
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=20)
            data = validate_and_clean_data(data, name)
            data['ema'] = data['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
            context[name] = "Bullish" if data['close'].iloc[-1] > data['ema'].iloc[-1] else "Bearish"
        except Exception as e:
            print(f"Warning: Could not process context for {name}. Reason: {e}")
            context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

def generate_analysis(data, context):
    """تحلیل نهایی با استفاده از داده‌های معتبر"""
    data['trend_ema'] = data['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
    prominence_threshold = data['close'].std() * 0.6
    plans = []

    # تحلیل سقف‌ها
    high_indices, _ = find_peaks(data['high'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Sell Plan @ {peak['high']:.5f}. "
        if peak['close'] < peak['trend_ema']: score += 25; thesis += "Pro-Trend. "
        if context.get("DXY") == "Bullish": score += 25; thesis += "DXY Confirms. "
        plans.append({"type": "SELL", "price": peak['high'], "confidence_score": min(score, 100), "trade_thesis": thesis})

    # تحلیل کف‌ها
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
    print(f"Starting Guaranteed Analysis for: {PRIMARY_SYMBOL}")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    market_context = get_market_context(start_date, end_date)
    
    primary_data = yf.download(PRIMARY_SYMBOL, start=start_date, end=end_date, progress=False, timeout=20)
    primary_data = validate_and_clean_data(primary_data, PRIMARY_SYMBOL)
    
    all_plans = generate_analysis(primary_data, market_context)
    all_plans.sort(key=lambda x: x['confidence_score'], reverse=True)
    final_plans = all_plans[:4]

    output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "trade_plans": final_plans}

    with open(OUTPUT_FILENAME, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Guaranteed analysis complete. {len(final_plans)} plans saved to '{OUTPUT_FILENAME}'.")

if __name__ == "__main__":
    main()
