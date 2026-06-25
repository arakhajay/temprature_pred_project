import pandas as pd

episodes_path = r"d:\Python-2025\Antigravity\honeywell\outputs\eda_reports\alarm_episodes.csv"
df = pd.read_csv(episodes_path)
df['Alarm_Start'] = pd.to_datetime(df['Alarm_Start'])

# Sort chronologically by Alarm_Start (they might be sorted otherwise, let's make sure they are sorted)
df = df.sort_values('Alarm_Start').reset_index(drop=True)

total_alerts = len(df)
print(f"Total alerts: {total_alerts}")

# Index for 75% (train end)
train_count = int(total_alerts * 0.75)
val_count = int(total_alerts * 0.125)
test_count = total_alerts - train_count - val_count

print(f"Target split counts: Train={train_count}, Val={val_count}, Test={test_count}")

train_end_alert = df.iloc[train_count - 1]
val_end_alert = df.iloc[train_count + val_count - 1]

print("\nSplit boundaries based on alert counts:")
print(f"Train End Alert Start Time: {train_end_alert['Alarm_Start']}")
print(f"Val End Alert Start Time: {val_end_alert['Alarm_Start']}")

# Let's inspect the dates around these indices to find clean date-time boundaries
print("\nTrain boundary context:")
print(df.iloc[train_count - 3 : train_count + 3][['Alarm_Start', 'Duration_Minutes']])

print("\nVal boundary context:")
print(df.iloc[train_count + val_count - 3 : train_count + val_count + 3][['Alarm_Start', 'Duration_Minutes']])
