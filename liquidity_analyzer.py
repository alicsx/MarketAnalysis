# liquidity_analyzer_final.py
# Copyright 2025, Gemini AI - The Final, Comprehensive Version

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json

# --- تنظیمات اصلی ---
PRIMARY_SYMBOL = "EURUSD=X"
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB", "SPX": "^GSPC"}
LOOKBACK_DAYS = 120
NUM_LEVELS_TO_KEEP = 2
EMA_PERIOD_TREND = 50
OUTPUT_FILENAME = "liquidity_analysis_final.json"

def get_market_context(corr_symbols, start_date, end_date):
    """زمینه کلی بازار را بر اساس نمادهای همبستگی تحلیل می‌کند"""
    context = {}
    print("Analyzing market context...")
    for name, ticker in corr_symbols.items():
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False, timeout=10)
            if not data.empty and 'Close' in data.columns:
                data.ta.ema(length=EMA_PERIOD_TREND, append=True)
                last_close = data['Close'].iloc[-1]
                last_ema = data[f'EMA_{EMA_PERIOD_TREND}'].iloc[-1]
                context[name] = "Bullish" if last_close > last_ema else "Bearish"
            else:
                context[name] = "Unknown"
        except Exception as e:
            print(f"Could not fetch data for {name}: {e}")
            context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

def analyze_final_levels(data, context):
    """سطوح نقدینگی را با استفاده از تحلیل جامع و چند وجهی شناسایی می‌کند"""
    if data.empty or len(data) < EMA_PERIOD_TREND: return []
    
    # محاسبه اندیکاتورهای جامع
    data.ta.atr(length=14, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.ichimoku(append=True)
    data = data.dropna()

    prominence_threshold = data['ATRr_14'].mean() * 0.7
    levels = []

    # تحلیل سقف‌ها
    high_indices, _ = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Sell @ {peak['High']:.5f} (D1). "
        if context.get("DXY") == "Bullish": score += 30; thesis += "DXY Strength confirms. "
        if context.get("SPX") == "Bearish": score += 10; thesis += "Risk-off sentiment. "
        if peak['RSI_14'] > 68: score += 15; thesis += "Overbought RSI. "
        if peak['Close'] < peak['ISA_9']: score += 15; thesis += "Rejected by Ichimoku. "
        levels.append({"type": "high", "price": peak['High'], "validity_score": int(min(score, 100)), "trade_thesis": thesis})

    # تحلیل کف‌ها
    low_indices, _ = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in low_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Buy @ {peak['Low']:.5f} (D1). "
        if context.get("DXY") == "Bearish": score += 30; thesis += "DXY Weakness confirms. "
        if context.get("SPX") == "Bullish": score += 10; thesis += "Risk-On sentiment. "
        if peak['RSI_14'] < 32: score += 15; thesis += "Oversold RSI. "
        if peak['Close'] > peak['ISA_9']: score += 15; thesis += "Supported by Ichimoku. "
        levels.append({"type": "low", "price": peak['Low'], "validity_score": int(min(score, 100)), "trade_thesis": thesis})
        
    return levels

def main():
    print(f"Starting Final Analysis (V-Final) for: {PRIMARY_SYMBOL}")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        
        market_context = get_market_context(CORRELATION_SYMBOLS, start_date, end_date)
        primary_data = yf.download(PRIMARY_SYMBOL, start=start_date, end_date, progress=False, timeout=10)
        
        all_levels = analyze_final_levels(primary_data, market_context)
        all_levels.sort(key=lambda x: x['validity_score'], reverse=True)
        final_levels = all_levels[:NUM_LEVELS_TO_KEEP*2]

        output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "liquidity_levels": final_levels}

        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        print(f"Final analysis complete. {len(final_levels)} key levels saved to '{OUTPUT_FILENAME}'.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
