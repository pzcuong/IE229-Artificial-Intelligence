# -*- coding: utf-8 -*-
"""IE229 - Lab 04.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1cC4Ak2d0yhrEdrGxf6XHaHDrwXBseprJ

Q1. Implement the MNIST learning and inference program by following the 10th lecture’s slides (copy the program on the slide), and submit the program (.py) and the execution results, i.e., loss at each epoch during training and accuracy against test data, displayed on the console in a word file.
"""

import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
import torchvision as tv
import seaborn as sns
from sklearn.metrics import confusion_matrix

train_dataset=tv.datasets.MNIST(root="./",train=True,transform=tv.transforms.ToTensor(),download=True)
test_dataset=tv.datasets.MNIST(root="./",train=False,transform=tv.transforms.ToTensor(),download=True)

train_loader=torch.utils.data.DataLoader(dataset=train_dataset,batch_size=100,shuffle=True)
test_loader=torch.utils.data.DataLoader(dataset=test_dataset,batch_size=100,shuffle=False)

MODELNAME = 'mnist.model'
EPOCH = 10
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

class MNIST(torch.nn.Module):
    losses = []

    def __init__(self):
        super(MNIST,self).__init__()
        self.l1 = torch.nn.Linear(784,300)
        self.l2 = torch.nn.Linear(300,300)
        self.l3 = torch.nn.Linear(300,10)

    def forward(self,x):
        h = F.relu(self.l1(x))
        h = F.relu(self.l2(h))
        y = self.l3(h)
        return y

def train():
    model = MNIST().to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters())
    for epoch in range(EPOCH):
        loss = 0
        for images, labels in train_loader:
            images = images.view(-1,28*28).to(DEVICE)
            labels = labels.to(DEVICE)
            optimizer.zero_grad()
            y = model(images)
            batchloss = F.cross_entropy(y, labels)
            batchloss.backward()
            optimizer.step()
            loss = loss + batchloss.item()
        print('epoch: ', epoch,', loss: ',loss)
        model.losses.append(loss)
    torch.save(model.state_dict(), MODELNAME)

    plt.plot(model.losses)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss')
    plt.show()

train()

def test():
    total = len(test_loader.dataset)
    correct = 0
    model = MNIST().to(DEVICE)
    model.load_state_dict(torch.load(MODELNAME))
    model.eval()

    true_labels = []
    pred_labels = []

    for images, labels in test_loader:
        images = images.view(-1, 28 * 28).to(DEVICE)
        y = model(images)
        labels = labels.to(DEVICE)
        pred = y.max(dim=1)[1]

        true_labels.extend(labels.cpu().numpy())
        pred_labels.extend(pred.cpu().numpy())

        correct += (pred == labels).sum()

    print('Correct: ', correct.item())
    print('Total: ', total)
    print('Accuracy: ', correct.item() / float(total))

    # Generate confusion matrix
    cm = confusion_matrix(true_labels, pred_labels)

    # Plot the confusion matrix as an image
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.xlabel('Predicted Labels')
    plt.ylabel('True Labels')
    plt.title('Confusion Matrix')
    plt.show()

test()

"""Q2. Rewrite the program you wrote in Q1 to train and infer on the image recognition dataset CIFAR-10, and submit the program (.py) and the execution results, i.e., loss at each epoch during training and accuracy against test data, displayed on the console in a word file. CIFAR-10 is a 10-class image classification data, and can be downloaded by the following program."""

train_dataset = tv.datasets.CIFAR10(root="./", train=True, transform=tv.transforms.ToTensor(), download=True)
test_dataset = tv.datasets.CIFAR10(root="./", train=False, transform=tv.transforms.ToTensor(), download=True)

train_loader=torch.utils.data.DataLoader(dataset=train_dataset,batch_size=100,shuffle=True)
test_loader=torch.utils.data.DataLoader(dataset=test_dataset,batch_size=100,shuffle=False)

MODELNAME = 'cifar-10.model'
EPOCH = 10
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

class CIFAR(torch.nn.Module):
    losses = [] # List to store the loss values

    def __init__(self):
        super(CIFAR,self).__init__()
        self.l1 = torch.nn.Linear(32*32*3,300)
        self.l2 = torch.nn.Linear(300,300)
        self.l3 = torch.nn.Linear(300,10)

    def forward(self,x):
        h = F.relu(self.l1(x))
        h = F.relu(self.l2(h))
        y = self.l3(h)
        return y

