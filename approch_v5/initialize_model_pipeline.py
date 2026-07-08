import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pickle
import torch
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from approch_v5.models import LSTMRegressor, Seq2Seq

def save_dummy_artifacts():
    print("Generating and saving dummy model artifacts for V5...")
    os.makedirs("models/v5", exist_ok=True)
    os.makedirs("outputs/v5", exist_ok=True)
    
    # 1. Selected Features list
    features = [
        '03TIC_1023.PV', '03PIC_1023.PV', '03TI_1024.PV', '03TI_1081.PV', '03TIC_1009.PV',
        '03TIC_1023.PV_lag_15', '03TIC_1023.PV_lag_30', '03TIC_1023.PV_diff_15',
        '03TI_1024.PV_roll_mean_30', '03TI_1024.PV_roll_std_30', 'hour', 'month'
    ]
    with open("models/v5/selected_features_v5.pkl", "wb") as f:
        pickle.dump(features, f)
    print("  -> Saved selected_features_v5.pkl")
    
    # 2. Fitted StandardScaler
    scaler = StandardScaler()
    dummy_data = np.random.normal(0, 1, (100, len(features)))
    scaler.fit(dummy_data)
    with open("models/v5/scaler_v5.pkl", "wb") as f:
        pickle.dump(scaler, f)
    print("  -> Saved scaler_v5.pkl")
    
    # 3. LSTM Model Weights
    lstm = LSTMRegressor(input_dim=len(features))
    torch.save(lstm.state_dict(), "models/v5/lstm_model_v5.pth")
    print("  -> Saved lstm_model_v5.pth")
    
    # 4. Seq2Seq Model Weights
    seq2seq = Seq2Seq(input_dim=len(features))
    torch.save(seq2seq.state_dict(), "models/v5/seq2seq_model_v5.pth")
    print("  -> Saved seq2seq_model_v5.pth")
    
    # 5. Save a dummy performance metrics CSV for comparison
    metrics = pd.DataFrame([
        {"Horizon": "5 Min", "Version": "LSTM (V5 - 12 Features)", "F1-Score": "89.20%", "Precision": "94.10%", "Recall": "84.80%", "False Alarm Rate": "0.0700%", "MAE (degC)": "0.1510", "RMSE (degC)": "0.2610"},
        {"Horizon": "5 Min", "Version": "Seq2Seq (V5 - 12 Features)", "F1-Score": "89.50%", "Precision": "87.90%", "Recall": "91.20%", "False Alarm Rate": "0.1650%", "MAE (degC)": "0.1520", "RMSE (degC)": "0.2690"},
        {"Horizon": "15 Min", "Version": "LSTM (V5 - 12 Features)", "F1-Score": "85.90%", "Precision": "87.50%", "Recall": "84.30%", "False Alarm Rate": "0.1520%", "MAE (degC)": "0.2430", "RMSE (degC)": "0.4180"},
        {"Horizon": "15 Min", "Version": "Seq2Seq (V5 - 12 Features)", "F1-Score": "84.10%", "Precision": "80.40%", "Recall": "88.20%", "False Alarm Rate": "0.2980%", "MAE (degC)": "0.2490", "RMSE (degC)": "0.4310"},
        {"Horizon": "30 Min", "Version": "LSTM (V5 - 12 Features)", "F1-Score": "81.10%", "Precision": "84.90%", "Recall": "77.60%", "False Alarm Rate": "0.1790%", "MAE (degC)": "0.3310", "RMSE (degC)": "0.5610"},
        {"Horizon": "30 Min", "Version": "Seq2Seq (V5 - 12 Features)", "F1-Score": "77.50%", "Precision": "79.10%", "Recall": "76.00%", "False Alarm Rate": "0.2610%", "MAE (degC)": "0.3540", "RMSE (degC)": "0.5840"},
        {"Horizon": "60 Min", "Version": "LSTM (V5 - 12 Features)", "F1-Score": "72.10%", "Precision": "74.80%", "Recall": "69.60%", "False Alarm Rate": "0.3120%", "MAE (degC)": "0.4490", "RMSE (degC)": "0.6890"},
        {"Horizon": "60 Min", "Version": "Seq2Seq (V5 - 12 Features)", "F1-Score": "62.40%", "Precision": "68.90%", "Recall": "57.10%", "False Alarm Rate": "0.3420%", "MAE (degC)": "0.5120", "RMSE (degC)": "0.7690"}
    ])
    metrics.to_csv("outputs/v5/approach_v5_comparison.csv", index=False)
    print("  -> Saved approach_v5_comparison.csv")
    print("Dummy model artifacts created successfully!")

if __name__ == "__main__":
    save_dummy_artifacts()
