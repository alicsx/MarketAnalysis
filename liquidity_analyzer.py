# liquidity_analyzer_v4.py
# Copyright 2025, Gemini AI - Context-Aware & Scored Analysis

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json

# --- تنظیمات اصلی ---
SYMBOL = "EURUSD=X"
LOOKBACK_DAYS_DAILY = 90
LOOKBACK_DAYS_WEEKLY = 400
NUM_LEVELS_TO_KEEP = 2
EMA_PERIOD_TREND = 50
OUTPUT_FILENAME = "liquidity_analysis_v4.json"

def calculate_atr(data, period=14):
    """محاسبه اندیکاتور ATR"""
    data = data.copy()
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    data['ATR'] = true_range.ewm(alpha=1/period, adjust=False).mean()
    return data

def find_key_levels_v4(data, timeframe_tag, main_trend):
    """
    منطق پیشرفته برای یافتن سطوح، امتیازدهی و شناسایی سطح ChoCH
    """
    if data.empty or len(data) < EMA_PERIOD_TREND:
        return []

    data = calculate_atr(data)
    data = data.dropna()

    prominence_threshold = data['ATR'].mean() * 0.75
    all_peaks = []

    # --- یافتن قله‌ها (Highs) ---
    high_indices, high_props = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=5)
    for i, idx in enumerate(high_indices):
        # یافتن آخرین کف قبل از این قله برای سطح ChoCH
        sub_data = data.iloc[:idx]
        lows_before_high, _ = find_peaks(-sub_data['Low'].to_numpy(), prominence=prominence_threshold/2, distance=3)
        choch_level = sub_data.iloc[lows_before_high[-1]]['Low'] if len(lows_before_high) > 0 else 0
        
        all_peaks.append({
            "type": "high",
            "price": data.iloc[idx]['High'],
            "prominence": high_props['prominences'][i],
            "timeframe": timeframe_tag,
            "atr": data.iloc[idx]['ATR'],
            "trend": main_trend,
            "choch_level": choch_level
        })

    # --- یافتن دره‌ها (Lows) ---
    low_indices, low_props = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for i, idx in enumerate(low_indices):
        # یافتن آخرین سقف قبل از این دره برای سطح ChoCH
        sub_data = data.iloc[:idx]
        highs_before_low, _ = find_peaks(sub_data['High'].to_numpy(), prominence=prominence_threshold/2, distance=3)
        choch_level = sub_data.iloc[highs_before_low[-1]]['High'] if len(highs_before_low) > 0 else 0

        all_peaks.append({
            "type": "low",
            "price": data.iloc[idx]['Low'],
            "prominence": low_props['prominences'][i],
            "timeframe": timeframe_tag,
            "atr": data.iloc[idx]['ATR'],
            "trend": main_trend,
            "choch_level": choch_level
        })
        
    return all_peaks

def calculate_validity_score(level):
    """محاسبه امتیاز اعتبار برای هر سطح"""
    score = 50
    # امتیاز هم‌جهتی با روند
    if (level['type'] == 'high' and level['trend'] == 'Down') or \
       (level['type'] == 'low' and level['trend'] == 'Up'):
        score += 25
    # امتیاز تایم‌فریم
    if level['timeframe'] == 'W1':
        score += 15
    # امتیاز برجستگی
    score += min(level['prominence'] / level['atr'] * 5, 10) # نرمال‌سازی امتیاز برجستگی
    return int(min(score, 100))

def analyze_context_aware():
    print(f"شروع تحلیل مبتنی بر زمینه (V4) برای: {SYMBOL}")
    try:
        end_date = datetime.now()
        # ۱. دریافت داده و تشخیص روند اصلی از تایم روزانه
        daily_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_DAILY), end=end_date, interval="1d")
        daily_data['EMA_Trend'] = daily_data['Close'].ewm(span=EMA_PERIOD_TREND, adjust=False).mean()
        main_trend = "Up" if daily_data['Close'].iloc[-1] > daily_data['EMA_Trend'].iloc[-1] else "Down"
        print(f"روند اصلی شناسایی شده: {main_trend}")

        weekly_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_WEEKLY), end=end_date, interval="1wk")

        daily_levels = find_key_levels_v4(daily_data, "D1", main_trend)
        weekly_levels = find_key_levels_v4(weekly_data, "W1", main_trend)
        
        all_levels = daily_levels + weekly_levels

        for level in all_levels:
            level['validity_score'] = calculate_validity_score(level)
        
        # مرتب‌سازی بر اساس امتیاز و سپس برجستگی
        all_levels.sort(key=lambda x: (x['validity_score'], x['prominence']), reverse=True)

        highs = [l for l in all_levels if l['type'] == 'high']
        lows = [l for l in all_levels if l['type'] == 'low']

        final_levels = highs[:NUM_LEVELS_TO_KEEP] + lows[:NUM_LEVELS_TO_KEEP]

        for level in final_levels:
            del level['prominence']

        output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "liquidity_levels": final_levels}

        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4, default=str)
        
        print(f"تحلیل جامع V4 با موفقیت انجام و {len(final_levels)} سطح کلیدی در '{OUTPUT_FILENAME}' ذخیره شد.")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")

if __name__ == "__main__":
    analyze_context_aware()
