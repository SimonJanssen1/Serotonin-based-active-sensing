'''
Course:  Human-Robot Interaction
Authors: Filip Novicky, Joshua Offergeld, Simon Janssen, Ariyan Tufchi
Date:    13-01-2023

This script is used to test the connection between the python2 and python3 script. Two threads are created:

- Touches are simulated in the Sense class. 
- Actions are simulated in the Act class. 

The Touch class is needed to share variables between the two threads.
'''

import socket
from threading import Lock, Thread, Event
import time
import random

HOST = 'localhost'     # set host for connection with python3 script
CONNPORT = 8081        # set connection port for connection with python3 script

class Touch():
    def __init__(self):
        self.lock = Lock()
        self.touched = 1.0
        self.state = None

    def getLock(self):
        return self.lock

    def getState(self):
        return self.state

    def setState(self, state):
        self.state = state

    def readAndReset(self, value):
        val = self.touched
        self.touched = value
        return val

def main():
    """ Main entry point

    """
    touchData = Touch()                # Create shared class to update touch variable
    timesteps = 80                     # Decide how long to run the experiment
    
    actThread = Act(touchData, timesteps)         # Create thread for acting in environment
    senseThread = Sense(touchData)                # Create thread for sensing in environment

    # This is the experimental data for the experiments in which a state was not always touched
    experimentTouchData = [[12, 14, 20, 22, 24, 26, 38],                                                              # Experiment 1
                           [12, 14, 20, 22, 29, 36, 38],                                                              # Experiment 4 initial
                           [11, 15, 19, 23, 25, 27, 29, 31, 35,37,39],                                                # Experiment 6
                           [8, 9, 24, 26],                                                                            # Experiment 7
                           [10, 16, 18, 20, 22, 24, 27, 39, 40, 43, 47, 49, 51, 53, 55, 57, 59, 67, 71, 73, 75, 76],  # Experiment 8
                           [11, 12, 15, 19, 23, 27, 31, 33, 35, 41, 43, 44, 45, 47]]                                  # Experiment 9


    # Decide how to simulate touches: a list of timesteps, a specific state, or random
    senseThread.setSimulationMode('list', touched=experimentTouchData[4])

    # senseThread.setSimulationMode('state', 3)

    # senseThread.setSimulationMode('random')

    # Start threads
    actThread.start()
    senseThread.start()

    # Check whether the act thread has finished
    while actThread.is_alive():
        time.sleep(0.1)

    # Stop the sense thread when act thread finished
    senseThread.stop()

    # Wait till both threads finished before closing
    actThread.join()
    senseThread.join()


class Act(Thread):
    ''' This class is used to act in the environment and communicate with the python3 script

    It displays the following behaviour:
        - Read whether a touch occurred in the Touch class
        - Send information about a touch to the python3 script
        - Receive information about a next action from the python3 script
        - Execute the action in the environment (simulated in this case)
    '''
    def __init__(self, touchInstance, timesteps):
        # call the parent constructor
        super(Act, self).__init__()

        # Initiate shared class to share touch data
        self.touchData = touchInstance

        # Initiate the number of timesteps to execute
        self.timesteps = timesteps

        # Initiate socket for connection with python3 script
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Define states and joint names
        self.map = {"S1":[0.1, 0.2, 1.74], "S2": [0.1, -0.1, 1.74], "S3": [0.1, -0.4, 1.74], "S4": [0.1, -0.7, 1.74], "S5": [0.1, -1.0, 1.74], "S6": [0.1, -0.7, 1.74], "S7": [0.1, -0.4, 1.74], "S8": [0.1, -0.1, 1.74]}
        
    def run(self):
        # Connect to python 3 script
        self.socket.connect((HOST, CONNPORT))
        self.socket.settimeout(10)
        print("Connected")

        lock = self.touchData.getLock()
        for _ in range(self.timesteps):  
            lock.acquire()
            # Read whether robot has been touched
            touchVal = self.touchData.readAndReset(1.0)
            # Send value to python3 script
            self.socket.sendall(str(touchVal))
            # Receive action from python3 script
            data = self.socket.recv(1024)
            # Set the shared class state to the new state
            self.touchData.setState(int(data))
            lock.release()
            # Simulate time for robot to move to the new position
            #time.sleep(1)
            # Print information about simulated joint positions and action
            print(data, "Joint positions:", self.map["S{}".format(int(data)+1)])

        # End connection with script
        self.socket.sendall(b"end")
        self.socket.close()

class Sense(Thread):
    ''' This class is used to sense in the environment and update the shared variable if touched

    It displays the following behaviour:
        - Simulate touch either randomly or in specific states
        - Update shared variable when touched
        - Check whether act thread finished and stop thread accordingly
    '''
    def __init__(self, touchInstance):
        # call the parent constructor
        super(Sense, self).__init__()

        # Initiate shared class to store touch data
        self.touchData = touchInstance

        self.i = 0
        self.s = 0
        self.timestep = 1

        # Variable to determine whether touch is random or not
        self.mode = 'random'
        self.state = None
        self.touched = []

        # Create event to stop thread
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def setSimulationMode(self, mode, state=None, touched = []):
        self.mode = mode
        if mode == 'state':
            self.state = state
        elif mode == 'list':
            self.touched = touched

    def run(self):
        lock = self.touchData.getLock()
        while True:
            lock.acquire()
            if self.mode == 'random':                                 # If random touching is initialised, simulate touch randomly
                self.simulateRandomTouch(0.02)
            elif self.mode == 'state':                                           # Else, simulate touch in a specific state
                self.simulateStateTouch()
            else:
                self.simulateTouchList()
            lock.release()
            time.sleep(0.1)
            # Check whether other thread finished
            if self.stopped():
                # If so, break and stop thread
                break

    def simulateRandomTouch(self, prob):
        touchVal = random.random()
        if touchVal < prob:
            self.touchData.readAndReset(0.0)

    def simulateStateTouch(self):
        state = self.touchData.getState()
        if (state == self.state or state == (8-self.state)):
            self.i += 1
            if self.i > 2:
                self.touchData.readAndReset(0.0)

    def simulateTouchList(self):
        if self.i == len(self.touched):
            return
        state = self.touchData.getState()
        if state != self.s:
            if self.timestep == self.touched[self.i]:
                self.i += 1
                self.touchData.readAndReset(0.0)
            self.timestep += 1
            self.s = state
        

if __name__ == "__main__":
    main()