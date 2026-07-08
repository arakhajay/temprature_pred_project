"""
Approach v5 - PyTorch Deep Learning Models
Implements:
1. Single-horizon LSTM model
2. Encoder-Decoder Seq2Seq model (multi-step output)
"""

import torch
import torch.nn as nn

class LSTMRegressor(nn.Module):
    """
    Standard single-horizon LSTM model for temperature alarm forecasting.
    Takes input of shape (batch, window_size, num_features) and maps to a scalar prediction.
    """
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, output_dim=1):
        super(LSTMRegressor, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # LSTM layer
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)
        
        # Fully connected regression head
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        # x shape: (batch_size, window_size, input_dim)
        # Initialize hidden and cell states
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        
        # LSTM forward pass
        out, _ = self.lstm(x, (h0, c0))
        
        # Extract prediction from last sequence step
        out = self.fc(out[:, -1, :])
        return out


class Encoder(nn.Module):
    """
    Seq2Seq Encoder. Processes historical feature sequence.
    """
    def __init__(self, input_dim, hidden_dim=64, num_layers=2):
        super(Encoder, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)

    def forward(self, x):
        # x shape: (batch_size, window_size, input_dim)
        _, (hidden, cell) = self.lstm(x)
        return hidden, cell


class Decoder(nn.Module):
    """
    Seq2Seq Decoder. Generates future sequence step-by-step.
    """
    def __init__(self, output_dim=1, hidden_dim=64, num_layers=2):
        super(Decoder, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Decoder input is 1-dimensional (previous target temperature)
        self.lstm = nn.LSTM(1, hidden_dim, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x, hidden, cell):
        # x shape: (batch_size, 1, 1) - single step target input
        out, (hidden, cell) = self.lstm(x, (hidden, cell))
        pred = self.fc(out[:, -1, :])
        return pred, hidden, cell


class Seq2Seq(nn.Module):
    """
    Seq2Seq Wrapper uniting Encoder and Decoder for multi-step autoregressive forecasting.
    """
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, forecast_len=60):
        super(Seq2Seq, self).__init__()
        self.encoder = Encoder(input_dim, hidden_dim, num_layers)
        self.decoder = Decoder(1, hidden_dim, num_layers)
        self.forecast_len = forecast_len

    def forward(self, src, target_seq=None, teacher_forcing_ratio=0.5):
        """
        Args:
            src (tensor): Historical inputs (batch_size, window_size, input_dim).
            target_seq (tensor): True future targets for teacher forcing (batch_size, forecast_len).
            teacher_forcing_ratio (float): Probability of feeding true target vs. model prediction to next step.
        """
        batch_size = src.size(0)
        outputs = torch.zeros(batch_size, self.forecast_len).to(src.device)
        
        # 1. Encode source sequence to obtain context vectors (hidden, cell)
        hidden, cell = self.encoder(src)
        
        # 2. Initialize decoder input with last known target value (e.g. at index target_idx)
        # For simplicity, we initialize using the batch's last target value from src
        # Let's say it is passed in or extracted:
        # decoder_input = src[:, -1, target_idx].unsqueeze(1).unsqueeze(2) (batch_size, 1, 1)
        # Placeholder initialization:
        decoder_input = torch.zeros(batch_size, 1, 1).to(src.device)
        
        # 3. Autoregressive loop
        for t in range(self.forecast_len):
            pred, hidden, cell = self.decoder(decoder_input, hidden, cell)
            outputs[:, t] = pred.squeeze(1)
            
            # Decide if teacher forcing is used
            use_teacher_forcing = target_seq is not None and torch.rand(1).item() < teacher_forcing_ratio
            if use_teacher_forcing:
                decoder_input = target_seq[:, t].unsqueeze(1).unsqueeze(2)
            else:
                decoder_input = pred.unsqueeze(2) # feed model's own prediction
                
        return outputs
