from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import os

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.utils import quaternion_conversions as qc

'''
        --quat_force_euler_angle
            -output data is the same shape as input
            -output data is quaternion representation of input data, where
                specified axes have been replaced with specified values
       --quat_to_euler
           -output has same number of rows as input
           -specific examples
       --euler_to_quat
           -output has same number of rows as input
           -specific examples

'''


def test_quat_force_euler_angle():
    '''
    Tests include:

        -output data is the same shape as input
        -output data is quaternion representation of input data, where
            specified axes have been replaced with specified values

    '''

    x90 = np.array([[np.sqrt(2)/2, np.sqrt(2)/2, 0, 0], [np.sqrt(2)/2, np.sqrt(2)/2, 0, 0], [np.sqrt(2)/2, np.sqrt(2)/2, 0, 0]])
    y90 = np.array([[np.sqrt(2)/2, 0, np.sqrt(2)/2, 0], [np.sqrt(2)/2, 0, np.sqrt(2)/2, 0], [np.sqrt(2)/2, 0, np.sqrt(2)/2, 0]])
    z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
    eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
    z90_from_eye = np.array([[np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2]])
    z90_shape = z90.shape
    z90_to_eye = qc.quat_force_euler_angle(z90, psi=0)
    z90_to_eye_shape = z90_to_eye.shape
    eye_to_x90 = qc.quat_force_euler_angle(eye, phi=90*np.pi/180)
    eye_to_y90 = qc.quat_force_euler_angle(eye, theta=90*np.pi/180)
    eye_to_z90 = qc.quat_force_euler_angle(eye, psi=90*np.pi/180)

    # output data is same shape as input
    assert z90_shape == z90_to_eye_shape

    # output data is quaternion representation of input data, where
        # specified axes have been replaced with specified values
    assert np.allclose(z90_to_eye, eye)
    assert np.allclose(eye_to_x90, x90)
    assert np.allclose(eye_to_y90, y90)
    assert np.allclose(eye_to_z90, z90_from_eye)


def test_euler_to_quat():
    '''
    Tests include:
        -output has same number of rows as input
        -specific examples

    '''
    z90eul = np.array([[0, 0, 90 * np.pi / 180]])
    z90eul_shape = z90eul.shape
    z90quat = qc.euler_to_quat(z90eul)
    z90quat_shape = z90quat.shape

    # output only has same number of rows as input
    assert z90eul_shape[0] == z90quat_shape[0]
    assert z90eul_shape[1] != z90quat_shape[1]

    # specific examples
    assert (np.allclose(z90quat, np.array([[0.70710678, 0, 0, 0.70710678]])) or
           np.allclose(z90quat, np.array([[-0.70710678, 0, 0, -0.70710678]])))


def test_quat_to_euler():
    '''
    Tests include:
        -output has same number of rows as input
        -specific examples

    '''

    z90quat = np.array([[np.sqrt(2) / 2, 0, 0, np.sqrt(2) / 2]])
    z90nquat = np.array([[-np.sqrt(2) / 2, 0, 0, -np.sqrt(2) / 2]])
    z90quat_shape = z90quat.shape
    z90eul = qc.quat_to_euler(z90quat)
    z90eul_shape = z90eul.shape
    z90neul = qc.quat_to_euler(z90nquat)

    # output has same number of rows as input
    assert z90quat_shape[0] == z90eul_shape[0]
    assert z90quat_shape[1] != z90eul_shape[1]

    # specific examples
    # complementary quats pointing to same eul set
    assert np.allclose(z90eul, np.array([[0, 0, 1.57079633]]))
    assert np.allclose(z90neul, np.array([[0, 0, 1.57079633]]))

    # cases of imaginary pitch returned as real pitch
    y90quatimag = np.array([[0, 0, 1, 0]])
    y90eulimag = qc.quat_to_euler(y90quatimag)

    assert np.allclose(y90eulimag, np.array([[0, np.pi, 0]]))

