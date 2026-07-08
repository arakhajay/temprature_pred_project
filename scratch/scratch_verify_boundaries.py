import pandas as pd

episodes_path = r"d:\Python-2025\Antigravity\honeywell\outputs\eda_reports\alarm_episodes.csv"
df = pd.read_csv(episodes_path)
df['Alarm_Start'] = pd.to_datetime(df['Alarm_Start'])
df = df.sort_values('Alarm_Start').reset_index(drop=True)

total = len(df)
target_train = 0.75 * total
target_val = 0.125 * total
target_test = 0.125 * total

print(f"Target counts: Train={target_train:.1f}, Val={target_val:.1f}, Test={target_test:.1f}\n")

# Find index of train end
train_idx = int(target_train)
# Find index of val end
val_idx = train_idx + int(target_val)

train_end_dt = df.iloc[train_idx]['Alarm_Start']
val_end_dt = df.iloc[val_idx]['Alarm_Start']

print(f"Index {train_idx} start time: {train_end_dt}")
print(f"Index {val_idx} start time: {val_end_dt}")

# Let's count alerts if we split at midnight of those days
for train_day in [11, 12, 13, 14]:
    for val_day in [7, 8, 9, 10, 11]:
        t_end = pd.to_datetime(f'2025-06-{train_day} 23:59:00')
        v_end = pd.to_datetime(f'2025-08-{val_day:02d} 23:59:00')
        
        train_cnt = len(df[df['Alarm_Start'] <= t_end])
        val_cnt = len(df[(df['Alarm_Start'] > t_end) & (df['Alarm_Start'] <= v_end)])
        test_cnt = len(df[df['Alarm_Start'] > v_end])
        
        err_train = abs(train_cnt - target_train) / total
        err_val = abs(val_cnt - target_val) / total
        err_test = abs(test_cnt - target_test) / total
        total_err = err_train + err_val + err_test
        
        print(f"Split TrainEnd='2025-06-{train_day}', ValEnd='2025-08-{val_day:02d}': "
              f"Train={train_cnt} ({train_cnt/total:.2%}), Val={val_cnt} ({val_cnt/total:.2%}), Test={test_cnt} ({test_cnt/total:.2%}) "
              f"| Error={total_err:.4f}")
