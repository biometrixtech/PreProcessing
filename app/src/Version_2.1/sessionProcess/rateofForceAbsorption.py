# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 08:01:53 2016

@author: ankurmanikandan
"""

import numpy as np
from phaseDetection import combine_phase
from phaseID import phase_id
from mechStressTraining import prepare_data

def det_rofa(l_ph, r_ph, m_stress, hz):
    '''
    Determine rate of force absorption.
    
    Args:
        l_ph: array, left foot phase
        r_ph: array, right foot phase
        m_stress: array, total mechanical stress
        hz: int, sampling rate
        
    Returns:
        lf_rofa: array, rate of force absorption left foot
        rf_rofa: array, rate of force absorption right foot
    '''
    
    # determine the start and end of impact phase for left & right feet
    lf_start_imp, lf_end_imp = _bound_det(ph=l_ph, lf_or_rf='lf')
    rf_start_imp, rf_end_imp = _bound_det(ph=r_ph, lf_or_rf='rf')
    
    # determine rate of force absorption for left & right feet
    lf_rofa = _det_lf_rf_rofa(me_stress=m_stress, s_imp=lf_start_imp, 
                              e_imp=lf_end_imp, hz=hz)
    rf_rofa = _det_lf_rf_rofa(me_stress=m_stress, s_imp=rf_start_imp, 
                              e_imp=rf_end_imp, hz=hz)        
    
    return lf_rofa, rf_rofa
    

def _bound_det(ph, lf_or_rf):
    '''
    Determine the start and end if each impact phase.
    
    Args:
        ph: array, left/right foot phase
        lf_or_rf: string, indicates whether boundaries are being determined 
        for left/right foot
        
    Returns:
        start_imp: array, start of an impact
        end_imp: array, end of an impact
    '''
    
    start_imp = []
    end_imp = []
    
    if lf_or_rf == 'lf':
        imp_value = phase_id.lf_imp.value
    else:
        imp_value = phase_id.rf_imp.value
        
    for i in range(len(ph)-1):
        if ph[i] != imp_value and ph[i+1] == imp_value:
            start_imp.append(i+1)
        elif ph[i] == imp_value and ph[i+1] != imp_value:
            end_imp.append(i)
            
    return np.array(start_imp), np.array(end_imp)
    
    
def _det_lf_rf_rofa(me_stress, s_imp, e_imp, hz):
    '''
    Determine rate of force absorption.
    
    Args:
        me_stress: array, total mechanical stress
        s_imp: array, start of impact phases
        e_imp: array, end of impact phases
        hz: int, sampling rate
        
    Returns:
        rofa: array, rate of force absorption
    '''
    
    rofa = []
    
    for i, j in zip(s_imp, e_imp):
        num = np.max(me_stress[i:j])  # maximum force during impact
        length_subset_ms = len(me_stress[i:i+np.argmax(me_stress[i:j])])
        if length_subset_ms != 0:
            denom = float(length_subset_ms)/hz  # time
            # taken from start of an impact to peak force
        elif length_subset_ms == 0:
            denom = 1.0/hz
        rofa.append(num/denom)
        
    return np.array(rofa).reshape(-1, 1)
    

if __name__ == '__main__':
    
    import pickle
    import time
    
    file_name = 'Ivonna_Combined_Sensor_Transformed_Data.csv'
    data = np.genfromtxt(file_name, names=True, dtype=float, delimiter=',')
    
    # convert numpy ndarray to rec array
    data_rec_array = data.view(np.recarray)
    
    # sampling rate
    sampl_rate = 125
    
    # need to pass in phase to determine rate of force absorption during 
    # impacts
    lf_phase, rf_phase = combine_phase(laccz = data['LaZ'], 
                                       raccz = data['RaZ'], 
                                       hz = sampl_rate)
                                       
    # need to pass in mechanical stress as well (to determine the 'force')
    mech_stress_pkl_file = 'ms_trainmodel.pkl'
    with open(mech_stress_pkl_file) as model_file:
        mstress_fit = pickle.load(model_file)
#    mstress_fit = pickle.load(mech_stress_pkl_file)
    ms_data = prepare_data(data_rec_array, False)
    mech_stress = abs(mstress_fit.predict(ms_data).reshape(-1, 1))  # NOTE:
    # need to pass in only the absolute value of mechanical stress
    
    s = time.time()
    # determine rate of force absorption
    l_rofa, r_rofa = det_rofa(l_ph=lf_phase, r_ph=rf_phase, 
                              m_stress=mech_stress, hz=sampl_rate)
    print 'time taken:', time.time() - s