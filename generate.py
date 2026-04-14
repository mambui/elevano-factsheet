import os
import requests
import hashlib
import hmac
import time
import json
import pandas as pd
import numpy as np
import quantstats as qs
from datetime import datetime, timedelta
from supabase import create_client

# Config from environment variables
BYBIT_API_KEY = os.environ.get('BYBIT_API_KEY')
BYBIT_API_SECRET = os.environ.get('BYBIT_API_SECRET')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
BASE_URL = 'https://api.bybit.com'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def bybit_request(endpoint, params={}):
    timestamp = str(int(time.time() * 1000))
    recv_window = '5000'
    query_string = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
    sign_payload = timestamp + BYBIT_API_KEY + recv_window + query_string
    signature = hmac.new(
        BYBIT_API_SECRET.encode('utf-8'),
        sign_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    headers = {
        'X-BAPI-API-KEY': BYBIT_API_KEY,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-SIGN': signature,
        'X-BAPI-RECV-WINDOW': recv_window,
    }
    response = requests.get(f'{BASE_URL}{endpoint}', params=params, headers=headers)
    return response.json()

def get_nav_from_supabase():
    """Get NAV history from Supabase"""
    result = supabase.table('nav_history').select('date,nav').gte('date', '2026-01-01').order('date').execute()
    data = result.data
    if not data:
        return None
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df['nav'] = pd.to_numeric(df['nav'])
    # Calculate daily returns
    returns = df['nav'].pct_change().dropna()
    returns.index = returns.index.tz_localize('UTC')
    return returns

def generate_factsheet():
    print("Fetching NAV data from Supabase...")
    returns = get_nav_from_supabase()
    
    if returns is None or len(returns) < 5:
        print("Not enough data")
        return None

    print(f"Got {len(returns)} days of returns")
    
    # Generate Quantstats report
    output_path = '/tmp/factsheet.html'
    
    qs.reports.html(
        returns,
        benchmark=None,
        output=output_path,
        title='Elevano Capital — Performance Report',
        download_filename='elevano_factsheet.html'
    )
    
    print(f"Report generated: {output_path}")
    return output_path

def upload_to_supabase(file_path):
    """Upload HTML report to Supabase Storage"""
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Upload to Supabase Storage bucket 'factsheet'
    result = supabase.storage.from_('factsheet').upload(
        'latest.html',
        content,
        {'content-type': 'text/html', 'upsert': 'true'}
    )
    
    # Get public URL
    url = supabase.storage.from_('factsheet').get_public_url('latest.html')
    print(f"Uploaded to: {url}")
    return url

def main():
    print("Starting factsheet generation...")
    file_path = generate_factsheet()
    if file_path:
        url = upload_to_supabase(file_path)
        # Save URL to Supabase stats table
        supabase.table('stats').upsert({
            'key': 'factsheet_url',
            'value': 0,
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        print(f"Done! Factsheet available at: {url}")
        return url
    return None

if __name__ == '__main__':
    main()
