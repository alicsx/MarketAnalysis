# liquidity_analyzer_v7.py
# Copyright 2025, Gemini AI - Inter-Market Correlation Analysis

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json

# --- تنظیمات اصلی ---
PRIMARY_SYMBOL = "EURUSD=X"
CORRELATION_SYMBOLS = {
    "DXY": "DX-Y.NYB",      # شاخص دلار
    "SPX": "^GSPC"          # شاخص S&P 500
}
LOOKBACK_DAYS = 120
NUM_LEVELS_TO_KEEP = 2
EMA_PERIOD = 50
OUTPUT_FILENAME = "liquidity_analysis_v7.json"

def get_technical_summary(data, symbol_name):
    """خلاصه وضعیت تکنیکال یک نماد را برمی‌گرداند"""
    if data.empty or len(data) < EMA_PERIOD:
        return {"trend": "Unknown"}
    data.ta.ema(length=EMA_PERIOD, append=True)
    last_close = data['Close'].iloc[-1]
    last_ema = data[f'EMA_{EMA_PERIOD}'].iloc[-1]
    
    summary = {}
    if last_close > last_ema * 1.005:
        summary["trend"] = "Strong Bullish"
    elif last_close > last_ema:
        summary["trend"] = "Bullish"
    elif last_close < last_ema * 0.995:
        summary["trend"] = "Strong Bearish"
    else:
        summary["trend"] = "Bearish"
        
    return summary

def analyze_levels_with_correlation(data, correlation_context):
    """سطوح نقدینگی را با در نظر گرفتن زمینه بازار تحلیل می‌کند"""
    if data.empty: return []
    data.ta.atr(length=14, append=True)
    data = data.dropna()
    
    prominence_threshold = data['ATRr_14'].mean() * 0.7
    levels = []
    
    high_indices, _ = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        level_price = data.iloc[idx]['High']
        
        score = 50
        thesis = f"Sell setup at {level_price:.5f}. "
        
        # امتیازدهی بر اساس همبستگی
        if correlation_context.get("DXY", {}).get("trend", "").endswith("Bullish"):
            score += 30
            thesis += "Confirmed by DXY strength. "
        if correlation_context.get("SPX", {}).get("trend", "").endswith("Bearish"):
            score += 10 # ریسک گریزی به نفع دلار و علیه یورو است
            thesis += "Risk-off sentiment. "
            
        levels.append({"type": "high", "price": level_price, "validity_score": score, "trade_thesis": thesis})

    low_indices, _ = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in low_indices:
        level_price = data.iloc[idx]['Low']
        
        score = 50
        thesis = f"Buy setup at {level_price:.5f}. "
        
        if correlation_context.get("DXY", {}).get("trend", "").endswith("Bearish"):
            score += 30
            thesis += "Confirmed by DXY weakness. "
        if correlation_context.get("SPX", {}).get("trend", "").endswith("Bullish"):
            score += 10 # ریسک پذیری به نفع یورو و علیه دلار است
            thesis += "Risk-on sentiment. "
            
        levels.append({"type": "low", "price": level_price, "validity_score": score, "trade_thesis": thesis})
        
    return levels

def main():
    print(f"شروع تحلیل همبستگی V7 برای: {PRIMARY_SYMBOL}")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        
        # ۱. تحلیل بازارهای مرتبط
        correlation_context = {}
        for name, ticker in CORRELATION_SYMBOLS.items():
            print(f"Analyzing correlation symbol: {name}")
            corr_data = yf.download(ticker, start=start_date, end=end_date)
            correlation_context[name] = get_technical_summary(corr_data, name)
        
        print(f"Correlation Context: {correlation_context}")
        
        # ۲. تحلیل نماد اصلی با استفاده از زمینه همبستگی
        primary_data = yf.download(PRIMARY_SYMBOL, start=start_date, end=end_date)
        levels = analyze_levels_with_correlation(primary_data, correlation_context)
        
        levels.sort(key=lambda x: x['validity_score'], reverse=True)
        final_levels = levels[:NUM_LEVELS_TO_KEEP*2]

        output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "liquidity_levels": final_levels}

        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        print(f"تحلیل جامع V7 با موفقیت انجام و {len(final_levels)} سطح کلیدی در '{OUTPUT_FILENAME}' ذخیره شد.")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")

if __name__ == "__main__":
    main()
