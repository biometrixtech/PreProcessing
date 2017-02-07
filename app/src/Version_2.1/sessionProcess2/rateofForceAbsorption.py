# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 08:01:53 2016

@author: ankurmanikandan
"""

import numpy as np

from phaseID import phase_id


def det_rofa(lf_imp, rf_imp, laccz, raccz, user_mass, hz):
    '''
    Determine rate of force absorption.
    
    Args:
        lf_imp: 2d array, start and end indices of impact phase, left foot
        rf_imp: 2d array, start and end indices of impact phase, right foot
        laccz: array, left foot vertical acceleration
        raccz: array, right foot vertical acceleration
        user_mass: float, mass of the user in kg
        hz: int, sampling rate
        
    Returns:
        lf_rofa: array, rate of force absorption left foot
        rf_rofa: array, rate of force absorption right foot
    '''
    
#    # determine the start and end of impact phase for left & right feet
#    lf_start_imp, lf_end_imp = _bound_det(ph=l_ph, lf_or_rf='lf')
#    del l_ph  # not used in further computations
#    rf_start_imp, rf_end_imp = _bound_det(ph=r_ph, lf_or_rf='rf')
#    del r_ph  # not used in further computations
    
    # determine rate of force absorption for left & right feet
    if len(lf_imp) != 0:
        lf_rofa = _det_lf_rf_rofa(accz=abs(laccz), s_imp=lf_imp[:, 0], 
                                  e_imp=lf_imp[:, 1], mass=user_mass, hz=hz)
    else:
        lf_rofa = np.zeros((len(laccz), 1))*np.nan
        
    # delete variables that are not used in further computations
    del lf_imp, laccz

    if len(rf_imp) != 0:
        rf_rofa = _det_lf_rf_rofa(accz=abs(raccz), s_imp=rf_imp[:, 0], 
                                  e_imp=rf_imp[:, 1], mass=user_mass, hz=hz) 
    else:
        rf_rofa = np.zeros((len(raccz), 1))*np.nan
        
    # delete variables that are not used in further computations
    del rf_imp, raccz
    
    return lf_rofa, rf_rofa
    

#def _bound_det(ph, lf_or_rf):
#    '''
#    Determine the start and end if each impact phase.
#    
#    Args:
#        ph: array, left/right foot phase
#        lf_or_rf: string, indicates whether boundaries are being determined 
#        for left/right foot
#        
#    Returns:
#        start_imp: array, start of an impact
#        end_imp: array, end of an impact
#    '''
#    
#    start_imp = []
#    end_imp = []
#    
#    if lf_or_rf == 'lf':
#        imp_value = phase_id.lf_imp.value
#    else:
#        imp_value = phase_id.rf_imp.value
#        
#    for i in range(len(ph)-1):
#        if i == 0 and ph[i] == imp_value:
#            start_imp.append(i)
#        elif ph[i] != imp_value and ph[i+1] == imp_value:
#            start_imp.append(i+1)
#        elif ph[i] == imp_value and ph[i+1] != imp_value:
#            end_imp.append(i)
#        elif i+1 == len(ph)-1 and ph[i+1] == imp_value:
#            end_imp.append(i+1)
#            
#    return np.array(start_imp), np.array(end_imp)
    
    
def _det_lf_rf_rofa(accz, s_imp, e_imp, mass, hz):
    '''
    Determine rate of force absorption.
    
    Args:
        accz: array, absolute vertical acceleration left/right foot 
        s_imp: array, start of impact phases
        e_imp: array, end of impact phases
        mass: float, mass of user in kg
        hz: int, sampling rate
        
    Returns:
        rofa: array, rate of force absorption
    '''
    
    rofa = np.zeros((len(accz), 1))*np.nan
    
    for i, j in zip(s_imp, e_imp):
        num = np.max(accz[i:j])  # maximum force during impact
        length_subset_acc = len(accz[i:i+np.argmax(accz[i:j])])
        if length_subset_acc != 0:
            denom = float(length_subset_acc)/hz  # time
            # taken from start of an impact to peak force
        elif length_subset_acc == 0:
            denom = 1.0/hz
        rofa[i,0] = num/denom
                
    return rofa*mass
    

if __name__ == '__main__':
    
    import pickle
    import time
    from phaseDetection import combine_phase
    
    file_name = 'Ivonna_Combined_Sensor_Transformed_Data.csv'
    data = np.genfromtxt(file_name, names=True, dtype=float, delimiter=',')
    
    # convert numpy ndarray to rec array
    data_rec_array = data.view(np.recarray)
    
    # sampling rate
    sampl_rate = 125
    
    # user mass
    mass = 50
    
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
                              laccz=data['LaZ'], raccz=data['RaZ'], 
                              user_mass=mass, hz=sampl_rate)
    print 'time taken:', time.time() - s
    
    '''
    Dipesh, this should help you integrate rate of force absorption to the
    run analytics script.
    
    'det_rofa' is the function that you need to call in the run analytics 
    script.
    
    Inputs:
        lf_ph = left foot phase, flat array
        rf_ph = right foot phase, flat array
        laccz = left foot vertical acceleration, flat array
        raccz = right foot vertical acceleration, flat array
        user_mass = user mass in kg, float (you need to get the user mass
        from the user table using the uuid)
        hz = sampling rate, int
    '''
