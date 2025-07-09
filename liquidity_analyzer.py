# liquidity_analyzer_v3.py
# Copyright 2025, Gemini AI - Multi-Timeframe & Comprehensive Analysis

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json

# --- تنظیمات اصلی ---
SYMBOL = "EURUSD=X"
LOOKBACK_DAYS_DAILY = 60      # دوره تحلیل روزانه
LOOKBACK_DAYS_WEEKLY = 365    # دوره تحلیل هفتگی (یک سال)
NUM_LEVELS_TO_KEEP = 2        # تعداد سطوح برتر برای هر نوع (سقف/کف)
OUTPUT_FILENAME = "liquidity_analysis.json" # خروجی جدید با فرمت JSON

def calculate_atr(data, period=14):
    """محاسبه اندیکاتور ATR"""
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def find_key_levels(data, timeframe_tag):
    """
    منطق اصلی برای یافتن سطوح برجسته در یک دیتافریم مشخص.
    """
    if data.empty:
        return []

    data['ATR'] = calculate_atr(data)
    data = data.dropna()

    prominence_threshold = data['ATR'].mean() * 0.5
    levels = []

    # --- یافتن قله‌ها (Highs) ---
    # FIX: تبدیل به numpy array برای جلوگیری از خطا
    high_peaks_indices, high_props = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=3)
    
    for i, idx in enumerate(high_peaks_indices):
        level_data = data.iloc[idx]
        levels.append({
            "type": "high",
            "price": level_data['High'],
            "prominence": high_props['prominences'][i],
            "timeframe": timeframe_tag,
            "atr": level_data['ATR']
        })

    # --- یافتن دره‌ها (Lows) ---
    # FIX: تبدیل به numpy array برای جلوگیری از خطا
    low_peaks_indices, low_props = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=3)

    for i, idx in enumerate(low_peaks_indices):
        level_data = data.iloc[idx]
        levels.append({
            "type": "low",
            "price": level_data['Low'],
            "prominence": low_props['prominences'][i],
            "timeframe": timeframe_tag,
            "atr": level_data['ATR']
        })
        
    return levels

def analyze_multi_timeframe():
    print(f"شروع تحلیل جامع چند تایم‌فریمی برای: {SYMBOL}")
    try:
        # ۱. دریافت داده‌های روزانه و هفتگی
        end_date = datetime.now()
        daily_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_DAILY), end=end_date, interval="1d")
        weekly_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_WEEKLY), end=end_date, interval="1wk")

        # ۲. تحلیل هر دو تایم‌فریم
        daily_levels = find_key_levels(daily_data, "D1")
        weekly_levels = find_key_levels(weekly_data, "W1")
        
        all_levels = daily_levels + weekly_levels

        # ۳. فیلتر کردن و مرتب‌سازی نهایی برای یافتن بهترین سطوح
        highs = sorted([l for l in all_levels if l['type'] == 'high'], key=lambda x: x['prominence'], reverse=True)
        lows = sorted([l for l in all_levels if l['type'] == 'low'], key=lambda x: x['prominence'], reverse=True)

        # انتخاب N سطح برتر از هر کدام
        final_levels = highs[:NUM_LEVELS_TO_KEEP] + lows[:NUM_LEVELS_TO_KEEP]
        
        # حذف کلید برجستگی که دیگر برای ربات لازم نیست
        for level in final_levels:
            del level['prominence']

        output_data = {
            "symbol": SYMBOL,
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "liquidity_levels": final_levels
        }

        # ۴. ذخیره در فایل JSON
        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4)
        
        print(f"تحلیل جامع با موفقیت انجام و {len(final_levels)} سطح کلیدی در '{OUTPUT_FILENAME}' ذخیره شد.")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")

if __name__ == "__main__":
    analyze_multi_timeframe()
