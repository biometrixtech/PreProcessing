from scipy.fftpack import fft as _fft
from scipy.signal.windows import blackmanharris as _window
from scipy.signal import find_peaks as _find_peaks, filtfilt as _filtfilt
import numpy as np


def myfft(x, fs=1):
    """Compute the FFT of a signal."""
    x = x * _window(x.size)
    n = 2**int(np.ceil(np.log2(x.size)))
    n1 = n // 2 + 1
    n2 = n - n1 + 1
    X = _fft(x, n)
    X = X[:n1] / x.size
    X[1:n2] *= 2
    y = np.abs(X)
    f = np.linspace(0, fs/2, n1)
    return y, f, X


def mfiltfilt(b, a, x, *args, **kwargs):
    return _filtfilt(b, a, x, *args, **kwargs, padtype="odd", padlen=3*(max(len(b), len(a))-1))


def todd_andrews_adaptive_v5(data, delta, distance, op_cond):
    """
    This code works on acceleration filtered signal: the aim of is to collect
    troughs ONLY after the main peak.
    The troughs founded and selected with this criterie are used than used for
    drift correction procedure.
    """
    imin = 0
    imax = 0

    direction = 0
    threshold = delta

    iset = 0
    setp = np.zeros(data.size, dtype=int)
    setv = np.zeros(data.size)
    peaks_pos = []
    peaks_val = []
    troughs_pos = []
    troughs_val = []
    peak_discarded = False

    # Recognize main peak of the first period subwindow
    M = data[:3*distance].max()

    for i in range(1, data.size):
        if not op_cond[i]:
            continue

        if direction == 0:
            if data[i] <= data[imax] - threshold:
                direction = -1
            elif data[i] >= data[imin] + threshold:
                direction = 1
            if data[i] > data[imax]:
                imax = i
            elif data[i] < data[imin]:
                imin = i
            iset = 0
            setp[iset] = i
            setv[iset] = data[i]

        elif direction == 1:
            # Ascending phase of the signal
            if data[i] > data[imax]:
                iset = 0
                setp[iset] = i
                setv[iset] = data[i]
                imax = i
            elif data[i] == data[imax]:
                iset += 1
                setp[iset] = i
                setv[iset] = data[i]
            elif data[i] <= data[imax] - threshold:
                # Overthreshold - peak detection
                if iset == 0:
                    if not peaks_pos:
                        if setv[iset] > M*0.95:
                            peaks_pos.append(setp[iset])
                            peaks_val.append(setv[iset])
                    else:
                        if (np.abs(peaks_pos[-1] - setp[0]) >= distance # Distance peaks-to-peaks (position)
                                and np.abs(troughs_pos[-1] - setp[0]) >= 0.75*distance): # Distance troughs-to-peaks (position)
                                # and np.abs(troughs_val[-1] - setv[0]) >= th): # Distance troughs-to-peaks (amplitude)
                            if setv[0] > 1000:
                                peaks_pos.append(setp[0] - 1)
                                peaks_val.append(setv[0])
                        # BioMx Version
                        # Compares the current candidate peak with the last one: discard the last one
                        if 0.2 < (i - peaks_pos[-1]) / distance < 0.9 and setv[0] > peaks_val[-1]:
                            peaks_pos[-1] = setp[0] - 1
                            peaks_val[-1] = setv[0]
                            peak_discarded = True
                        # if a peak has been discarded, a control on (eventual) existing trough related to the peak discarded is carried out:
                        # if such a trough is found, it's discarded
                        if (len(peaks_pos) > 1 and len(troughs_pos) > 1 and peak_discarded
                                and troughs_pos[-1] - troughs_pos[-2] > troughs_pos[-2] - peaks_pos[-2]
                                and troughs_pos[-2] - peaks_pos[-2] > 0
                                and troughs_pos[-1] - peaks_pos[-2] > 0
                                and peaks_pos[-1] > troughs_pos[-1]):
                            troughs_pos.pop()
                            troughs_val.pop()
                            peak_discarded = False
                iset = 0
                setp[iset] = i
                setv[iset] = data[i]
                imin = i
                direction = -1

        elif direction == -1:
            # Descending phase of the signal
            if data[i] < data[imin]:
                iset = 0
                setp[iset] = i
                setv[iset] = data[i]
                imin = i
            elif data[i] == data[imin]:
                # Manage plateau condition during descending
                iset += 1
                setp[iset] = i
                setv[iset] = data[i]
            elif data[i] >= data[imin] + threshold:
                # Overthreshold - trough detection
                if iset == 0:
                    if not troughs_pos:
                        if setv[iset] < 0 and peaks_pos:
                            troughs_pos.append(setp[iset])
                            troughs_val.append(setv[iset])
                    else:
                        if (np.abs(troughs_pos[-1] - setp[0]) >= distance # Distance troughs-to-troughs (position)
                                and 3 <= np.abs(peaks_pos[-1] - setp[0]) <= distance/3): # Distance peaks-to-troughs (position)
                                # and np.abs(peaks_val[-1] - setv[0]) >= th): # Distance peaks-to-troughs (amplitude)
                            if setv[0] < 0 and peaks_pos[-1] > troughs_pos[-1]:
                                troughs_pos.append(setp[0] - 1)
                                troughs_val.append(setv[0])
                iset = 0
                setp[iset] = i
                setv[iset] = data[i]
                imax = i
                direction = 1

    return np.asarray(peaks_pos) + 1, np.asarray(troughs_pos) + 1

