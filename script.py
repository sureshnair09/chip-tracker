import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime

def generate_watchlist_dashboard():
    # Define the sector watchlist
    watchlist = ["SOXX", "NVDA", "AVGO", "AMD", "TSM", "INTC"]
    summary_rows = []
    
    print(f"Beginning core scan for watchlist: {watchlist}...")
    
    for ticker in watchlist:
        try:
            # Download 2 years of daily data for baseline SMAs
            df_daily = yf.download(ticker, period="2y", interval="1d")
            if df_daily.empty:
                continue
                
            if isinstance(df_daily.columns, pd.MultiIndex):
                df_daily.columns = df_daily.columns.get_level_values(0)
                
            current_price = float(df_daily['Close'].iloc[-1])
            prev_price = float(df_daily['Close'].iloc[-2])
            daily_change = ((current_price - prev_price) / prev_price) * 100
            
            # --- Technical Indicator Calculations ---
            df_daily['ema9'] = ta.trend.ema_indicator(df_daily['Close'], window=9)
            df_daily['ema21'] = ta.trend.ema_indicator(df_daily['Close'], window=21)
            df_daily['sma50'] = ta.trend.sma_indicator(df_daily['Close'], window=50)
            df_daily['sma200'] = ta.trend.sma_indicator(df_daily['Close'], window=200)
            df_daily['macd_hist'] = ta.trend.macd_diff(df_daily['Close'])
            
            # Multi-Day Resampling for higher timeframe checks
            df_3d = df_daily.resample('3D').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
            df_3d['ema9'] = ta.trend.ema_indicator(df_3d['Close'], window=9)
            
            df_5d = df_daily.resample('5D').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
            df_5d['ema9'] = ta.trend.ema_indicator(df_5d['Close'], window=9)
            
            # Extract latest readings
            d_last = df_daily.iloc[-1]
            m3_last = df_3d.iloc[-1]
            m5_last = df_5d.iloc[-1]
            
            # --- Phase Compliance Scoring Matrix ---
            p1_pass = (current_price > d_last['ema9']) and (d_last['ema9'] > d_last['ema21']) and (d_last['macd_hist'] > 0)
            p2_pass = (current_price > m3_last['ema9']) and (current_price > m5_last['ema9'])
            p4_pass = (current_price > d_last['sma50']) and (d_last['sma50'] > d_last['sma200'])
            
            # Establish Global Bias Verdict
            if p1_pass and p2_pass and p4_pass:
                bias = "🟢 STRONGLY BULLISH"
            elif not p1_pass and not p2_pass and p4_pass:
                bias = "⚠️ HEALTHY PULLBACK"
            elif not p4_pass:
                bias = "🚨 MACRO BEARISH"
            else:
                bias = "🟡 CHOPPY / NEUTRAL"
                
            # Append compiled results row
            summary_rows.append([
                ticker,
                f"${current_price:.2f}",
                f"{daily_change:+.2f}%",
                "🟢 PASS" if p1_pass else "🔴 FAIL",
                "🟢 PASS" if p2_pass else "🔴 FAIL",
                "🟢 PASS" if p4_pass else "🔴 FAIL",
                bias
            ])
            print(f"Processed metrics for {ticker} successfully.")
        except Exception as e:
            print(f"Skipping {ticker} due to error: {e}")
            
    # Create Summary Dataframe
    report_df = pd.DataFrame(summary_rows, columns=[
        "Ticker", "Price", "Daily Change", "Phase 1 (Daily)", "Phase 2 (Weekly)", "Phase 4 (Macro)", "System Bias Verdict"
    ])
    
    html_table = report_df.to_html(index=False, classes='styled-table')
    
    # --- Mobile-First Responsive CSS Template ---
    html_document = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sector Monitor</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 15px; margin: 0; }}
            .container {{ max-width: 100%; margin: auto; }}
            h1 {{ color: #38bdf8; font-size: 1.5rem; margin-bottom: 2px; font-weight: 700; text-align: center; }}
            .timestamp {{ color: #6b7280; font-size: 0.8rem; margin-bottom: 20px; text-align: center; font-family: monospace; }}
            .table-container {{ overflow-x: auto; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }}
            .styled-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; }}
            .styled-table th {{ background-color: #1f2937; color: #38bdf8; padding: 12px 10px; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; border-bottom: 2px solid #374151; }}
            .styled-table td {{ padding: 14px 10px; border-bottom: 1px solid #1f2937; background-color: #111827; white-space: nowrap; font-weight: 500; }}
            .styled-table tbody tr:nth-of-type(even) td {{ background-color: #0f172a; }}
            .status-pass {{ color: #4ade80; font-weight: bold; background: rgba(74, 222, 128, 0.15); padding: 4px 6px; border-radius: 6px; font-size: 0.8rem; }}
            .status-fail {{ color: #f87171; font-weight: bold; background: rgba(248, 113, 113, 0.15); padding: 4px 6px; border-radius: 6px; font-size: 0.8rem; }}
            .change-pos {{ color: #4ade80; font-family: monospace; }}
            .change-neg {{ color: #f87171; font-family: monospace; }}
            .ticker-col {{ font-weight: 700 !important; color: #ffffff; font-size: 1rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📡 Semiconductor Watchlist Matrix</h1>
            <div class="timestamp">LAST CLOUD SCAN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
            <div class="table-container">
                {html_table}
            </div>
        </div>
    </body>
    </html>
    """
    
    # Injection of dynamic color formatting tags
    html_document = html_document.replace("🟢 PASS", "<span class='status-pass'>PASS</span>")
    html_document = html_document.replace("🔴 FAIL", "<span class='status-fail'>FAIL</span>")
    html_document = html_document.replace("<td>+", "<td class='change-pos'>+")
    html_document = html_document.replace("<td>-", "<td class='change-neg'>-")
    html_document = html_document.replace("<tr><td>", "<tr><td class='ticker-col'>")
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_document)
    print("🎉 Success! Managed index.html update matrix.")

if __name__ == "__main__":
    generate_watchlist_dashboard()
