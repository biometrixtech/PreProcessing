# pylint: disable=C0326


import numpy as np
from scipy.signal import butter as _butter, find_peaks as _find_peaks

from utils.quaternion_operations import hamilton_product, quat_conjugate, quat_interp
from utils.quaternion_conversions import quat_as_euler_angles, quat_from_euler_angles
from utils.signal_processing import mfiltfilt, myfft, all_sensors_todd_andrews_adaptive_v6


__author__ = "Daniele Comotti and Giorgio Barzon"
__copyright__ = "Copyright 2019, 221e s.r.l."
__credits__ = ["Daniele Comotti", "Giorgio Barzon", "Francesco Galizzi"]
__version__ = "1.6.0"
__maintainer__ = "Giorgio Barzon"
__email__ = "giorgio.barzon@221e.com"
__license__ = """
Copyright (c) 2019, 221e srl All rights reserved.


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


def sensors_drift_correction(op_cond, axl_refCH, q_refCH, parameters, Foot):
    """
    Correction drift function for a single foot sensor data.

    Parameters
    ----------
    op_cond : array_like
        Dynamic to static index.
    axl_refCH : array_like
        Accelerations heading corrected.
    q_refCH : array_like
        Orientations heading corrected.
    parameters: array_like
        Thresholds specific of each sensor     
    Foot : logic_value
        Define foot or hip sensor     

    Returns
    -------
    q_refCH : array_like
        Orientations drift corrected.
    """
    op_cond = np.asanyarray(op_cond)
    q_refCH = np.copy(q_refCH)

    # Sampling frequency
    fs = 100
    # Data length
    n = op_cond.size
    # Axl filter parameters- cutoff frequencies [Hz]
    f_cut_low = parameters[0]
    f_cut_high = parameters[1]
    ## FFT double peak control parameters
    #FFT samples
    fft_num_samples = parameters[2]
    # Threshold to discard double of fundamental frequency peak
    epsilon = parameters[3]
    # Threshold to consider max frequency valid peaks
    Max_fq = parameters[4]
    # Window enlarging factor
    fac = parameters[5]
    # Factor scaling on Max FFT
    scaling_fac = parameters[6]
    # Troughs discarding thresholds, on the basis of avg axl value of the dynamic window troughs position
    avg_troughs_max_TH = parameters[7]
    avg_troughs_min_TH = parameters[8]
    ## Correction thresholds
    #Number of troughs found after which begin to correct
    corr_point_threshold = parameters[9]
    # Treshold on pitch and roll and yaw to manage jumps in q_delta in rhythm changes [deg]
    tilt_th_pitch = parameters[10]
    tilt_th_roll = parameters[11]
    yaw_th = parameters[15]
    ## Todd Andrews hip input threshold
    # scaling on amplitude
    s_ampl = parameters[12]
    # scaling on number of samples
    s_sampl = parameters[13]
    tilt_discard_th = parameters[14]
    
    if Foot:
        # Band Pass filtering on Axl magnitude
       axl_norm_f = np.linalg.norm(axl_refCH, axis=1)
    else:
        # Use only y-axl for hip
       axl_norm_f = axl_refCH
       
    bl, al = _butter(1, f_cut_low, "lowpass", fs=fs)
    bh, ah = _butter(1, f_cut_high, "highpass", fs=fs)
    axl_norm_f[:] = mfiltfilt(bl, al, axl_norm_f)
    axl_norm_f[:] = mfiltfilt(bh, ah, axl_norm_f)

    # Initialize for tresholds and global vectors
    # Beginning of the current operating condition within the dataset
    start_op_cond = 0
    # Peaks and troughs found
    all_corr_points = []
    all_candidate_corr_points = []

    # Backward correction points
    backward_points = []

    # Frequency and amplitude of the current peak found (FFT)
    freq_peak = np.zeros(n)
    height_peak = np.zeros(n)
    # Marker changing rhythm
    marker_fft = np.zeros(n)

    # Quaternion initialization
    # Corrected quaternion (eventually overwrited in different sections)
    q_corr = np.copy(q_refCH)
    # Orientation jumps between two consecutive troughs
    q_delta = np.zeros((n, 4))
    q_delta[:,0] = 1
    q_delta2=np.copy(q_delta)

    # Initialization
    short_static_found = False
    jumplastsample = True

    # Iteration through the dataset - i is the index pointing at the end of a dynamic condition window
    for i in range(1, n):
        # Search for the beginning of an operating condition
        if op_cond[i - 1] == 0 and op_cond[i] == 1 and not short_static_found:
            start_op_cond = i

        if i == n - 1 and i - start_op_cond > fft_num_samples:
            jumplastsample = False

        if (op_cond[i - 1] != 1 or op_cond[i] != 0) and jumplastsample:
            continue
        # Found dynamic condition window - i points to the end of the dynamic operating condition

        # Managing short static phases
        op_cond_down_TH = 19
        op_cond_down_count = 1
        last_up = i - 1
        # Check if it's a long enough static
        h = i
        while h < min(i + 5*fs, n-1) and op_cond_down_count < op_cond_down_TH:
            h += 1
            if op_cond[h] == 0:
                op_cond_down_count += 1
            # Save extra windows quaternion, the last static window sample
            elif op_cond[h-1] == 0:
                # Save the last static sample, of many statics
                last_up = h

        # Manage and correct quaternion in short jumps cases
        short_static_found = (op_cond_down_count <= op_cond_down_TH and op_cond[h] == 1)
        if short_static_found:
            # Save the last static orientation, of many statics
            q_tmp_last = np.copy(q_refCH[last_up-1,:])
            # Initialize q_d
            q_d = np.array((1., 0., 0., 0.))
            last_stat = i
            for k in range(i, min(last_up, n-1)):
                if op_cond[k] == 0:
                    if op_cond[k+1] == 0: # Overwrite orientation
                        q_refCH[k,:] = q_refCH[k-1,:]
                    else:
                        last_stat = k # Save q_tmp before overwrite orientation
                        q_tmp = np.copy(q_refCH[last_stat-1,:])
                        # Compute q_d with any precedent q_d
                        q_d[:] = hamilton_product(hamilton_product(q_tmp, quat_conjugate(np.copy(q_refCH[last_stat,:]))), q_d)
                        q_refCH[k,:] = q_refCH[k-1,:] # Overwrite orientation
                else:
                    # Correct dynamics with q_d
                    q_refCH[k,:] = hamilton_product(q_d, q_refCH[k,:])
            # Find last delta quaternion to be applied in the remainent dynamic phase
            q_delta_corr = hamilton_product(q_refCH[last_stat,:], quat_conjugate(q_tmp_last))
            t = np.argwhere(op_cond[last_up:] != 1) + last_up
            t = np.amin(t) if t.size else n
            # Apply delta quaternion
            q_refCH[last_up:t,:] = hamilton_product(q_delta_corr, q_refCH[last_up:t,:])
            # Overwrite q_corr
            q_corr[i:t,:] = q_refCH[i:t,:]

        if (i - start_op_cond < fft_num_samples or short_static_found) and jumplastsample:
            continue
        # Found dynamic condition window - i points to the end of the dynamic operating condition
        # Reset current operating condition peaks/troughs
        corr_point_pos = []
        # FFT computation and peaks/troughs detection for each window
        # The first max peak within the FFT corresponds to the fundamental frequency
        for j in range(start_op_cond, i, fft_num_samples):
            if (j+fft_num_samples-1)<n:
                y, f, _ = myfft(axl_norm_f[j:j+fft_num_samples], fs)
                M=axl_norm_f[j:j+fft_num_samples].max();
                FFT_Peak_th=np.sqrt(M) * scaling_fac;
                # Fundamental frequency of the FFT
                peakfft_pos, _ = _find_peaks(y, height=FFT_Peak_th)
                peakfft_val = y[peakfft_pos]
                
                ## Control that the frequency is not too high (> FFT_Peak_th Hz), otherwise halve FFT_Peak_th threshold
                if peakfft_pos.size != 0 and f[peakfft_pos[0]]>Max_fq:
                    FFT_Peak_th/=2
                    peakfft_pos = []
                    peakfft_val = []
                    peakfft_pos, _ = _find_peaks(y, height=FFT_Peak_th)
                    peakfft_val = y[peakfft_pos] 
                    
                ## Control that there're not other significant and meningful peaks, linked to a sudden change of rhythm
                # Nr FFT peaks of interest counter
                count_peaks=1
                for h in range(0, peakfft_pos.size):
                    if f[peakfft_pos[h]]>0 and f[peakfft_pos[h]]<Max_fq:
                        # Control that it's not a multiple of fundamental frequency (so double, 3 times and (3/2) times between second and third )
                        if (h>0 and np.abs(f[peakfft_pos[h]]/f[peakfft_pos[h-1]]-2)>epsilon and np.abs(f[peakfft_pos[h]]/f[peakfft_pos[h-1]]-3)>epsilon and np.abs(f[peakfft_pos[h]]/f[peakfft_pos[h-1]]-1.5)>epsilon):
                            count_peaks+=1
                        ## If a second meaningful peak is found in FFT trigger the marker in an extended window centered on j 
                        if count_peaks==2:
                            if j>fac*fft_num_samples and j<n-fac*fft_num_samples:
                                marker_fft[j-fac*fft_num_samples:j+fac*fft_num_samples]=True
                              
                # FFT peak and frequency detection
                if peakfft_pos.size != 0:
                    # Frequency and peak
                    freq_peak = f[peakfft_pos[0]]
                    height_peak = round(peakfft_val[0] * 2 * np.sqrt(2))
                    # Todd-Andrews based on peak parameters with some margins
                    corr_point_pos_sw = all_sensors_todd_andrews_adaptive_v6(
                            axl_norm_f[j:j+fft_num_samples], height_peak/s_ampl,
                            int(round(fs/freq_peak*s_sampl)), op_cond[j:j+fft_num_samples],Foot)
                    if corr_point_pos_sw.size>0:
                        # Discard any outliers +/- avg of the dynamic window troughs position
                        _axl_troughs = axl_norm_f[corr_point_pos_sw+j]
                        avg_troughs = np.mean(_axl_troughs)
                        corr_point_pos_sw = corr_point_pos_sw[np.logical_and(avg_troughs_min_TH*avg_troughs <= _axl_troughs, _axl_troughs <= avg_troughs_max_TH*avg_troughs)]
                    
                        # Store all peaks/troughs
                        corr_point_pos.append(corr_point_pos_sw + j)

        if corr_point_pos:
            corr_point_pos = np.concatenate(corr_point_pos)
        else:
            corr_point_pos = np.array(())

        all_candidate_corr_points.append(corr_point_pos.astype(int))
        # Drift correction procedure
        if corr_point_pos.size > corr_point_threshold:
            # Discard any troughs which are close to the end of the dynamic window
            corr_point_pos = corr_point_pos[corr_point_pos <= i - 200]
            corr_point_pos = corr_point_pos.astype(int)

            # Manage wrong correction points ONLY IN HIP that cause tilt offset
            if not Foot:
                # remove correction points that are not close to left foot correction points
                corr_points_foot = parameters[16]
                corr_points_foot_sub = [t for t in corr_points_foot if start_op_cond < t < i]
                corr_point_pos = _discard_hip_corr_points(corr_point_pos, corr_points_foot_sub)

                if corr_point_pos.size > 0: # check some correction points are still left
                    q_points = q_refCH[corr_point_pos,:]
                    discard=[]

                    for j in range(1, corr_point_pos.size-1):
                        q_tmp = hamilton_product(quat_conjugate(q_points[j-1,:]), q_points[j,:])
                        a_tmp = quat_as_euler_angles(q_tmp)
                        if np.logical_or(np.abs(a_tmp[0]) > tilt_discard_th, np.abs(a_tmp[1]) > tilt_discard_th):
                            q_tmp2= hamilton_product(quat_conjugate(q_points[j-1,:]), q_points[j+1,:])
                            a_tmp2= quat_as_euler_angles(q_tmp2)
                            if np.logical_or(np.abs(a_tmp2[0]) > tilt_discard_th, np.abs(a_tmp2[1]) > tilt_discard_th):
                                discard.append(j)
                                discard.append(j+1)
                            else:
                                discard.append(j)

                    corr_point_pos[discard]=-1
                    corr_point_pos = corr_point_pos[corr_point_pos >= 0]

            if corr_point_pos.size > corr_point_threshold: # need to check again as we might've dropped too many for hip
                # Iterate through the troughs (and therefore the windows) in order to
                # compensate each window for the drift quaternion computed up to the
                # previous
                # Store current window troughs quaternions in temporary variables (q_points)
                q_points = q_refCH[corr_point_pos,:]
                # Drift correction procedure
                j = np.arange(corr_point_threshold - 1, corr_point_pos.size)
                # Differential quaternion calculation
                q_tmp = hamilton_product(quat_conjugate(q_points[j-1,:]), q_points[j,:])
                a_tmp = quat_as_euler_angles(q_tmp)

                ## Manage change in rhythm (see FFT)
                #Save marker_fft logic values
                mark=marker_fft[corr_point_pos[j]]

                # Control pitch jump between two correction points. In change of rhythm pitch change when the foot touches the ground has been noticed
                q_delta[corr_point_pos[j],:] =np.where(np.expand_dims(mark==False,1), q_tmp[...,:],
                       np.where(np.expand_dims(np.abs(a_tmp[...,1]) < tilt_th_pitch, 1),q_tmp[...,:],
                       np.where(np.logical_and(np.expand_dims(np.abs(a_tmp[...,0]) < tilt_th_roll, 1),np.expand_dims(np.abs(a_tmp[...,2]) < yaw_th, 1)),
                                 [1, 0, 0, 0],q_tmp[...,:])))

                # Actual correction where q_delta is distributed step by step between two consecutive troughs (interpolation)
                for j in range(corr_point_threshold- 1, corr_point_pos.size):
                    first, last = corr_point_pos[j-1], corr_point_pos[j]
                    h = np.arange(first, last + 1)
                    q_delta_step = quat_interp([1, 0, 0, 0], q_delta[last,:], (h - first) / (last - first))
                    q_tmp = hamilton_product(quat_conjugate(q_refCH[first-1,:]),q_refCH[h,:])
                    q_corr[h,:] = hamilton_product(
                            q_corr[first-1,:],
                            hamilton_product(quat_conjugate(q_delta_step),q_tmp))

                # Additional correction of drift
                q_refCH2=np.copy(q_corr)
                # Store current window troughs quaternions in temporary variables (q_peaks and q_troughs)
                q_points = q_refCH2[corr_point_pos,:]

                j = np.arange(corr_point_threshold - 1, corr_point_pos.size)
                # Differential quaternion calculation
                q_tmp = hamilton_product(quat_conjugate(q_points[j-1,:]), q_points[j,:])
                a_tmp = quat_as_euler_angles(q_tmp)

                #Save marker_fft logic values
                mark=marker_fft[corr_point_pos[j]]

                ## Manage change in rhythm (see FFT)
                q_delta2[corr_point_pos[j],:] =np.where(np.expand_dims(mark==False,1), q_tmp[...,:],
                np.where(np.expand_dims(np.abs(a_tmp[...,1]) < tilt_th_pitch, 1),q_tmp[...,:],
                       np.where(np.logical_and(np.expand_dims(np.abs(a_tmp[...,0]) < tilt_th_roll, 1),np.expand_dims(np.abs(a_tmp[...,2]) < yaw_th, 1)),
                                 [1, 0, 0, 0],q_tmp[...,:])))


                # Actual correction where q_delta is distributed step by step between two consecutive troughs (interpolation)
                for j in range(corr_point_threshold- 1, corr_point_pos.size):
                    first, last = corr_point_pos[j-1], corr_point_pos[j]
                    h = np.arange(first, last + 1)
                    q_delta_step = quat_interp([1, 0, 0, 0], q_delta2[last,:], (h - first) / (last - first))
                    q_tmp = hamilton_product(quat_conjugate(q_refCH2[first-1,:]),q_refCH2[h,:])
                    q_corr[h,:] = hamilton_product(
                            q_corr[first-1,:],
                            hamilton_product(quat_conjugate(q_delta_step),q_tmp))

                # Correct remaining part of the signal on the basis of the last corrected trough
                if corr_point_pos.size != 0:
                    if i==n-1:
                        stop=i+1
                    else:
                        stop=i
                    j = np.arange(corr_point_pos[-1] + 1, stop)
                    q_corr[j,:] = hamilton_product(
                            q_corr[j[0]-1,:],
                            hamilton_product(quat_conjugate(q_refCH[j[0]-1,:]), q_refCH[j,:]))

                # All peaks/troughs store
                all_corr_points.append(corr_point_pos)

        # Backward offset compensation
        # Search for the first N samples of static within the next 5 secs
        static_threshold = 20
        static_counter = 0
        q_odd = []
        q_even = [q_corr[i - 1, :]]
        for j in range(i, min(i + 5 * fs, n)):
            if static_counter >= static_threshold:
                break
            if op_cond[j] == 0:
                static_counter += 1
                if static_counter >= static_threshold:
                    q_odd.append(q_refCH[j, :])
            if j > i:
                # Save extra windows quaternion, the last static window sample
                if op_cond[j - 1] == 0 and op_cond[j] == 1:
                    q_odd.append(q_refCH[j - 1, :])
                # Save extra windows quaternion, at the end of new dyn phase, main dynamic phase included
                if op_cond[j - 1] == 1 and op_cond[j] == 0:
                    q_even.append(q_refCH[j - 1, :])

        q_odd = np.asarray(q_odd)
        q_even = np.asarray(q_even)

        if static_counter >= static_threshold:
            # Compute the actual quaternion at the end of the main dynamic window
            q0_c = np.array((1., 0., 0., 0.))
            for h in range(q_odd.shape[0] - 1, 0, -1):
                q0_c[:] = hamilton_product(
                        hamilton_product(q0_c, q_odd[h, :]),
                        quat_conjugate(q_even[h, :]))

            q0_c[:] = hamilton_product(q0_c, q_odd[0, :])

            # Compute the differential quaternion to compensate for within the main dynamic window
            a_stat = quat_as_euler_angles(q0_c)
            q_stat = hamilton_product(
                    quat_from_euler_angles(a_stat[1], [0, 1, 0]),
                    quat_from_euler_angles(a_stat[0], [1, 0, 0]))
            # Dynamic
            a_dyn = quat_as_euler_angles(q_even[0, :])
            q_dyn = hamilton_product(
                    quat_from_euler_angles(a_dyn[1], [0, 1, 0]),
                    quat_from_euler_angles(a_dyn[0], [1, 0, 0]))
            # Dynamic to static index
            q_ds = hamilton_product(quat_conjugate(q_stat), q_dyn)
            # Beginning of the compensation process
            if corr_point_pos.size > corr_point_threshold:
                # If enough correction points are found, apply backward from the last one to the static
                start_index = corr_point_pos[-1]
            else:
                # If there're no correction points (<corr_point_threshold) apply backward on all the dynamic phase
                start_index = start_op_cond

            # Offset compensation process
            h = np.arange(start_index, i)
            q_ds_step = quat_interp([1, 0, 0, 0], q_ds, (h - start_index + 1) / (i - start_index - 1))
            q_corr[h, :] = hamilton_product(q_corr[h, :], quat_conjugate(q_ds_step))

            # Manage and correct quaternion from dyn_index+1 to stat_index=j
            for h in range(i, j):
                if op_cond[h] == 0:
                    q_corr[h, :] = q_corr[h - 1, :]
                    last_stat = h
                else:
                    q_corr[h, :] = hamilton_product(
                            hamilton_product(q_corr[last_stat, :], quat_conjugate(q_refCH[last_stat, :])),
                            q_refCH[h, :])

            # Save backward points (check)
            backward_points.append(j)
    # all_corr_points= np.concatenate(all_corr_points)

    corr_points = np.zeros(n)
    candidate_trough_points = np.zeros(n)
    if len(all_corr_points) > 0:
        all_corr_points = np.concatenate(all_corr_points)
        if len(all_corr_points) > 0:
            corr_points[all_corr_points] = 1
    if len(all_candidate_corr_points) > 0:
        all_candidate_corr_points = np.concatenate(all_candidate_corr_points)
        if len(all_candidate_corr_points) > 0:
            candidate_trough_points[all_candidate_corr_points] = 1

    return q_corr, candidate_trough_points, corr_points


def _discard_hip_corr_points(corr_points_h, corr_points_foot):
    if len(corr_points_foot) > 0:
        troughs_foot_padded = set(np.concatenate([np.arange(i - 8, i + 5) for i in corr_points_foot]))
    else:
        troughs_foot_padded = []

    corr_points_h_subset = [i for i in corr_points_h if i in troughs_foot_padded]
    return np.array(corr_points_h_subset)
