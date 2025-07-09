# liquidity_analyzer_robust.py
# Copyright 2025, Gemini AI - The Final, Robust & Error-Proof Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json
import sys # برای خروج اضطراری

# --- تنظیمات نهایی ---
PRIMARY_SYMBOL = "EURUSD=X"
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 120
EMA_PERIOD_TREND = 50
OUTPUT_FILENAME = "liquidity_analysis_final.json"

# --- توابع داخلی و مستقل برای محاسبه اندیکاتورها ---
def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    if loss.iloc[-1] == 0: return pd.Series(100.0, index=series.index)
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def validate_data(data, symbol_name):
    """تابع حیاتی برای اعتبارسنجی داده‌های دانلود شده"""
    if data is None or data.empty:
        print(f"FATAL ERROR: No data downloaded for {symbol_name}. Exiting.")
        sys.exit(1) # خروج از اسکریپت
    
    required_columns = ['High', 'Low', 'Close']
    if not all(col in data.columns for col in required_columns):
        print(f"FATAL ERROR: Data for {symbol_name} is missing required columns. Exiting.")
        sys.exit(1)
    
    # حذف سطرهایی که داده ناقص دارند
    data.dropna(subset=required_columns, inplace=True)
    if len(data) < EMA_PERIOD_TREND:
        print(f"FATAL ERROR: Not enough historical data for {symbol_name} after cleaning. Exiting.")
        sys.exit(1)
    
    return data


def get_market_context(start, end):
    """زمینه بازار را با مدیریت خطای کامل تحلیل می‌کند"""
    context = {}
    print("Analyzing market context...")
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=15)
            data = validate_data(data, name) # اعتبارسنجی داده‌ها
            data['EMA'] = calculate_ema(data['Close'], EMA_PERIOD_TREND)
            context[name] = "Bullish" if data['Close'].iloc[-1] > data['EMA'].iloc[-1] else "Bearish"
        except Exception as e:
            print(f"Could not process data for {name}: {e}")
            context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

def generate_final_analysis(data, context):
    """تحلیل نهایی با استفاده از اندیکاتورهای داخلی و داده‌های معتبر"""
    data['RSI_14'] = calculate_rsi(data['Close'], 14)
    data['Trend_EMA'] = calculate_ema(data['Close'], EMA_PERIOD_TREND)
    data = data.dropna()

    prominence_threshold = data['Close'].std() * 0.5 # آستانه برجستگی بر اساس انحراف معیار قیمت
    trade_plans = []

    # تحلیل سقف‌ها
    high_indices, _ = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Sell Plan @ {peak['High']:.5f}. "
        if peak['Close'] < peak['Trend_EMA']: score += 20; thesis += "Pro-Trend. "
        if context.get("DXY") == "Bullish": score += 30; thesis += "DXY Confirms. "
        if peak['RSI_14'] > 68: score += 15; thesis += "Overbought. "
        trade_plans.append({"type": "SELL", "price": peak['High'], "confidence_score": min(score, 100), "trade_thesis": thesis})

    # تحلیل کف‌ها
    low_indices, _ = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in low_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Buy Plan @ {peak['Low']:.5f}. "
        if peak['Close'] > peak['Trend_EMA']: score += 20; thesis += "Pro-Trend. "
        if context.get("DXY") == "Bearish": score += 30; thesis += "DXY Confirms. "
        if peak['RSI_14'] < 32: score += 15; thesis += "Oversold. "
        trade_plans.append({"type": "BUY", "price": peak['Low'], "confidence_score": min(score, 100), "trade_thesis": thesis})
        
    return trade_plans

def main():
    print(f"Starting Robust Analysis (V-Final) for: {PRIMARY_SYMBOL}")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    market_context = get_market_context(start_date, end_date)
    
    primary_data = yf.download(PRIMARY_SYMBOL, start=start_date, end=end_date, progress=False, timeout=15)
    primary_data = validate_data(primary_data, PRIMARY_SYMBOL) # اعتبارسنجی داده اصلی
    
    all_plans = generate_final_analysis(primary_data, market_context)
    all_plans.sort(key=lambda x: x['confidence_score'], reverse=True)
    final_plans = all_plans[:4]

    output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "trade_plans": final_plans}

    with open(OUTPUT_FILENAME, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Robust analysis complete. {len(final_plans)} trade plans saved to '{OUTPUT_FILENAME}'.")

if __name__ == "__main__":
    main()
