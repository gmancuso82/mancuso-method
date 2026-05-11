import os
import anthropic
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv
from IPython.display import Markdown, display


import json
from pathlib import Path

def load_previous_conversation():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    json_file = Path(f"conversations/{yesterday}.json")
    
    try:
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
                conversation = data.get('conversation', [])
                # Extract just the user/coach messages, skip the initial data prompt
                messages = [m for m in conversation if m['role'] in ['user', 'assistant']][4:]
                summary = []
                for m in messages[:10]:  # last 10 exchanges
                    role = "You" if m['role'] == 'user' else "Coach"
                    summary.append(f"{role}: {m['content'][:200]}")
                return '\n'.join(summary)
    except Exception as e:
        return None
    return None

def save_conversation(conversation_history, nutrition=None, df_today_activities=None):
    today = date.today().isoformat()
    Path("conversations").mkdir(exist_ok=True)
    
    save_data = {
        "date": today,
        "conversation": conversation_history,
        "nutrition": nutrition
    }
    
    filename = f"conversations/{today}.json"
    with open(filename, 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    
    print(f"\nConversation saved to {filename}")

load_dotenv()

client_ai = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_briefing(df_full, nutrition=None, df_today_activities=None):
    prev_conversation = load_previous_conversation()
    print(f"DEBUG - Previous conversation loaded: {prev_conversation[:200] if prev_conversation else 'NONE'}")
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Get today's Oura readiness specifically
    df_oura_today = df_full[df_full['date'] == today.isoformat()]
    df_oura_yesterday = df_full[df_full['date'] == yesterday.isoformat()]

    # Sleep and training context comes from yesterday
    yesterday_data = df_oura_yesterday.dropna(subset=['sleep_score'])
    yesterday_data = yesterday_data.iloc[0] if not yesterday_data.empty else df_full.dropna(subset=['sleep_score']).iloc[-1]

    #  Readiness comes from today
    todays_readiness = df_oura_today['oura_readiness_score'].iloc[0] if not df_oura_today.empty and df_oura_today['oura_readiness_score'].notna().any() else yesterday_data.get('oura_readiness_score')


    # Last 7 days
    last_7 = df_full[df_full['date'] >= (today - timedelta(days=7)).isoformat()]

    briefing_prompt = f"""
You are Gina Mancuso's personal AI recovery and performance coach. Generate her daily morning briefing.

ATHLETE PROFILE:
- Right hip surgery: December 9, 2025 (~5 months ago)
- Left hip surgery: March 13, 2026 (~7 weeks ago, most recent and sensitive surgical site)
- Currently in PT 2x per week focused on hip strength and single-leg stability
- High school teacher (school ends May 18 — training volume increases after)
- Long term goals: return to tennis July 2026, Hyrox Pro races September 2026
- Current target event: Hyrox Open June 7, 2026 ({(date(2026,6,7) - today).days} days away)

PERSONAL PROFILE:
- 43-year-old female, competitive Hyrox athlete (normally Pro level) and tennis player
- The right quad and knee are weaker due to acl injury history
- Currently training: Indoor Cycling, Elliptical, Strength, Cardio (no running yet)
- Single mom, high school teacher, UVA grad student in data science

LAST NIGHT'S RECOVERY:
- Oura Readiness Score: {todays_readiness} (today's score)
- Sleep Score (Garmin): {yesterday_data.get('sleep_score')}
- Overnight HRV: {yesterday_data.get('overnight_hrv')} ms
- HRV Status: {yesterday_data.get('hrv_status')}
- Body Battery Change: {yesterday_data.get('body_battery_change')}
- Temperature Deviation: {yesterday_data.get('temperature_deviation')}C

YESTERDAY'S COACHING CONVERSATION:
{prev_conversation if prev_conversation else 'No previous conversation logged'}

LAST 7 DAYS TRAINING:
{last_7[['date','activityName','duration_mins','calories','averageHR','oura_readiness_score']].to_string()}

YESTERDAY'S NUTRITION:
- Calories: {nutrition['calories'] if nutrition else 'Not logged'} / {nutrition['calorie_goal'] if nutrition else 'N/A'} goal ({nutrition['calorie_pct'] if nutrition else 'N/A'}% of goal)
- Protein: {nutrition['protein'] if nutrition else 'Not logged'}g / {nutrition['protein_goal'] if nutrition else 'N/A'}g goal
- Carbs: {nutrition['carbs'] if nutrition else 'Not logged'}g
- Fat: {nutrition['fat'] if nutrition else 'Not logged'}g

TODAY SO FAR:
- Activities logged: {', '.join(df_today_activities['activityName'].tolist()) if len(df_today_activities) else 'None yet'}

Generate a morning briefing with:
1. Recovery Status (1 - 2 sentences, direct)
2. What the data says (2-3 key insights)
3. Today's Training Recommendation (specific, with duration and intensity)
4. Any nutrition advice for today based on yesterday's intake and today's training
5. One thing to watch today
6. Coach's note (1 -2 sentences, honest and motivational)

Be concise and direct. She is an experienced athlete - no fluff.

YESTERDAY'S COACHING CONVERSATION:
{prev_conversation if prev_conversation else 'No previous conversation logged.'}

"""

    message = client_ai.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": briefing_prompt}]
    )

    return message.content[0].text



def chat_with_coach(df_full, nutrition=None, df_today_activities=None):
    today = date.today()
    prev_conversation = load_previous_conversation()
    briefing_text = generate_briefing(df_full, nutrition, df_today_activities)
    

    print(f"\n🌅 MORNING BRIEFING — {today.strftime('%A, %B %d')}")
    print("=" * 50)
    print(briefing_text)
    print("\n" + "-" * 50)

    conversation_history = [
        {"role": "user", "content": f"Here is my data and morning briefing:\n{briefing_text}"},
        {"role": "assistant", "content": "I've reviewed your data and generated your briefing. What questions do you have?"}
    ]

    while True:
        user_input = input("\nChat with your coach (press Enter to exit): ").strip()
        if not user_input:
            save_conversation(conversation_history, nutrition)
            print("Have a great training session!")
            break

        conversation_history.append({"role": "user", "content": user_input})

        response = client_ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=f"""You are Gina's personal AI coach. She is a 43-year-old Hyrox athlete recovering from two hip surgeries targeting Hyrox Open on June 7 2026. Be direct, specific, and reference her actual data.

            YESTERDAY'S CONVERSATION CONTEXT:
            {prev_conversation if prev_conversation else 'No previous conversation logged.'}""",
            messages=conversation_history
        )

        reply = response.content[0].text
        conversation_history.append({"role": "assistant", "content": reply})
        print(f"\nCoach: {reply}")