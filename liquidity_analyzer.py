# multi_currency_final_corrected.py
# Copyright 2025, Gemini AI - Final Corrected Logic Version

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json
import sys

# --- تنظیمات ---
# نام نمادها را برای سادگی در کد، بدون "=X" نگه می‌داریم
PRIMARY_SYMBOLS = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCAD", "NZDUSD"]
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 120
EMA_PERIOD = 50
TOP_N_PLANS_PER_SYMBOL = 2
OUTPUT_FILENAME = "multi_currency_analysis.json"

def validate_and_standardize_data(data, symbol_name):
    if data is None or data.empty: return None
    data.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in data.columns]
    required = ['high', 'low', 'close']
    if not all(col in data.columns for col in required): return None
    data.dropna(subset=required, inplace=True)
    if len(data) < EMA_PERIOD: return None
    return data

def get_market_context(start, end):
    context = {}
    print("Analyzing market context...")
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=20)
            data = validate_and_standardize_data(data, name)
            if data is not None:
                data['ema'] = data['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
                context[name] = "Bullish" if data['close'].iloc[-1] > data['ema'].iloc[-1] else "Bearish"
        except Exception: context[name] = "Unknown"
    print(f"Market Context: {context}")
    return context

# +++ تابع تحلیل با منطق اصلاح شده +++
def generate_analysis(data, context, symbol_name):
    data['trend_ema'] = data['close'].ewm(span=200, adjust=False).mean()
    main_trend = "Up" if data['close'].iloc[-1] > data['trend_ema'].iloc[-1] else "Down"
    prominence_threshold = data['close'].std() * 0.6
    plans = []
    
    # === ویژگی جدید: دریافت زمان فعلی برای timestamp ===
    now_str = datetime.now().strftime("%Y.%m.%d %H:%M")
    
    high_indices, _ = find_peaks(data['high'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Sell Plan @ {peak['high']:.5f}. "
        if main_trend == "Down":
            score += 25
            thesis += "Pro-Trend. "
        
        # === منطق جدید و صحیح برای DXY ===
        # اگر USD ارز دوم است (مثل EURUSD)، فروش یعنی خرید دلار -> با DXY صعودی تایید می‌شود
        if "USD" in symbol_name[3:] and context.get("DXY") == "Bullish":
            score += 25
            thesis += "DXY Confirms. "
        # اگر USD ارز اول است (مثل USDCAD)، فروش یعنی فروش دلار -> با DXY نزولی تایید می‌شود
        elif "USD" in symbol_name[:3] and context.get("DXY") == "Bearish":
            score += 25
            thesis += "DXY Confirms. "

        plans.append({
            "type": "SELL",
            "price": peak['high'],
            "confidence_score": min(score, 100),
            "timestamp": now_str, # << ویژگی جدید اضافه شد
            "trade_thesis": thesis
        })

    low_indices, _ = find_peaks(-data['low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in low_indices:
        peak = data.iloc[idx]
        score = 50
        thesis = f"Buy Plan @ {peak['low']:.5f}. "
        if main_trend == "Up":
            score += 25
            thesis += "Pro-Trend. "
            
        # === منطق جدید و صحیح برای DXY ===
        # اگر USD ارز دوم است (مثل EURUSD)، خرید یعنی فروش دلار -> با DXY نزولی تایید می‌شود
        if "USD" in symbol_name[3:] and context.get("DXY") == "Bearish":
            score += 25
            thesis += "DXY Confirms. "
        # اگر USD ارز اول است (مثل USDCAD)، خرید یعنی خرید دلار -> با DXY صعودی تایید می‌شود
        elif "USD" in symbol_name[:3] and context.get("DXY") == "Bullish":
            score += 25
            thesis += "DXY Confirms. "

        plans.append({
            "type": "BUY",
            "price": peak['low'],
            "confidence_score": min(score, 100),
            "timestamp": now_str, # << ویژگی جدید اضافه شد
            "trade_thesis": thesis
        })
    return plans

def main():
    print("--- Starting Corrected Multi-Currency Analysis ---")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    market_context = get_market_context(start_date, end_date)
    all_analyses = {}

    for symbol in PRIMARY_SYMBOLS:
        print(f"\n--- Analyzing {symbol} ---")
        try:
            # تیکر یاهو فایننس "=X" را برای دانلود اضافه می‌کنیم
            ticker = symbol + "=X"
            primary_data = yf.download(ticker, start=start_date, end=end_date, progress=False, timeout=20)
            primary_data = validate_and_standardize_data(primary_data, symbol)
            
            if primary_data is None:
                continue

            # نام نماد (بدون "=X") به تابع تحلیل ارسال می‌شود
            potential_plans = generate_analysis(primary_data, market_context, symbol)
            
            potential_plans.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            top_plans_for_this_symbol = potential_plans[:TOP_N_PLANS_PER_SYMBOL]
            
            # نام تمیز نماد در خروجی استفاده می‌شود
            all_analyses[symbol] = {"trade_plans": top_plans_for_this_symbol}
            print(f"Analysis for {symbol} complete. Top {len(top_plans_for_this_symbol)} plans selected.")

        except Exception as e:
            print(f"ERROR while processing {symbol}: {e}")

    # ساختار نهایی خروجی JSON (بدون تغییر)
    # توجه: ساختار فایل خروجی را تغییر ندادم تا با ربات فعلی شما سازگار بماند
    # ربات شما باید داخل کلید اصلی هر ارز به دنبال "trade_plans" بگردد
    final_json_data = all_analyses 
    
    with open(OUTPUT_FILENAME, 'w') as f:
        json.dump(final_json_data, f, indent=4)
        
    print(f"\n--- Multi-currency analysis complete. Results for all symbols saved to '{OUTPUT_FILENAME}' ---")

if __name__ == "__main__":
    main()
