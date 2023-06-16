# -*- coding: utf-8 -*-
"""IE229_Lab_06

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tkMYByFWjGOdBQ0hJjdj-TUnCLYicQB2
"""

import requests
import torch
import torch.nn.functional as F
import torchtext
import tarfile

url = "https://nlp.stanford.edu/projects/nmt/data/iwslt15.en-vi/"
train_en = [line.split() for line in requests.get(url+"train.en").text.splitlines()]
train_vi = [line.split() for line in requests.get(url+"train.vi").text.splitlines()]
test_en = [line.split() for line in requests.get(url+"tst2013.en").text.splitlines()]
test_vi = [line.split() for line in requests.get(url+"tst2013.vi").text.splitlines()]

# def iwslt15(train_test):
#   url = "https://github.com/stefan-it/nmt-en-vi/raw/master/data/"
#   r = requests.get(url + train_test + "-en-vi.tgz")
#   filename = train_test+"-en-vi.tar.gz"
#   with open(filename, "wb") as f:
#     f.write(r.content)
#     tarfile.open(filename, "r:gz").extractall("iwslt15")

# iwslt15("train")
# iwslt15("test-2013")

# f = open("iwslt15/train.en")
# train_en = [line.split() for line in f]
# f.close()

# f = open("iwslt15/train.vi")
# train_vi = [line.split() for line in f]
# f.close()

# f = open("iwslt15/tst2013.en")
# test_en = [line.split() for line in f]
# f.close()

# f = open("iwslt15/tst2013.en")
# test_vi = [line.split() for line in f]
# f.close()

for i in range(10):
  print(train_en[i])
  print(train_vi[i])
print("# of line", len(train_en), len(train_vi), len(test_en), len(test_vi))

MODELNAME = "iwslt15-en-vi-rnn.model"
EPOCH = 10
BATCHSIZE = 128
LR = 0.0001
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def make_vocab(train_data, min_freq):
  vocab = {}
  for tokenlist in train_data:
    for token in tokenlist:
      if token not in vocab:
        vocab[token] = 0
      vocab[token] += 1
  vocablist = [('<unk>', 0), ('<pad>', 0), ('<cls>', 0), ('<eos>', 3)]
  vocabidx = {}
  for token, freq in vocab.items():
    if freq >= min_freq:
      idx = len(vocablist)
      vocablist.append((token, freq))
      vocabidx[token] = idx
  vocabidx['<unk>'] = 0
  vocabidx['<pad>'] = 1
  vocabidx['<cls>'] = 2
  vocabidx['<eos>'] = 3
  return vocablist, vocabidx

vocablist_en, vocabidx_en = make_vocab(train_en, 3)
vocablist_vi, vocabidx_vi = make_vocab(train_vi, 3)

print("vocab size en:", len(vocablist_en))
print("vocab size vi:", len(vocablist_vi))

def preprocess(data, vocabidx):
  rr = []
  for tokenlist in data:
    tkl = ['<cls>']
    for token in tokenlist:
      tkl.append(token if token in vocabidx else '<unk>')
    tkl.append('<eos>')
    rr.append((tkl))
  return rr

train_en_prep = preprocess(train_en, vocabidx_en)
train_vi_prep = preprocess(train_vi, vocabidx_vi)
test_en_prep = preprocess(test_en, vocabidx_en)

for i in range(5):
  print(train_en_prep[i])
  print(train_vi_prep[i])
  print(test_en_prep[i])

train_data = list(zip(train_en_prep, train_vi_prep))
train_data.sort(key = lambda x: (len(x[0]), len(x[1])))
test_data = list(zip(test_en_prep, test_en, test_vi))

for i in range(5):
  print(train_data[i])
for i in range(5):
  print(test_data[i])

def make_batch(data, batchsize):
  bb = []
  ben = []
  bvi = []
  for en, vi in data:
    ben.append(en)
    bvi.append(vi)
    if len(ben) >= batchsize:
      bb.append((ben, bvi))
      ben = []
      bvi = []
  if len(ben) > 0:
    bb.append((ben, bvi))
  return bb

train_data = make_batch(train_data, BATCHSIZE)

for i in range(10):
  print(train_data[i])

def padding_batch(b):
  maxlen = max([len(x) for x in b])
  for tkl in b:
    for i in range(maxlen - len(tkl)):
      tkl.append('<pad>')

def padding(bb):
  for ben, bvi in bb:
    padding_batch(ben)
    padding_batch(bvi)

