"""
Approach v5 - Model Training Module
Handles PyTorch model training loops, loss optimization, learning rate schedules, early stopping, and checkpoints.
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

def train_one_epoch(model, dataloader, criterion, optimizer, device, is_seq2seq=False, teacher_forcing_ratio=0.5):
    """
    Runs a single epoch of training.
    """
    model.train()
    total_loss = 0.0
    
    for batch in dataloader:
        optimizer.zero_grad()
        
        if is_seq2seq:
            src, target, last_target = batch
            src, target = src.to(device), target.to(device)
            # Forward pass through Seq2Seq
            outputs = model(src, target_seq=target, teacher_forcing_ratio=teacher_forcing_ratio)
            loss = criterion(outputs, target)
        else:
            src, target = batch
            src, target = src.to(device), target.to(device).unsqueeze(1)
            outputs = model(src)
            loss = criterion(outputs, target)
            
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * src.size(0)
        
    return total_loss / len(dataloader.dataset)

def evaluate_loss(model, dataloader, criterion, device, is_seq2seq=False):
    """
    Evaluates loss on a validation/test loader.
    """
    model.eval()
    total_loss = 0.0
    
    with torch.no_grad():
        for batch in dataloader:
            if is_seq2seq:
                src, target, last_target = batch
                src, target = src.to(device), target.to(device)
                outputs = model(src, target_seq=None, teacher_forcing_ratio=0.0) # no teacher forcing on validation
                loss = criterion(outputs, target)
            else:
                src, target = batch
                src, target = src.to(device), target.to(device).unsqueeze(1)
                outputs = model(src)
                loss = criterion(outputs, target)
                
            total_loss += loss.item() * src.size(0)
            
    return total_loss / len(dataloader.dataset)

def train_model(model, train_loader, val_loader, epochs=10, lr=0.001, patience=5, is_seq2seq=False, model_path="models/model.pth"):
    """
    Orchestrates the full model training loop, tracking early stopping on validation loss.
    
    Args:
        model (nn.Module): The model to train.
        train_loader (DataLoader): PyTorch training loader.
        val_loader (DataLoader): PyTorch validation loader.
        epochs (int): Max number of epochs.
        lr (float): Initial learning rate.
        patience (int): Early stopping patience epochs.
        is_seq2seq (bool): Flag indicating if model is Seq2Seq.
        model_path (str): Filepath to save the best model weights.
        
    Returns:
        tuple: (trained_model, history_dict)
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)
    
    best_val_loss = float('inf')
    patience_counter = 0
    history = {"train_loss": [], "val_loss": []}
    
    logger_str = "Seq2Seq" if is_seq2seq else "LSTM"
    print(f"Starting training for {logger_str} model on device: {device}")
    
    for epoch in range(1, epochs + 1):
        # Decay teacher forcing ratio for Seq2Seq
        teacher_forcing_ratio = max(0.0, 0.5 - 0.05 * epoch) if is_seq2seq else 0.0
        
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device, is_seq2seq, teacher_forcing_ratio)
        val_loss = evaluate_loss(model, val_loader, criterion, device, is_seq2seq)
        
        scheduler.step(val_loss)
        
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        
        print(f"  Epoch {epoch}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        
        # Check early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            torch.save(model.state_dict(), model_path)
            print(f"    --> Saved best model checkpoint to {model_path}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"    --> Early stopping triggered after {epoch} epochs.")
                break
                
    # Load the best model weights back
    model.load_state_dict(torch.load(model_path))
    return model, history
