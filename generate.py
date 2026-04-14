import os
import requests
import hashlib
import hmac
import time
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

def get_nav_from_supabase():
    print("Fetching NAV data from Supabase...")
    data = supabase_get('nav_history', 'select=date,nav&date=gte.2026-01-01&order=date.asc')
    if not data or isinstance(data, dict):
        print(f"Error: {data}")
        return None
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df['nav'] = pd.to_numeric(df['nav'])
    returns = df['nav'].pct_change().dropna()
    returns.index = returns.index.tz_localize('UTC')
    print(f"Got {len(returns)} days of returns")
    return returns

def generate_factsheet():
    returns = get_nav_from_supabase()
    if returns is None or len(returns) < 5:
        print("Not enough data")
        return None
    output_path = '/opt/render/project/src/factsheet.html'
    qs.reports.html(
        returns,
        benchmark=None,
        output=output_path,
        title='Elevano Capital — Performance Report',
        download_filename='elevano_factsheet.html'
    )
    print(f"Report saved to: {output_path}")
    return output_path

def main():
    print("Starting factsheet generation...")
    generate_factsheet()
    print("Done!")

if __name__ == '__main__':
    main()
