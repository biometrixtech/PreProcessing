#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 12:41:32 2017

@author: dipeshgautam
"""

hz = 100

# filters
cutoff_acc = 35
order_acc = 4
cutoff_magn = 12
lowcut_pitch = 1
highcut_pitch = 40

#ground vs movement
thresh = 2.7 # threshold to detect balance phase
bal_win = int(0.12*hz)  # sampling window to determine balance phase
min_thresh_mov = int(.1*hz)



# takeoff
g = 9.80665
pos_thres_takeoff = .75 * g
neg_thres_takeoff = -.1 * g
jump_thres_takeoff = 1.5 * g


# in_air

min_air_time = int(0.16 * hz)

#impact
neg_thresh = -.45*g  # negative threshold
pos_thresh = .45*g  # positive threshold
jump_thresh = 1.25*g
win = int(0.06*hz)  # sampling window for impact detect
imp_len = int(0.12*hz) #impact length
end_imp_thresh = int(0.35*hz)
max_imp_length = int(0.35*hz)
drop_thresh = 0. * g
drop_win = 3
