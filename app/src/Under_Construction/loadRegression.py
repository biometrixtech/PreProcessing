# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 10:28:21 2016

@author: Ankur
"""

"""
Dipesh kindly read the comments before diving in to the code.

Comments: This script has a ton of lines that are commented out. I wanted to keep them 
in there just to give you an idea of the methods that we tried. You don't have to spend
time reading through the commented lines of code. You can read the single line
description before the blocks of code. That will give you a brief idea of what that block
of code does. 

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas.tools.plotting import scatter_matrix
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from phaseDetection import combine_phase
from sklearn.cross_validation import cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.grid_search import GridSearchCV
from sklearn.neighbors import KNeighborsRegressor, RadiusNeighborsRegressor

path = 'C:\\Users\\Ankur\\python\\Biometrix\\Data analysis\\data exploration\\data files\\GRF Data _Abigail\\combined\\sensor&grfdata.csv'
data = np.genfromtxt(path, delimiter = ",", dtype = float, names = True)
#data = pd.read_csv(path)

#phase detection
sampl_rate = 250
lf_phase, rf_phase = combine_phase(data['RAccX'], data['RAccZ'], sampl_rate)

#converting numpy array to a pandas dataframe
data = pd.DataFrame(data)

#adding the phase columns for each foot
data['LPhase'] = lf_phase
data['RPhase'] = rf_phase

dblsquat_neutral = pd.DataFrame()
dblsquat_neutral = data.ix[:,:]
print(type(dblsquat_neutral))


#plot of the acceleration data with phase detection

#plt.figure(1)
#plt.plot(dblsquat_neutral['LAccZ'])
#plt.plot(lf_phase)
#plt.legend()
#plt.show()


#FEATURES

#LEFT FOOT
lfoot_resforce = []
lfoot_resacc = []
lfoot_lfx = []
lfoot_lfy = []
lfoot_lfz = []
lfoot_sumforces = []
lfoot_laccx = []
lfoot_laccy = []
lfoot_laccz = []
lfoot_leulx = []
lfoot_leuly = []
lfoot_leulz = []
lfoot_abslaccz = []
lfoot_sumabsacc = []
lfoot_sumacc = []
lfoot_count = []
lfoot_phase = []
a_lf = 0
b_lf = 0
#RIGHT FOOT
rfoot_resforce = []
rfoot_resacc = []
rfoot_rfx = []
rfoot_rfy = []
rfoot_rfz = []
rfoot_sumforces = []
rfoot_raccx = []
rfoot_raccy = []
rfoot_raccz = []
rfoot_reulx = []
rfoot_reuly = []
rfoot_reulz = []
rfoot_absraccz = []
rfoot_sumabsacc = []
rfoot_sumacc = []
rfoot_count = []
rfoot_phase = []
a_rf = 0
b_rf = 0
#HIP
h_accx = []
h_accy = []
h_accz = []
h_eulx = []
h_euly = []
h_eulz = []

#Constants
mass = 57
g = 9.80665
count = 0