padding(train_data)

for i in range(3):
  print(train_data[i])

train_data = [([[vocabidx_en[token] for token in tokenlist] for tokenlist in ben],
               [[vocabidx_vi[token] for token in tokenlist] for tokenlist in bvi]) for ben, bvi in train_data]
test_data = [([vocabidx_en[token] for token in enprep], en, vi) for enprep, en, vi in test_data]

for i in range(3):
  print(train_data[i])
for i in range(3):
  print(test_data[i])

class RNNEncDec(torch.nn.Module):
    def __init__(self, vocablist_x, vocabidx_x, vocablist_y, vocabidx_y):
        super(RNNEncDec, self).__init__()
        self.encemb = torch.nn.Embedding(len(vocablist_x), 300, padding_idx = vocabidx_x['<pad>'])
        self.encrnn = torch.nn.Linear(300, 300)
        self.decemb = torch.nn.Embedding(len(vocablist_x), 300, padding_idx = vocabidx_y['<pad>'])
        self.decrnn = torch.nn.Linear(300, 300)
        self.decout = torch.nn.Linear(300, len(vocablist_y))

    def forward(self,x):
        x, y = x[0], x[1]
        #enc
        e_x = self.encemb(x)
        n_x = e_x.size()[0]
        h = torch.zeros(300, dtype=torch.float32).to(DEVICE)
        for i in range(n_x):
          h = F.relu(e_x[i] + self.encrnn(h))
        #dec
        e_y = self.decemb(y)
        n_y = e_y.size()[0]
        loss = torch.tensor(0., dtype=torch.float32).to(DEVICE)
        for i in range(n_y-1):
            h = F.relu(e_y[i] + self.decrnn(h))
            loss += F.cross_entropy(self.decout(h), y[i+1])
        return loss

    def evaluate(self, x, vocablist_y, vocabidx_y):
        # encoder
        #推論は1⽂ずつ⾏うので、 xには⽂⻑✕バッチサイズ1のミニバッチが⼊っている。
        e_x = self.encemb(x)
        n_x = e_x.size()[0]
        #エンコーダー部はforwardとほぼ同じ。
        h = torch.zeros(300, dtype = torch.float32).to(DEVICE)
        for i in range(n_x):
            h = F.relu(e_x[i] + self.encrnn(h))
        # decoder
        #デコーダーの⼊⼒(バッチサイズ1)を作る。最初はトークンを⼊⼒する
        y = torch.tensor([vocabidx_y['<cls>']]).to(DEVICE)
        e_y = self.decemb(y)
        pred = []
        for i in range(30):
            h = F.relu(e_y + self.decrnn(h))
            pred_id = self.decout(h).squeeze().argmax()
            #pred_idが予測する出⼒単語ID pred_idがのIDと等しければ推論終了
            if pred_id == vocabidx_y['<eos>']:
                break
            pred_y = vocablist_y[pred_id][0]
            pred.append(pred_y)
            #デコーダーは1単語ずつ処理をし、得られた出⼒を次の⼊⼒とする
            y[0] = pred_id
            e_y = self.decemb(y)

        return pred

def train():
  model = RNNEncDec(vocablist_en, vocabidx_en, vocablist_vi, vocabidx_vi).to(DEVICE)
  optimizer = torch.optim.Adam(model.parameters(), lr = LR)
  for epoch in range(EPOCH):
    loss = 0
    step = 0
    for ben, bvi in train_data:
      ben = torch.tensor(ben, dtype=torch.int64).transpose(0,1).to(DEVICE)
      bvi = torch.tensor(bvi, dtype=torch.int64).transpose(0,1).to(DEVICE)
      optimizer.zero_grad()
      batchloss = model((ben, bvi))
      batchloss.backward()
      optimizer.step()
      loss = loss + batchloss.item()
      if step % 100 == 0:
        print("step:", step, "batchloss:", batchloss.item())
      step += 1

    print("epoch", epoch, ": loss", loss)
  torch.save(model.state_dict(), MODELNAME)

train()

def test():
    total = 0
    correct = 0
    model = RNNEncDec(vocablist_en, vocabidx_en, vocablist_vi, vocabidx_vi).to(DEVICE)
    model.load_state_dict(torch.load(MODELNAME))
    model.eval()
    ref = []
    pred = []
    for enprep, en, vi in test_data:
        input = torch.tensor([enprep], dtype=torch.int64).transpose(0, 1).to(DEVICE)
        p = model.evaluate(input, vocablist_vi, vocabidx_vi)
        print("INPUT", en)
        print("REF", vi)
        print("MT", p)
        ref.append([vi])
        pred.append(p)
    bleu = torchtext.data.metrics.bleu_score(pred, ref)
    print("total:", len(test_data))
    print("bleu:", bleu)

