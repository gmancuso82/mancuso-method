import os
import anthropic
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv
from IPython.display import Markdown, display

load_dotenv()

client_ai = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_briefing(df_full):
    today = date.today()
    yesterday = today - timedelta(days=1)

    yesterday_rows = df_full[df_full['date'].dt.date == yesterday]
    yesterday_data = yesterday_rows.iloc[0] if not yesterday_rows.empty else df_full.iloc[-1]
    last_7 = df_full[df_full['date'].dt.date >= (today - timedelta(days=7))]

    briefing_prompt = f"""
You are Gina's personal AI recovery and performance coach. Generate her daily morning briefing.

ATHLETE PROFILE:
- 43-year-old female, competitive Hyrox athlete (normally Pro level)
- Two hip surgeries: Dec 9 2025 and March 13 2026
- Target event: Hyrox Open, June 7 2026 ({(date(2026,6,7) - today).days} days away)
- Currently training: Indoor Cycling, Elliptical, Strength, Cardio (no running yet)
- Single mom, UVA grad student in data science
- Had flu April 10-11 (explains metrics crash those days)

LAST NIGHT'S RECOVERY:
- Oura Readiness Score: {yesterday_data.get('oura_readiness_score')}
- Sleep Score (Garmin): {yesterday_data.get('sleep_score')}
- Overnight HRV: {yesterday_data.get('overnight_hrv')} ms
- HRV Status: {yesterday_data.get('hrv_status')}
- Body Battery Change: {yesterday_data.get('body_battery_change')}
- Temperature Deviation: {yesterday_data.get('temperature_deviation')}C

LAST 7 DAYS TRAINING:
{last_7[['date','activityName','duration_mins','calories','averageHR','oura_readiness_score']].to_string()}

Generate a morning briefing with:
1. Recovery Status (1 sentence, direct)
2. What the data says (2-3 key insights)
3. Today's Training Recommendation (specific, with duration and intensity)
4. One thing to watch today
5. Coach's note (honest and motivational)

Be concise and direct. She is an experienced athlete - no fluff.
"""

    message = client_ai.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": briefing_prompt}]
    )

    return message.content[0].text

def chat_with_coach(df_full):
    today = date.today()
    briefing_text = generate_briefing(df_full)

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
            print("Have a great training session!")
            break

        conversation_history.append({"role": "user", "content": user_input})

        response = client_ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system="""You are Gina's personal AI coach. She is a 43-year-old Hyrox athlete 
            recovering from two hip surgeries targeting Hyrox Open on June 7 2026. 
            Be direct, specific, and reference her actual data.""",
            messages=conversation_history
        )

        reply = response.content[0].text
        conversation_history.append({"role": "assistant", "content": reply})
        print(f"\nCoach: {reply}")