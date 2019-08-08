from aws_xray_sdk.core import xray_recorder
xray_recorder.configure(sampling=False)
xray_recorder.begin_segment(name="test")
import numpy as np
import os

# Use theano backend for keras
os.environ['KERAS_BACKEND'] = 'theano'

from app.utils import quaternion_operations as qo
"""
    Testing all quatOps functions.

    Tests included:
        --quat_prod
            -Output data is same shape as input
            -Product of a quaternion with its conjugate is unit quaternion
            -Multiplying by unit quaternion returns input
        --quat_norm
            -Output data is same shape as input
            -Magnitude of all quaternions is 1 after normalizing
        --find_rot
            -Output data is same shape as input
            -Rotation between self is [1,0,0,0]
            -Rotation between input and -input os [-1,0,0,0]
            -Rotation between input and [1,0,0,0] is input
        --quat_conj
            -Output data is same shape as input
            -quat_conj(quat_cont(input)) is quat_norm(input)
        --vect_rot
            -Output data is same shape as v
            -Rotating by unit quaternion returns v
            -Rotating 90 deg 4 times about axis returns v
        --quat_avg
            -Output data has same number of columns as input
            -Output data's columns are averages of the values within
                respective columns
        --quat_multi_prod
            -output value is the same shape as each input
            -using this function gives the same result as individually run
                quat_prod functions
            -if input has no len, raise error



    """


def test_quat_prod():
    '''
    Tests included:

        -Output data is same shape as input
        -Product of a quaternion with its conjugate is unit quaternion
        -Multiplying by unit quaternion returns input

    '''
    eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
    z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
    eye_shape = eye.shape
    eye_prod = qo.quat_prod(eye, eye)
    eye_prod_shape = eye_prod.shape
    z90_conj = qo.quat_conj(z90)
    z90_z90_conj_prod = qo.quat_prod(z90, z90_conj)
    eye_z90_prod = qo.quat_prod(eye, z90)

    # output data is same shape as input
    assert eye_prod_shape == eye_shape

    # product of a quaternion with its conjugate is unit quaternion
    assert np.allclose(z90_z90_conj_prod, eye)

    # multiplying by a unit quaternion returns input
    assert np.allclose(eye_prod, eye)
    assert np.allclose(eye_z90_prod, z90)


def test_quat_norm():
    '''
    Tests included:

        -Output data is same shape as input
        -Magnitude of all quaternions is 1 after normalizing

    '''
    eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
    skewed = eye + np.array([[0, 0, 0, 0.4]])
    skewed_shape = skewed.shape
    skewed_norm = qo.quat_norm(skewed)
    skewed_norm_shape = skewed_norm.shape
    mag_skewed_norm = np.sqrt(np.sum(skewed_norm**2, axis=1))

    # output data is same shape as input
    assert skewed_shape == skewed_norm_shape

    # magnitude of quaternions is 1 after normalizing
    assert np.allclose(mag_skewed_norm, np.array([1, 1, 1]))


def test_find_rot():
    '''
    Tests included:

        -Output data is same shape as inputs
        -Rotation between self is [1, 0, 0, 0]
        -Rotation between input and -input is [-1, 0, 0, 0]
        -Rotation between input and [1, 0, 0, 0] is input

    '''
    eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
    z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
    z90_shape = z90.shape
    z90_z90_rot = qo.find_rot(z90, z90)
    z90_z90_rot_shape = z90_z90_rot.shape
    z90_nz90_rot = qo.find_rot(z90, -z90)
    z90_eye_rot = qo.find_rot(eye, z90)

    # output data is same shape as inputs
    assert z90_z90_rot_shape == z90_shape

    # rotation between self is [1, 0, 0, 0]
    assert np.allclose(z90_z90_rot, eye)

    # rotation between input and -input is [-1, 0, 0, 0]
    assert np.allclose(z90_nz90_rot, -eye)

    # rotation between [1, 0, 0, 0] and input is input
    assert np.allclose(z90_eye_rot, z90)


def test_quat_conj():
    '''
    Tests include:

        -Output data is same shape as input
        -quat_conj(quat_conj(input)) is quat_norm(input)

    '''

    z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
    z90_shape = z90.shape
    z90_conj = qo.quat_conj(z90)
    z90_conj_shape = z90_conj.shape
    z90_norm = qo.quat_norm(z90)
    z90_conj_conj = qo.quat_conj(z90_conj)

    # output data is same shape as input
    assert z90_shape == z90_conj_shape

    # quat_conj(quat_conj(input)) is quat_norm(input)
    assert np.allclose(z90_conj_conj, z90_norm)


def test_vect_rot():
    '''
    Tests include:

        -Output data is same shape as v
        -Rotating by unit quaternion returns v
        -Rotating 90 deg 4 times about axis returns v

    '''

    vect = np.array([[1, 0, 0], [1, 0, 0], [1, 0, 0]])
    eye = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]])
    z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2]])
    vect_shape = vect.shape
    vect_eye_rot = qo.vect_rot(vect, eye)
    vect_eye_rot_shape = vect_eye_rot.shape
    rot_4 = qo.vect_rot(qo.vect_rot(qo.vect_rot(qo.vect_rot(vect, z90), z90), z90), z90)

    # output data is same shape as v
    assert vect_shape == vect_eye_rot_shape

    # rotating by unit quaternion returns v
    assert np.allclose(vect, vect_eye_rot)

    # rotating 90 deg 4 times about axis returns v
    assert np.allclose(vect, rot_4)


def test_quat_avg():
    '''
    Tests include:
        -Output data has same number of columns as input
        -Output data's columns are normalized averages of the values within
            respective columns

    '''

    z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
    z90_avg = qo.quat_avg(z90)
    z90_shape = z90.shape
    z90_avg_shape = z90_avg.shape
    z90_np_avg = qo.quat_norm([np.sum(z90, axis=0)/3])

    # output has same number of columns as input
    assert z90_shape[1] == z90_avg_shape[1]

    # output columns are normed avgs of the vals within respective input cols
    assert np.allclose(z90_avg, z90_np_avg)


def test_quat_multi_prod():
    '''
    Tests included:

        -output value is the same shape as each input
        -using this function gives the same result as individually run
            quat_prod functions
        -if input has no len, raise error

    '''

    z90 = np.array([[1, 0, 0, 0], [np.sqrt(2)/2, 0, 0, np.sqrt(2)/2], [0.44807362, 0, 0, 0.89399666]])
    y45 = np.array([[1, 0, 0, 0], [ 0.92387953, 0, -0.38268343, 0], [np.sqrt(2)/2, 0, np.sqrt(2)/2, 0]])
    z90_shape = z90.shape
    z90_3_prod = qo.quat_multi_prod(z90, z90, z90)
    y45_y45_z90 = qo.quat_multi_prod(y45, y45, z90)
    z90_3_prod_shape = z90_3_prod.shape
    z90_prod_prod = qo.quat_prod(qo.quat_prod(z90, z90), z90)
    y45_y45_z90_prod = qo.quat_prod(qo.quat_prod(y45, y45), z90)

    # output value is the same shape as each input
    assert z90_shape == z90_3_prod_shape

    # output is same as layered quat_prod functions
    assert np.allclose(z90_3_prod, z90_prod_prod)
    assert np.allclose(y45_y45_z90, y45_y45_z90_prod)

    try:
        qo.quat_multi_prod()
    except ValueError as context:
        assert 'Must supply at least one argument' in context.args


