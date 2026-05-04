import pandas as pd
from garmin_data import connect_garmin, get_activities, get_sleep
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

    # Merge all data
    # Merge all data
    df_activities['date'] = pd.to_datetime(df_activities['date'])
    df_sleep['date'] = pd.to_datetime(df_sleep['date'])
    df_oura['date'] = pd.to_datetime(df_oura['date'])

    df_merged = pd.merge(df_sleep, df_activities, on='date', how='left')
    df_full = pd.merge(df_merged, df_oura, on='date', how='outer')
    df_full = df_full.sort_values('date').reset_index(drop=True)

    print("Generating your morning briefing...\n")
    chat_with_coach(df_full)

if __name__ == "__main__":
    main()