for i in range(len(dblsquat_neutral)):
    #a_lf = np.sqrt((dblsquat_neutral['LFx'].ix[i]**2) + (dblsquat_neutral['LFy'].ix[i]**2) + (dblsquat_neutral['LFz'].ix[i]**2))
    a_lf = dblsquat_neutral['LFz'].ix[i]    
    b_lf = np.sqrt((dblsquat_neutral['LAccX'].ix[i]**2) + (dblsquat_neutral['LAccY'].ix[i]**2) + (dblsquat_neutral['LAccZ'].ix[i]**2))
    #b_lf = dblsquat_neutral['LAccZ'].ix[i]
    #a_rf = np.sqrt((dblsquat_neutral['RFx'].ix[i]**2) + (dblsquat_neutral['RFy'].ix[i]**2) + (dblsquat_neutral['RFz'].ix[i]**2))
    a_rf = dblsquat_neutral['RFz'].ix[i]     
    b_rf = np.sqrt((dblsquat_neutral['RAccX'].ix[i]**2) + (dblsquat_neutral['RAccY'].ix[i]**2) + (dblsquat_neutral['RAccZ'].ix[i]**2))   
    #b_rf = dblsquat_neutral['RAccZ'].ix[i]    
    count = count + 1    
    if a_rf == 0 and a_lf == 0: #if both feet in the air, we don't determine the load
        continue
    elif a_rf == 0 or a_lf == 0:
        continue
    else:
        lfoot_resforce.append(a_lf)
        lfoot_resacc.append(b_lf)
        #lfoot_lfx.append(dblsquat_neutral['LFx'].ix[i])
        #lfoot_lfy.append(dblsquat_neutral['LFy'].ix[i])
        #lfoot_lfz.append(dblsquat_neutral['LFz'].ix[i])
        #lfoot_sumforces.append(dblsquat_neutral['LFx'].ix[i] + dblsquat_neutral['LFy'].ix[i] + dblsquat_neutral['LFz'].ix[i])
        lfoot_laccx.append(dblsquat_neutral['LAccX'].ix[i])
        lfoot_laccy.append(dblsquat_neutral['LAccY'].ix[i])
        lfoot_laccz.append(dblsquat_neutral['LAccZ'].ix[i])
        lfoot_leulx.append(dblsquat_neutral['LEulerX'].ix[i])
        lfoot_leuly.append(dblsquat_neutral['LEulerY'].ix[i])
        lfoot_leulz.append(dblsquat_neutral['LEulerZ'].ix[i])
        #lfoot_abslaccz.append(abs(dblsquat_neutral['LAccZ'].ix[i]))
        #lfoot_sumabsacc.append(abs(dblsquat_neutral['LAccX'].ix[i]) + abs(dblsquat_neutral['LAccY'].ix[i]) + abs(dblsquat_neutral['LAccZ'].ix[i]))
        #lfoot_sumacc.append(dblsquat_neutral['LAccX'].ix[i] + dblsquat_neutral['LAccY'].ix[i] + dblsquat_neutral['LAccZ'].ix[i])
        #lfoot_mgresacc.append(((mass*g) + b))
        #lfoot_mglaccz.append((mass*g) + dblsquat_neutral['LAccZ'].ix[i])
        lfoot_count.append(count)
        lfoot_phase.append(dblsquat_neutral['LPhase'].ix[i])
        rfoot_resforce.append(a_rf)
        rfoot_resacc.append(b_rf)
        #rfoot_rfx.append(dblsquat_neutral['RFx'].ix[i])
        #rfoot_rfy.append(dblsquat_neutral['RFy'].ix[i])
        #rfoot_rfz.append(dblsquat_neutral['RFz'].ix[i])
        #rfoot_sumforces.append(dblsquat_neutral['RFx'].ix[i] + dblsquat_neutral['RFy'].ix[i] + dblsquat_neutral['RFz'].ix[i])
        rfoot_raccx.append(dblsquat_neutral['RAccX'].ix[i])
        rfoot_raccy.append(dblsquat_neutral['RAccY'].ix[i])
        rfoot_raccz.append(dblsquat_neutral['RAccZ'].ix[i])
        rfoot_reulx.append(dblsquat_neutral['REulerX'].ix[i])
        rfoot_reuly.append(dblsquat_neutral['REulerY'].ix[i])
        rfoot_reulz.append(dblsquat_neutral['REulerZ'].ix[i])
        #rfoot_absraccz.append(abs(dblsquat_neutral['RAccZ'].ix[i]))
        #rfoot_sumabsacc.append(abs(dblsquat_neutral['RAccX'].ix[i]) + abs(dblsquat_neutral['RAccY'].ix[i]) + abs(dblsquat_neutral['RAccZ'].ix[i]))
        rfoot_count.append(count)        
        #rfoot_sumacc.append(dblsquat_neutral['RAccX'].ix[i] + dblsquat_neutral['RAccY'].ix[i] + dblsquat_neutral['RAccZ'].ix[i])
        rfoot_phase.append(dblsquat_neutral['RPhase'].ix[i])        
        #lfoot_mgresacc.append(((mass*g) + b))
        #lfoot_mglaccz.append((mass*g) + dblsquat_neutral['LAccZ'].ix[i])
        h_accx.append(dblsquat_neutral['HAccX'].ix[i])
        h_accy.append(dblsquat_neutral['HAccY'].ix[i])
        h_accz.append(dblsquat_neutral['HAccZ'].ix[i])
        h_eulx.append(dblsquat_neutral['HEulerX'].ix[i])
        h_euly.append(dblsquat_neutral['HEulerY'].ix[i])
        h_eulz.append(dblsquat_neutral['HEulerZ'].ix[i])

# checking if the length of the relevant arrays are the same
print('Left foot:')
print(len(lfoot_resforce), len(lfoot_resacc), len(lfoot_laccz), len(lfoot_abslaccz), len(lfoot_sumabsacc), len(lfoot_count))
print(len(np.unique(lfoot_resforce)), len(np.unique(lfoot_resacc)), len(np.unique(lfoot_laccz)), len(np.unique(lfoot_abslaccz)), len(np.unique(lfoot_sumabsacc)))

print('Right foot:')
print(len(rfoot_resforce), len(rfoot_resacc), len(rfoot_raccz), len(rfoot_absraccz), len(rfoot_sumabsacc), len(rfoot_count))
print(len(np.unique(rfoot_resforce)), len(np.unique(rfoot_resacc)), len(np.unique(rfoot_raccz)), len(np.unique(rfoot_absraccz)), len(np.unique(rfoot_sumabsacc)))

print('Hip:')
print(len(h_accx))

#czero = [ i for i in range(len(lfoot_resforce)) if lfoot_resforce[i] == 0]
#print(len(czero))

#Creating a single data set with all the features and target variables of each foot

