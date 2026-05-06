from datetime import date, timedelta

import pandas as pd
from garmin_data import connect_garmin, get_activities, get_sleep, get_nutrition
from oura_data import get_oura_readiness
from briefing import chat_with_coach

def main():
    print("Connecting to Garmin...")
    client = connect_garmin()

    print("Fetching activity data...")
    df_activities = get_activities(client)

    print("Fetching sleep data...")
    df_sleep = get_sleep(client)

    print("Fetching Oura data...")
    df_oura = get_oura_readiness()

    print("Fetching nutrition data...")
    nutrition = get_nutrition(client)

    # Fix date types
    df_activities['date'] = pd.to_datetime(df_activities['date'])
    df_sleep['date'] = pd.to_datetime(df_sleep['date'])
    df_oura['date'] = pd.to_datetime(df_oura['date'])

    # Separate yesterday vs today activities
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)

    df_yesterday_activities = df_activities[
        df_activities['date'].dt.date == yesterday
    ]
    df_today_activities = df_activities[
        df_activities['date'].dt.date == date.today()
    ]

    # Aggregate yesterday only for the merged dataset
    df_agg = df_yesterday_activities.groupby('date').agg(
        activityName=('activityName', lambda x: ' + '.join(x)),
        duration_mins=('duration_mins', 'sum'),
        calories=('calories', 'sum'),
        averageHR=('averageHR', 'mean')
    ).reset_index()

    # Build full dataset
    df_merged = pd.merge(df_sleep, df_agg, on='date', how='left')
    df_full = pd.merge(df_merged, df_oura, on='date', how='outer')
    df_full = df_full.sort_values('date').reset_index(drop=True)

    print("Generating your morning briefing...\n")
    chat_with_coach(df_full, nutrition, df_today_activities)

if __name__ == "__main__":
    main()