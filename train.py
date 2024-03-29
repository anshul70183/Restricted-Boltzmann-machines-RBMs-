# -*- coding: utf-8 -*-
"""PA4_ME15B082_ME15B086.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YG08erzzdHdHiWAs0009y6BrT4trFl-H
"""


#importing required libraires
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from sklearn.manifold import TSNE
#from MulticoreTSNE import MulticoreTSNE as TSNE
import seaborn as sns
import matplotlib.patheffects as PathEffects
from random import shuffle
#parsing arguments

parser = argparse.ArgumentParser()
parser.add_argument("--lr", type = float, default = 0.001)
parser.add_argument("--batch_size", type = int, default = 1)
parser.add_argument("--save_dir", type = str, default = './')
parser.add_argument("--epochs", type = int, default = 5)
parser.add_argument("--n_h", type = int, default = 100)
parser.add_argument("--cd_steps", type = int, default = 1)
parser.add_argument("--train", type = str, default = './train.csv')
parser.add_argument("--test", type = str, default = './test.csv')

#loading parsed values
args = parser.parse_args() 

lr= args.lr
batch_size= args.batch_size
save_dir = args.save_dir
epochs = args.epochs
cd_steps = args.cd_steps
n_h = args.n_h
train_path = args.train
test_path = args.test

#loading train and test file

train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

#getting number of v's (number of pixels)
n_v = np.shape(train)[1] - 2


#function for getting data and labels from dataframe
def get_data_from_df(df):
  data_x = np.array(df.iloc[:, 1:785])
  data_y = np.array(df.iloc[:, 785:])
  return data_x, data_y

#function for thresholding pixels (if pixel value< 127, then new pixel value = 0 else 1)
def threshold_data(data_x):
  return np.where(data_x < 127, 0, 1)

#function for loading batches
def get_batches(x, y , batch_size, batch_num):
  batch_x = x[batch_size*batch_num : batch_size*batch_num + batch_size, :]
  batch_y = y[batch_size*batch_num : batch_size*batch_num + batch_size, :]
  
  return batch_x, batch_y

#sigmoid function
def sigmoid(x):
  x = np.clip(x, -500, 500 )
  sig = 1/(1+ np.exp(-x))
  return sig

#function for binarizing values 
def assign_binary(sig):
  #print(sig)
  prob = np.random.binomial(n=1, p=sig, size = np.shape(sig))
  return prob

#gibbs function to give visible state after cd_steps
def gibbs(visible, W, b, c, cd_steps):
  hidden = sigmoid(np.matmul(visible,W)+b)
  hidden = assign_binary(hidden)

  for t in range(cd_steps):

    visible_after_steps = sigmoid(np.matmul(hidden,W.T)+c)
    hidden = sigmoid(np.matmul(visible_after_steps,W)+b)
    
  return visible_after_steps

#loss function
def rmse(visible, visible_after_steps):
  return (np.square(visible- visible_after_steps).sum())/batch_size

#function for shuffling data
def shuffle_data(data, X, y):
  data = np.array(data)
  X_array = np.array(X)
  y_array = np.array(y)
  ind_list = [i for i in range(data.shape[0])]
  shuffle(ind_list)
  data  = data[ind_list, :]
  X_array = X_array[ind_list,:]
  y_array = y_array[ind_list]
  data= pd.DataFrame(data)
  return train, X_array, y_array

