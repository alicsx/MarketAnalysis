# liquidity_analyzer_v2.py
# Copyright 2025, Gemini AI - Advanced Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta

# --- تنظیمات اصلی ---
SYMBOL = "EURUSD=X"
LOOKBACK_DAYS = 60  # دوره تحلیل را برای یافتن سطوح معتبرتر افزایش می‌دهیم
OUTPUT_FILENAME = "liquidity_levels.txt"

def calculate_atr(data, period=14):
    """محاسبه اندیکاتور ATR"""
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def analyze_and_save_liquidity_v2():
    """
    با استفاده از تحلیل پیشرفته قله‌ها، مهم‌ترین سطوح نقدینگی را شناسایی می‌کند.
    """
    print(f"شروع تحلیل پیشرفته برای نماد: {SYMBOL}")
    try:
        # ۱. دریافت داده‌ها و محاسبه ATR
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        data = yf.download(SYMBOL, start=start_date, end=end_date, interval="1d")

        if data.empty:
            print("خطا: داده‌ای دریافت نشد.")
            return
            
        data['ATR'] = calculate_atr(data)
        data = data.dropna() # حذف سطرهای با مقدار NaN

        # ۲. یافتن قله‌ها (Swing Highs) و دره‌ها (Swing Lows) با تحلیل برجستگی
        # یک حد آستانه پویا برای برجستگی بر اساس میانگین ATR تعیین می‌کنیم
        prominence_threshold = data['ATR'].mean() * 0.5 

        # یافتن قله‌ها
        high_peaks_indices, high_properties = find_peaks(data['High'], prominence=prominence_threshold, distance=5)
        
        # یافتن دره‌ها (با معکوس کردن سری داده)
        low_peaks_indices, low_properties = find_peaks(-data['Low'], prominence=prominence_threshold, distance=5)

        if len(high_peaks_indices) == 0 or len(low_peaks_indices) == 0:
            print("هشدار: قله یا دره برجسته‌ای در دوره مشخص شده یافت نشد.")
            return

        # ۳. انتخاب برجسته‌ترین قله و دره
        most_prominent_high_index = high_peaks_indices[np.argmax(high_properties['prominences'])]
        most_prominent_low_index = low_peaks_indices[np.argmax(low_properties['prominences'])]

        # ۴. استخراج اطلاعات سطح نقدینگی نهایی
        key_high_data = data.iloc[most_prominent_high_index]
        key_low_data = data.iloc[most_prominent_low_index]
        
        key_high_price = key_high_data['High']
        key_high_date = key_high_data.name.strftime('%Y-%m-%d')
        key_high_atr = key_high_data['ATR']
        
        key_low_price = key_low_data['Low']
        key_low_date = key_low_data.name.strftime('%Y-%m-%d')
        key_low_atr = key_low_data['ATR']
        
        last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"برجسته‌ترین سطح بالا: {key_high_price:.5f} (ATR: {key_high_atr:.5f}) در تاریخ: {key_high_date}")
        print(f"برجسته‌ترین سطح پایین: {key_low_price:.5f} (ATR: {key_low_atr:.5f}) در تاریخ: {key_low_date}")

        # ۵. ساخت خروجی برای MQL4
        output_content = (
            f"key_high:{key_high_price:.5f}\n"
            f"key_high_atr:{key_high_atr:.5f}\n"
            f"key_low:{key_low_price:.5f}\n"
            f"key_low_atr:{key_low_atr:.5f}\n"
            f"last_update:{last_update_time}\n"
        )

        with open(OUTPUT_FILENAME, "w") as f:
            f.write(output_content)
            
        print(f"تحلیل پیشرفته با موفقیت در فایل '{OUTPUT_FILENAME}' ذخیره شد.")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")

if __name__ == "__main__":
    analyze_and_save_liquidity_v2()
