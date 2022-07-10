import torch
from torch.utils.data import DataLoader, random_split
import pytorch_lightning as pl

from transformers import BertTokenizerFast, EncoderDecoderModel, BertForQuestionAnswering, BertTokenizer, BartForConditionalGeneration

from dataset import QADataset

default = {'dataset': './PTT_QA.csv', 'train_size': 0.2, 'model_name': 'ckiplab/bert-base-chinese', 'freeze_bert': False,
           'num_workers': 4, 'batch_size': 16, 'lr': 1e-4, 'dropout': 0.2, 'seq_len': 64}

class chatBot(pl.LightningModule):
    def __init__(self, config=default):
        super(chatBot, self).__init__()
        self.config = config
        self.seq_len = self.config['seq_len']
        model = self.config['model_name']
        tokenizer = BertTokenizerFast.from_pretrained(model)
        tokenization = lambda s: tokenizer(
                        list(s),
                        add_special_tokens = True, # Add '[CLS]' and '[SEP]'
                        max_length = self.seq_len,
                        truncation = True,
                        padding = 'max_length',
                        return_attention_mask = True,
                        return_tensors = 'pt').to(self.config['device'])
        self.map_f = lambda Q, A: (tokenization(Q), tokenization(A))
        self.transformer = BertForQuestionAnswering.from_pretrained(model).to(self.config['device'])
        # self.attention = nn.MultiheadAttention(embed_dim=len(self.tokenizer), num_heads=1, dropout=self.config['dropout'], batch_first=True)
        if self.config['freeze_bert']:
            for param in self.transformer.bert.parameters():
                param.requires_grad = False
    
    def forward(self, x):
        Q, A = self.map_f(x['Q'], x['A'])
        output = self.transformer(input_ids=Q['input_ids'], attention_mask=Q['attention_mask'], labels=A['input_ids'])
        del Q, A
        loss, logits = output.loss, output.logits
        # output contains many attributes, use encoder_last_hidden_state or encoder_hidden_state to get encoder output
        return {'seq_loss': loss, 'logits': logits}

    def setup(self, stage=None):
        """
        setup dataset for each machine
        """
        dataset = QADataset(self.config['dataset'])
        dataset_length = len(dataset)
        train_length = int(self.config['train_size'] * dataset_length)
        self.train_dataset, self.val_dataset = random_split(dataset, [train_length, dataset_length - train_length])
        del dataset

    def train_dataloader(self):
        return DataLoader(self.train_dataset,
                          shuffle=True,
                          num_workers=self.config['num_workers'],
                          batch_size=self.config['batch_size'],
                          pin_memory=True)

    def val_dataloader(self):
        return DataLoader(self.val_dataset,
                          shuffle=False,
                          num_workers=self.config['num_workers'],
                          batch_size=self.config['batch_size'],
                          pin_memory=True)

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, self.parameters()), lr=self.config['lr'])
        return optimizer
    
    def training_step(self, batch, batch_idx):
        outputs = self(batch)

        loss = outputs['seq_loss']
        self.log('train_loss', loss)

        return loss

    def validation_step(self, batch, batch_idx):
        outputs = self(batch)

        loss = outputs['seq_loss']
        log = {'val_loss': loss}

        return log

    def validation_epoch_end(self, outputs):
        mean_loss = torch.stack([x['val_loss'] for x in outputs]).mean()

        self.log('val/loss', mean_loss, prog_bar=True)
        mean_loss = torch.stack([x['val_loss'] for x in outputs]).mean()

        self.log('val/loss', mean_loss, prog_bar=True)