wd = pd.DataFrame()
wd['resultant Lforce'] = lfoot_resforce
#wd['resultant Rforce'] = rfoot_resforce
#wd['wd left foot'] = ((np.array(lfoot_resforce)/(np.array(lfoot_resforce)+np.array(rfoot_resforce)))*100)
#wd['wd right foot'] = (np.array(rfoot_resforce)/(np.array(lfoot_resforce)+np.array(rfoot_resforce))*100)
#wd['Total load'] = np.array(lfoot_resforce) + np.array(rfoot_resforce)
#wd['diff in wd'] = abs((np.array(lfoot_resforce)/(np.array(lfoot_resforce)+np.array(rfoot_resforce))*100) - (np.array(rfoot_resforce)/(np.array(lfoot_resforce)+np.array(rfoot_resforce))*100))
wd['lfoot count'] = lfoot_count
wd['rfoot count'] = rfoot_count
#wd['lf resultant acceleration'] = lfoot_resacc
wd['left foot accx'] = lfoot_laccx
wd['left foot accy'] = lfoot_laccy
wd['left foot accz'] = lfoot_laccz
wd['left foot eulx'] = lfoot_leulx
wd['left foot euly'] = lfoot_leuly
wd['left foot eulz'] = lfoot_leulz
wd['LPhase'] = np.array(lfoot_phase)
#wd['rf resultant acceleration'] = rfoot_resacc
wd['right foot accx'] = rfoot_raccx
wd['right foot accy'] = rfoot_raccy
wd['right foot accz'] = rfoot_raccz
wd['right foot eulx'] = rfoot_reulx
wd['right foot euly'] = rfoot_reuly
wd['right foot eulz'] = rfoot_reulz
wd['RPhase'] = np.array(rfoot_phase)
wd['HAccX'] = np.array(h_accx)
wd['HAccY'] = np.array(h_accy)
wd['HAccZ'] = np.array(h_accz)
wd['HEulerX'] = np.array(h_eulx)
wd['HEulerY'] = np.array(h_euly)
wd['HEulerZ'] = np.array(h_eulz)

#print(wd.columns)


#Create the training and test sets 
lfoot_columns = ['lf resultant acceleration']#, 'left foot accx', 'left foot accy',
       #'left foot accz', 'lf azx', 'lf az*ay', 'lf ax*ay', 'lf axyz',
       #'lf xy+yz+xz', 'x*(x+y+z)', 'y*(x+y+z)', 'z*(x+y+z)', 'ax+az',
       #'lf res dir ax', 'lf res dir ay', 'lf res dir az', 'absolute laccx',
       #'absolute laccy', 'absolute laccz', 'lf sum abs acc', 'lf az-ax',
       #'lf ax-ay', 'lf ay-az', 'lf ax/ay', 'lf ay/az', 'lf az/ax',
       #'lf ressacc/ax', 'lf ressacc/ay', 'lf ressacc/az', 'lf ressacc*ax',
       #'lf ressacc*ay', 'lf ressacc*az', 'lf log(abs(ax))*ax/abs(ax)',
       #'lf log(abs(ay))*ay/abs(ay)', 'lf log(abs(az))*az/abs(az)']
#['lf xy+yz+xz',
#              'absolute laccx',
#              'absolute laccy',
#              'absolute laccz',
#              'lf sum abs acc']
rfoot_columns = ['rf resultant acceleration']#, 'right foot accx', 'right foot accy',
       #'right foot accz', 'rf azx', 'rf az*ay', 'rf ax*ay', 'rf axyz',
       #'rf xy+yz+xz', 'rf x*(x+y+z)', 'rf y*(x+y+z)', 'rf z*(x+y+z)',
       #'rf ax+az', 'rf res dir ax', 'rf res dir ay', 'rf res dir az',
       #'absolute raccx', 'absolute raccy', 'absolute raccz', 'rf sum abs acc',
       #'rf az-ax', 'rf ax-ay', 'rf ay-az', 'rf ax/ay', 'rf ay/az', 'rf az/ax',
       #'rf ressacc/ax', 'rf ressacc/ay', 'rf ressacc/az', 'rf ressacc*ax',
       #'rf ressacc*ay', 'rf ressacc*az', 'rf log(abs(ax))*ax/abs(ax)',
       #'rf log(abs(ay))*ay/abs(ay)', 'rf log(abs(az))*az/abs(az)']

total_columns = []     
total_columns = ['left foot accx', 'left foot accy',
       'left foot accz', 'left foot eulx', 'left foot euly',
       'left foot eulz', 'right foot accx', 'right foot accy',
       'right foot accz','right foot eulx', 'right foot euly',
       'right foot eulz','HAccX', 'HAccY', 'HAccZ', 'HEulerX', 'HEulerY', 'HEulerZ']
       
#total_columns = [ 'HAccX', 'HAccY', 'HAccZ', 'HEulerX', 'HEulerY', 'HEulerZ']
       
#total_columns = []
#total_columns = ['right foot eulx', 'HAccZ', 'HEulerX', 'HEulerY']
#['rf y*(x+y+z)',
#              'rf z*(x+y+z)',
#              'absolute raccx',
#              'absolute raccy',
#              'absolute raccz',
#              'rf sum abs acc']
       
hip_columns = ['HAccX', 'HAccY', 'HAccZ', 'HEulerX', 'HEulerY', 'HEulerZ']

wd_v2 = pd.DataFrame()
wd_v2 = wd.ix[:,:]
 
#creating a dataset only for the balance phase
#wd_v2 = wd[wd['LPhase'] == 0]

#delete_rows = range(11000,15600)
#wd_v2 = wd_v2.drop(delete_rows)
dummy1 = pd.DataFrame()
dummy2 = pd.DataFrame()
dummy3 = pd.DataFrame()
dummy4 = pd.DataFrame()
dummy5 = pd.DataFrame()
dummy6 = pd.DataFrame()

