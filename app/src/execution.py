# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 10:23:44 2016

@author: Brian
"""

import numpy as np
import pandas as pd
import Data_Processing as prep
import Exercise_Filter as exer
import Phase_Detect as phase

class ObjectMismatchError(ValueError):
    pass

if __name__ == "__main__":
    pathip = ''
    pathrf = ''
    pathlf = ''
    
    hip = pd.read_csv(pathip)
    lfoot = pd.read_csv(pathlf)
    rfoot = pd.read_csv(pathrf)
    
    if len(hip) != len(lfoot) or len(hip) != len(rfoot):
        raise ObjectMismatchError
    
    cols = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ"]
    hipbf, hipsf, rfbf, rfsf, lfbf, lfsf, hipfinal, rffinal, lffinal = [[] for i in range(9)]
    iters = len(hip)
       
    hq0 = np.matrix([hip.ix[0,'qW_raw'], hip.ix[0,'qX_raw'], hip.ix[0,'qY_raw'], hip.ix[0,'qZ_raw']]) #t=0 quaternion
    hyaw_fix = prep.yaw_offset(hq0) #uses yaw offset function above to compute yaw offset quaternion
    hyfix_c = prep.QuatConj(hyaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
    
    lq0 = np.matrix([lfoot.ix[0,'qW_raw'], lfoot.ix[0,'qX_raw'], lfoot.ix[0,'qY_raw'], lfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    lyaw_fix = prep.yaw_offset(lq0) #uses yaw offset function above to compute yaw offset quaternion
    lyfix_c = prep.QuatConj(lyaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
        
    rq0 = np.matrix([rfoot.ix[0,'qW_raw'], rfoot.ix[0,'qX_raw'], rfoot.ix[0,'qY_raw'], rfoot.ix[0,'qZ_raw']]) #t=0 quaternion
    ryaw_fix = prep.yaw_offset(rq0) #uses yaw offset function above to compute yaw offset quaternion
    ryfix_c = prep.QuatConj(ryaw_fix) #uses quaternion conjugate function to return conjugate of yaw offset
           
    for i in range(iters):
        hipbod, hipsen = prep.FrameTransform(hip.ix[i,:], hyfix_c)
        lfbod, lfsen = prep.FrameTransform(lfoot.ix[i,:], lyfix_c)
        rfbod, rfsen = prep.FrameTransform(rfoot.ix[i,:], ryfix_c)       
        hipbf.append(hipbod[0,:])
        hipsf.append(hipsen[0,:])
        lfbf.append(lfbod[0,:]) 
        lfsf.append(lfsen[0,:])
        rfbf.append(rfbod[0,:]) 
        rfsf.append(rfsen[0,:])    

        ###how to deal with endpoints
        if len(hipbf) < hz*.4 + 1:
            if i%2 != 0:
                hipfinal.append(np.append(hipbf[int((i-1)/2)],-1.5))
            else:
                None
        else:
            data = pd.DataFrame(hipbf[int(i-hz*.4):i+1], columns=cols)
            hipfinal.append(np.append(hipbf[int(i-hz*.2)], exer.Exercise_Filter(data, 'Double', hz)))
        
        #####how to deal with endpoints
        if i < hz*.2:
            None
        else:
            ldata = pd.DataFrame(lfbf[int(i-hz*.2):i], columns=cols)
            rdata = pd.DataFrame(rfbf[int(i-hz*.2):i], columns=cols)
            indic = phase.Phase_Detect(ldata, rdata, hz)
            lffinal.append(np.append(lfbf[int(i-hz*.2)],indic))
            rffinal.append(np.append(rfbf[int(i-hz*.2)],indic))

    hipcols = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ","Exercise"]
    ftcols = ["qW", "qX", "qY", "qZ", "EulerX", "EulerY", "EulerZ", "AccX", "AccY", "AccZ", "gyrX", "gyrY", "gyrZ", "magX", "magY", "magZ","Phase"]
    hipdata = pd.DataFrame(hipfinal, columns = hipcols)
    lfdata =  pd.DataFrame(lffinal, columns = ftcols)  
    rfdata = pd.DataFrame(rffinal, columns = ftcols)   






