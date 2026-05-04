import os
import requests
import pandas as pd
from datetime import date
from dotenv import load_dotenv

load_dotenv()

def get_oura_readiness(start_date="2026-03-13"):
    token = os.getenv("OURA_API_KEY")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        "https://api.ouraring.com/v2/usercollection/daily_readiness",
        headers=headers,
        params={
            "start_date": start_date,
            "end_date": date.today().isoformat()
        }
    )
    
    records = []
    for record in response.json().get('data', []):
        records.append({
            'date': pd.to_datetime(record['day']),
            'oura_readiness_score': record['score'],
            'hrv_balance': record['contributors'].get('hrv_balance'),
            'recovery_index': record['contributors'].get('recovery_index'),
            'temperature_deviation': record.get('temperature_deviation'),
        })
    
    return pd.DataFrame(records)