dummy1 = wd_v2.ix[5750:11000] #double leg squats neutral
dummy2 = wd_v2.ix[15600:21400] #double leg squats left loading
dummy3 = wd_v2.ix[11000:15600] #standing and the three jumps
dummy4 = wd_v2.ix[11000:13500] #standing 
dummy5 = wd_v2.ix[13800:14300] #the three jumps
dummy6 = wd_v2.ix[43700:] #explosive jumps right-left loading
#dummy1.append(dummy6)

#creating a dataset only for the impact phase
dummy6 = dummy6[(dummy6['LPhase'] == 4)]# & (wd['RPhase'] == 5)]

#eliminating the phase from the dataset
#dummy6 = dummy6.drop('LPhase', axis=1)
#dummy6 = dummy6.drop('RPhase', axis=1)


#plot of only the impact phase data
#plt.figure(1)
#plt.plot(range(len(dummy6['LPhase'])), dummy6['left foot accz'])
#plt.plot(range(len(dummy6['LPhase'])), dummy6['LPhase'])
#plt.show()


#Checking the true load values before smoothening
dummy1_true = pd.DataFrame()
dummy2_true = pd.DataFrame()
dummy6_true = pd.DataFrame()

dummy1_true = dummy1
dummy2_true = dummy2
dummy6_true = dummy6

frames_true = [dummy1_true, dummy2_true]
result_true = pd.concat(frames_true)

#smoothening the data
dummy1 = pd.rolling_mean(dummy1, 30, center = True)
dummy2 = pd.rolling_mean(dummy2, 30, center = True)
#dummy6 = pd.rolling_mean(dummy6, 30, center = True)

#neglecting all the NA's
dummy1 = dummy1.dropna()
dummy2 = dummy2.dropna()
#dummy6 = dummy6.dropna()

frames = [dummy1, dummy2]
result = pd.concat(frames)

#REGRESSION BEGINS FROM HERE

#Assiginig values to the x and y varaibles for the regression model
X1 = dummy6.ix[:,1:]
#X2 = dummy2.ix[:,1:]
#X2 = dummy1.ix[:,2:] #for left load
#X1 = X1.drop(X1.index[delete_rows])
#y = wd_v2[['resultant Lforce', 'resultant Rforce']]
y1 = dummy6['resultant Lforce']
#y2 = dummy1['Total load']
#y2 = dummy2['Total load']
#y2 = dummy1['resultant Lforce'] #for left load
#y1 = y1.drop(y1.index[delete_rows])

#print(len(X1), len(y1))

train_lf_accuracy = []
test_lf_accuracy = []
train_rf_accuracy = []
test_rf_accuracy = []
train_accuracy = []
test_accuracy = []
train_accuracy_lfload = []

for i in range(1):
    
    #lf_columns = []
    #rf_columns = []
    h_columns = []
    
    #lf_columns.append(i)
    #rf_columns.append(j)
    h_columns = total_columns
    
    #single_column = []
    #single_column.append(i)
    
    X = X1[h_columns]
    #X = np.array(X)
    y = y1
    #X_left = X2[h_columns]
    #y_left = y2    
    
    #X_lfload = X2[h_columns]
    #y_lfload = y2
    
    #creating test and training data sets
    #X_train = X_neutral
    #y_train = y_neutral
    #X_test = X_left
    #y_test = y_left
    #X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = 42)
    #count_lf_train = X_train[['lfoot count']]
    #count_lf_test = X_test[['lfoot count']]
    #robust_scaler = RobustScaler()
    #X_lf_train = pd.DataFrame(robust_scaler.fit_transform(X_train[lf_columns]), columns = lf_columns)
    #X_lf_test = pd.DataFrame(robust_scaler.fit_transform(X_test[lf_columns]), columns = lf_columns)
    #X_lf_train = X_train[lf_columns]
    #X_lf_test = X_test[lf_columns]
    #y_lf_train = y_train.ix[:,0]
    #y_lf_test = y_test.ix[:,0]
    #count_rf_train = X_train[['rfoot count']]
    #count_rf_test = X_test[['rfoot count']]
    #X_rf_train = pd.DataFrame(robust_scaler.fit_transform(X_train[rf_columns]), columns = rf_columns)
    #X_rf_test = pd.DataFrame(robust_scaler.fit_transform(X_test[rf_columns]), columns = rf_columns)
    #X_rf_train = X_train[rf_columns]
    #X_rf_test = X_test[rf_columns]
    #y_rf_train = y_train.ix[:,1]
    #y_rf_test = y_test.ix[:,1]

# In[]:

#correlation matrices left foot
#lf_corr = np.corrcoef(X_lf_test.values.T, y_lf_test.values.T)

#correlation matrices right foot
#rf_corr = np.corrcoef(X_rf_test.values.T, y_rf_test.values.T)

# In[]:

#Checking if the counts match for each foot
#c = 0
#d = 0
#c = count_lf_test.values
#d = count_rf_test.values
#print(c)
#for i in range(len(c)):
#    if c[i] != d[i]:
#        print('NOT EQUAL!')
#        
#c = 0
#d = 0
#c = count_lf_train.values
#d = count_rf_train.values
#print(c)
#for i in range(len(c)):
#    if c[i] != d[i]:
#        print('NOT EQUAL!')

