'''
Course:  Human-Robot Interaction
Authors: Filip Novicky, Joshua Offergeld, Simon Janssen, Ariyan Tufchi
Date:    13-01-2023

This script is used to initialise the matrices needed for the active inference model. 

Specifically, this script initialises the following matrices:
    - A matrix:
    - B matrix: 
    - D matrix:
    - E matrix:
'''

import numpy as np
from pymdp import utils
from scipy.special import softmax

num_states = [4, 8]
num_factors = len(num_states)
num_modalities = 1


def get_a():
    # compute and return the likelihood matrix with deterministic perception
    A = utils.obj_array(num_modalities)
    A[0] = np.ndarray((2, 4, 8))
    A[0].fill(.5)
    for i in range(1, 4):
        A[0][:, i, i] = [1, 0]
        A[0][:, i, 8 - i] = [1, 0]
    return A


def get_b():
    # compute and return the behaviour matrix with deterministic transitions
    B = utils.obj_array(num_factors)
    B[0] = np.ndarray((4, 4, 1)) # context x context x 1
    B[0][:, :, 0] = np.eye(4)

    # create the transition matrices as presented in the report
    B[1] = np.ndarray((8, 8, 2))
    B[1][:, :, 0] = np.roll(np.eye(8), -1)
    B[1][0, 7, 0] = 1
    B[1][7, 7, 0] = 0
    B[1][:, :, 1] = np.zeros((8, 8))
    B[1][1:3, :2, 1] = np.eye(2)

    for i in range(6):
        B[1][7 - i, 2 + i, 1] = 1
    return B


def get_d():
    # compute and return the D matrix with the starting hand position 7
    D = utils.obj_array(num_factors)
    D_context = np.array([1, 0, 0, 0])

    D[0] = D_context
    D_handposition = np.zeros(8)

    hand = 7
    D_handposition[hand] = 1.0
    D[1] = D_handposition
    return D


def get_e():
    # compute and return the habitual matrix with initial values of 0.75 for the broad and 0.25 for the precise movement
    E = np.array([0.75, 0.25])  # Higher probabilities for selecting the high amplitude movement independently on input (i.e., Habits)
    return E