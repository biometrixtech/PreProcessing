import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from itertools import islice
from phase_exploration import *
    
rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_rfdatabody_LESS.csv'
#rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Rheel_Gabby_changedirection_set1.csv'
#rpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Rheel_Gabby_walking_heeltoe_set1.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'   
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Stomp\Lheel_Gabby_stomp_set1.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\ChangeDirection\Lheel_Gabby_changedirection_set1.csv'
lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_LESS.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Jump\Lheel_Gabby_jumping_explosive_set2.csv'
#lpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Walking\Lheel_Gabby_walking_heeltoe_set1.csv'
#hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_set1.csv'
hpath = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_hipdatabody_LESS.csv'

rdata = pd.read_csv(rpath)
ldata = pd.read_csv(lpath)
hdata = pd.read_csv(hpath)

sampl_rate = 250

comp = 'AccZ'
ptch = 'EulerY'
racc = rdata[comp].values
lacc = ldata[comp].values #input AccZ values!
rpitch = rdata[ptch].values
lpitch = ldata[ptch].values
ph = Body_Phase(racc, lacc, rpitch, lpitch, sampl_rate)

rdata['Phase'] = ph
ldata['Phase'] = ph
hdata['Phase'] = ph 
#hdata['Phase'] = output
    
#sampl_rate = 250 #sampling rate, remember to change it when using data sets of different sampling rate
#w = int(0.5*sampl_rate)
#end_w = int(0.08*sampl_rate)
#start_imp = [] #stores the index of the start of the impact phase
#end_imp = []   #stores the index of the end of the impact phase 
#count = 0

az = ldata['AccZ'].values

plt.figure(1)
#plt.plot(ldata['AccX'])
#plt.plot(ldata['AccY'])
plt.plot(ldata['AccZ'])
plt.legend()
plt.show()  

#ALGORITHM TO DETECT THE IMPACT PHASE

g = 9.80665 
neg_thresh = -g/2
pos_thresh = g
win = int(0.1*sampl_rate)
start_imp = []
end_imp = []

numbers = iter(range(len(az)-win))

for i in numbers:
    if az[i] <= neg_thresh:
        for j in range(win):
            if az[i+j] >= pos_thresh:
                start_imp.append(i)
                #end_imp.append(i+j)
                break
        next(islice(numbers, win, 1 ), None)
        
print start_imp#, end_imp
