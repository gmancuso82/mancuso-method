import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
import anthropic
import os
from dotenv import load_dotenv
from garmin_data import connect_garmin, get_activities, get_sleep
from oura_data import get_oura_readiness

load_dotenv()

st.set_page_config(page_title="Gina's AI Coach", page_icon="🏋️", layout="wide")

st.markdown("""
<style>
    .stChatMessage {
        background-color: #f8f9fa !important;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    .stChatMessage p {
        color: #1a1a1a !important;
    }
    [data-testid="stChatMessageContent"] {
        color: #1a1a1a !important;
        background-color: #f8f9fa !important;
    }
</style>
""", unsafe_allow_html=True) 

# ── Data loading ──────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    import time
    client = connect_garmin()
    df_activities = get_activities(client)
    df_sleep = get_sleep(client)
    df_oura = get_oura_readiness()
    df_activities['date'] = pd.to_datetime(df_activities['date'])
    df_sleep['date'] = pd.to_datetime(df_sleep['date'])
    df_oura['date'] = pd.to_datetime(df_oura['date'])
    df_merged = pd.merge(df_sleep, df_activities, on='date', how='left')
    df_full = pd.merge(df_merged, df_oura, on='date', how='outer')
    df_full = df_full.sort_values('date').reset_index(drop=True)
    return df_full

# ── Header ────────────────────────────────────────────────
st.title("🏋️ Gina's AI Recovery Coach")
days_out = (date(2026, 6, 7) - date.today()).days
st.caption(f"Hyrox Open — June 7, 2026 · {days_out} days away · Post-op day {(date.today() - date(2026, 3, 13)).days}")

# ── Load data ─────────────────────────────────────────────
with st.spinner("Connecting to Garmin & Oura..."):
    try:
        df = load_data()
        st.success("Data loaded!")
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# ── Top metrics ───────────────────────────────────────────
latest = df.dropna(subset=['oura_readiness_score']).iloc[-1]
yesterday = df.dropna(subset=['sleep_score']).iloc[-1]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Oura Readiness", f"{int(latest.get('oura_readiness_score', 0))}", help="Today's readiness score")
col2.metric("Sleep Score", f"{int(yesterday.get('sleep_score', 0))}", help="Last night's sleep score")
col3.metric("HRV", f"{int(yesterday.get('overnight_hrv', 0))}ms", help="Overnight HRV")
col4.metric("Body Battery", f"+{int(yesterday.get('body_battery_change', 0))}", help="Overnight body battery change")
col5.metric("HRV Status", f"{yesterday.get('hrv_status', 'N/A')}", help="Garmin HRV status")

st.divider()

# ── Charts ────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Recovery trends")
    fig = go.Figure()
    df_plot = df.dropna(subset=['overnight_hrv'])
    fig.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['overnight_hrv'],
        name='HRV (ms)', line=dict(color='#1D9E75', width=2)))
    fig.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['sleep_score'],
        name='Sleep score', line=dict(color='#378ADD', width=2), yaxis='y2'))
    fig.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['oura_readiness_score'],
        name='Oura readiness', line=dict(color='#BA7517', width=2), yaxis='y2'))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=300, margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation='h', y=-0.2),
        yaxis=dict(title='HRV (ms)', color='#1D9E75'),
        yaxis2=dict(title='Score', overlaying='y', side='right', color='#378ADD'),
        xaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Training load")
    df_train = df.dropna(subset=['activityName'])
    fig2 = px.bar(df_train, x='date', y='calories', color='activityName',
        color_discrete_sequence=['#1D9E75','#378ADD','#BA7517','#D4537E','#8B5CF6'])
    fig2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=300, margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation='h', y=-0.2, title=''),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, title='Calories')
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Morning briefing ──────────────────────────────────────
st.subheader("Today's briefing")

if 'briefing' not in st.session_state:
    st.session_state.briefing = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

if st.button("Generate morning briefing", type="primary"):
    client_ai = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    today = date.today()
    yesterday_data = df.iloc[-1]
    last_7 = df[df['date'].dt.date >= (today - timedelta(days=7))]

    prompt = f"""
You are Gina's personal AI recovery and performance coach. Generate her daily morning briefing.

ATHLETE PROFILE:
- 43-year-old female, competitive Hyrox athlete (normally Pro level)
- Two hip surgeries: Dec 9 2025 and March 13 2026
- Target event: Hyrox Open, June 7 2026 ({days_out} days away)
- Currently training: Indoor Cycling, Elliptical, Strength, Cardio (no running yet)
- Single mom, UVA grad student in data science
- Had flu April 10-11

LAST NIGHT'S RECOVERY:
- Oura Readiness: {yesterday_data.get('oura_readiness_score')}
- Sleep Score: {yesterday_data.get('sleep_score')}
- Overnight HRV: {yesterday_data.get('overnight_hrv')}ms
- HRV Status: {yesterday_data.get('hrv_status')}
- Body Battery: +{yesterday_data.get('body_battery_change')}

LAST 7 DAYS:
{last_7[['date','activityName','duration_mins','calories','averageHR','oura_readiness_score']].to_string()}

Generate briefing with:
1. Recovery Status (1 sentence)
2. What the data says (2-3 insights)
3. Today's Training Recommendation (specific)
4. One thing to watch
5. Coach's note

Be direct. No fluff.
"""
    with st.spinner("Generating briefing..."):
        message = client_ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        st.session_state.briefing = message.content[0].text
        st.session_state.messages = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": st.session_state.briefing}
        ]

if st.session_state.briefing:
    st.markdown(st.session_state.briefing)
    st.divider()

    # ── Chat ──────────────────────────────────────────────
    st.subheader("Chat with your coach")

    for msg in st.session_state.messages[2:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt_input := st.chat_input("Ask your coach anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt_input})
        with st.chat_message("user"):
            st.markdown(prompt_input)

        client_ai = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client_ai.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=500,
                    system="You are Gina's personal AI coach. 43yo Hyrox athlete, two hip surgeries, targeting Hyrox Open June 7 2026. Be direct and specific.",
                    messages=st.session_state.messages
                )
                reply = response.content[0].text
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})