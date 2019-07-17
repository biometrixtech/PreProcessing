# pylint: disable=C0326


import numpy as _np
from scipy.signal import butter as _butter, find_peaks as _find_peaks
from utils.quaternion_operations import hamilton_product, quat_conjugate, quat_interp
from utils.quaternion_conversions import quat_as_euler_angles, quat_from_euler_angles
from utils.signal_processing import mfiltfilt, myfft, todd_andrews_adaptive_v5


__author__ = "Daniele Comotti and Giorgio Barzon"
__copyright__ = "Copyright 2019, 221e s.r.l."
__credits__ = ["Daniele Comotti", "Giorgio Barzon", "Francesco Galizzi"]
__version__ = "1.2.0"
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


def foot_drift_correction(op_cond, axl_refCH, q_refCH):
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

    Returns
    -------
    q_refCH : array_like
        Orientations drift corrected.
    """
    op_cond = _np.asanyarray(op_cond)
    q_refCH = _np.copy(q_refCH)

    # Sampling frequency
    fs = 100
    # Data length
    n = op_cond.size
    # Band Pass filtering on Axl magnitude
    axl_norm_f = _np.linalg.norm(axl_refCH, axis=1)
    bl, al = _butter(1, 8, "lowpass", fs=fs)
    bh, ah = _butter(1, .5, "highpass", fs=fs)
    axl_norm_f[:] = mfiltfilt(bl, al, axl_norm_f)
    axl_norm_f[:] = mfiltfilt(bh, ah, axl_norm_f)

    # Initialize for tresholds and global vectors
    # Beginning of the current operating condition within the dataset
    start_op_cond = 0
    # Peaks and troughs found
    all_peaks = []
    all_troughs = []

    all_candidate_troughs = []

    # Frequency and amplitude of the current peak found (FFT)
    freq_peak = _np.zeros(n)
    height_peak = _np.zeros(n)
    # FFT samples
    fft_num_samples = 2**10

    # Number of troughs found after which begin to correct
    troughs_threshold = 7

    # Threshold to manage yaw jumps
    yaw_threshold = 20

    # Backward correction points
    backward_points = []

    # Quaternion initialization
    # Corrected quaternion (eventually overwrited in different sections)
    q_corr = _np.copy(q_refCH)
    # Orientation jumps between two consecutive troughs
    q_delta = _np.zeros((n, 4))
    q_delta[:,0] = 1

    # Initialization
    short_static_found = False

    # Iteration through the dataset - i is the index pointing at the end of a dynamic condition window
    for i in range(1, n):
        # Search for the beginning of an operating condition
        if op_cond[i-1] == 0 and op_cond[i] == 1 and not short_static_found:
            start_op_cond = i

        if op_cond[i-1] != 1 or op_cond[i] != 0:
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
            q_tmp_last = _np.copy(q_refCH[last_up-1,:])
            # Initialize q_d
            q_d = _np.array((1., 0., 0., 0.))
            for k in range(i, min(last_up, n-1)):
                if op_cond[k] == 0:
                    if op_cond[k+1] == 0: # Overwrite orientation
                        q_refCH[k,:] = q_refCH[k-1,:]
                    else:
                        last_stat = k # Save q_tmp before overwrite orientation
                        q_tmp = q_refCH[last_stat-1,:]
                        # Compute q_d with any precedent q_d
                        q_d[:] = hamilton_product(hamilton_product(q_tmp, quat_conjugate(q_refCH[last_stat,:])), q_d)
                        q_refCH[k,:] = q_refCH[k-1,:] # Overwrite orientation
                else:
                    # Correct dynamics with q_d
                    q_refCH[k,:] = hamilton_product(q_d, q_refCH[k,:])
            # Find last delta quaternion to be applied in the remainent dynamic phase
            q_delta_corr = hamilton_product(q_refCH[last_stat,:], quat_conjugate(q_tmp_last))
            t = _np.argwhere(op_cond[last_up:] != 1) + last_up
            t = _np.amin(t) if t.size else n
            # Apply delta quaternion
            q_refCH[last_up:t,:] = hamilton_product(q_delta_corr, q_refCH[last_up:t,:])
            # Overwrite q_corr
            q_corr[i:t,:] = q_refCH[i:t,:]

        if i - start_op_cond < fft_num_samples or short_static_found:
            continue
        # Found dynamic condition window - i points to the end of the dynamic operating condition
        # Reset current operating condition peaks/troughs
        peaks_pos = []
        troughs_pos = []
        # FFT computation and peaks/troughs detection for each window
        # The first max peak within the FFT corresponds to the fundamental frequency
        for j in range(start_op_cond, i, fft_num_samples):
            y, f, _ = myfft(axl_norm_f[j:j+fft_num_samples], fs)
            # Fundamental frequency of the FFT
            peakfft_pos, _ = _find_peaks(y, height=100)
            peakfft_val = y[peakfft_pos]

            # FFT peak and frequency detection
            if peakfft_pos.size != 0:
                # Frequency and peak
                freq_peak = f[peakfft_pos[0]]
                height_peak = round(peakfft_val[0] * 2 * _np.sqrt(2))
                # Todd-Andrews based on peak parameters with some margins
                peaks_pos_sw, troughs_pos_sw = todd_andrews_adaptive_v5(
                        axl_norm_f[j:j+fft_num_samples], height_peak/3,
                        int(round(fs/freq_peak*0.9)), op_cond[j:j+fft_num_samples])
                # Store all peaks/troughs
                peaks_pos.append(peaks_pos_sw + j)
                troughs_pos.append(troughs_pos_sw + j)

        if peaks_pos:
            peaks_pos = _np.concatenate(peaks_pos)
            troughs_pos = _np.concatenate(troughs_pos)
        else:
            peaks_pos = _np.array(())
            troughs_pos = _np.array(())


        all_candidate_troughs.append(troughs_pos)
        # Drift correction procedure
        if troughs_pos.size > troughs_threshold:
            # Discard any troughs which are close to the end of the dynamic window
            troughs_pos = troughs_pos[troughs_pos <= i - 200]
            troughs_pos = troughs_pos.astype(int)

            # Discard any outliers +/- avg of the dynamic window troughs position
            _axl_troughs = axl_norm_f[troughs_pos]
            avg_troughs = _np.mean(_axl_troughs)
            troughs_pos = troughs_pos[_np.logical_and(2*avg_troughs <= _axl_troughs, _axl_troughs <= 0)]

            # Store current window troughs quaternions in temporary variables (q_peaks and q_troughs)
            q_troughs = q_refCH[troughs_pos,:]

            curr = slice(troughs_threshold - 1, troughs_pos.size - 0)
            prev = slice(troughs_threshold - 2, troughs_pos.size - 1)
            q_tmp = hamilton_product(quat_conjugate(q_troughs[prev,:]), q_troughs[curr,:])
            a_tmp = quat_as_euler_angles(q_tmp)
            yaw_jumps = _np.argwhere(_np.abs(a_tmp[...,2]) > yaw_threshold) + troughs_threshold - 1
            yaw_jumps = _np.repeat(yaw_jumps, 2)
            yaw_jumps[::2] -= 1
            troughs_pos[yaw_jumps] = -1
            troughs_pos = troughs_pos[troughs_pos >= 0]

            # Store current window troughs quaternions in temporary variables (q_peaks and q_troughs)
            q_troughs = q_refCH[troughs_pos,:]

            # Iterate through the troughs (and therefore the windows) in order to
            # compensate each window for the drift quaternion computed up to the
            # previous
            # Drift correction procedure - without yaw
            j = _np.arange(troughs_threshold - 1, troughs_pos.size)
            # Differential quaternion calculation
            q_tmp = hamilton_product(quat_conjugate(q_troughs[j-1,:]), q_troughs[j,:])
            a_tmp = quat_as_euler_angles(q_tmp)
            # Temporary variable providing current index within dataset for the selected trough
            q_delta[troughs_pos[j],:] = _np.where(
                    _np.expand_dims(_np.abs(a_tmp[...,2]) > yaw_threshold, 1),
                    [1, 0, 0, 0],
                    hamilton_product(
                            quat_from_euler_angles(a_tmp[...,1], [0, 1, 0]),
                            quat_from_euler_angles(a_tmp[...,0], [1, 0, 0])))

            # Actual correction where q_delta is distributed step by step between two consecutive troughs (interpolation)
            for j in range(troughs_threshold - 1, troughs_pos.size):
                first, last = troughs_pos[j-1], troughs_pos[j]
                h = _np.arange(first, last + 1)
                q_delta_step = quat_interp([1, 0, 0, 0], q_delta[last,:], (h - first) / (last - first))
                q_tmp = hamilton_product(q_refCH[h,:], quat_conjugate(q_delta_step))
                q_corr[h,:] = hamilton_product(
                        q_corr[first-1,:],
                        hamilton_product(quat_conjugate(q_refCH[first-1,:]), q_tmp))

            if troughs_pos.size!=0:
                # Correct remaining part of the signal on the basis of the last corrected trough
                j = _np.arange(troughs_pos[-1] + 1, i)
                q_corr[j,:] = hamilton_product(
                        q_corr[j[0]-1,:],
                        hamilton_product(quat_conjugate(q_refCH[j[0]-1,:]), q_refCH[j,:]))

                # All peaks/troughs store
                all_peaks.append(peaks_pos)
                all_troughs.append(troughs_pos)

        # Backward offset compensation
        # Search for the first N samples of static within the next 5 secs
        static_threshold = 20
        static_counter = 0
        q_odd = []
        q_even = [q_corr[i-1,:]]
        for j in range(i, min(i + 5*fs, n)):
            if static_counter >= static_threshold:
                break
            if op_cond[j] == 0:
                static_counter += 1
                if static_counter >= static_threshold:
                    q_odd.append(q_refCH[j,:])
            if j > i:
                # Save extra windows quaternion, the last static window sample
                if op_cond[j-1] == 0 and op_cond[j] == 1:
                    q_odd.append(q_refCH[j-1,:])
                # Save extra windows quaternion, at the end of new dyn phase, main dynamic phase included
                if op_cond[j-1] == 1 and op_cond[j] == 0:
                    q_even.append(q_refCH[j-1,:])

        q_odd = _np.asarray(q_odd)
        q_even = _np.asarray(q_even)

        if static_counter >= static_threshold:
            # Compute the actual quaternion at the end of the main dynamic window
            q0_c = _np.array((1, 0, 0, 0))
            for h in range(q_odd.shape[0] - 1, 0, -1):
                q0_c = hamilton_product(
                        hamilton_product(q0_c, q_odd[h,:]),
                        quat_conjugate(q_even[h,:]))

            q0_c = hamilton_product(q0_c, q_odd[0,:])

            # Compute the differential quaternion to compensate for within the main dynamic window
            a_stat = quat_as_euler_angles(q0_c)
            q_stat = hamilton_product(
                    quat_from_euler_angles(a_stat[1], [0, 1, 0]),
                    quat_from_euler_angles(a_stat[0], [1, 0, 0]))
            # Dynamic
            a_dyn = quat_as_euler_angles(q_even[0,:])
            q_dyn = hamilton_product(
                    quat_from_euler_angles(a_dyn[1], [0, 1, 0]),
                    quat_from_euler_angles(a_dyn[0], [1, 0, 0]))
            # Dynamic to static index
            q_ds = hamilton_product(quat_conjugate(q_stat), q_dyn)

            # Offset compensation process
            h = _np.arange(start_op_cond, i)
            q_ds_step = quat_interp([1, 0, 0, 0], q_ds, (h - start_op_cond + 1) / (i - start_op_cond - 1))
            q_corr[h,:] = hamilton_product(q_corr[h,:], quat_conjugate(q_ds_step))

            # Manage and correct quaternion from dyn_index+1 to stat_index=j
            for h in range(i, j):
                if op_cond[h] == 0:
                    q_corr[h,:] = q_corr[h-1,:]
                    last_stat = h
                else:
                    q_corr[h,:] = hamilton_product(
                            hamilton_product(q_corr[last_stat,:], quat_conjugate(q_refCH[last_stat,:])),
                            q_refCH[h,:])

            # Save backward points (check)
            backward_points.append(j)

    # all_peaks = _np.concatenate(all_peaks)
    all_troughs = _np.concatenate(all_troughs)
    all_candidate_troughs = _np.concatenate(all_candidate_troughs)
    all_candidate_troughs = all_candidate_troughs.astype(int)
    # backward_points = _np.asarray(backward_points)
    candidate_troughs = _np.zeros(n)
    candidate_troughs[all_candidate_troughs] = 1
    troughs = _np.zeros(n)
    troughs[all_troughs] = 1

    return q_corr, candidate_troughs, troughs