# In[]:
    
    #GRADIENT BOOSTING REGRESSOR
    params = {'n_estimators': 1000, 'max_depth': 4, 'min_samples_split': 1,
          'learning_rate': 0.01, 'loss': 'lad'}
    slr = GradientBoostingRegressor(**params)
    
    #KNN REGRESSOR
    #slr = KNeighborsRegressor(n_neighbors = 30, weights = 'distance', algorithm = 'auto', p = 1, n_jobs = -1)
    
    #RADIUS NEIGHBHORS REGRESSOR
    #slr = RadiusNeighborsRegressor(radius = 1.0, weights = 'distance', algorithm = 'auto', n_jobs = -1)    
    
    #GRID SEARCH FOR GRADIENT BOOSTING REGRESSOR
    #n_estimators_range = [100,500,1000,1500,2000]
    #max_depth_range = [3,4,5,7,10,12,15]
    #min_samples_split_range = [1,2,3,4,5,6,7,8,9,10]
    #min_samples_leaf_range = [1,2,3,4,5,6,7,8,9,10]
    #learning_rate_range = [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0]
    
    #param_grid = {"loss": ["ls", "lad"]}
    #              "learning_rate:" [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0],
    #              "n_estimators:" [100, 500, 1000, 1500, 2000],
    #              "min_samples_split:" [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    #              "min_samples_leaf:" [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
                  
    #gs = GridSearchCV(estimator = slr, param_grid = param_grid, cv = 10, n_jobs = -1)
    
    #gs = gs.fit(X,y) 

    #break         

    #y_lf_train_pred = cross_val_predict(slr, X_lf_train, y_lf_train, cv=10)
    #y_lf_test_pred = cross_val_predict(slr, X_lf_test, y_lf_test, cv=10)
    
    #when using total load only
    #y_train_pred = cross_val_predict(slr, X_train, y_train, cv=10)
    #y_test_pred = cross_val_predict(slr, X_test, y_test, cv=10)
    #no test and training data sets
    y_pred = cross_val_predict(slr, X, y, cv = 10)
    #y_pred_lfload = cross_val_predict(slr, X_lfload, y_lfload, cv = 10)
    

    #RIGHT FOOT

    #y_rf_train_pred = cross_val_predict(slr, X_rf_train, y_rf_train, cv=10)
    #y_rf_test_pred = cross_val_predict(slr, X_rf_test, y_rf_test, cv=10)
  
    #Determining the weight distribution

    #Actual weight distribution
    #Training set
    #wd_lf_train = (np.array(y_lf_train)/(np.array(y_lf_train) + np.array(y_rf_train)))*100
    #wd_rf_train = (np.array(y_rf_train)/(np.array(y_lf_train) + np.array(y_rf_train)))*100
    #test set
    #wd_lf_test = (np.array(y_lf_test)/(np.array(y_lf_test) + np.array(y_rf_test)))*100
    #wd_rf_test = (np.array(y_rf_test)/(np.array(y_lf_test) + np.array(y_rf_test)))*100

    #Predicted weight distribution
    #Training set
    #wd_lf_train_pred = (np.array(y_lf_train_pred)/(np.array(y_lf_train_pred) + np.array(y_rf_train_pred)))*100
    #wd_rf_train_pred = (np.array(y_rf_train_pred)/(np.array(y_lf_train_pred) + np.array(y_rf_train_pred)))*100
    #test set
    #wd_lf_test_pred = (np.array(y_lf_test_pred)/(np.array(y_lf_test_pred) + np.array(y_rf_test_pred)))*100
    #wd_rf_test_pred = (np.array(y_rf_test_pred)/(np.array(y_lf_test_pred) + np.array(y_rf_test_pred)))*100

    #Determining the accuracy of the model
    thresh = 0.04 #predicted value within +/- x% of the actual value
    #thresh_wd = 2.0
    
    #y_lf_train = np.array(y_lf_train)
    #y_rf_train = np.array(y_rf_train)
    #y_lf_test = np.array(y_lf_test)
    #y_rf_test = np.array(y_rf_test)
    
    #only when using the total load as the target variable    
    #y_test = np.array(y_test)
    #y_train = np.array(y_train)
    y = np.array(y)
    #y_lfload = np.array(y_lfload)
    
    #TESTING THE ACCURACY OF REGRESSION MODEL
    
    #testing the accuracy when using the weight distribution as the target variable
    #Training set
    count = 0
    for k in range(len(y)):
        thresh_train = 0
        thresh_train = abs(thresh*y[k])
        if abs(abs(y[k])-abs(y_pred[k])) <= thresh_train: #and abs(y_train[k]-y_train_pred[k]) < thresh:
            count = count + 1
    
    #print('Training set score: %.3f' %((count/len(wd_lf_train))*100))
    train_accuracy.append((count/len(y))*100)
    #Test set
    #count = 0
    #for k in range(len(y_test)):
    #    thresh_test = 0
    #    thresh_test = abs(thresh*y_test[k])
    #    if abs(abs(y_test[k])-abs(y_test_pred[k])) <= thresh_test: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        count = count + 1
    
    #print('Training set score: %.3f' %((count/len(wd_lf_train))*100))
    #test_accuracy.append((count/len(y_test))*100)
    #Training set for left load
    #count_lfload = 0
    #for k_lfload in range(len(y_lfload)):
    #    thresh_train = 0
    #    thresh_train = abs(thresh*y_lfload[k_lfload])
    #    if abs(abs(y_lfload[k_lfload])-abs(y_pred_lfload[k_lfload])) <= thresh_train: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        count_lfload = count_lfload + 1
    
    #print('Training set score: %.3f' %((count/len(wd_lf_train))*100))
    #train_accuracy_lfload.append((count_lfload/len(y_lfload))*100)
    #Test set
    #count = 0
    #for k in range(len(y_test)):
        #thresh_train = 0
        #thresh_train = abs(thresh*y_lf_train[k])
    #    if abs(y_test[k])-abs(y_test_pred[k]) < thresh: #and abs(y_train[k]-y_train_pred[k]) < thresh:
            #count = count + 1
    
    #print('Training set score: %.3f' %((count/len(wd_lf_train))*100))
    #test_accuracy.append((count/len(y_test))*100)
    
    #Testing when the load is the target variable
    #Training set
    #Left foot
    #count = 0
    #for k in range(len(y_lf_train)):
    #    thresh_train = 0
    #    thresh_train = abs(thresh*y_lf_train[k])
    #    if abs(y_lf_train[k])-abs(y_lf_train_pred[k]) < thresh_train: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        count = count + 1
    
    #print('Training set score: %.3f' %((count/len(wd_lf_train))*100))
    #train_lf_accuracy.append((count/len(y_lf_train))*100)
    #Right foot
    #count = 0
    #for k in range(len(y_rf_train)):
    #    thresh_train = 0
    #    thresh_train = abs(thresh*y_rf_train[k])
    #    if abs(y_rf_train[k])-abs(y_rf_train_pred[k]) < thresh_train: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        count = count + 1
    
    #print('Training set score: %.3f' %((count/len(wd_lf_train))*100))
    #train_rf_accuracy.append((count/len(y_rf_train))*100)
    
    #Test set
    #Left foot
    #count = 0
    #for l in range(len(y_lf_test)):
    #    thresh_test = 0
    #    thresh_test = abs(thresh*y_lf_test[l])
    #    if abs(y_lf_test[l])-abs(y_lf_test_pred[l]) < thresh_test:# and abs(y_rf_test[l]-y_rf_test_pred[l]) < thresh:
    #        count = count + 1
        
    #print('Test set score: %.3f' %((count/len(wd_lf_test))*100))
    #test_lf_accuracy.append((count/len(y_lf_test))*100)
    #Right foot
    #count = 0
    #for l in range(len(y_rf_test)):
    #    thresh_test = 0
    #    thresh_test = abs(thresh*y_rf_test[l])
    #    if abs(y_rf_test[l])-abs(y_rf_test_pred[l]) < thresh_test:# and abs(y_rf_test[l]-y_rf_test_pred[l]) < thresh:
    #        count = count + 1
        
    #print('Test set score: %.3f' %((count/len(wd_lf_test))*100))
    #test_rf_accuracy.append((count/len(y_rf_test))*100)
    
    #COMPENSATING FOR THE DEFICIT/EXTRA LOAD TO DETERMINE A BETTER ACCUACY WITH WD
    #Training set
    #Left foot
    #new_y_lf_train = []
    #for k in range(len(y_lf_train)):
    #    if abs(y_lf_train[k])-abs(y_lf_train_pred[k]) > 0: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        new_y_lf_train.append(y_lf_train_pred[k] - (y_lf_train[k]*0.10))
    #    elif abs(y_lf_train[k])-abs(y_lf_train_pred[k]) < 0: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        new_y_lf_train.append(y_lf_train_pred[k] + (y_lf_train[k]*0.10))
    #Right foot
    #new_y_rf_train = []
    #for k in range(len(y_rf_train)):
    #    if abs(y_rf_train[k])-abs(y_rf_train_pred[k]) > 0: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        new_y_rf_train.append(y_rf_train_pred[k] - (y_rf_train[k]*0.10))
    #    elif abs(y_rf_train[k])-abs(y_rf_train_pred[k]) < 0: #and abs(y_train[k]-y_train_pred[k]) < thresh:
    #        new_y_rf_train.append(y_rf_train_pred[k] + (y_rf_train[k]*0.10))
            
    #DETERMINING THE WEIGHT DISTRIBUTION
    #Training set
    #wd_lf_train = (np.array(y_lf_train)/(np.array(y_lf_train) + np.array(y_rf_train)))*100
    #wd_rf_train = (np.array(y_rf_train)/(np.array(y_lf_train) + np.array(y_rf_train)))*100
    #wd_lf_train_pred = (np.array(new_y_lf_train)/(np.array(new_y_lf_train) + np.array(new_y_rf_train)))*100
    #wd_rf_train_pred = (np.array(new_y_rf_train)/(np.array(new_y_lf_train) + np.array(new_y_rf_train)))*100
    
    #count = 0
    #for x in range(len(wd_lf_train)):
    #    if abs(wd_lf_train[x] - wd_lf_train_pred[x]) < thresh_wd:
    #        count = count + 1
            
    #train_accuracy.append(((count/len(wd_lf_train))*100))
            
    #checking for the accuracy of the weight distribution
    #actual weight distribution
    #wd_actual = [ ((j/i)*100) for i,j in zip(y,y_lfload) ]
    #wd_pred = [ ((j/i)*100) for i,j in zip(y_pred,y_pred_lfload) ]

