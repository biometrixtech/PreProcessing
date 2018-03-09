# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 16:10:46 2018

@author: Administrator
"""

import numpy as np
import pandas as pd


import matplotlib.pyplot as plt
#
#def detect_peak(grf):
#    plt.figure(0)
#    plt.plot(grf)
#    peaks = [1,2,3]
#    return peaks


def detect_peaks(x, mph=None, mpd=1, threshold=0, edge='rising',
                 kpsh=False, valley=False, show=False, ax=None):

    """Detect peaks in data based on their amplitude and other features.

    Parameters
    ----------
    x : 1D array_like
        data.
    mph : {None, number}, optional (default = None)
        detect peaks that are greater than minimum peak height.
    mpd : positive integer, optional (default = 1)
        detect peaks that are at least separated by minimum peak distance (in
        number of data).
    threshold : positive number, optional (default = 0)
        detect peaks (valleys) that are greater (smaller) than `threshold`
        in relation to their immediate neighbors.
    edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
        for a flat peak, keep only the rising edge ('rising'), only the
        falling edge ('falling'), both edges ('both'), or don't detect a
        flat peak (None).
    kpsh : bool, optional (default = False)
        keep peaks with same height even if they are closer than `mpd`.
    valley : bool, optional (default = False)
        if True (1), detect valleys (local minima) instead of peaks.
    show : bool, optional (default = False)
        if True (1), plot data in matplotlib figure.
    ax : a matplotlib.axes.Axes instance, optional (default = None).

    Returns
    -------
    ind : 1D array_like
        indeces of the peaks in `x`.

    Notes
    -----
    The detection of valleys instead of peaks is performed internally by simply
    negating the data: `ind_valleys = detect_peaks(-x)`
    
    The function can handle NaN's 

    See this IPython Notebook [1]_.

    References
    ----------
    .. [1] http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb

    Examples
    --------
    >>> from detect_peaks import detect_peaks
    >>> x = np.random.randn(100)
    >>> x[60:81] = np.nan
    >>> # detect all peaks and plot data
    >>> ind = detect_peaks(x, show=True)
    >>> print(ind)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # set minimum peak height = 0 and minimum peak distance = 20
    >>> detect_peaks(x, mph=0, mpd=20, show=True)

    >>> x = [0, 1, 0, 2, 0, 3, 0, 2, 0, 1, 0]
    >>> # set minimum peak distance = 2
    >>> detect_peaks(x, mpd=2, show=True)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # detection of valleys instead of peaks
    >>> detect_peaks(x, mph=0, mpd=20, valley=True, show=True)

    >>> x = [0, 1, 1, 0, 1, 1, 0]
    >>> # detect both edges
    >>> detect_peaks(x, edge='both', show=True)

    >>> x = [-2, 1, -2, 2, 1, 1, 3, 0]
    >>> # set threshold = 2
    >>> detect_peaks(x, threshold = 2, show=True)
    """

    x = np.atleast_1d(x).astype('float64')
    if x.size < 3:
        return np.array([], dtype=int)
    if valley:
        x = -x
    # find indices of all peaks
    dx = x[1:] - x[:-1]
    # handle NaN's
    indnan = np.where(np.isnan(x))[0]
    if indnan.size:
        x[indnan] = np.inf
        dx[np.where(np.isnan(dx))[0]] = np.inf
    ine, ire, ife = np.array([[], [], []], dtype=int)
    if not edge:
        ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
    else:
        if edge.lower() in ['rising', 'both']:
            ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
        if edge.lower() in ['falling', 'both']:
            ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
    ind = np.unique(np.hstack((ine, ire, ife)))
    # handle NaN's
    if ind.size and indnan.size:
        # NaN's and values close to NaN's cannot be peaks
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan-1, indnan+1))), invert=True)]
    # first and last values of x cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == x.size-1:
        ind = ind[:-1]
    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[x[ind] >= mph]
    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx = np.min(np.vstack([x[ind]-x[ind-1], x[ind]-x[ind+1]]), axis=0)
        ind = np.delete(ind, np.where(dx < threshold)[0])
    # detect small peaks closer than minimum peak distance
    if ind.size and mpd > 1:
        ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                # keep peaks with the same height if kpsh is True
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                    & (x[ind[i]] > x[ind] if kpsh else True)
                idel[i] = 0  # Keep current peak
        # remove the small peaks and sort back the indices by their occurrence
        ind = np.sort(ind[~idel])

    if show:
        if indnan.size:
            x[indnan] = np.nan
        if valley:
            x = -x
        _plot(x, mph, mpd, threshold, edge, valley, ax, ind)

    return ind


def _plot(x, mph, mpd, threshold, edge, valley, ax, ind):
    """Plot results of the detect_peaks function, see its help."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print 'matplotlib is not available.'
    else:
        if ax is None:
            _, ax = plt.subplots(1, 1, figsize=(8, 4))

        ax.plot(x, 'b', lw=1)
        if ind.size:
            label = 'valley' if valley else 'peak'
            label = label + 's' if ind.size > 1 else label
            ax.plot(ind, x[ind], '+', mfc=None, mec='r', mew=2, ms=8,
                    label='%d %s' % (ind.size, label))
            plt.axhline(mph)
            ax.legend(loc='best', framealpha=.5, numpoints=1)
        ax.set_xlim(-.02*x.size, x.size*1.02-1)
        ymin, ymax = x[np.isfinite(x)].min(), x[np.isfinite(x)].max()
        yrange = ymax - ymin if ymax > ymin else 1
        ax.set_ylim(ymin - 0.1*yrange, ymax + 0.1*yrange)
        ax.set_xlabel('Data #', fontsize=14)
        ax.set_ylabel('Amplitude', fontsize=14)
        mode = 'Valley detection' if valley else 'Peak detection'
        ax.set_title("%s (mph=%s, mpd=%d, threshold=%s, edge='%s')"
                     % (mode, str(mph), mpd, str(threshold), edge))
        # plt.grid()
        plt.show()