test()

"""LSTM"""

MODELNAME = "iwslt15-en-vi-lstm.model"
EPOCH = 10
BATCHSIZE = 128
LR = 0.0001
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class LSTM(torch.nn.Module):
    def __init__(self, vocablist_x, vocabidx_x, vocablist_y, vocabidx_y):
        super(LSTM, self).__init__()

        self.encemb = torch.nn.Embedding(len(vocablist_x), 256, padding_idx = vocabidx_x['<pad>'])
        self.dropout = torch.nn.Dropout(0.5)
        self.enclstm = torch.nn.LSTM(256,516,2,dropout=0.5)

        self.decemb = torch.nn.Embedding(len(vocablist_x), 256, padding_idx = vocabidx_y['<pad>'])
        self.declstm = torch.nn.LSTM(256,516,2,dropout=0.5)
        self.decout = torch.nn.Linear(516, len(vocabidx_y))

    def forward(self,x):
        x, y = x[0], x[1]
        # print(x.size())
        # print(y.size())

        e_x = self.dropout(self.encemb(x))

        outenc,(hidden,cell) = self.enclstm(e_x)

        n_y=y.shape[0]
        outputs = torch.zeros(n_y,BATCHSIZE,len(vocablist_vi)).to(DEVICE)
        loss = torch.tensor(0.,dtype=torch.float32).to(DEVICE)
        for i in range(n_y-1):
            input = y[i]
            input = input.unsqueeze(0)
            input = self.dropout(self.decemb(input))
            outdec, (hidden,cell) = self.declstm(input,(hidden,cell))
            output = self.decout(outdec.squeeze(0))
            input = y[i+1]
            loss += F.cross_entropy(output, y[i+1])
        return loss

    def evaluate(self,x,vocablist_y,vocabidx_y):
        e_x = self.dropout(self.encemb(x))
        outenc,(hidden,cell)=self.enclstm(e_x)

        y = torch.tensor([vocabidx_y['<cls>']]).to(DEVICE)
        pred=[]
        for i in range(30):
            input = y
            input = input.unsqueeze(0)
            input = self.dropout(self.decemb(input))
            outdec,(hidden,cell)= self.declstm(input,(hidden,cell))
            output = self.decout(outdec.squeeze(0))
            pred_id = output.squeeze().argmax().item()
            if pred_id == vocabidx_y['<eos>']:
                break
            pred_y = vocablist_y[pred_id][0]
            pred.append(pred_y)
            y[0]=pred_id
            input=y
        return pred

def train():
    model = LSTM(vocablist_en, vocabidx_en, vocablist_vi, vocabidx_vi).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr = LR)
    for epoch in range(EPOCH):
        loss = 0
        step = 0
        for ben, bvi in train_data:
            ben = torch.tensor(ben, dtype=torch.int64).transpose(0,1).to(DEVICE)
            bvi = torch.tensor(bvi, dtype=torch.int64).transpose(0,1).to(DEVICE)
            optimizer.zero_grad()
            batchloss = model((ben, bvi))
            batchloss.backward()
            optimizer.step()
            loss = loss + batchloss.item()
            if step % 100 == 0:
                print("step:", step, "batchloss:", batchloss.item())
            step += 1

        print("epoch", epoch, ": loss", loss)
    torch.save(model.state_dict(), MODELNAME)

train()

def test():
    total = 0
    correct = 0
    model = LSTM(vocablist_en, vocabidx_en, vocablist_vi, vocabidx_vi).to(DEVICE)
    model.load_state_dict(torch.load(MODELNAME))
    model.eval()
    ref = []
    pred = []
    for enprep, en, vi in test_data:
        input = torch.tensor([enprep], dtype=torch.int64).transpose(0, 1).to(DEVICE)
        p = model.evaluate(input, vocablist_vi, vocabidx_vi)
        print("INPUT", en)
        print("REF", vi)
        print("MT", p)
        ref.append([vi])
        pred.append(p)
    bleu = torchtext.data.metrics.bleu_score(pred, ref)
    print("total:", len(test_data))
    print("bleu:", bleu)

test()