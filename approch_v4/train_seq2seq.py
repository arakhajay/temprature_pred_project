import os
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib

# Import utils
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import preprocess_and_feature_engineering, get_feature_lists, prepare_split_datasets, TimeSeriesDataset

# Check device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Paths
MODEL_DIR = r"d:\Python-2025\Antigravity\honeywell\models\seq2seq_v4"
OUTPUT_DIR = r"d:\Python-2025\Antigravity\honeywell\outputs\seq2seq_v4"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Encoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, dropout=0.2):
        super(Encoder, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        _, (hidden, cell) = self.lstm(x)
        return hidden, cell

class Decoder(nn.Module):
    def __init__(self, output_dim=1, hidden_dim=64, num_layers=2, dropout=0.2):
        super(Decoder, self).__init__()
        self.lstm = nn.LSTM(output_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        self.fc = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x, hidden, cell):
        # x shape: (batch, 1, output_dim)
        out, (hidden, cell) = self.lstm(x, (hidden, cell))
        # out shape: (batch, 1, hidden_dim)
        out_proj = self.fc(out) # (batch, 1, output_dim)
        return out_proj, hidden, cell

class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder, pred_len=60):
        super(Seq2Seq, self).__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.pred_len = pred_len
        
    def forward(self, x, target_idx, y=None, teacher_forcing_ratio=0.5):
        # x shape: (batch, seq_len, input_dim)
        # target_idx: index of target_col in feature list
        # y shape: (batch, pred_len)
        batch_size = x.size(0)
        
        # Encode
        hidden, cell = self.encoder(x)
        
        # Decoder input: (batch, 1, 1) initialized with the current target value
        dec_input = x[:, -1, target_idx].unsqueeze(-1).unsqueeze(-1)
        
        outputs = []
        for t in range(self.pred_len):
            dec_out, hidden, cell = self.decoder(dec_input, hidden, cell)
            # dec_out shape: (batch, 1, 1)
            outputs.append(dec_out.squeeze(1)) # shape: (batch, 1)
            
            # Determine next input
            if y is not None and torch.rand(1).item() < teacher_forcing_ratio:
                dec_input = y[:, t].unsqueeze(-1).unsqueeze(-1) # Teacher forcing
            else:
                dec_input = dec_out # Autoregressive (use previous prediction)
                
        outputs = torch.cat(outputs, dim=1) # shape: (batch, pred_len)
        return outputs

class Seq2SeqDataset(torch.utils.data.Dataset):
    """
    Seq-to-Seq dataset returning history sequence and future sequence.
    """
    def __init__(self, features_np, targets_np, valid_indices, seq_len, pred_len):
        self.features = features_np
        self.targets = targets_np
        self.valid_indices = valid_indices
        self.seq_len = seq_len
        self.pred_len = pred_len

    def __len__(self):
        return len(self.valid_indices)

    def __getitem__(self, idx):
        end_idx = self.valid_indices[idx]
        start_idx = end_idx - self.seq_len + 1
        
        seq_x = self.features[start_idx:end_idx + 1]
        seq_y = self.targets[end_idx + 1 : end_idx + 1 + self.pred_len]
        
        return torch.tensor(seq_x, dtype=torch.float32), torch.tensor(seq_y, dtype=torch.float32)

def prepare_split_datasets_seq2seq(df, feature_cols, target_col, seq_len=10, pred_len=60, sample_step=1):
    train_end = pd.to_datetime('2025-06-12 23:59:00')
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    
    train_mask = df.index <= train_end
    val_mask = (df.index > train_end) & (df.index <= val_end)
    test_mask = df.index > val_end
    
    # Fit StandardScaler
    print("Fitting Scalers on Train Split...")
    scaler_x = StandardScaler()
    scaler_x.fit(df.loc[train_mask, feature_cols].fillna(0.0))
    
    scaler_y = StandardScaler()
    train_y_nonnan = df.loc[train_mask, target_col].dropna().values.reshape(-1, 1)
    if len(train_y_nonnan) > 0:
        scaler_y.fit(train_y_nonnan)
    else:
        scaler_y.fit(df[[target_col]].fillna(0.0))
        
    features_scaled = scaler_x.transform(df[feature_cols].fillna(0.0))
    targets_scaled = scaler_y.transform(df[[target_col]].fillna(0.0)).flatten()
    
    # Find valid windows
    print("Finding valid windows...")
    valid_features = df[feature_cols].notna().all(axis=1)
    valid_seq_x = valid_features.rolling(window=seq_len).min() == 1
    
    valid_target = df[target_col].notna()
    # The targets from t+1 to t+pred_len must be non-NaN
    valid_seq_y = valid_target.shift(-pred_len).rolling(window=pred_len).min() == 1
    
    valid_mask = valid_seq_x & valid_seq_y
    
    indices = np.arange(len(df))
    train_indices = indices[train_mask & valid_mask]
    val_indices = indices[val_mask & valid_mask]
    test_indices = indices[test_mask & valid_mask]
    
    if sample_step > 1:
        train_indices = train_indices[::sample_step]
        val_indices = val_indices[::sample_step]
        
    print(f"Dataset summary: Train size: {len(train_indices)}, Val size: {len(val_indices)}, Test size: {len(test_indices)}")
    
    train_dataset = Seq2SeqDataset(features_scaled, targets_scaled, train_indices, seq_len, pred_len)
    val_dataset = Seq2SeqDataset(features_scaled, targets_scaled, val_indices, seq_len, pred_len)
    test_dataset = Seq2SeqDataset(features_scaled, targets_scaled, test_indices, seq_len, pred_len)
    
    return train_dataset, val_dataset, test_dataset, scaler_x, scaler_y, test_indices

