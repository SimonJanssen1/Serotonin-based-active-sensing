'''
Course:  Human-Robot Interaction
Authors: Filip Novicky, Joshua Offergeld, Simon Janssen, Ariyan Tufchi
Date:    19-01-2023

This script implements the active inference model described in the report. 
The script receives information about observations from a python2 script connected to the robot.
Based on the observations, the inference model computes the next state for the robot.
'''

from pymdp.agent import Agent
import numpy as np
import scipy
from scipy.special import softmax
import matplotlib.pyplot as plt

import socket
from model_definition import get_a, get_b, get_d, get_e

HOST = 'localhost'          # set host for connection with python2 script
PORT = 8081                 # set connection port for connection with python2 script

class SearchEnv(object):
    """Environment that keeps track of the state and the B matrix"""
    def __init__(self, D, n, B):
        self.start = SearchEnv.one_hot(n, np.argmax(D))
        self.state = self.start
        self.n = n
        self.B_obj = B[0]
        self.B_act = B[1]

    def reset(self):
        self.state = self.start

    def step(self, action):
        # take a step given the action selected, store and return the new state
        B_choice = self.B_act[:, :, action]
        self.state = B_choice @ self.state
        return self.state

    @staticmethod
    def one_hot(n, idx):
        # return a zero vector of length n with a 1 in position idx
        vec = np.zeros(n)
        vec[idx] = 1.0
        return vec


def step(agent, env, obs, q_pis, context):
    # update model
    qs = agent.infer_states(obs)
    q_pi, efe = agent.infer_policies()
    # get action
    chosen_action_id = agent.sample_action()
    idx = int(chosen_action_id[1])
    # logging
    q_pis.append(q_pi)
    context.append(qs[0])
    interm = env.step(idx)

    return np.argmax(interm), q_pis, context


def createSubplot(ax, data, name, timesteps, colors=None, labels=None):
    # If there are multiple states to be plotted, plot them individually
    if name == 'Context posterior' or name == 'Policy posterior':
        for i, line in enumerate(np.transpose(data)):
            ax.plot(line, c=colors[i], label=labels[i])
        ax.set_ylim([-0.1,1.1])
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25))
    # The hand position state should have points plotted individually
    elif name == 'Arm position':
        ax.plot(data, c='blue', marker='o', markersize=4)
        ax.set_ylim([0,6])
    else:
        ax.plot(data, c= 'blue')
        ax.set_ylim([-0.1,1.1])

    # Set the appropriate labels and limits
    ax.set_title(name)
    ax.set_xlabel("Timestep")
    ax.set_ylabel(name)
    ax.axvline(x=30, color='red')
    ax.set_xlim([0,timesteps])


def plot_data(fig, axs, obs, q_pi, cont, action, timesteps):
    # Clear axes before overwriting contents
    for ax in axs:
        for j in ax:
            j.clear()

    # Initialise labels and colors for the individual hidden states and policies
    contextColors = ['black', 'blue', 'yellow', 'red']
    contextLabels = ['Not touched', 'Touched left', 'Touched middle', 'Touched right']

    policyColors = ['yellow', 'purple']
    policyLabels = ['Large amplitude', 'Small amplitude']

    # Create subplots for the different variables
    createSubplot(axs[0,0], obs, "Observation", timesteps)
    createSubplot(axs[1,1], cont, "Context posterior", timesteps, contextColors, contextLabels)
    createSubplot(axs[1,0], q_pi, "Policy posterior", timesteps, policyColors, policyLabels)
    createSubplot(axs[0,1], action, "Arm position", timesteps)

    # Make sure that the layout is tight
    fig.tight_layout()


if __name__ == '__main__':
    """ Main entry point

    """
    # Get the matrices for the active inference model
    A = get_a()
    B = get_b()
    D = get_d()
    E = get_e()

    ## Initialize precision terms
    zeta = 0.5
    omega = 0.8
    rho = 0.5

    ## Initialise number of timesteps
    timesteps = 80

    for i in range(1, 4):
        A[0][:, i, :] = scipy.special.softmax(zeta * np.log(A[0][:, i, :] + np.exp(-8)), axis=0)

    B[0][:, :, 0] = scipy.special.softmax(omega * np.log(np.eye(4) + np.exp(-8)), axis=0)
    E = scipy.special.softmax(rho * np.log(E + np.exp(-8)), axis=0)

    # Initialise agent and environment
    my_agent = Agent(A=A, B=B, C=None, D=D, E=E, use_utility=True, use_states_info_gain=True, sampling_mode="full")
    my_env = SearchEnv(D[1], 8, B)

    # Plot figure during simulation
    fig, axs = plt.subplots(2, 2, figsize=(9, 7))
    plt.ion()

    # Keep track of important variables
    observations = []
    q_pis = []
    context = []
    actions = []

    # Set up a connection with the robot
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        conn.settimeout(10)                             # Set a time out to allow for the robot to execute actions before sending a new observation
        s.close()
        with conn:
            print(f"Connected by {addr}")
            while True:
                # Receive an observation
                data = conn.recv(1024)                  # Wait for the observation from the robot (0.0 = touched, 1.0 = not touched)
                if data == b'end':
                    break                               # If the robot is done, end the script and close the connection
                else:
                    obs = int(float(data))              # Else, convert the received data to the correct type

                print("Observation: ", obs)
                observations.append(1-obs)

                # Compute the action and send it to the robot
                action, q_pis, context = step(my_agent, my_env, [obs], q_pis, context)
                print("Action: ", action)
                storeAction = action
                if action > 4:
                    storeAction = 8 - action
                actions.append(storeAction+1)
                conn.sendall(bytes(str(action), 'utf8'))

                # Plot the important variables interactively
                plot_data(fig, axs, observations, q_pis, context, actions, timesteps)
                plt.draw()
                plt.pause(0.1)  # interactive

            # Save the final plot
            plt.savefig("Data plot experimental run", format='pdf')
            conn.close()
    
