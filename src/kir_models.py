#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''Module returns models with best hyperparameters
'''
from sklearn.svm import SVC
from sklearn.naive_bayes import BernoulliNB
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression

import load
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score, roc_curve, auc



def svm(params=None):
    if not params:
        ## Best Model Params; invert results?
        params = {
            'max_iter': 700,
            'C': 1,
            'gamma': 'auto',
            'probability': True
        }

    return SVC(**params)

def nb(params=None):
    if not params:
        ## Best Model Params
        params = {
            'alpha': 1.0, 
            'binarize': 0.0, 
            'class_prior': None, 
            'fit_prior': True
        }
    
    return BernoulliNB(**params)
        
def nn(params=None):
    if not params:
        ## Best Model Params
        params = {
            'activation': 'logistic', 
            'alpha': 0.1, 
            'hidden_layer_sizes': (255, 100, 50), 
            'learning_rate': 'constant', 
            'max_iter': 200, 
            'solver': 'sgd'
        }

    return MLPClassifier(**params)

def lr(params=None):
    if not params:
        ## Best Model Params
        params = {
            'C': 0.1,
            'max_iter': 100,
            'penalty': 'l2',
            'solver': 'liblinear'
        }

    return LogisticRegression(**params)

def featureEngineering(df_x, df_y=None, fake_user_set=set()):
    
    df = df_x.sort_values('date')
    new_features = ['rating_indicator', 'previous_fake', 'reviews_today']
    
    df[new_features] = pd.DataFrame([[0, 0, 0]], index=df.index)
    
    today = None
    
    for index, row in df.iterrows():  
        # rolling date calculations
        if row['date'] != today:
            today  = row['date']
            users_reviews_today = {}
        
        if row.user_id in users_reviews_today:
            users_reviews_today[row['user_id']] += 1
        else:
            users_reviews_today.update({row['user_id']:1})
        
        # set values
        if row['rating'] == 1 or row['rating'] == 5:
            df.at[index, 'rating_indicator'] = 1
            
        if row['user_id'] in fake_user_set:
            df.at[index, 'previous_fake'] = 1
            
        df.at[index, 'reviews_today'] = users_reviews_today[row['user_id']]
        
        # Update fake_user_set after setting values to avoid leakage
        try: 
            if df_y.at[index, 'label'] == 1:
                fake_user_set.add(row['user_id'])
        except:
            # no df_y included; probably on the test set
            pass
            
    df.sort_index(inplace=True)
    
    return df, fake_user_set
    
def metrics(clf, test_X, test_y, name):
    def plotAUC(preds, truth, score, name):
        if len(preds.shape) == 1:
            fpr, tpr, thresholds = roc_curve(truth, preds)
        else: 
            fpr, tpr, thresholds = roc_curve(truth, preds[:, 1])
        roc_auc = auc(fpr, tpr)
        
        plt.figure(figsize = (8, 8))
        plt.plot(fpr, tpr, label=f'(AUC:{roc_auc:0.3f}, AP:{score:0.3f})')
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'{name} - AUC')
        plt.xlim((0,1))
        plt.ylim((0,1))
        plt.legend(loc="lower right")
        
        # convience for me...
        plt.savefig(f'{load.get_data_path()}_{name}.png')
        # plt.savefig(f'{load.get_data_path()}_{name.split("-")[0]}/_{name}.png')
    
    def printConfusionMatrix(preds, truth):
        print(pd.crosstab(truth.ravel(), preds, rownames=['True'],
                          colnames=['Predicted'], margins=True))
        
    def pickleData(clf, test_X, test_y, name):
        with open(f'{load.get_data_path()}_{name}_metrics.pickle', 'wb') as file:
            pickle.dump((clf, test_X, test_y, name), file)
        
    y_truth, y_pred, y_prob = test_y, clf.predict(test_X), clf.predict_proba(test_X)
    score = average_precision_score(y_truth,y_prob[:, 1])
    
    printConfusionMatrix(y_truth, y_pred)
    plotAUC(y_truth, y_pred, score, name)
    pickleData(clf, test_X, test_y, name)


    
    
