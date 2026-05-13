# Mancuso Method — AI Recovery Coach

A personal AI coaching system built for a competitive Hyrox athlete recovering from two hip surgeries, targeting Hyrox Open on June 7, 2026.

Built as a portfolio project for the M.S. in Data Science program at the University of Virginia.

---

## What It Does

Pulls live biometric data from Garmin and Oura Ring every morning and uses Claude AI to generate a personalized recovery and training briefing — then lets you chat with your coach about your data. The coach remembers yesterday's conversation, knows your surgical history, and references your actual nutrition and training from the prior day.

---

## Features

- **Morning briefing** — personalized AI coaching report based on live biometrics
- **Conversational coaching** — chat with your coach about recovery, training, and nutrition
- **Memory** — yesterday's conversation feeds into today's briefing context
- **Browser UI** — clean dark-mode interface with readiness ring, sleep, and nutrition cards
- **Multi-source data pipeline** — Garmin (activity, sleep, HRV, nutrition) + Oura Ring (readiness, temperature)
- **Flask API** — serves live data to the browser interface

---

## Tech Stack

- Python 3.12
- Garmin Connect API + garminconnect SDK
- Oura Ring REST API v2
- Anthropic Claude API (claude-sonnet)
- pandas, Flask, flask-cors, requests
- VS Code + Windsurf

---

## How to Run

**1. Set up environment**
```bash
conda activate health-llm
```

**2. Add credentials to `.env`** GARMIN_EMAIL=your_email
GARMIN_PASSWORD=your_password
ANTHROPIC_API_KEY=your_key
OURA_API_KEY=your_token**3. Run morning briefing (terminal)**
```bash
python morning_briefing.py
```

**4. Run Flask API + open browser UI**
```bash
# Terminal 1 — start API
python api.py

# Terminal 2 — open UI
open lumen.html
```

---

## Data Sources

- **Garmin Connect** — activities, sleep, HRV, body battery, nutrition logs
- **Oura Ring** — readiness score, temperature deviation, sleep stages

---

## Project Background

I am a competitive Hyrox athlete (normally Pro level), high school statistics and economics teacher, single mom, and first-year student in UVA's online M.S. in Data Science program. In December 2025 I had my first hip surgery. In March 2026, my second.

With expensive coaching off the table and a Hyrox Open 25 days away, I built my own AI coach using the biometric data I was already generating every day. The hardest problems were not the AI — they were the data engineering: merging APIs with different date formats, handling Garmin rate limits, and keeping conversation memory persistent across sessions.

Read the full story: [UVA Data Science Blog](https://datascience.virginia.edu)

---

## GitHub

[github.com/gmancuso82/mancuso-method](https://github.com/gmancuso82/mancuso-method)
