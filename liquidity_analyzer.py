# liquidity_analyzer_v6.py
# Copyright 2025, Gemini AI - Predictive & Self-Optimizing Analysis

import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json

# --- تنظیمات اصلی ---
SYMBOL = "EURUSD=X"
LOOKBACK_DAYS_DAILY = 120
LOOKBACK_DAYS_WEEKLY = 500
NUM_LEVELS_TO_KEEP = 2
EMA_PERIOD_TREND = 50
OUTPUT_FILENAME = "liquidity_analysis_v6.json"

def analyze_predictive_levels(data, timeframe_tag, main_trend):
    if data.empty or len(data) < EMA_PERIOD_TREND:
        return []

    # محاسبه اندیکاتورهای جامع با pandas_ta
    data.ta.atr(length=14, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.bbands(length=20, append=True) # Bollinger Bands
    data.ta.ichimoku(append=True) # Ichimoku Cloud
    data = data.dropna()
    
    prominence_threshold = data['ATRr_14'].mean() * 0.7
    all_peaks = []
    
    high_indices, _ = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        is_pro_trend = main_trend == 'Down'
        is_overbought = peak['RSI_14'] > 68
        # بررسی هم‌راستایی با ابر ایچیموکو آینده
        is_ichimoku_aligned = peak['High'] > peak['ITS_9'] and peak['Close'] < peak['IKS_26'] and peak['Close'] < peak['ISA_9']
        is_after_squeeze = data['BBB_20_2.0'].iloc[max(0, idx-5):idx].mean() < data['BBB_20_2.0'].mean() * 0.8
        
        thesis = f"Sell setup at {timeframe_tag} high. "
        if is_pro_trend: thesis += "Pro-trend. "
        if is_overbought: thesis += "Overbought RSI. "
        if is_ichimoku_aligned: thesis += "Rejected by Ichimoku. "
        if is_after_squeeze: thesis += "Post-squeeze volatility expected. "
        
        all_peaks.append({
            "type": "high", "price": peak['High'], "timeframe": timeframe_tag,
            "ichimoku_aligned": is_ichimoku_aligned,
            "after_squeeze": is_after_squeeze,
            "validity_score": 50 + (25 if is_pro_trend else 0) + (15 if is_overbought else 0) + (20 if is_ichimoku_aligned else 0),
            "trade_thesis": thesis
        })

    low_indices, _ = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in low_indices:
        peak = data.iloc[idx]
        is_pro_trend = main_trend == 'Up'
        is_oversold = peak['RSI_14'] < 32
        is_ichimoku_aligned = peak['Low'] < peak['ITS_9'] and peak['Close'] > peak['IKS_26'] and peak['Close'] > peak['ISA_9']
        is_after_squeeze = data['BBB_20_2.0'].iloc[max(0, idx-5):idx].mean() < data['BBB_20_2.0'].mean() * 0.8
        
        thesis = f"Buy setup at {timeframe_tag} low. "
        if is_pro_trend: thesis += "Pro-trend. "
        if is_oversold: thesis += "Oversold RSI. "
        if is_ichimoku_aligned: thesis += "Supported by Ichimoku. "
        if is_after_squeeze: thesis += "Post-squeeze volatility expected. "

        all_peaks.append({
            "type": "low", "price": peak['Low'], "timeframe": timeframe_tag,
            "ichimoku_aligned": is_ichimoku_aligned,
            "after_squeeze": is_after_squeeze,
            "validity_score": 50 + (25 if is_pro_trend else 0) + (15 if is_oversold else 0) + (20 if is_ichimoku_aligned else 0),
            "trade_thesis": thesis
        })
        
    return all_peaks

def main():
    print(f"شروع تحلیل پیش‌بینانه V6 برای: {SYMBOL}")
    try:
        end_date = datetime.now()
        daily_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_DAILY), end=end_date, interval="1d")
        daily_data.ta.ema(length=EMA_PERIOD_TREND, append=True)
        main_trend = "Up" if daily_data['Close'].iloc[-1] > daily_data[f'EMA_{EMA_PERIOD_TREND}'].iloc[-1] else "Down"
        
        weekly_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_WEEKLY), end=end_date, interval="1wk")
        
        levels = analyze_predictive_levels(daily_data, "D1", main_trend) + analyze_predictive_levels(weekly_data, "W1", main_trend)
        levels.sort(key=lambda x: x['validity_score'], reverse=True)

        final_levels = levels[:NUM_LEVELS_TO_KEEP*2]
        output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "liquidity_levels": final_levels}

        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        print(f"تحلیل جامع V6 با موفقیت انجام و {len(final_levels)} سطح کلیدی در '{OUTPUT_FILENAME}' ذخیره شد.")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")

if __name__ == "__main__":
    main()
