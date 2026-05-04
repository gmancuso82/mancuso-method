# 🏋️ AI Recovery Coach

A personal AI coaching system built for a Hyrox athlete recovering from two hip surgeries, targeting Hyrox Open on June 7, 2026.

## What it does

Pulls real-time data from Garmin and Oura Ring every morning and uses Claude AI to generate a personalized recovery and training briefing — then lets you chat with your coach about your data.

## Features

- **Morning briefing** — daily AI-generated coaching report based on your actual biometrics
- **Conversational coaching** — chat with Claude about your recovery, training, and nutrition
- **Streamlit dashboard** — visual recovery trends, training load charts, and chat interface
- **Multi-source data** — Garmin (activity, sleep, HRV) + Oura Ring (readiness, temperature)

## Tech stack

- Python
- Garmin Connect API
- Oura Ring API  
- Anthropic Claude API (claude-sonnet-4-6)
- Pandas
- Streamlit
- Plotly

## How to run

```bash
# Terminal briefing with chat
python morning_briefing.py

# Visual dashboard
streamlit run dashboard.py
```

## Background

I built this as a portfolio project while getting my MSDS at University of Virginia. Former professional athlete, now fitness enthusiast, tennis obssessed and Hyrox pro athlete I am rehabbing after two hip surgeries (Dec 2025 and March 2026). I am signed up for Hyrox NYC in June and I needed a way to train intelligently for my return to Hyrox competition without overspending on coaching. So I built my own.

## Data sources

- Garmin Connect — activity, sleep, HRV, body battery
- Oura Ring — readiness score, temperature deviation, recovery index 