# liquidity_analyzer.py
# Copyright 2025, Gemini AI

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- تنظیمات اصلی ---
SYMBOL = "EURUSD=X"         # نماد معاملاتی در یاهو فایننس (برای طلا: GC=F, برای بیت‌کوین: BTC-USD)
LOOKBACK_DAYS = 30          # تعداد روزهای گذشته برای تحلیل
OUTPUT_FILENAME = "liquidity_levels.txt" # نام فایل خروجی

def analyze_and_save_liquidity():
    """
    داده‌های تاریخی را دریافت کرده، سطوح نقدینگی کلیدی را تحلیل و در فایل ذخیره می‌کند.
    """
    print(f"شروع تحلیل برای نماد: {SYMBOL}")

    try:
        # ۱. دریافت داده‌های تاریخی
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        
        data = yf.download(SYMBOL, start=start_date, end=end_date, interval="1d")

        if data.empty:
            print("خطا: داده‌ای برای بازه زمانی مشخص شده دریافت نشد. نماد یا بازه را چک کنید.")
            return

        # ۲. یافتن بالاترین سقف و پایین‌ترین کف در دوره
        key_high = data['High'].max()
        key_high_date = data['High'].idxmax().strftime('%Y-%m-%d')
        
        key_low = data['Low'].min()
        key_low_date = data['Low'].idxmin().strftime('%Y-%m-%d')
        
        last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"سطح نقدینگی بالا (High): {key_high:.5f} در تاریخ: {key_high_date}")
        print(f"سطح نقدینگی پایین (Low): {key_low:.5f} در تاریخ: {key_low_date}")

        # ۳. ساختن محتوای فایل خروجی
        # فرمت ساده برای خواندن آسان در MQL4
        output_content = (
            f"key_high:{key_high:.5f}\n"
            f"key_high_date:{key_high_date}\n"
            f"key_low:{key_low:.5f}\n"
            f"key_low_date:{key_low_date}\n"
            f"last_update:{last_update_time}\n"
        )

        # ۴. ذخیره کردن محتوا در فایل
        with open(OUTPUT_FILENAME, "w") as f:
            f.write(output_content)
            
        print(f"تحلیل با موفقیت انجام شد و نتایج در فایل '{OUTPUT_FILENAME}' ذخیره گردید.")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")


if __name__ == "__main__":
    analyze_and_save_liquidity()
