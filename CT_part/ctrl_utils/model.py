import torch
import torch.nn as nn
import torch.nn.functional as F

class LSTM(nn.Module):
    
    def __init__(self, input_dim, hidden_dim, num_layers, output_len, device='cuda') -> None:
        super(LSTM, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_len = output_len
        self.num_layers = num_layers
        self.device = device
        self.lstm = nn.LSTM(self.input_dim, self.hidden_dim, self.num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_len)
        
    def forward(self, x:torch.Tensor):
        batch_size = x.shape[0]
        h0 = torch.zeros((self.num_layers, batch_size, self.hidden_dim), device=self.device).requires_grad_().detach()
        c0 = torch.zeros((self.num_layers, batch_size, self.hidden_dim), device=self.device).requires_grad_().detach()
        # print(c0.shape, h0.shape)
        o, _ = self.lstm(x, (h0, c0))
        o = o[:,-1,:]
        o = self.fc(o)
        return o
    