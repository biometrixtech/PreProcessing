# pylint: disable=C0326

from numpy import newaxis as nx
import numpy as np
from scipy.signal import butter as _butter
from utils.quaternion_operations import hamilton_product, quat_conjugate, quat_interp
from utils.quaternion_conversions import quat_as_euler_angles, quat_from_euler_angles
from utils.signal_processing import mfiltfilt


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


def hip_drift_correction(op_cond, q_refCH):
    """
    Run through the hip sensor data compensating the orientation for the drift
    on the basis of a low pass filtering technique.

    Parameters
    ----------
    op_cond : array_like
        Dynamic to static index.
    q_refH : array_like
        Orientations heading corrected.

    Returns
    -------
    q_refCH : numpy.ndarray
        Orientations drift corrected.
    """
    op_cond = np.asanyarray(op_cond)
    q_refCH = np.copy(q_refCH)

    # Sampling frequency
    fs = 100
    # Data length
    n = op_cond.size
    # Initialize for dynamic tresholds
    # Beginning of the current operating condition within the dataset
    start_op_cond = 1
    q_corr = np.copy(q_refCH)
    # Threshold on the yaw
    yaw_threshold = 20
    # Periodic correction interval [samples]
    correction_period = 5*fs
    # Filter settling at the beginning of the dynamic window
    filter_settling = 500

    # Angles filtering parameters
    bl, al = _butter(1, 0.2, "lowpass", fs=fs)
    backward_points = []
    q_cum = np.zeros((n, 4))
    q_cum[:,0] = 1

    sigma_pitch = np.zeros(n)
    sigma_roll = np.zeros(n)
    corr_points = []

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
        while h < min(i + 5 * fs, n - 1) and op_cond_down_count < op_cond_down_TH:
            h += 1
            if op_cond[h] == 0:
                op_cond_down_count += 1
            # Save extra windows quaternion, the last static window sample
            elif op_cond[h - 1] == 0:
                # Save the last static sample, of many statics
                last_up = h

        # Manage and correct quaternion in short jumps cases
        short_static_found = (op_cond_down_count <= op_cond_down_TH and op_cond[h] == 1)
        if short_static_found:
            # Save the last static orientation, of many statics
            q_tmp_last = np.copy(q_refCH[last_up - 1, :])
            # Initialize q_d
            q_d = np.array((1., 0., 0., 0.))
            for k in range(i, min(last_up, n - 1)):
                if op_cond[k] == 0:
                    if op_cond[k + 1] == 0:  # Overwrite orientation
                        q_refCH[k, :] = q_refCH[k - 1, :]
                    else:
                        last_stat = k  # Save q_tmp before overwrite orientation
                        q_tmp = q_refCH[last_stat - 1, :]
                        # Compute q_d with any precedent q_d
                        q_d[:] = hamilton_product(
                            hamilton_product(q_tmp, quat_conjugate(q_refCH[last_stat, :])), q_d)
                        q_refCH[k, :] = q_refCH[k - 1, :]  # Overwrite orientation
                else:
                    # Correct dynamics with q_d
                    q_refCH[k, :] = hamilton_product(q_d, q_refCH[k, :])
            # Find last delta quaternion to be applied in the remainent dynamic phase
            q_delta_corr = hamilton_product(q_refCH[last_stat, :], quat_conjugate(q_tmp_last))
            t = np.argwhere(op_cond[last_up:] != 1) + last_up
            t = np.amin(t) if t.size else n
            # Apply delta quaternion
            q_refCH[last_up:t, :] = hamilton_product(q_delta_corr, q_refCH[last_up:t, :])
            # Overwrite q_corr
            q_corr[i:t, :] = q_refCH[i:t, :]

        if i - start_op_cond <= 1000:
            continue

        start_index = start_op_cond
        for k in range(start_op_cond, i):
            # Update corrected quaternion on the basis of the differential quaternion
            q_corr[k,:] = hamilton_product(
                    q_corr[k-1,:],
                    hamilton_product(quat_conjugate(q_refCH[k-1,:]), q_refCH[k,:]))

            if k <= max(start_index, start_op_cond + filter_settling) + correction_period:
                continue

            # Low pass filter on the angles
            a_tmp = quat_as_euler_angles(q_corr[start_index:k+1,:])
            a_f = mfiltfilt(bl, al, a_tmp, axis=0)

            # Skip the first # filter_settling samples
            if start_index == start_op_cond:
                start_index += filter_settling
                a_f = a_f[filter_settling:,:]

            h = np.arange(start_index, k + 1)

            # Fitting with linear regression formula
            S_x = h - start_index + 1
            S_xx = S_x**2
            S_ry = a_f[:,0]
            S_py = a_f[:,1]
            S_rxy = S_x * S_ry
            S_pxy = S_x * S_py

            S_r = np.sum(np.c_[S_x, S_ry, S_xx, S_rxy], axis=0)
            S_p = np.sum(np.c_[S_x, S_py, S_xx, S_pxy], axis=0)
            S = np.stack((S_r, S_p))

            # Linear equation parameter in the form y=mx+q, both for roll and pitch
            m = ((k - start_index + 1) * S[:,3] - S[:,0] * S[:,1]) / ((k - start_index + 1) * S[:,2] - S[:,0]**2)
            q = np.mean(a_f[:, :2], axis=0) - m * (k - start_index + 2) / 2

            # Error fit estimation OLS (Ordinary Least Squares)
            tmp = (a_f[:,:2] - q[nx, :] - m[nx, :] * (h[:, nx] - start_index + 1)) ** 2
            sum_tmp = tmp.sum(axis=0)

            # Linear equation error, both for roll and pitch
            sigma_roll[k], sigma_pitch[k] = np.sqrt(sum_tmp / (k - start_index))

            # Manage bad fitting procedure (sigma > 1 [deg]), if found then skip correction
            q_tmp = hamilton_product(quat_conjugate(q_refCH[start_index,:]), q_refCH[h,:])
            a_tmp = quat_as_euler_angles(q_tmp)

            if sigma_pitch[k] <= 1 and sigma_roll[k] <= 1 and np.all(np.abs(a_tmp[:, 2]) <= yaw_threshold):
                # Drift correction with Dy=m*Dx
                tmp_r, tmp_p = m * (k - start_index + 1)
                q_delta = hamilton_product(
                        quat_from_euler_angles(tmp_p, [0, 1, 0]),
                        quat_from_euler_angles(tmp_r, [1, 0, 0]))
                # Save correction points
                corr_points.append(k)
                # Filtered quaternion dump
                q_tmp = quat_interp([1, 0, 0, 0], q_delta, (h - start_index) / (k - start_index))
                q_corr[h,:] = hamilton_product(q_corr[h,:], quat_conjugate(q_tmp))

            start_index = k

        # Backward offset compensation
        # Search for the first N samples of static within the next 5 secs
        static_threshold = 20
        static_counter = 1 if op_cond[i] == 0 else 0
        q_odd = []
        q_even = [q_corr[i-1,:]]
        for j in range(i + 1, min(i + 5*fs + 1, n)):
            if static_counter >= static_threshold:
                break
            if op_cond[j] == 0:
                static_counter += 1
                if static_counter >= static_threshold:
                    q_odd.append(q_refCH[j,:])
            # Save extra windows quaternion, the last static window sample
            if op_cond[j-1] == 0 and op_cond[j] == 1:
                q_odd.append(q_refCH[j-1,:])
            # Save extra windows quaternion, at the end of new dyn phase, main dynamic phase included
            if op_cond[j-1] == 1 and op_cond[j] == 0:
                q_even.append(q_refCH[j-1,:])

        q_odd = np.asarray(q_odd)
        q_even = np.asarray(q_even)

        if static_counter >= static_threshold:
            # Compute the actual quaternion at the end of the main dynamic window
            q0_c = np.array((1., 0., 0., 0.))
            for h in range(q_odd.shape[0] - 1, 0, -1):
                q0_c[:] = hamilton_product(
                        hamilton_product(q0_c, q_odd[h,:]),
                        quat_conjugate(q_even[h,:]))

            q0_c[:] = hamilton_product(q0_c, q_odd[0,:])

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
            h = np.arange(start_op_cond, i)
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

    corr_points = np.asarray(corr_points)
    backward_points = np.asarray(backward_points)

    return q_corr
