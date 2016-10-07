# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 17:42:39 2016

@author: court
"""

# import relevant packages
import numpy as np
import quatOps as qo

"""
#########################################################################################
Conversions between quaternions and Euler angles, using embedded direction cosine matrices

Conceptual explanations to be given under:
https://sites.google.com/a/biometrixtech.com/wiki/home/preprocessing/anatomical/concepts
Further documentation of code to be given under:
https://drive.google.com/drive/folders/0Bzd7PD0NIJ7ZZmJ5aVRsUnVOZ3c
#########################################################################################
"""

#### Function that transforms quaternion into Euler angles, assuming ZYX config
def q2eul(q):
    a=2*q[0]**2-1+2*q[1]**2
    b=2*(q[1]*q[2]-q[0]*q[3])
    c=2*(q[1]*q[3]+q[0]*q[2])
    d=2*(q[2]*q[3]-q[0]*q[1])
    e=2*q[0]**2-1+2*q[3]**2
    phi=np.arctan2(d,e)
    C=c/np.sqrt(1-c**2)
    theta=-np.arctan(C)
    psi=np.arctan2(b,a)
    
    return phi,theta,psi
  
def eul2q(phi,theta,psi):

    a=np.cos(psi)*np.cos(theta)
    b=-np.sin(psi)*np.cos(phi)+np.cos(psi)*np.sin(theta)*np.sin(phi)
    c=np.sin(psi)*np.sin(phi)+np.cos(psi)*np.sin(theta)*np.cos(phi)
    d=np.sin(psi)*np.cos(theta)
    e=np.cos(psi)*np.cos(phi)+np.sin(psi)*np.sin(theta)*np.sin(phi)
    f=-np.cos(psi)*np.sin(phi)+np.sin(psi)*np.sin(theta)*np.cos(phi)
    g=-np.sin(theta)
    h=np.cos(theta)*np.sin(phi)
    k=np.cos(theta)*np.cos(phi)

    A=(a-e-k)/3
    B=(d+b)/3
    C=(g+c)/3
    D=(f-h)/3
    E=(d+b)/3
    F=(e-a-k)/3
    G=(h+f)/3
    H=(g-c)/3
    I=(g+c)/3
    J=(h+f)/3
    K=(k-a-e)/3
    L=(b-d)/3
    M=(f-h)/3
    N=(g-c)/3
    O=(b-d)/3
    P=(a+e+k)/3
    
    Q=np.array([[A,B,C,D],[E,F,G,H],[I,J,K,L],[M,N,O,P]])
    [D,V] = np.linalg.eig(Q)
    
#    print 'D'
#    print D
#    print 'Q'
#    print Q
#    print 'Eigenvectors'
#    print V
    i=np.argmax(D)
    
    q = V[:,i]
    q= [q[3],q[0],q[1],q[2]]
    
    return q