def train_seq2seq(model, train_loader, val_loader, target_idx, epochs=10, lr=1e-3, early_stopping_patience=2):
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_weights = None
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        start_time = time.time()
        
        # Calculate teacher forcing ratio decay
        teacher_forcing_ratio = max(0.0, 0.5 - epoch * 0.1)
        
        for x_batch, y_batch in train_loader:
            x_batch, y_batch = x_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            
            # Predict shape: (batch, pred_len)
            preds = model(x_batch, target_idx, y_batch, teacher_forcing_ratio)
            loss = criterion(preds, y_batch)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * x_batch.size(0)
            
        train_loss /= len(train_loader.dataset)
        
        # Validation (No teacher forcing during validation)
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x_batch, y_batch in val_loader:
                x_batch, y_batch = x_batch.to(device), y_batch.to(device)
                preds = model(x_batch, target_idx, y=None, teacher_forcing_ratio=0.0)
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

def evaluate_seq2seq(model, test_loader, target_idx, scaler_y, pred_len=60):
    model.eval()
    all_preds = []
    all_actuals = []
    
    with torch.no_grad():
        for x_batch, y_batch in test_loader:
            x_batch = x_batch.to(device)
            preds = model(x_batch, target_idx, y=None, teacher_forcing_ratio=0.0).cpu().numpy()
            all_preds.append(preds)
            all_actuals.append(y_batch.numpy())
            
    all_preds = np.vstack(all_preds) # shape: (N, pred_len)
    all_actuals = np.vstack(all_actuals) # shape: (N, pred_len)
    
    # Inverse transform sequence columns one by one or by reshaping
    N = all_preds.shape[0]
    preds_inv = scaler_y.inverse_transform(all_preds.reshape(-1, 1)).reshape(N, pred_len)
    actuals_inv = scaler_y.inverse_transform(all_actuals.reshape(-1, 1)).reshape(N, pred_len)
    
    return preds_inv, actuals_inv

