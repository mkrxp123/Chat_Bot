import re
import torch
import pandas as pd

class QADataset(torch.utils.data.Dataset):
    def __init__(self, path):
        data = pd.read_csv(path)
        data = data[data['question'].notna()]
        self.patterns = {re.compile(r'[^!?，？。！ \u4e00-\u9fa5]') : '', re.compile(r'(.+?)\1+'): r'\1'}
        self.Q = data['question'].apply(self.regularExpression)
        self.A = data['answer'].apply(self.regularExpression)
        self.len = len(data['answer'])
        del data
    
    def regularExpression(self, x):
        for pattern, replace in self.patterns.items():
            x = pattern.sub(replace, x)
        return x
    
    def __getitem__(self, idx):
        item = {'Q': self.Q.iloc[idx], 'A': self.A.iloc[idx]}
        return item

    def __len__(self):
        return self.len