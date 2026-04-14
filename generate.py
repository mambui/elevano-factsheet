import os
import requests
import hashlib
import hmac
import time
import pandas as pd
import numpy as np
import quantstats as qs
from datetime import datetime

# Config
BYBIT_API_KEY = os.environ.get('BYBIT_API_KEY')
BYBIT_API_SECRET = os.environ.get('BYBIT_API_SECRET')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
BASE_URL = 'https://api.bybit.com'

def supabase_get(table, query=''):
    """Direct REST call to Supabase — no client library needed"""
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    print(f"Calling: {url}")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    return response.json()

def supabase_upload(bucket, filename, content, content_type='text/html'):
    """Upload file to Supabase Storage"""
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{filename}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': content_type,
        'x-upsert': 'true'
    }
    response = requests.post(url, headers=headers, data=content)
    return response.status_code

def get_nav_from_supabase():
    print("Fetching NAV data from Supabase...")
    data = supabase_get('nav_history', 'select=date,nav&date=gte.2026-01-01&order=date.asc')
    if not data or isinstance(data, dict):
        print(f"Error fetching data: {data}")
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
    with open(file_path, 'rb') as f:
        content = f.read()
    status = supabase_upload('factsheet', 'latest.html', content)
    print(f"Upload status: {status}")
    url = f"{SUPABASE_URL}/storage/v1/object/public/factsheet/latest.html"
    print(f"Public URL: {url}")
    return url

def main():
    print("Starting factsheet generation...")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"SUPABASE_KEY starts with: {SUPABASE_KEY[:10] if SUPABASE_KEY else 'None'}")
    file_path = generate_factsheet()
    if file_path:
        url = upload_to_supabase(file_path)
        print(f"Done! Factsheet at: {url}")

if __name__ == '__main__':
    main()