# In[]:

#plotting the smoothened predicted value over the un-smoothened actual data
#print(len(y_test_pred), len(dummy2_true))
#dummy2_true = dummy2_true.drop(range(15600,15615))
#dummy2_true = dummy2_true.drop(range(21386, 21400))
#print(len(dummy2_true))

#h = np.array(dummy2_true['Total load'])

#tacc = []

#count = 0
#for k in range(len(h)):
#    thresh_test = 0
#    thresh_test = abs(thresh*h[k])
#    if abs(abs(h[k])-abs(y_test_pred[k])) <= thresh_test: #and abs(y_train[k]-y_train_pred[k]) < thresh:
#        count = count + 1
    
#print('Training set score: %.3f' %((count/len(wd_lf_train))*100))
#tacc.append((count/len(y_test_pred))*100)

# In[]:

#determing sum of the load during an activity
#sum_actual = 0
#sum_pred = 0

#sum_actual = np.sum(-y)
#sum_pred = np.sum(-y_pred)
#pdiff = (abs(sum_actual - sum_pred)/sum_actual)*100

# In[]:

#plotting the true load without smoothening
#plt.figure(6)
#plt.plot(range(len(dummy6_true['Total load'])), -dummy6_true['Total load'])
#plt.show()

# In[]:

#checking the accuracy by smoothening the predicted values as well
#y_pred_df = pd.DataFrame()
#y_pred_df['predicted values'] = y_pred
#y_pred_df = pd.rolling_mean(y_pred_df, 30, center = True)
#y_pred_df = y_pred_df.dropna()
#y_pred_df = np.array(y_pred_df)