def train_and_eval_seq2seq_all(df, feature_mode="selected", seq_len=10, pred_len=60, train_sample_step=5, epochs=8):
    print(f"\n=======================================================")
    print(f" Starting Seq-to-Seq Training | Feature Mode: {feature_mode.upper()} ")
    print(f"=======================================================")
    
    all_features, selected_features_by_horizon = get_feature_lists(df)
    
    # For Seq-to-Seq, if selected mode, we use the union of selected features
    if feature_mode == "selected":
        feature_cols = list(selected_features_by_horizon['union'])
    else:
        feature_cols = list(all_features)
        
    target_col = '03TIC_1023.PV'
    if target_col not in feature_cols:
        feature_cols.append(target_col)
        
    print(f"Number of input features: {len(feature_cols)}")
    target_idx = feature_cols.index(target_col)
    print(f"Target variable index: {target_idx}")
    
    # Prepare datasets
    train_ds, val_ds, test_ds, scaler_x, scaler_y, test_indices = prepare_split_datasets_seq2seq(
        df=df,
        feature_cols=feature_cols,
        target_col=target_col,
        seq_len=seq_len,
        pred_len=pred_len,
        sample_step=train_sample_step
    )
    
    # Dataloaders
    train_loader = DataLoader(train_ds, batch_size=512, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=1024, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=1024, shuffle=False)
    
    # Initialize components
    encoder = Encoder(input_dim=len(feature_cols), hidden_dim=64, num_layers=2, dropout=0.2)
    decoder = Decoder(output_dim=1, hidden_dim=64, num_layers=2, dropout=0.2)
    model = Seq2Seq(encoder, decoder, pred_len=pred_len).to(device)
    
    # Train
    print("Training Seq-to-Seq model...")
    model = train_seq2seq(model, train_loader, val_loader, target_idx, epochs=epochs, lr=1e-3)
    
    # Save model and scalers
    model_path = os.path.join(MODEL_DIR, f"seq2seq_model_{feature_mode}.pth")
    torch.save(model.state_dict(), model_path)
    
    scalers_path = os.path.join(MODEL_DIR, f"scalers_{feature_mode}.pkl")
    joblib.dump({
        'scaler_x': scaler_x,
        'scaler_y': scaler_y,
        'feature_cols': feature_cols,
        'target_idx': target_idx
    }, scalers_path)
    print(f"Saved model to {model_path} and scalers to {scalers_path}")
    
    # Evaluate
    print("Evaluating Seq-to-Seq model on test split...")
    test_preds, test_actuals = evaluate_seq2seq(model, test_loader, target_idx, scaler_y, pred_len=pred_len)
    
    # Extract prediction horizons: 5m, 15m, 30m, 60m
    # Python is 0-indexed, so 5 minutes is index 4, 15 minutes is index 14, etc.
    horizons = [5, 15, 30, 60]
    results = {}
    
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    test_df = df.loc[val_end + pd.Timedelta(minutes=1):].copy()
    test_preds_df = pd.DataFrame(index=test_df.index)
    test_preds_df['actual'] = test_df['03TIC_1023.PV']
    
    for h in horizons:
        idx_h = h - 1
        h_preds = test_preds[:, idx_h]
        h_actuals = test_actuals[:, idx_h]
        
        # Align test predictions back to original test timestamps
        test_timestamps = df.index[test_indices]
        test_preds_df[f'pred_{h}m'] = pd.Series(h_preds, index=test_timestamps)
        
        # Calculate metrics
        mae = mean_absolute_error(h_actuals, h_preds)
        rmse = np.sqrt(mean_squared_error(h_actuals, h_preds))
        
        threshold = 21.0
        actual_alarm = (h_actuals >= threshold).astype(int)
        pred_alarm = (h_preds >= threshold).astype(int)
        
        precision, recall, f1, _ = precision_recall_fscore_support(actual_alarm, pred_alarm, average='binary', zero_division=0)
        tn, fp, fn, tp = confusion_matrix(actual_alarm, pred_alarm).ravel()
        far = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        print(f"Horizon {h}m | MAE: {mae:.4f} | RMSE: {rmse:.4f} | F1: {f1*100:.2f}% | Prec: {precision*100:.2f}% | Rec: {recall*100:.2f}% | FAR: {far*100:.4f}%")
        
        results[h] = {
            'Horizon': f"{h} Min",
            'Version': f'Seq2Seq ({feature_mode.capitalize()} Features)',
            'F1-Score': f"{f1 * 100:.2f}%",
            'Precision': f"{precision * 100:.2f}%",
            'Recall': f"{recall * 100:.2f}%",
            'False Alarm Rate': f"{far * 100:.4f}%",
            'MAE (degC)': f"{mae:.4f}",
            'RMSE (degC)': f"{rmse:.4f}"
        }
        
    # Save test predictions Parquet
    preds_path = os.path.join(OUTPUT_DIR, f"predictions_seq2seq_{feature_mode}.parquet")
    test_preds_df.to_parquet(preds_path)
    print(f"\nSaved Seq-to-Seq ({feature_mode}) predictions to {preds_path}")
    
    # Save performance summary
    summary_df = pd.DataFrame(list(results.values()))
    summary_path = os.path.join(OUTPUT_DIR, f"summary_seq2seq_{feature_mode}.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"Saved summary to {summary_path}")
    
    return summary_df

if __name__ == "__main__":
    df = preprocess_and_feature_engineering()
    
    # Train selected features model if not already exists
    summary_selected_path = os.path.join(OUTPUT_DIR, "summary_seq2seq_selected.csv")
    if not os.path.exists(summary_selected_path):
        summary_selected = train_and_eval_seq2seq_all(df, feature_mode="selected", train_sample_step=5, epochs=8)
    else:
        print("\nSkipping Seq-to-Seq (Selected Features) because summary already exists.")
        summary_selected = pd.read_csv(summary_selected_path)
        
    # Train all features model if not already exists
    summary_all_path = os.path.join(OUTPUT_DIR, "summary_seq2seq_all.csv")
    if not os.path.exists(summary_all_path):
        summary_all = train_and_eval_seq2seq_all(df, feature_mode="all", train_sample_step=10, epochs=8)
    else:
        print("\nSkipping Seq-to-Seq (All Features) because summary already exists.")
        summary_all = pd.read_csv(summary_all_path)
    
    print("\nSeq-to-Seq Training Finished!")
    print("Summary Selected Features (Union):")
    print(summary_selected)
    print("Summary All Features:")
    print(summary_all)