def train():
    model = CIFAR().to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters())
    for epoch in range(EPOCH):
        loss =0
        for images, labels in train_loader:
            images = images.view(-1,32*32*3).to(DEVICE)
            labels = labels.to(DEVICE)
            optimizer.zero_grad()
            y = model(images)
            batchloss = F.cross_entropy(y, labels)
            batchloss.backward()
            optimizer.step()
            loss = loss + batchloss.item()
        print('epoch: ', epoch,', loss: ',loss)
        model.losses.append(loss)
    torch.save(model.state_dict(), MODELNAME)
    # Plot the losses result
    plt.plot(model.losses)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss')
    plt.show()

train()

def test():
    total = len(test_loader.dataset)
    correct = 0
    model = CIFAR().to(DEVICE)
    model.load_state_dict(torch.load(MODELNAME))
    model.eval()

    true_labels = []
    pred_labels = []

    for images, labels in test_loader:
        images = images.view(-1, 32 * 32 * 3).to(DEVICE)
        y = model(images)
        labels = labels.to(DEVICE)
        pred = y.max(dim=1)[1]

        true_labels.extend(labels.cpu().numpy())
        pred_labels.extend(pred.cpu().numpy())

        correct += (pred == labels).sum()

    print('Correct: ', correct.item())
    print('Total: ', total)
    print('Accuracy: ', correct.item() / float(total))

    # Generate confusion matrix
    cm = confusion_matrix(true_labels, pred_labels)

    # Plot the confusion matrix as an image
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.xlabel('Predicted Labels')
    plt.ylabel('True Labels')
    plt.title('Confusion Matrix')
    plt.show()

test()

"""Q3. Rewrite the program you wrote in Q2 to create an NN with one intermediate layer as a convolutional layer, and submit the program (.py) and the execution results, i.e., loss at each epoch during training and accuracy against test data, displayed on the console in a word file. The convolutional layer can be obtained by the following program

**nn.Conv2d(in_channel, out_channel, filtersize)**

where  in_channel  is  the  number  of  input  channels,  out_channel  is  the  number  of  output  channels,  and  filtersize is the size of the filter.
"""

MODELNAME = 'cifar-10-conv2d.model'
EPOCH = 10
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

class CIFAR_Conv2D(torch.nn.Module):
    losses = [] # List to store the loss values

    def __init__(self):
        super(CIFAR_Conv2D,self).__init__()
        self.l1 = torch.nn.Conv2d(3,100,4)
        self.l2 = torch.nn.Linear(29*29*100,300)
        self.l3 = torch.nn.Linear(300,10)

    def forward(self,x):
        h = F.relu(self.l1(x))
        h = torch.flatten(h, start_dim=1)
        h = F.relu(self.l2(h))
        y = self.l3(h)
        return y

def train():
    model = CIFAR_Conv2D().to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters())

    for epoch in range(EPOCH):
        loss = 0
        for images, labels in train_loader:
            images = images.view(-1,3,32,32).to(DEVICE)
            labels = labels.to(DEVICE)
            optimizer.zero_grad()
            y = model(images)
            batchloss = F.cross_entropy(y, labels)
            batchloss.backward()
            optimizer.step()
            loss = loss + batchloss.item()

        print('epoch: ', epoch,', loss: ',loss)
        model.losses.append(loss)  # Append the loss to the list

    torch.save(model.state_dict(), MODELNAME)

    plt.plot(model.losses)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss')
    plt.show()

train()

def test():
    total = len(test_loader.dataset)
    correct = 0
    model = CIFAR_Conv2D().to(DEVICE)
    model.load_state_dict(torch.load(MODELNAME))
    model.eval()

    true_labels = []
    pred_labels = []

    for images, labels in test_loader:
        images = images.view(-1, 3, 32, 32).to(DEVICE)
        y = model(images)
        labels = labels.to(DEVICE)
        pred = y.max(dim=1)[1]

        true_labels.extend(labels.cpu().numpy())
        pred_labels.extend(pred.cpu().numpy())

        correct += (pred == labels).sum()

    print('Correct: ', correct.item())
    print('Total: ', total)
    print('Accuracy: ', correct.item() / float(total))

    # Generate confusion matrix
    cm = confusion_matrix(true_labels, pred_labels, labels=range(10))

    # Plot the confusion matrix as an image
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=range(10), yticklabels=range(10))
    plt.xlabel('Predicted Labels')
    plt.ylabel('True Labels')
    plt.title('Confusion Matrix')
    plt.show()

test()