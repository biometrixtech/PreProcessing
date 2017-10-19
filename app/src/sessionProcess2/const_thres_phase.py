#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 12:41:32 2017

@author: dipeshgautam
"""

hz = 100

#balance vs movement
cutoff_body = 10
order_body = 4
thresh = 1.7 # threshold to detect balance phase
bal_win = int(0.15*hz)  # sampling window to determine balance phase
min_thresh_mov = int(.1*hz)


#impact
g = 9.80665
neg_thresh = -.5*g  # negative threshold
pos_thresh = .9*g  # positive threshold
win = int(0.05*hz)+1  # sampling window for impact detect
imp_len = int(0.08*hz) #impact length
end_imp_thresh = int(0.35*hz)
drop_thresh = 1.4*g
drop_win = 3