#count = 0
#for k in range(len(y)):
#    thresh_train = 0
#    thresh_train = abs(thresh*y[k])
#    if abs(abs(y[k])-abs(y_pred_df[k])) <= thresh_train: #and abs(y_train[k]-y_train_pred[k]) < thresh:
#        count = count + 1
#    if k == 9678:
#        break
    
#train_accuracy_smooth = []
#train_accuracy_smooth.append((count/len(y_pred_df))*100)

#plottig the actual vs. predicted weight distribution
#plt.figure(6)
#plt.plot(range(len(y)), -y)
#plt.plot(range(len(y_pred_df)), -y_pred_df)
#plt.legend(['Actual', 'Predicted'])
#plt.show()
    
# In[]:
    
#plottig the actual vs. predicted weight distribution
#plt.figure(6)
#plt.plot(range(len(wd_actual)), wd_actual)
#plt.plot(range(len(wd_pred)), wd_pred)
#plt.legend(['Actual', 'Predicted'])
#plt.show()

# In[]:

#checking the accuracy of the weight dsitribution
#count = 0
#thresh_wd = 2.0
#for x in range(len(wd_actual)):
#    if abs(wd_actual[x] - wd_pred[x]) <= thresh_wd:
#        count = count + 1
        
#wd_accuracy = []
#wd_accuracy.append((count/len(wd_actual))*100)
#print('Weight dsitribution accuracy: ')
#print(wd_accuracy) 
   
# In[]:
    
#print(min(y_train), min(y_train_pred))
#print(max(y_train), max(y_train_pred))

#print(min(y_test), min(y_test_pred))
#print(max(y_test), max(y_test_pred))

# In[]:

#plt.figure(1)
#plt.scatter(X1['HAccZ'], y1)
#plt.scatter(range(len(y_train_pred)), y_train_pred)
#plt.title('training set')
#plt.show()

#plt.figure(2)
#plt.scatter(range(len(y_test)), y_test)
#plt.scatter(range(len(y_test_pred)), y_test_pred, color = 'red')
#plt.title('test set')
#plt.show()

# In[]:

#Plot the relationship of a feature with the target variable
#Left Foot
#Test set
#plt.figure(1)
#plt.scatter(X_lf_test[lf_columns], y_lf_test)
#plt.plot(X_lf_test, y_lf_test_pred, color='blue',
#         linewidth=3)
#plt.title('Left foot')
#plt.show()

#Right Foot
#Test set
#plt.figure(2)
#plt.scatter(X_rf_test[rf_columns], y_rf_test)
#plt.plot(X_rf_test, y_rf_test_pred, color='blue', linewidth=3)
#plt.title('Right foot')
#plt.show()

# In[]:

