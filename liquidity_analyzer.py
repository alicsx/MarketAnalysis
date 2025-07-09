# liquidity_analyzer_standalone.py
# Copyright 2025, Gemini AI - The Final, Standalone & Error-Free Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json

# --- تنظیمات نهایی ---
PRIMARY_SYMBOL = "EURUSD=X"
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 120
EMA_PERIOD_TREND = 50
OUTPUT_FILENAME = "liquidity_analysis_final.json"

# --- پیاده‌سازی مستقیم اندیکاتورها (حذف وابستگی به pandas_ta) ---
def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return calculate_ema(tr, period)

def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_market_context(start, end):
    """زمینه کلی بازار را بر اساس نمادهای همبستگی تحلیل می‌کند"""
    context = {}
    print("Analyzing market context...")
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=10)
            if not data.empty:
                data['EMA'] = calculate_ema(data['Close'], EMA_PERIOD_TREND)
                context[name] = "Bullish" if data['Close'].iloc[-1] > data['EMA'].iloc[-1] else "Bearish"
        except Exception:
            context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

def generate_final_analysis(data, context):
    """تحلیل نهایی با استفاده از اندیکاتورهای داخلی"""
    if data.empty or len(data) < EMA_PERIOD_TREND: return []
    
    data['ATRr_14'] = calculate_atr(data, 14)
    data['RSI_14'] = calculate_rsi(data['Close'], 14)
    data['Trend_EMA'] = calculate_ema(data['Close'], EMA_PERIOD_TREND)
    data = data.dropna()

    prominence_threshold = data['ATRr_14'].mean() * 0.7
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
    print(f"Starting Standalone Analysis (V-Final) for: {PRIMARY_SYMBOL}")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        
        market_context = get_market_context(start_date, end_date)
        primary_data = yf.download(PRIMARY_SYMBOL, start=start_date, end=end_date, progress=False, timeout=10)
        
        all_plans = generate_final_analysis(primary_data, market_context)
        all_plans.sort(key=lambda x: x['confidence_score'], reverse=True)

        output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "trade_plans": all_plans[:4]}

        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        print(f"Final standalone analysis complete. {len(all_plans[:4])} trade plans saved to '{OUTPUT_FILENAME}'.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
