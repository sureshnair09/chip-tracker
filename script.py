import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime

def generate_perfect_mobile_dashboard():
    # Master tracking array - Feel free to change "SOXX" to "SOXL" to watch the 3X variant directly
    watchlist = ["SOXX", "NVDA", "AVGO", "AMD", "TSM", "INTC"]
    summary_rows = []
    
    print(f"Executing master synchronization for watchlist: {watchlist}...")
    
    for ticker in watchlist:
        print(f"Scanning technical & fundamental attributes for: {ticker}...")
        try:
            ticker_obj = yf.Ticker(ticker)
            
            # 1. High-reliability endpoint download (Prevents loop crashing)
            df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
            if df_daily.empty:
                print(f"⚠️ Warning: Missing price arrays for {ticker}. Skipping.")
                continue
                
            if isinstance(df_daily.columns, pd.MultiIndex):
                df_daily.columns = df_daily.columns.get_level_values(0)
                
            current_price = float(df_daily['Close'].iloc[-1])
            prev_price = float(df_daily['Close'].iloc[-2])
            daily_change = ((current_price - prev_price) / prev_price) * 100
            
            # --- Technical Analysis Matrices ---
            df_daily['ema9'] = ta.trend.ema_indicator(df_daily['Close'], window=9)
            df_daily['ema21'] = ta.trend.ema_indicator(df_daily['Close'], window=21)
            df_daily['sma50'] = ta.trend.sma_indicator(df_daily['Close'], window=50)
            df_daily['sma200'] = ta.trend.sma_indicator(df_daily['Close'], window=200)
            df_daily['macd_hist'] = ta.trend.macd_diff(df_daily['Close'])
            
            # ADX & DMI Volatility Calculations
            df_daily['adx'] = ta.trend.adx(df_daily['High'], df_daily['Low'], df_daily['Close'], window=14)
            df_daily['plus_di'] = ta.trend.adx_pos(df_daily['High'], df_daily['Low'], df_daily['Close'], window=14)
            df_daily['minus_di'] = ta.trend.adx_neg(df_daily['High'], df_daily['Low'], df_daily['Close'], window=14)
            
            # Fibonacci Structural Retracements (52-Week Frame)
            high_52w = float(df_daily['High'].rolling(window=252).max().iloc[-1])
            low_52w = float(df_daily['Low'].rolling(window=252).min().iloc[-1])
            diff = high_52w - low_52w
            fib_50 = high_52w - (0.500 * diff)
            fib_618 = high_52w - (0.618 * diff)
            
            # Phase 2 High-Timeframe Resampling
            df_3d = df_daily.resample('3D').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
            df_3d['ema9'] = ta.trend.ema_indicator(df_3d['Close'], window=9)
            df_5d = df_daily.resample('5D').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
            df_5d['ema9'] = ta.trend.ema_indicator(df_5d['Close'], window=9)
            
            d_last = df_daily.iloc[-1]
            m3_last = df_3d.iloc[-1]
            m5_last = df_5d.iloc[-1]
            
            # --- System Trend Logic ---
            p1_pass = (current_price > d_last['ema9']) and (d_last['ema9'] > d_last['ema21']) and (d_last['macd_hist'] > 0)
            p2_pass = (current_price > m3_last['ema9']) and (current_price > m5_last['ema9'])
            p4_pass = (current_price > d_last['sma50']) and (d_last['sma50'] > d_last['sma200'])
            
            if p1_pass and p2_pass and p4_pass:
                bias = "🟢 STRONGLY BULLISH"
            elif not p1_pass and not p2_pass and p4_pass:
                bias = "⚠️ HEALTHY PULLBACK"
            elif not p4_pass:
                bias = "🚨 MACRO BEARISH"
            else:
                bias = "🟡 CHOPPY / NEUTRAL"
                
            # --- Golden Pocket Entry Logic ---
            is_in_fib_zone = (current_price <= fib_50) and (current_price >= fib_618)
            is_adx_exhausted = d_last['adx'] < 22
            is_dmi_bullish = d_last['plus_di'] > d_last['minus_di']
            
            if is_in_fib_zone and is_adx_exhausted and is_dmi_bullish:
                entry_signal = "🎯 BUY ZONE"
            elif is_in_fib_zone and not is_dmi_bullish:
                entry_signal = "⏳ WATCHING ZONE (Waiting DMI Cross)"
            elif current_price > fib_50:
                entry_signal = "📈 EXTENDED (Wait for Dip)"
            else:
                entry_signal = "💤 NO SIGNAL"

            # --- Cloud-Protected Metadata Layers ---
            countdown_str = "N/A"
            pe_str = "N/A"
            val_verdict = "Fair Value"
            
            if ticker in ["SOXX", "SOXL"]:
                val_verdict = "ETF Sleeve"
            else:
                # Isolated Protected Calendar Processing
                try:
                    calendar = ticker_obj.calendar
                    if calendar is not None and 'Earnings Date' in calendar and len(calendar['Earnings Date']) > 0:
                        earnings_date = calendar['Earnings Date'].date() if hasattr(calendar['Earnings Date'], 'date') else calendar['Earnings Date']
                        days_remaining = (earnings_date - datetime.now().date()).days
                        if days_remaining < 0: countdown_str = "Completed"
                        elif days_remaining == 0: countdown_str = "🚨 TODAY"
                        elif days_remaining <= 7: countdown_str = f"⚠️ {days_remaining} Days"
                        else: countdown_str = f"{days_remaining} Days"
                    else: countdown_str = "No Date"
                except Exception: countdown_str = "Rate Blocked"

                # Isolated Protected Valuation Processing
                try:
                    info = ticker_obj.info
                    current_pe = info.get('trailingPE', None)
                    historical_medians = {"NVDA": 45.0, "AVGO": 32.0, "AMD": 40.0, "TSM": 22.0, "INTC": 18.0}
                    five_year_median = historical_medians.get(ticker, 25.0)
                    
                    if current_pe and current_pe != "N/A":
                        pe_str = f"{current_pe:.1f}"
                        deviation = ((current_pe - five_year_median) / five_year_median) * 100
                        if deviation > 25.0: val_verdict = f"🔥 OVERVALUED (+{deviation:.0f}%)"
                        elif deviation < -15.0: val_verdict = f"💎 UNDERVALUED ({deviation:.0f}%)"
                        else: val_verdict = "⚖️ FAIR VALUE"
                    else: val_verdict = "No PE Data"
                except Exception: val_verdict = "Rate Blocked"

            summary_rows.append([
                ticker, f"${current_price:.2f}", f"{daily_change:+.2f}%",
                "🟢 PASS" if p1_pass else "🔴 FAIL",
                "🟢 PASS" if p2_pass else "🔴 FAIL",
                "🟢 PASS" if p4_pass else "🔴 FAIL",
                bias, countdown_str, val_verdict, entry_signal
            ])
            print(f"Data mapping array row appended for {ticker}")
            
        except Exception as e:
            print(f"❌ Error skipping compilation loop for {ticker}: {e}")

    # --- Build Master Dataframe Mapping Architecture ---
    report_df = pd.DataFrame(summary_rows, columns=[
        "Ticker", "Price", "Daily Change", "Phase 1", "Phase 2", "Phase 4", "System Bias", "Earnings", "Valuation", "Advanced Entry Signal"
    ])
    
    # Export pandas matrix cleanly into raw standard HTML
    html_table = report_df.to_html(index=False, classes='styled-table')
    
    # --- Mobile-Responsive Touch UI Viewport ---
    html_document = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sector Monitor</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 10px; margin: 0; }}
            .container {{ max-width: 100%; margin: auto; }}
            h1 {{ color: #38bdf8; font-size: 1.25rem; margin-bottom: 2px; font-weight: 700; text-align: center; }}
            .timestamp {{ color: #6b7280; font-size: 0.7rem; margin-bottom: 12px; text-align: center; font-family: monospace; }}
            .table-container {{ overflow-x: auto; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.6); }}
            .styled-table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left; }}
            .styled-table th {{ background-color: #1f2937; color: #38bdf8; padding: 12px 6px; font-weight: 600; text-transform: uppercase; font-size: 0.65rem; border-bottom: 2px solid #374151; }}
            .styled-table td {{ padding: 12px 6px; border-bottom: 1px solid #1f2937; background-color: #111827; white-space: nowrap; font-weight: 500; }}
            .styled-table tbody tr:nth-of-type(even) td {{ background-color: #0f172a; }}
            .status-pass {{ color: #4ade80; font-weight: bold; background: rgba(74, 222, 128, 0.1); padding: 3px 5px; border-radius: 4px; }}
            .status-fail {{ color: #f87171; font-weight: bold; background: rgba(248, 113, 113, 0.1); padding: 3px 5px; border-radius: 4px; }}
            .change-pos {{ color: #4ade80; font-family: monospace; }}
            .change-neg {{ color: #f87171; font-family: monospace; }}
            .ticker-col {{ font-weight: 700 !important; color: #ffffff; }}
            .val-over {{ color: #f87171; font-weight: bold; background: rgba(248, 113, 113, 0.12); padding: 3px 5px; border-radius: 4px; }}
            .val-under {{ color: #38bdf8; font-weight: bold; background: rgba(56, 189, 248, 0.12); padding: 3px 5px; border-radius: 4px; }}
            .signal-buy {{ color: #4ade80; font-weight: 800; background: rgba(74, 222, 128, 0.25); padding: 4px 6px; border-radius: 6px; }}
            .signal-watch {{ color: #fbbf24; font-weight: 700; background: rgba(251, 191, 36, 0.12); padding: 3px 5px; border-radius: 4px; }}
            @keyframes pulse {{ 0% {{ opacity: 0.6; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.6; }} }}
            </style>
        </head>
        <body>
        📡 Institutional Macro TrackerLAST CLOUD REFRESH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
            {html_table}"""

# Precise regex structural replacements for clean UI mapping
html_document = html_document.replace("🟢 PASS", "PASS")
html_document = html_document.replace("🔴 FAIL", "FAIL")
html_document = html_document.replace("+", "+")
html_document = html_document.replace("-", "-")
html_document = html_document.replace("", "")
html_document = html_document.replace("🔥 OVERVALUED", "🔥 OVERVALUED")
html_document = html_document.replace("💎 UNDERVALUED", "💎 UNDERVALUED")
html_document = html_document.replace("🎯 BUY ZONE", "🎯 BUY ZONE")
html_document = html_document.replace("⏳ WATCHING ZONE", "⏳ WATCHING ZONE")
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_document)
print("🎉 System tracking alignment complete! Fresh index.html with all 10 columns deployed.")
if name == "main":
generate_perfect_mobile_dashboard()
    
