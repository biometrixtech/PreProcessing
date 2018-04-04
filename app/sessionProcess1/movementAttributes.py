import copy
import numpy as np


def get_total_accel(accel_data):
    """Get magnitude of acceleration
    """
    return np.sqrt(np.sum(accel_data**2, axis=1))


def standing_or_not(hip_eul, freq):
    """Determine when the subject is standing or not.

    Args:
        hip_eul: body frame euler angle position data at hip
        freq: an int, sampling rate of sensor

    Returns:
        2 binary lists characterizing position:
            standing
            not_standing
    """

    # create storage for variables
    standing = np.zeros((len(hip_eul), 1))

    # define minimum window to be characterized as standing
    _standing_win = int(0.5*freq)

    # make copy of relevant data so as not to overwrite old
    hip_y = copy.deepcopy(hip_eul)
    del hip_eul  # not used in further computations
    hip_y = hip_y[:, 1][:].reshape(-1, 1)

    # set threshold for standing
    _forward_standing_thresh = np.pi/2
    _backward_standing_thresh = -np.pi/4

    # create binary array based on elements' relation to threshold
    hip_y[np.where(hip_y == 0)] = 1
    hip_y[np.where(hip_y > _forward_standing_thresh)] = 0
    hip_y[np.where(hip_y < _backward_standing_thresh)] = 0
    hip_y[np.where(hip_y != 0)] = 1

    # find lengths of stretches where standing is true
    one_indices = _num_runs(hip_y, 1)
    diff_1s = one_indices[:, 1] - one_indices[:, 0]

    # isolate periods of standing which are significant in length, then mark=2
    sig_diff_1s = one_indices[np.where(diff_1s > _standing_win), :]
    del one_indices, diff_1s  # not used in further computations
    sig_diff_1s = sig_diff_1s.reshape(len(sig_diff_1s[0]), 2)

    for i in range(len(sig_diff_1s)):
        hip_y[sig_diff_1s[i][0]:sig_diff_1s[i][1]] = 2
    del sig_diff_1s  # not used in further computations

    # reset binary array to only record periods of significant standing
    hip_y[np.where(hip_y != 2)] = 0
    hip_y[np.where(hip_y != 0)] = 1

    # eliminate periods of insignificant 'not standing' by repeating method
    zero_indices = _num_runs(hip_y, 0)
    diff_0s = zero_indices[:, 1] - zero_indices[:, 0]

    sig_diff_0s = zero_indices[np.where(diff_0s < 4*_standing_win), :]
    del zero_indices, diff_0s  # not used in further computations
    sig_diff_0s = sig_diff_0s.reshape(len(sig_diff_0s[0]), 2)

    for i in range(len(sig_diff_0s)):
        hip_y[sig_diff_0s[i][0]:sig_diff_0s[i][1]] = 1

    standing = hip_y
    del sig_diff_0s, hip_y  # not used in further computations

    # define not_standing as the points in time where subject is not standing
    not_standing = [1]*len(standing)
    not_standing = np.asarray(not_standing).reshape((len(standing), 1))
    not_standing = not_standing - standing

    return standing


def _num_runs(arr, num):
    """
    Function that determines the beginning and end indices of stretches of
    of the same value in an array.

    Args:
        arr: array to be analyzed for runs of a value
        num: number to searched for in the array arr

    Returns:
        ranges: nx2 np.array, with each row containing start and stop + 1
            indices of runs of the value num

    Example:
    >> arr = np.array([1, 1, 2, 3, 2, 0, 0, 1, 3, 1, 1, 1, 6])
    >> _num_runs(arr, 1)
    Out:
    array([[ 0,  2],
           [ 7,  8],
           [ 9, 12]], dtype=int64)
    >> _num_runs(arr, 0)
    Out:
    array([[5, 7]], dtype=int64)

    """
    # Create an array that is 1 where a=num, and pad each end with an extra 0.
    iszero = np.concatenate(([0], np.equal(arr.reshape(-1,), num), [0]))
    del arr, num  # not used in further computations
    absdiff = np.abs(np.diff(iszero))
    del iszero  # not used in further computations

    # Runs start and end where absdiff is 1.
    ranges = np.where(absdiff == 1)[0].reshape(-1, 2)

    return ranges
