from flask import Flask, jsonify
from flask_cors import CORS
from datetime import date, timedelta
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import anthropic

load_dotenv(dotenv_path=Path('/Users/ginamancuso/health-llm/.env'), override=True)

from garmin_data import connect_garmin, get_activities, get_sleep, get_nutrition
from oura_data import get_oura_readiness

app = Flask(__name__)
CORS(app)

# Connect to Garmin at startup (handles MFA once)
print("Connecting to Garmin...")
client = connect_garmin()
print("Ready!")

client = None

@app.route('/connect', methods=['POST'])
def connect():
    global client
    client = connect_garmin()
    return jsonify({"status": "connected"})

@app.route('/data', methods=['GET'])
def get_data():
    global client
    if not client:
        client = connect_garmin()
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Get all data
    two_weeks_ago = (date.today() - timedelta(days=14)).isoformat()
    df_sleep = get_sleep(client, start_date=two_weeks_ago)
    df_activities = get_activities(client, start_date=two_weeks_ago)
    df_oura = get_oura_readiness(start_date=two_weeks_ago)
    nutrition = get_nutrition(client)
    
    # Get yesterday's sleep
    df_yesterday = df_sleep[df_sleep['date'].astype(str).str[:10] == yesterday.isoformat()]
    yesterday_data = df_yesterday.iloc[0] if not df_yesterday.empty else df_sleep.iloc[-1]
    
    # Get today's Oura readiness
    df_oura_today = df_oura[df_oura['date'].astype(str).str[:10] == today.isoformat()]
    todays_readiness = int(df_oura_today['oura_readiness_score'].iloc[0]) if not df_oura_today.empty else 77
    
    # Get last 7 days activities
    df_activities['date'] = df_activities['date'].astype(str).str[:10]
    last_7_activities = df_activities[df_activities['date'] >= (today - timedelta(days=7)).isoformat()]
    
    # Load yesterday's conversation
    conv_file = Path(f"conversations/{yesterday.isoformat()}.json")
    prev_conversation = None
    if conv_file.exists():
        with open(conv_file) as f:
            data = json.load(f)
            msgs = [m for m in data.get('conversation', []) if m['role'] in ['user', 'assistant']][4:]
            prev_conversation = '\n'.join([f"{'You' if m['role']=='user' else 'Coach'}: {m['content'][:200]}" for m in msgs[:10]])
    
    return jsonify({
        "date": today.strftime("%A, %B %d"),
        "days_to_hyrox": (date(2026, 6, 7) - today).days,
        "readiness": {
            "score": todays_readiness,
            "band": "good" if todays_readiness >= 80 else "fair" if todays_readiness >= 60 else "low",
            "delta_vs_7day": -4,
            "drivers": [
                {"label": "Sleep quality", "impact": int(yesterday_data.get('sleep_score', 70)) - 75, "note": f"Score: {yesterday_data.get('sleep_score', 'N/A')}"},
                {"label": "HRV", "impact": 2 if yesterday_data.get('hrv_status') == 'BALANCED' else -3, "note": f"{yesterday_data.get('overnight_hrv', 'N/A')}ms — {yesterday_data.get('hrv_status', 'N/A')}"},
                {"label": "Body Battery", "impact": 3 if yesterday_data.get('body_battery_change', 0) > 40 else -2, "note": f"+{yesterday_data.get('body_battery_change', 'N/A')} overnight"},
            ]
        },
        "sleep": {
            "total_hours": round(float(yesterday_data.get('total_sleep_hrs', 7.0)), 1),
            "target_hours": 7.5,
            "bedtime": "10:30 PM",
            "wake": "5:45 AM",
            "efficiency": 88,
            "stages": [
                {"label": "Awake", "hours": 0.3, "pct": 4},
                {"label": "REM", "hours": round(float(yesterday_data.get('rem_sleep_hrs', 1.2)), 1), "pct": 16},
                {"label": "Light", "hours": round(float(yesterday_data.get('total_sleep_hrs', 7.0)) * 0.6, 1), "pct": 60},
                {"label": "Deep", "hours": round(float(yesterday_data.get('deep_sleep_hrs', 1.4)), 1), "pct": 20},
            ],
            "resting_hr": int(yesterday_data.get('resting_hr', 40)),
            "hrv_ms": int(yesterday_data.get('overnight_hrv', 45)),
            "hrv_baseline": 55,
        },
        "nutrition": {
            "target_kcal": nutrition['calorie_goal'] if nutrition else 1800,
            "base_kcal": nutrition['calorie_goal'] if nutrition else 1800,
            "calories": nutrition['calories'] if nutrition else 0,
            "protein_g": int(nutrition['protein']) if nutrition else 0,
            "carbs_g": int(nutrition['carbs']) if nutrition else 0,
            "fat_g": int(nutrition['fat']) if nutrition else 0,
        },
        "recent_activities": last_7_activities[['date', 'activityName', 'duration_mins', 'calories', 'averageHR']].fillna('').to_dict(orient='records'),
        "prev_conversation": prev_conversation or "No previous conversation logged.",
        "context_signals": [
            f"Right hip surgery: Dec 9, 2025 (~5 months ago)",
            f"Left hip surgery: March 13, 2026 (~7 weeks ago, most sensitive)",
            "Currently in PT 2x per week",
            f"School ends May 18",
            f"Hyrox Open: June 7, 2026 ({(date(2026,6,7)-today).days} days away)",
        ]
    })

@app.route('/chat', methods=['POST'])
def chat():
    from flask import request
    body = request.json
    ai = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = ai.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=body['messages']
    )
    return jsonify({"reply": message.content[0].text})

if __name__ == '__main__':
    app.run(port=5001, debug=False)