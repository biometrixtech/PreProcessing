import numpy as np
import pandas as pd

def stab_score(rel_peakpos, sens_location):
    
    sens_loc = ['hipdatabody', 'lfdatabody', 'rfdatabody']
    
    sampling_rate = 250 #sampling rate (Hz)

    #declaring threshold variables
    thresh_lfoot = 250
    thresh_rfoot = 300
    thresh_hip = 350
    
    if sens_location == sens_loc[0]:
        time_elapse_hip = abs(rel_peakpos[:,1] - rel_peakpos[:,0])/sampling_rate*1000 #determining the time elapsed (in ms) between the consecutive relevant peaks
        utime_elapse_hip =  np.unique(time_elapse_hip, return_counts=True) #determining the unique time elapses and corresponding counts 
        #(these variables will be used for the time-elapsed frequency plot)

        #filtering the time elapses based on a threshold (thresholds vary for the hip and the foot)
        rel_utime_ehip = np.array([ [x,y] for x,y in zip(utime_elapse_hip[0],utime_elapse_hip[1])  if x <= thresh_hip]) #setting the threshold for the time elapse
        #to be 350ms for the left foot. 

        #score
        dummy_score = []
        dummy_score.append([[((thresh_hip - i)/thresh_hip)*j] for i,j in zip(rel_utime_ehip[:,0], rel_utime_ehip[:,1])])
        score_hip = np.sum(dummy_score)/np.sum(rel_utime_ehip[:,1])        
        return score_hip
    elif sens_location == sens_loc[1]:
        time_elapse_lfoot = abs(rel_peakpos[:,1] - rel_peakpos[:,0])/sampling_rate*1000 #determining the time elapsed (in ms) between the consecutive relevant peaks
        utime_elapse_lfoot =  np.unique(time_elapse_lfoot, return_counts=True) #determining the unique time elapses and corresponding counts 
        #(these variables will be used for the time-elapsed frequency plot)

        #filtering the time elapses based on a threshold (thresholds vary for the hip and the foot)
        rel_utime_elfoot = np.array([ [x,y] for x,y in zip(utime_elapse_lfoot[0],utime_elapse_lfoot[1])  if x <= thresh_lfoot]) #setting the threshold for the time elapse
        #to be 350ms for the left foot. 

        #score
        dummy_score = []
        dummy_score.append([[((thresh_lfoot - i)/thresh_lfoot)*j] for i,j in zip(rel_utime_elfoot[:,0], rel_utime_elfoot[:,1])])
        score_lfoot = np.sum(dummy_score)/np.sum(rel_utime_elfoot[:,1])
        return score_lfoot
    else:
        time_elapse_rfoot = abs(rel_peakpos[:,1] - rel_peakpos[:,0])/sampling_rate*1000 #determining the time elapsed (in ms) between the consecutive relevant peaks
        utime_elapse_rfoot =  np.unique(time_elapse_rfoot, return_counts=True) #determining the unique time elapses and corresponding counts 
        #(these variables will be used for the time-elapsed frequency plot)

        #filtering the time elapses based on a threshold (thresholds vary for the hip and the foot)
        rel_utime_erfoot = np.array([ [x,y] for x,y in zip(utime_elapse_rfoot[0],utime_elapse_rfoot[1])  if x <= thresh_rfoot]) #setting the threshold for the time elapse
        #to be 350ms for the left foot. 

        #score
        dummy_score = []
        dummy_score.append([[((thresh_rfoot - i)/thresh_rfoot)*j] for i,j in zip(rel_utime_erfoot[:,0], rel_utime_erfoot[:,1])])
        score_rfoot = np.sum(dummy_score)/np.sum(rel_utime_erfoot[:,1])
        return score_rfoot
        
if __name__ == '__main__':
    import rel_peakdet
    
    subjects = ['\Subject3', '\Subject5', '\Subject6', '\Subject7']
    root = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files'
    sens_loc = ['hipdatabody', 'lfdatabody', 'rfdatabody']
    
    #reading the data
    #data = pd.read_csv(root + i + i + '_' + j + '_set1.csv')
    data = pd.read_csv('C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject7\Subject7_rfdatabody_set1.csv')
    data = data[data.Exercise != 1] #use only relevant data (when user is active)
    series = data[['EulerX', 'EulerY']].reset_index(drop=True) #re-indexing the data
    
    p = np.array(rel_peakdet.rel_peakdet(series, sens_loc[2])) #remember to change sens_loc[] if you're changing the datasets (hip, left foot, right foot)
    
    score = stab_score(p, sens_loc[2]) #remember to change sens_loc[] if you're changing the datasets (hip, left foot, right foot)
            




