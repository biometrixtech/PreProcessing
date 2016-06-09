import pandas as pd
import peak_det
import numpy as np

def rel_peakdet(series, sens_location):
    
    sens_loc = ['hipdatabody', 'lfdatabody', 'rfdatabody']
    
    if sens_location == sens_loc[0]:
        maxtab_hip, mintab_hip = peak_det.peakdet(series['EulerY'],0.0003) #calling the peak detection function for the hip
        relpeak_mag_hip = [ [x,y] for x,y in zip(maxtab_hip[:,1], mintab_hip[:,1]) if abs(x-y) > 0.01 ] #setting the
        #threshold for the difference in magnitude of the consecutive peaks to 0.01. This will help us target the relevant peaks for the hip.
        #storing the magnitude in relpeak_mag_hip
        relpeak_pos_hip = [ [a,b] for a,x,b,y in zip(maxtab_hip[:,0], maxtab_hip[:,1], mintab_hip[:,0], mintab_hip[:,1]) if abs(x-y) > 0.01 ] #storing the positions
        #of the relevant peaks in repeak_pos_hip
        return relpeak_pos_hip
    elif sens_location == sens_loc[1]:
        maxtab_lfoot, mintab_lfoot = peak_det.peakdet(series['EulerX'],0.0003) #calling the peak detection function for the foot
        #relevant peaks for the foot and hip
        relpeak_mag_lfoot = [ [x,y] for x,y in zip(maxtab_lfoot[:,1], mintab_lfoot[:,1]) if abs(x-y) > 0.01 ] #setting the
        #threshold for the difference in magnitude of the consecutive peaks to 0.01. This will help us target the relevant peaks for the foot.
        #storing the magnitude in relpeak_mag_foot
        relpeak_pos_lfoot = [ [a,b] for a,x,b,y in zip(maxtab_lfoot[:,0], maxtab_lfoot[:,1], mintab_lfoot[:,0], mintab_lfoot[:,1]) if abs(x-y) > 0.01 ] #storing the positions
        #of the relevant peaks in repeak_pos_foot
        return relpeak_pos_lfoot
    else:
        maxtab_rfoot, mintab_rfoot = peak_det.peakdet(series['EulerX'],0.0003) #calling the peak detection function for the foot
        #relevant peaks for the foot and hip
        relpeak_mag_rfoot = [ [x,y] for x,y in zip(maxtab_rfoot[:,1], mintab_rfoot[:,1]) if abs(x-y) > 0.01 ] #setting the
        #threshold for the difference in magnitude of the consecutive peaks to 0.01. This will help us target the relevant peaks for the foot.
        #storing the magnitude in relpeak_mag_foot
        relpeak_pos_rfoot = [ [a,b] for a,x,b,y in zip(maxtab_rfoot[:,0], maxtab_rfoot[:,1], mintab_rfoot[:,0], mintab_rfoot[:,1]) if abs(x-y) > 0.01 ] #storing the positions
        #of the relevant peaks in repeak_pos_foot
        return relpeak_pos_rfoot
    
if __name__ == '__main__':
    subjects = ['\Subject3', '\Subject5', '\Subject6', '\Subject7']
    root = 'C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files'
    sens_loc = ['hipdatabody', 'lfdatabody', 'rfdatabody']
    
    #reading the data
    #data = pd.read_csv(root + i + i + '_' + j + '_set1.csv')
    data = pd.read_csv('C:\Users\Ankur\python\Biometrix\Data analysis\data exploration\data files\Subject5\Subject5_lfdatabody_set1.csv')
    data = data[data.Exercise != 1] #use only relevant data (when user is active)
    series = data[['EulerX', 'EulerY']].reset_index(drop=True) #re-indexing the data
    
    p = np.array(rel_peakdet(series, sens_loc[1])) #remember to change sens_loc[] if you're changing the datasets (hip, left foot, right foot)
    
 



