import os
from datetime import date, timedelta
from dotenv import load_dotenv
from garminconnect import Garmin
import pandas as pd

load_dotenv()

def connect_garmin():
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    def get_mfa():
        return input("Enter Garmin MFA code: ")
    
    client = Garmin(email, password, prompt_mfa=get_mfa)
    client.login()
    print("Connected to Garmin!")
    return client

def get_activities(client, start_date="2026-03-13"):
    activities = client.get_activities_by_date(start_date, date.today().isoformat())
    df = pd.DataFrame(activities)
    key_cols = ['activityId','activityName','startTimeLocal','duration',
                'distance','calories','averageHR','maxHR',
                'hrTimeInZone_1','hrTimeInZone_2','hrTimeInZone_3',
                'hrTimeInZone_4','hrTimeInZone_5']
    df = df[[c for c in key_cols if c in df.columns]].copy()
    df['duration_mins'] = (df['duration'] / 60).round(1)
    df['date'] = pd.to_datetime(df['startTimeLocal']).dt.date
    return df

def get_sleep(client, start_date="2026-03-13"):
    from datetime import datetime
    import time
    start = date.fromisoformat(start_date)
    end = date.today()
    records = []
    for i in range((end - start).days + 1):
        d = start + timedelta(days=i)
        try:
            s = client.get_sleep_data(d.isoformat())
            daily = s.get('dailySleepDTO', {})
            records.append({
                'date': pd.to_datetime(d),
                'sleep_score': daily.get('sleepScores', {}).get('overall', {}).get('value'),
                'total_sleep_hrs': round(daily.get('sleepTimeSeconds', 0) / 3600, 1),
                'deep_sleep_hrs': round(daily.get('deepSleepSeconds', 0) / 3600, 1),
                'rem_sleep_hrs': round(daily.get('remSleepSeconds', 0) / 3600, 1),
                'resting_hr': s.get('restingHeartRate'),
                'overnight_hrv': s.get('avgOvernightHrv'),
                'hrv_status': s.get('hrvStatus'),
                'body_battery_change': s.get('bodyBatteryChange'),
            })
            time.sleep(0.5)
        except Exception as e:
            pass
    return pd.DataFrame(records)