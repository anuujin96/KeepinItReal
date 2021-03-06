#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import datetime
import pickle
import load

from sklearn.preprocessing import MinMaxScaler
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import roc_curve, auc

import matplotlib
import matplotlib.pyplot as plt

import warnings

def pre_process_to_pickle(version='large'):
    """Multi-layer Perceptron is sensitive to feature scaling;
        this function uses MinMaxScaler to scale input features between (-1,1)
    
    Returns:
        scaled: train_X, val_X
    """
    train_X, val_X, train_y, val_y = load.read_data(bert=version)
    train_X.date = pd.to_datetime(train_X.date).astype('int64')
    train_X = pd.concat([train_X.drop('review', axis=1),
                         pd.DataFrame(train_X.review.tolist(),dtype=np.float32)],
                        axis=1)
    val_X.date = pd.to_datetime(val_X.date).astype('int64')
    val_X = pd.concat([val_X.drop('review', axis=1),
                         pd.DataFrame(val_X.review.tolist(),dtype=np.float32)],
                        axis=1)
    
    cols = ['ex_id', 'user_id', 'prod_id', 'rating', 'date']
    scaler = MinMaxScaler(feature_range=(-1,1)).fit(train_X[cols])
    
    train_X[cols] = scaler.transform(train_X[cols])
    val_X[cols] = scaler.transform(val_X[cols])
    
    path = load.get_data_path()
    with open(f'{path}train_{version}.pickle', 'wb') as file:
        pickle.dump(train_X, file)
        
    with open(f'{path}dev_{version}.pickle', 'wb') as file:
        pickle.dump(val_X, file)
        
    return train_X, val_X

def save_ROC_plot(preds, truth, score, file_name):
    if len(preds.shape) == 1:
        fpr, tpr, thresholds = roc_curve(truth, preds)
    else: 
        fpr, tpr, thresholds = roc_curve(truth, preds[:, 1])
    
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize = (8, 8))
    plt.plot(fpr, tpr, label = 'MLP (AUC = %0.3f, AP = %0.3f)' % (roc_auc, score))
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('NN - AUC vs AP ??, is this a thing')
    plt.xlim((0,1))
    plt.ylim((0,1))
    plt.legend(loc="lower right")
    
    path = load.get_data_path()
    plt.savefig(path+file_name)
    
    return roc_auc

def trainNN(x, y, params=None):
    '''Returns MLP NN fitted with best params
    '''
    if not params:
        params = {
            'activation': 'logistic', 
            'alpha': 0.1, 
            'hidden_layer_sizes': (255, 100, 50), 
            'learning_rate': 'constant', 
            'max_iter': 200, 
            'solver': 'sgd'
        }
    
    NN = MLPClassifier(**params).fit(x, y.values.ravel())
    return NN
    

def searchNN(x, y, param_space):
    # declare model, search params
    model = MLPClassifier()
    clf = RandomizedSearchCV(model, param_space, n_jobs=5, cv=3, scoring='average_precision', n_iter=30, verbose=10).fit(x, y.values.ravel())
    
    return clf


def main():
    train_X, val_X, train_y, val_y = load.read_data(bert='large', debug=True)
    
    # Grid Search Params
    param_space = {
        'hidden_layer_sizes': [(255,100,50), (50,50,50), (255,), (100,), (50,)],
        'activation': ['logistic', 'tanh', 'relu'],
        'solver': ['sgd', 'adam', 'lbfgs'],
        'alpha': 10.0 ** -np.arange(1, 4),
        'learning_rate': ['constant', 'adaptive', 'invscaling'],
        'max_iter': [100, 200, 300],
    }
    
    # Test Params -- soon to be Best Params, after I Grid Search
    # params = {
    #     'hidden_layer_sizes': (255,),
    #     'activation': 'relu',
    #     'solver': 'adam',
    #     'alpha': 1e-05,
    #     'learning_rate': 'adaptive',
    #     'max_iter': 300,
    # }
    
    # Grid search
    NN = searchNN(train_X, train_y, param_space)
    
    # Or single run
    # NN = MLPClassifier(**params).fit(train_X, train_y)
    
    path = load.get_data_path()
    with open(path+'pickle_clf.pickle', 'wb') as file:
        pickle.dump(NN, file)
    
    # check train data
    y_truth, y_pred, y_prob = train_y, NN.predict(train_X), NN.predict_proba(train_X)
    score = NN.score(train_X,train_y)
    print(f"Train Score: {100 * score:.2f}")
    try:
        plots_probs = save_ROC_plot(y_prob, y_truth, score, 'train')
        print(f"Train ROC AUC: {plots_probs}")
    except:
        pass
    
    # check test data
    y_truth, y_pred, y_prob = val_y, NN.predict(val_X), NN.predict_proba(val_X)
    score = NN.score(val_X,val_y)
    print(f"Test Score: {100 * score:.2f}")
    try:
        plots_probs = save_ROC_plot(y_prob, y_truth, score, 'test')
        print(f"Test ROC AUC: {plots_probs}")
    except:
        pass
    
    with open(path+'pickle_nn.pickle', 'wb') as file:
        pickle.dump(NN.best_estimator_, file)
    
    
if __name__ == "__main__":
    print("Training MLP Classifier")
    warnings.filterwarnings("ignore")
    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    main()
    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    

        