import matplotlib
matplotlib.use('Agg')
import os
import requests
import pandas as pd
import numpy as np
import quantstats as qs
from datetime import datetime

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

def supabase_get(table, query=''):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    response = requests.get(url, headers=headers)
    return response.json()

def get_data_from_supabase():
    print("Fetching data from Supabase...")
    data = supabase_get('nav_history', 'select=date,nav,btc_price&date=gte.2025-12-31&order=date.asc')
    if not data or isinstance(data, dict):
        print(f"Error: {data}")
        return None, None
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
    df['btc_price'] = pd.to_numeric(df['btc_price'], errors='coerce')
    
    # Set Dec 31 nav to 999.86 (same as Jan 1 base) so pct_change gives Jan 1 return
    if pd.Timestamp('2025-12-31') in df.index:
        df.loc[pd.Timestamp('2025-12-31'), 'nav'] = 999.86
    
    nav_df = df['nav'][df['nav'] > 0]
    btc_df = df['btc_price'].dropna()
    
    nav_returns = nav_df.pct_change().dropna()
    btc_returns = btc_df.pct_change().dropna()
    
    # Localize BEFORE filtering and aligning
    nav_returns.index = pd.DatetimeIndex(nav_returns.index).tz_localize('UTC')
    btc_returns.index = pd.DatetimeIndex(btc_returns.index).tz_localize('UTC')
    
    # Keep only 2026 dates
    cutoff = pd.Timestamp('2026-01-01', tz='UTC')
    nav_returns = nav_returns[nav_returns.index >= cutoff]
    btc_returns = btc_returns[btc_returns.index >= cutoff]
    
    # Align dates
    common_dates = nav_returns.index.intersection(btc_returns.index)
    nav_returns = nav_returns[common_dates]
    btc_returns = btc_returns[common_dates]
    
    print(f"Got {len(nav_returns)} days — from {nav_returns.index[0].date()} to {nav_returns.index[-1].date()}")
    return nav_returns, btc_returns

def generate_factsheet():
    nav_returns, btc_returns = get_data_from_supabase()
    if nav_returns is None or len(nav_returns) < 5:
        print("Not enough data")
        return None
    
    output_path = '/opt/render/project/src/factsheet.html'
    # Strip timezone for quantstats compatibility
    nav_returns_qs = nav_returns.copy()
    nav_returns_qs.index = nav_returns_qs.index.tz_localize(None)
    btc_returns_qs = btc_returns.copy()
    btc_returns_qs.index = btc_returns_qs.index.tz_localize(None)

    qs.reports.html(
        nav_returns_qs,
        benchmark=btc_returns_qs,
        output=output_path,
        title='Elevano Capital — Performance Report · Jan 1, 2026',
        download_filename='elevano_factsheet.html',
        benchmark_title='Bitcoin (BTC)'
    )
    
    # Inject disclaimer note into HTML
    disclaimer = """
    <div style="background:#f9f5f0;border-left:3px solid #c07a8a;padding:12px 16px;margin:20px 0;font-size:12px;color:#555;font-family:Arial,sans-serif;">
        <strong>Note on methodology:</strong> QuantStats was designed for traditional finance and annualises metrics using 252 business days. 
        Elevano Capital operates in crypto markets (24/7, 365 days/year). As a result, figures such as Sharpe Ratio and annualised returns 
        may differ slightly from those displayed on <a href="https://elevanocapital.com" style="color:#c07a8a;">elevanocapital.com</a>, 
        which uses 365-day annualisation to reflect the continuous nature of crypto trading.
    </div>
    """
    
    with open(output_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    html = html.replace('<body onload="save()">', f'<body onload="save()">{disclaimer}')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Report saved to: {output_path}")
    return output_path

def main():
    print("Starting factsheet generation...")
    generate_factsheet()
    print("Done!")

if __name__ == '__main__':
    main()
