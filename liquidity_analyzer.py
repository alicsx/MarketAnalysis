# liquidity_analyzer_v5.py
# Copyright 2025, Gemini AI - Dynamic, ML-Ready Analysis

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
OUTPUT_FILENAME = "liquidity_analysis_v5.json"

def get_market_volatility(data):
    """میزان کلی نوسانات بازار را بر اساس ATR نرمال شده برمی‌گرداند"""
    atr = data['ATR'].iloc[-1]
    price = data['Close'].iloc[-1]
    normalized_atr = (atr / price) * 100
    if normalized_atr > 0.8: return "High"
    if normalized_atr < 0.4: return "Low"
    return "Normal"

def find_key_levels_v5(data, timeframe_tag, main_trend):
    """
    منطق جامع برای یافتن سطوح، غنی‌سازی با ویژگی‌های جدید و امتیازدهی
    """
    if data.empty or len(data) < EMA_PERIOD_TREND:
        return []

    # محاسبه اندیکاتورهای لازم
    data.ta.atr(length=14, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.ema(length=20, append=True, col="Volume") # میانگین حجم
    data = data.dropna()
    
    market_volatility = get_market_volatility(data)
    prominence_multiplier = 1.0 if market_volatility == "High" else 0.6
    prominence_threshold = data['ATR_14'].mean() * prominence_multiplier
    
    all_peaks = []
    
    # --- یافتن قله‌ها (Highs) ---
    high_indices, high_props = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=5)
    for i, idx in enumerate(high_indices):
        peak_data = data.iloc[idx]
        peak_date = peak_data.name.to_pydatetime()
        
        # یافتن آخرین کف قبل از این قله
        sub_data = data.loc[data.index < peak_date]
        lows_before, _ = find_peaks(-sub_data['Low'].to_numpy(), prominence=prominence_threshold/2, distance=3)
        choch_level = sub_data.iloc[lows_before[-1]]['Low'] if len(lows_before) > 0 else 0

        all_peaks.append({
            "type": "high",
            "price_zone_high": peak_data['High'],
            "price_zone_low": peak_data['Open'] if peak_data['Open'] < peak_data['Close'] else peak_data['Close'],
            "prominence": high_props['prominences'][i],
            "timeframe": timeframe_tag, "main_trend": main_trend,
            "choch_level": choch_level,
            "rsi_at_formation": round(peak_data['RSI_14'], 2),
            "days_since_formation": (datetime.now() - peak_date).days,
            "volume_ratio": round(peak_data['Volume'] / peak_data['Volume_EMA_20'], 2) if peak_data['Volume_EMA_20'] > 0 else 1
        })

    # --- یافتن دره‌ها (Lows) ---
    low_indices, low_props = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for i, idx in enumerate(low_indices):
        peak_data = data.iloc[idx]
        peak_date = peak_data.name.to_pydatetime()
        
        # یافتن آخرین سقف قبل از این دره
        sub_data = data.loc[data.index < peak_date]
        highs_before, _ = find_peaks(sub_data['High'].to_numpy(), prominence=prominence_threshold/2, distance=3)
        choch_level = sub_data.iloc[highs_before[-1]]['High'] if len(highs_before) > 0 else 0

        all_peaks.append({
            "type": "low",
            "price_zone_high": peak_data['Open'] if peak_data['Open'] > peak_data['Close'] else peak_data['Close'],
            "price_zone_low": peak_data['Low'],
            "prominence": low_props['prominences'][i],
            "timeframe": timeframe_tag, "main_trend": main_trend,
            "choch_level": choch_level,
            "rsi_at_formation": round(peak_data['RSI_14'], 2),
            "days_since_formation": (datetime.now() - peak_date).days,
            "volume_ratio": round(peak_data['Volume'] / peak_data['Volume_EMA_20'], 2) if peak_data['Volume_EMA_20'] > 0 else 1
        })
        
    return all_peaks

def calculate_validity_score_v5(level):
    """سیستم امتیازدهی چند عاملی"""
    score = 40
    # هم‌جهتی با روند
    if (level['type'] == 'high' and level['main_trend'] == 'Down') or (level['type'] == 'low' and level['main_trend'] == 'Up'):
        score += 25
    # وضعیت RSI
    if (level['type'] == 'high' and level['rsi_at_formation'] > 65) or (level['type'] == 'low' and level['rsi_at_formation'] < 35):
        score += 15
    # حجم بالا
    if level['volume_ratio'] > 1.5: score += 10
    # تازگی سطح
    if level['days_since_formation'] < 30: score += 10
    
    return int(min(score, 100))

def analyze_machine_learning_ready():
    print(f"شروع تحلیل V5 (آماده برای یادگیری ماشین) برای: {SYMBOL}")
    try:
        end_date = datetime.now()
        daily_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_DAILY), end=end_date, interval="1d")
        daily_data.ta.ema(length=EMA_PERIOD_TREND, append=True, col="Close")
        main_trend = "Up" if daily_data['Close'].iloc[-1] > daily_data[f'EMA_{EMA_PERIOD_TREND}'].iloc[-1] else "Down"
        
        weekly_data = yf.download(SYMBOL, start=end_date - timedelta(days=LOOKBACK_DAYS_WEEKLY), end=end_date, interval="1wk")

        levels = find_key_levels_v5(daily_data, "D1", main_trend) + find_key_levels_v5(weekly_data, "W1", main_trend)
        
        for level in levels:
            level['validity_score'] = calculate_validity_score_v5(level)
            
        levels.sort(key=lambda x: x['validity_score'], reverse=True)
        final_levels = [l for l in levels if l['validity_score'] > 50][:NUM_LEVELS_TO_KEEP*2]

        output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "liquidity_levels": final_levels}

        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4, default=str)
        
        print(f"تحلیل جامع V5 با موفقیت انجام و {len(final_levels)} سطح کلیدی در '{OUTPUT_FILENAME}' ذخیره شد.")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")

if __name__ == "__main__":
    analyze_machine_learning_ready()
