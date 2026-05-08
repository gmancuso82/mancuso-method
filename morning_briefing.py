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


    # Keep full activity history for 7-day context
    df_activities_agg_all = df_activities.groupby('date').agg(
    activityName=('activityName', lambda x: ' + '.join(x)),
    duration_mins=('duration_mins', 'sum'),
    calories=('calories', 'sum'),
    averageHR=('averageHR', 'mean')
    ).reset_index()

    df_activities_agg_all['date'] = df_activities_agg_all['date'].astype(str).str[:10]

    df_activities_agg_all['date'] = df_activities_agg_all['date'].astype(str).str[:10]
    df_sleep['date'] = df_sleep['date'].astype(str).str[:10]  # ADD THIS
    df_oura['date'] = df_oura['date'].astype(str).str[:10]    # ADD THIS

    df_full_history = pd.merge(df_sleep, df_activities_agg_all, on='date', how='left')
    df_full_history = pd.merge(df_full_history, df_oura, on='date', how='outer')
    df_full_history = df_full_history.sort_values('date').reset_index(drop=True)


    print("Raw activities last 7 days:")
    print(df_activities[df_activities['date'].dt.date >= (date.today() - timedelta(days=7))][['date','activityName','duration_mins']].to_string())

    print("\nAggregated activities last 7 days:")
    print(df_activities_agg_all[df_activities_agg_all['date'] >= (date.today() - timedelta(days=7)).isoformat()][['date','activityName','duration_mins']].to_string())

    df_agg['date'] = df_agg['date'].astype(str).str[:10]
    df_sleep['date'] = df_sleep['date'].astype(str).str[:10]
    df_oura['date'] = df_oura['date'].astype(str).str[:10]

    df_merged = pd.merge(df_sleep, df_agg, on='date', how='left')
    df_full = pd.merge(df_merged, df_oura, on='date', how='outer')
    df_full = df_full.sort_values('date').reset_index(drop=True)

    print("Generating your morning briefing...\n")
    print("Last 7 days activities:")
    print(df_full_history[df_full_history['date'] >= (date.today() - timedelta(days=7)).isoformat()][['date','activityName','duration_mins']].to_string())
    chat_with_coach(df_full_history, nutrition, df_today_activities)

if __name__ == "__main__":
    main()