def plot_euler(data, num):
    plt.figure(num)
    plt.subplot(211)
    plt.plot(data.LeX * 180 / np.pi)
    plt.plot(data.LeY * 180 / np.pi)
#    plt.plot(data.LeY_transformed * 180 / np.pi)
#    plt.plot(data.LeZ * 180 / np.pi)
#    plt.plot(data.corrupt_lf)
    plt.legend()

#    plt.subplot(312)
#    plt.plot(data.HeX * 180 / np.pi)
#    plt.plot(data.HeY * 180 / np.pi)
##    plt.plot(data.HeZ * 180 / np.pi)
#    plt.legend()
#    
    plt.subplot(212)
    plt.plot(data.ReX * 180 / np.pi)
    plt.plot(data.ReY * 180 / np.pi)
#    plt.plot(data.ReY_transformed * 180 / np.pi)
#    plt.plot(data.ReZ * 180 / np.pi)
#    plt.plot(data.corrupt_rf)
    plt.legend()

def check_sync(data_in, num, filename):
    import copy
    data = copy.deepcopy(data_in)
#    data.reset_index(inplace=True, drop=True)

    # recode phase to differentiate ground contact vs air
    data.loc[data.phase_lf==1, 'phase_lf'] = 0
    data.loc[(data.phase_lf==2) | (data.phase_lf==3), 'phase_lf'] = 1
    data.loc[data.phase_lf==4, 'phase_lf'] = 0
    data.loc[data.phase_lf==6, 'phase_lf'] = 0

    data.loc[data.phase_rf==2, 'phase_rf'] = 0
    data.loc[(data.phase_rf==1) | (data.phase_rf==3), 'phase_rf'] = 1
    data.loc[data.phase_rf==5, 'phase_rf'] = 0
    data.loc[data.phase_rf==7, 'phase_rf'] = 0

    plt.figure(num)
    plt.suptitle(filename)
#    plt.subplot(211)
    plt.plot(data.LaZ)
#    plt.plot(data.HaZ)

#    plt.legend()
#    plt.subplot(212)

    plt.plot(data.RaZ)

    plt.plot(data.HaZ)
#    plt.plot(data.phase_lf * 10)
#    plt.plot(data.phase_rf * 10)
    plt.legend()

def plot_accel(data, num):
    plt.figure(num)
#    plt.subplot(211)
#    acc_magn_l = np.sqrt(data.LaX**2 + data.LaY**2 + data.LaZ**2)
#    plt.plot(data.LaX)
    plt.plot(data.LaY)
#    plt.plot(data.LaZ)
#    plt.plot(acc_magn_l)
#    plt.legend()
    
#    plt.subplot(312)
#    plt.plot(data.HaX) 
#    plt.plot(data.HaY)
#    plt.plot(data.HaZ)
#    plt.legend()
    
#    plt.subplot(212)
#    acc_magn_r = np.sqrt(data.RaX**2 + data.RaY**2 + data.RaZ**2)
#    plt.plot(data.RaX)
    plt.plot(data.RaY)
#    plt.plot(data.RaZ)
#    plt.plot(acc_magn_r)
    plt.legend()

def plot_grf(data, num):
    plt.figure(num)
    plt.plot(data.grf)
    plt.plot(data.LaZ)
    plt.plot(data.RaZ)
    plt.legend()

if __name__ == '__main__':
    file_loc = 'C:\\Users\\Administrator\\Desktop\\GRFPeakDetection\\input_data\\'
#    filename = 'gabby_trial2_combined_real'
#    filename = 'gabby_trial2_combined_pred'
#    filename = 'b97c97f9-a56d-4e18-81a5-777452bd278d_v1'
#    filename = 'gabby_runs'
    filename = 'subj023_combined.csv'
    data = pd.read_csv(file_loc+filename)
    data.loc[data['fz_lf'] < 25, 'fz_lf'] = 0
    data.loc[data['fz_rf'] < 25, 'fz_rf'] = 0
#    plot_euler(data, 1)
#    plot_accel(data, 2)
#    check_sync(data, 0, filename)
    data['grf'] = data.fz_lf + data.fz_rf
#    grf = data.grf
#    mph = np.mean(grf[100:300]) + 20
#    grf[grf < 50] = 0
    data['phaseLF'] = data.fz_lf == 0
    data['phaseRF'] = data.fz_rf == 0
    plt.plot(data.grf)
    plt.plot(data.fz_lf)
    plt.plot(data.fz_rf)
    plt.plot(data.phaseLF * 100)
    plt.plot(data.phaseRF * 100)
    plt.legend()
#    data.loc[:, 'grf'] = grf
#    plot_grf(data, 1)
#    plt.figure(4)
#    plt.plot(grf)
#    peaks = detect_peaks(grf[0:100000], mph=1000, mpd=15, show=True, edge='both')
#    print(np.sum(grf[750:2500])/1000000 /900 * 2 * 60 * 100)
#    print(np.sum(grf[20000:21750])/1000000 /900 * 2 * 60 * 100)
    
    