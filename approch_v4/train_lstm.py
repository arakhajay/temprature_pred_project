import os
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, confusion_matrix
import joblib

# Import utils
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import preprocess_and_feature_engineering, get_feature_lists, prepare_split_datasets, TimeSeriesDataset

# Check device (we know from check it is cpu)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Paths
MODEL_DIR = r"d:\Python-2025\Antigravity\honeywell\models\lstm_v4"
OUTPUT_DIR = r"d:\Python-2025\Antigravity\honeywell\outputs\lstm_v4"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class LSTMRegressor(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, dropout=0.2):
        super(LSTMRegressor, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        self.fc = nn.Linear(hidden_dim, 1)
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        out, _ = self.lstm(x)
        # out shape: (batch, seq_len, hidden_dim)
        out_last = out[:, -1, :] # Take last step
        out_proj = self.fc(out_last)
        return out_proj.squeeze(-1) # Output shape: (batch,)

def train_model(model, train_loader, val_loader, epochs=10, lr=1e-3, early_stopping_patience=2):
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_weights = None
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        start_time = time.time()
        
        for x_batch, y_batch in train_loader:
            x_batch, y_batch = x_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            preds = model(x_batch)
            loss = criterion(preds, y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * x_batch.size(0)
            
        train_loss /= len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x_batch, y_batch in val_loader:
                x_batch, y_batch = x_batch.to(device), y_batch.to(device)
                preds = model(x_batch)
                loss = criterion(preds, y_batch)
                val_loss += loss.item() * x_batch.size(0)
        val_loss /= len(val_loader.dataset)
        
        elapsed = time.time() - start_time
        print(f"  Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f} | Time: {elapsed:.1f}s")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= early_stopping_patience:
                print(f"  Early stopping triggered. Best Val Loss: {best_val_loss:.6f}")
                break
                
    if best_weights is not None:
        model.load_state_dict(best_weights)
    return model

def evaluate_lstm(model, test_loader, scaler_y):
    model.eval()
    all_preds = []
    all_actuals = []
    
    with torch.no_grad():
        for x_batch, y_batch in test_loader:
            x_batch = x_batch.to(device)
            preds = model(x_batch).cpu().numpy()
            all_preds.extend(preds)
            all_actuals.extend(y_batch.numpy())
            
    all_preds = np.array(all_preds).reshape(-1, 1)
    all_actuals = np.array(all_actuals).reshape(-1, 1)
    
    # Inverse transform
    preds_inv = scaler_y.inverse_transform(all_preds).flatten()
    actuals_inv = scaler_y.inverse_transform(all_actuals).flatten()
    
    return preds_inv, actuals_inv

def train_and_eval_lstm_all_horizons(df, feature_mode="selected", seq_len=10, train_sample_step=5, epochs=8):
    """
    feature_mode: "all" or "selected"
    """
    print(f"\n=======================================================")
    print(f" Starting LSTM Training | Feature Mode: {feature_mode.upper()} ")
    print(f"=======================================================")
    
    all_features, selected_features_by_horizon = get_feature_lists(df)
    horizons = [5, 15, 30, 60]
    
    results = {}
    
    # We will accumulate test predictions for final comparison export
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    test_df = df.loc[val_end + pd.Timedelta(minutes=1):].copy()
    test_preds_df = pd.DataFrame(index=test_df.index)
    test_preds_df['actual'] = test_df['03TIC_1023.PV']
    
    for h in horizons:
        print(f"\n--- Horizon: {h} Minutes ---")
        target_name = f'target_{h}m'
        
        # Select feature list based on configuration
        if feature_mode == "selected":
            feature_cols_h = selected_features_by_horizon[f'{h}m']
        else:
            feature_cols_h = all_features
            
        print(f"Number of input features: {len(feature_cols_h)}")
        
        # Prepare datasets
        train_ds, val_ds, test_ds, scaler_x, scaler_y, test_indices = prepare_split_datasets(
            df=df,
            feature_cols=feature_cols_h,
            target_col=target_name,
            seq_len=seq_len,
            sample_step=train_sample_step
        )
        
        # Dataloaders
        train_loader = DataLoader(train_ds, batch_size=512, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=1024, shuffle=False)
        test_loader = DataLoader(test_ds, batch_size=1024, shuffle=False)
        
        # Initialize model
        model = LSTMRegressor(input_dim=len(feature_cols_h), hidden_dim=64, num_layers=2, dropout=0.2).to(device)
        
        # Train
        print("Training model...")
        model = train_model(model, train_loader, val_loader, epochs=epochs, lr=1e-3)
        
        # Save PyTorch model and scalers
        model_path = os.path.join(MODEL_DIR, f"lstm_model_{h}m_{feature_mode}.pth")
        torch.save(model.state_dict(), model_path)
        
        scalers_path = os.path.join(MODEL_DIR, f"scalers_{h}m_{feature_mode}.pkl")
        joblib.dump({'scaler_x': scaler_x, 'scaler_y': scaler_y, 'feature_cols': feature_cols_h}, scalers_path)
        print(f"Saved model to {model_path} and scalers to {scalers_path}")
        
        # Evaluate
        print("Evaluating on test split...")
        test_preds, test_actuals = evaluate_lstm(model, test_loader, scaler_y)
        
        # Align test predictions back to the original test indices
        # test_indices maps to row offsets in the full df
        test_timestamps = df.index[test_indices]
        pred_series = pd.Series(test_preds, index=test_timestamps)
        test_preds_df[f'pred_{h}m'] = pred_series
        
        # regression metrics
        mae = mean_absolute_error(test_actuals, test_preds)
        rmse = np.sqrt(mean_squared_error(test_actuals, test_preds))
        
        # classification metrics
        threshold = 21.0
        actual_alarm = (test_actuals >= threshold).astype(int)
        pred_alarm = (test_preds >= threshold).astype(int)
        
        precision, recall, f1, _ = precision_recall_fscore_support(actual_alarm, pred_alarm, average='binary', zero_division=0)
        tn, fp, fn, tp = confusion_matrix(actual_alarm, pred_alarm).ravel()
        far = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        print(f"Metrics | MAE: {mae:.4f} | RMSE: {rmse:.4f} | F1: {f1*100:.2f}% | Prec: {precision*100:.2f}% | Rec: {recall*100:.2f}% | FAR: {far*100:.4f}%")
        
        results[h] = {
            'Horizon': f"{h} Min",
            'Version': f'LSTM ({feature_mode.capitalize()} Features)',
            'F1-Score': f"{f1 * 100:.2f}%",
            'Precision': f"{precision * 100:.2f}%",
            'Recall': f"{recall * 100:.2f}%",
            'False Alarm Rate': f"{far * 100:.4f}%",
            'MAE (degC)': f"{mae:.4f}",
            'RMSE (degC)': f"{rmse:.4f}"
        }
        
    # Save test predictions Parquet
    preds_path = os.path.join(OUTPUT_DIR, f"predictions_lstm_{feature_mode}.parquet")
    test_preds_df.to_parquet(preds_path)
    print(f"\nSaved LSTM ({feature_mode}) predictions to {preds_path}")
    
    # Save performance summary
    summary_df = pd.DataFrame(list(results.values()))
    summary_path = os.path.join(OUTPUT_DIR, f"summary_lstm_{feature_mode}.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"Saved summary to {summary_path}")
    
    return summary_df

if __name__ == "__main__":
    # Prepare data (computes features once)
    df = preprocess_and_feature_engineering()
    
    # Train both models
    summary_selected = train_and_eval_lstm_all_horizons(df, feature_mode="selected", train_sample_step=5, epochs=8)
    summary_all = train_and_eval_lstm_all_horizons(df, feature_mode="all", train_sample_step=10, epochs=8)
    
    print("\nLSTM Training Finished!")
    print("Summary Selected Features:")
    print(summary_selected)
    print("Summary All Features:")
    print(summary_all)
