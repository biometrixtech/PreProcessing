import pandas as pd
import numpy as np
import stability_score
import rel_peakdet

if __name__ == '__main__':
    subjects = ['\Subject3', '\Subject5', '\Subject6', '\Subject7']
    root = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files'
    sens_loc = ['hipdatabody', 'lfdatabody', 'rfdatabody']
    
    #reading the data
    #data = pd.read_csv(root + i + i + '_' + j + '_set1.csv')
    data = pd.read_csv('C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv')
    data = data[data.Exercise != 1] #use only relevant data (when user is active)
    series = data[['EulerX', 'EulerY']].reset_index(drop=True) #re-indexing the data
    
    p = np.array(rel_peakdet.rel_peakdet(series, sens_loc[1])) #remember to change sens_loc[] if you're changing the datasets (hip, left foot, right foot)
    
    score = stability_score.stab_score(p, sens_loc[1]) #remember to change sens_loc[] if you're changing the datasets (hip, left foot, right foot)
    
    #print the stability score 
    #print score 



