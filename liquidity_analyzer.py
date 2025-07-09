# liquidity_analyzer_production.py
# Copyright 2025, Gemini AI - Final, Production-Ready Version

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import json

# --- تنظیمات ---
PRIMARY_SYMBOL = "EURUSD=X"
CORRELATION_SYMBOLS = {"DXY": "DX-Y.NYB"}
LOOKBACK_DAYS = 120
EMA_TREND_PERIOD = 50
OUTPUT_FILENAME = "liquidity_plan.json"

def get_market_context(start, end):
    context = {}
    for name, ticker in CORRELATION_SYMBOLS.items():
        try:
            # FIX: Corrected yf.download call
            data = yf.download(ticker, start=start, end=end, progress=False, timeout=10)
            if not data.empty:
                data.ta.ema(length=EMA_TREND_PERIOD, append=True)
                context[name] = "Bullish" if data['Close'].iloc[-1] > data[f'EMA_{EMA_TREND_PERIOD}'].iloc[-1] else "Bearish"
        except Exception:
            context[name] = "Unknown"
    return context

def generate_trade_plan(data, context):
    if data.empty or len(data) < EMA_TREND_PERIOD: return []
    
    data.ta.atr(length=14, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.ema(length=EMA_TREND_PERIOD, append=True)
    data['trend'] = data.apply(lambda row: "Up" if row['Close'] > row[f'EMA_{EMA_TREND_PERIOD}'] else "Down", axis=1)
    
    prominence_threshold = data['ATRr_14'].mean() * 0.8
    trade_plans = []

    # تحلیل سقف‌ها برای پلن فروش
    high_indices, _ = find_peaks(data['High'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in high_indices:
        peak = data.iloc[idx]
        if peak.name < data.index[-2]: # Ignore very recent peaks
            entry_zone_high = peak['High']
            entry_zone_low = max(peak['Open'], peak['Close'])
            stop_loss_price = entry_zone_high + peak['ATRr_14'] * 0.2
            
            # پیدا کردن اهداف سود (کف‌های نوسانی قبلی)
            lows_before, _ = find_peaks(-data.iloc[:idx]['Low'].to_numpy(), prominence=prominence_threshold*0.5, distance=3)
            targets = [{"price": data.iloc[l_idx]['Low'], "rr": round((entry_zone_low - data.iloc[l_idx]['Low']) / (stop_loss_price - entry_zone_low), 2)} for l_idx in lows_before[-2:]]
            
            score = 40
            if peak['trend'] == "Down": score += 20
            if context.get("DXY") == "Bullish": score += 30
            if peak['RSI_14'] > 65: score += 10
            
            trade_plans.append({
                "type": "SELL", "confidence_score": min(score, 100),
                "entry_zone_high": entry_zone_high, "entry_zone_low": entry_zone_low,
                "stop_loss_price": stop_loss_price, "take_profit_targets": targets
            })

    # تحلیل کف‌ها برای پلن خرید
    low_indices, _ = find_peaks(-data['Low'].to_numpy(), prominence=prominence_threshold, distance=5)
    for idx in low_indices:
        peak = data.iloc[idx]
        if peak.name < data.index[-2]:
            entry_zone_low = peak['Low']
            entry_zone_high = min(peak['Open'], peak['Close'])
            stop_loss_price = entry_zone_low - peak['ATRr_14'] * 0.2

            highs_before, _ = find_peaks(data.iloc[:idx]['High'].to_numpy(), prominence=prominence_threshold*0.5, distance=3)
            targets = [{"price": data.iloc[h_idx]['High'], "rr": round((data.iloc[h_idx]['High'] - entry_zone_high) / (entry_zone_high - stop_loss_price), 2)} for h_idx in highs_before[-2:]]

            score = 40
            if peak['trend'] == "Up": score += 20
            if context.get("DXY") == "Bearish": score += 30
            if peak['RSI_14'] < 35: score += 10

            trade_plans.append({
                "type": "BUY", "confidence_score": min(score, 100),
                "entry_zone_high": entry_zone_high, "entry_zone_low": entry_zone_low,
                "stop_loss_price": stop_loss_price, "take_profit_targets": targets
            })
            
    return trade_plans

def main():
    print(f"Starting Production Analysis (V-Final) for: {PRIMARY_SYMBOL}")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        
        market_context = get_market_context(start_date, end_date)
        # FIX: Corrected yf.download call
        primary_data = yf.download(PRIMARY_SYMBOL, start=start_date, end=end_date, progress=False, timeout=10)
        
        all_plans = generate_trade_plan(primary_data, market_context)
        all_plans.sort(key=lambda x: x['confidence_score'], reverse=True)

        output_data = {"last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "trade_plans": all_plans[:4]}

        with open(OUTPUT_FILENAME, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        print(f"Production analysis complete. {len(all_plans[:4])} trade plans saved to '{OUTPUT_FILENAME}'.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