#training function
def training(train, test, n_v, n_h, lr, batch_size, epochs, cd_steps):
    #loading data and thresholding
  train_x, train_y = get_data_from_df(train)
  test_x, test_y = get_data_from_df(test)

  train_x = threshold_data(train_x)
  test_x = threshold_data(test_x)
  
  #initiliazation of params
  W = np.reshape(np.random.normal(0,0.01, size = (n_v*n_h)), newshape = (n_v,n_h))
  b = np.reshape(np.random.normal(0,0.01, size = (1*n_h)), newshape = (1,n_h))
  c = np.reshape(np.random.normal(0,0.01, size = (1*n_v)), newshape = (1,n_v))
  
  #grad initialization to zero
  dL_dc = np.zeros_like(c)
  dL_db = np.zeros_like(b)
  dL_dW = np.zeros_like(W)
  

  train_error=[]
  test_error=[]
  samples=[]
  step = 0
  
  
  for epoch in range(epochs):
     #shuffling data
    train, train_x, train_y= shuffle_data(train, train_x, train_y)
    
    for i in range(len(train)// batch_size):
      visible = train_x[(i*batch_size):((i+1)*batch_size),:]
      #getting hidden prob
      hidden = sigmoid(np.matmul(visible,W)+b)
      #getting hidden binary values
      hidden = assign_binary(hidden)
      
      #for cd_steps (k)
      for t in range(cd_steps):
        #getting visible and hidden values k times
        visible_after_steps = sigmoid(np.matmul(hidden,W.T)+c)
        hidden = sigmoid(np.matmul(visible_after_steps,W)+b)
    #getting gradients
      dL_dc = np.mean(visible - visible_after_steps, axis=0)
      dL_db = np.mean((sigmoid(np.matmul(visible, W)+ b)) - (sigmoid(np.matmul(visible_after_steps, W)+b)),axis=0)
      dL_dW = (np.matmul(visible.T, sigmoid(np.matmul(visible,W)+b))) - (np.matmul(visible_after_steps.T, sigmoid(np.matmul(visible_after_steps,W)+b)))
      
      #updating weights (params)
      c = c + lr* dL_dc
      b = b + lr* dL_db
      W = W + lr* dL_dW
      
      step+=1
      
      #printing batch error after every 5000 steps
      if step%5000 ==0:
        
        print("Error: {}".format(rmse(visible, visible_after_steps)))
    
    #taking samples after every 100 steps for question 3 plotting
      if step<=6400:
        if step%100==0:
          samples.append(visible_after_steps)
    
    #end of epoch loss for train and test set
    visible_after_steps_train = gibbs(train_x, W,b,c, cd_steps)
    visible_after_steps_test = gibbs(test_x, W,b,c, cd_steps)

    err= rmse(train_x, visible_after_steps_train)/len(train)
    err_test = rmse(test_x, visible_after_steps_test)/len(test)
    
    train_error.append(err)
    test_error.append(err_test)

    print("Epoch Error Train : {}".format(train_error))
    print("Epoch Error Test: {}".format(test_error))

  return W, b, c , samples

#getting updated params W, b, c, samples and epoch errors for training and testing
W, b, c, samples = training(train, test, n_v, n_h, lr, batch_size, epochs, cd_steps)

#epoch errors can be used to form plots required in question 2 for various cd_steps (k)

#Question 1 : tSNE Plot

#getting data and thresholding
train_x, train_y = get_data_from_df(train)
test_x, test_y = get_data_from_df(test)

train_x = threshold_data(train_x)
test_x = threshold_data(test_x)

hidden_after_steps_test =  sigmoid(np.matmul(test_x,W)+ b)

#getting TSNE representation
tsne = TSNE(n_components=2)
x_new_test = tsne.fit_transform(hidden_after_steps_test[:,:])

#defining function for plotting 
def fashion_scatter(x, labels, n_h):
    #num_classes = len(np.unique(colors))
    num_classes=10
    palette = np.array(sns.color_palette("hls", num_classes))

    # create a scatter plot.
    f = plt.figure(figsize=(8, 8))
    ax = plt.subplot(aspect='equal')
    sc = ax.scatter(x[:,0], x[:,1], lw=0, c=palette[labels.astype(np.int)])
    plt.xlim(-25, 25)
    plt.ylim(-25, 25)
    ax.axis('off')
    ax.axis('tight')
    plt.title('Number of Hidden Neurons:{}'.format(n_h))
    
    
      # add the labels for each digit corresponding to the label
    txts = []

    for i in range(num_classes):
    # Position of each label at median of data points.
      xtext, ytext = np.median(x[labels == i, :], axis=0)
      txt = ax.text(xtext, ytext, str(i), fontsize=24)
      txt.set_path_effects([
          PathEffects.Stroke(linewidth=5, foreground="w"),
          PathEffects.Normal()])
      txts.append(txt)
    return f, ax, sc, txts

#plotting TSNE scatter
fashion_scatter(x_new_test, test_y[:].ravel(), n_h)


# Question 3: Sample Plot

#sample plots
fig = plt.figure(figsize=(10,10))
for i in range(64):
    ax = fig.add_subplot(8, 8, i+1)
    ax.imshow(samples[i].reshape(28,28),cmap = 'gray')