# Scatter matrix plot
sm = pd.DataFrame()
wd2 = X1
sm['resultant Lforce'] = y1
#sm['Total load'] = wd2['Total load']
sm['HAccX'] = wd2['HAccX']
sm['HAccY'] = wd2['HAccY']
sm['HAccZ'] = wd2['HAccZ']
#sm['HEulerX'] = wd2['HEulerX']
#sm['HEulerY'] = wd2['HEulerY']
#sm['HEulerZ'] = wd2['HEulerZ']
#sm ['LAccZ'] = wd2['left foot accz']
#sm['RAccZ'] = wd2['right foot accz']
#sm['wd right foot'] = wd2['wd right foot']
sm['right foot accx'] = wd2['right foot accx']
sm['right foot accy'] = wd2['right foot accy']
sm['right foot accz'] = wd2['right foot accz']
sm['left foot accx'] = wd2['left foot accx']
sm['left foot accy'] = wd2['left foot accy']
sm['left foot accz'] = wd2['left foot accz']

print(type(sm))

plt.figure(1)
scatter_matrix(sm, alpha = 0.2, figsize = (6,6), diagonal = 'kde')
plt.show()

#correlation matrix
#corr = np.corrcoef(y1.values.T, X.values.T)
corr_mat = 0
corr_mat = dummy2.corr(method = 'pearson')

# In[]:

plt.figure(3)
#plt.plot(X1['HAccZ']*10)
plt.plot(X1['left foot accz']*10)
plt.plot(y1)
#plt.plot(sm['Total load'])
plt.legend()
plt.xlabel('Index')
plt.ylabel('Load (N)')
#plt.title('Load (N) during double leg squats (left:neutral; right:left loading)')
plt.show()

# In[]:

#plot the regression line along with the scatter plot
plt.figure(4)
plt.scatter(X['HAccZ'], y)
plt.plot(X['HAccZ'], y_pred, color='blue', linewidth=3)
#plt.xlabel('HAccZ')
#plt.ylabel('Vertical Load (N)')
#plt.title('Regression line')
plt.show()

#plt.figure(5)
#plt.scatter(X['left foot accy'], y)
#plt.plot(X['left foot accy'], y_pred, color='blue', linewidth=3)
#plt.plot(range(len(X['right foot eulx'])), X['right foot eulx'])
#plt.plot(range(len(X['left foot eulx'])), X['left foot eulx'])
#plt.plot(range(len(X['HAccX'])), X['HAccX'])
#plt.plot(range(len(X['HAccY'])), X['HAccY'])
#plt.plot(range(len(X['HAccZ'])), X['HAccZ'])
#plt.show()

#plot the difference between actual-pred vs. the actual values
plt.figure(6)
#plt.plot(range(len(y)), X1['right foot accx'])
plt.plot(range(len(y)), abs(abs(y)-abs(y_pred)), color = 'black')
plt.plot(range(len(y)), y)
plt.plot(range(len(y)), y_pred)
#plt.plot(range(len(X['HAccX'])), X['HAccX']*10)
#plt.plot(range(len(X['HAccY'])), X['HAccY']*10)
#plt.plot(range(len(X['HAccZ'])), X['HAccZ']*10)
#plt.plot(range(len(X['right foot eulx'])), X['right foot eulx']*20)
#plt.plot(range(len(X['left foot eulx'])), X['left foot eulx']*20)
#plt.plot(range(len(X['HEulerY'])), X['HEulerY']*20)
#plt.xlabel('time')
#plt.ylabel('Vertical Load (N)')
#plt.title('Relationship betweent the actual and predicted load values')
#plt.legend(['Actual-Predicted', 'Actual', 'Predicted'])
plt.show()

# In[]:

#printing the sum of errors between the actual and predicted values
print(np.sum(abs(abs(y)-abs(y_pred)))/np.sum(abs(y)))

# In[]:

#c = 0
#c = lfoot_columns
#d = 0
#d = ola
#for i in d:
#    print(c[i])
    

#force determined through acceleration
#mass = 57
#g = 9.80665
#lfoot_predforce = []
#lfoot_vgrf = []
#
#for i in range(len(lfoot_laccz)):
#    lfoot_predforce.append(((mass*g) + (mass*lfoot_laccz[i])))
    
#for i in range(len(dblsquat_neutral)):
#    lfoot_vgrf.append(dblsquat_neutral['TotalFz'].ix[i])
#    lfoot_predforce.append(((mass*g) + (mass*dblsquat_neutral['LAccZ'].ix[i])))

#plt.figure(1)
#plt.plot(lfoot_vgrf)
#plt.plot(lfoot_predforce)
#plt.show()

# In[]:

#Determining the accuracy of the model
#thresh = np.arange(0,100,0.5)
#train_score = []
#test_score =[]
#
#for k in thresh:
#
#
#    #Training set
#    count = 0
#    for i in range(len(wd_lf_train)):
#        if abs(wd_lf_train[i]-wd_lf_train_pred[i]) < k and abs(wd_rf_train[i]-wd_rf_train_pred[i]) < k:
#            count = count + 1
#        
#    train_score.append((count/len(wd_lf_train))*100)
#
#    #Test set
#    count = 0
#    for i in range(len(wd_lf_test)):
#        if abs(wd_lf_test[i]-wd_lf_test_pred[i]) < k and abs(wd_rf_test[i]-wd_rf_test_pred[i]) < k:
#            count = count + 1
#        
#    test_score.append((count/len(wd_lf_test))*100)
#    
#plt.figure(1)
#plt.plot(thresh, train_score, thresh, test_score)
#plt.show()