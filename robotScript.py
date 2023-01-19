'''
Course:  Human-Robot Interaction
Authors: Filip Novicky, Joshua Offergeld, Simon Janssen, Ariyan Tufchi
Date:    13-01-2023

This script is used to execute active sensing in the robot. Two threads are created:

- Touches are simulated in the Sense class. 
- Actions are simulated in the Act class. 

The Touch class is needed to share variables between the two threads.
'''
import argparse
from naoqi import ALProxy
import socket
from threading import Lock, Thread, Event
import time

IP = "169.254.66.84"   # set your robot IP address here
PORT = 9559            # set your robot connection port here

HOST = 'localhost'     # set host for connection with python3 script
CONNPORT = 8081        # set connection port for connection with python3 script

class Touch():
    def __init__(self):
        self.lock = Lock()
        self.touched = 1.0

    def getLock(self):
        return self.lock

    def readAndReset(self, value):
        val = self.touched
        self.touched = value
        return val

def main(args):
    """ Main entry point

    """
    touchData = Touch()                # Create shared class to update touch variable
    
    actThread = Act(args, touchData)         # Create thread for acting in environment
    senseThread = Sense(args, touchData)     # Create thread for sensing in environment

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
        - Execute the action in the environment
    '''
    def __init__(self, args, touchInstance):
        # call the parent constructor
        super(Act, self).__init__()

        # Initiate shared touch variable
        self.touchData = touchInstance

        # Initiate socket for connection with python3 script
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Get access to robot joints and speech unit
        self.motionProxy = ALProxy("ALMotion", args.ip, args.port) 
        self.tts = ALProxy("ALTextToSpeech", args.ip, args.port) 

        # Define states and joint names
        self.map = {"S1":[0.1, 0.2, 1.74], "S2": [0.1, -0.1, 1.74], "S3": [0.1, -0.4, 1.74], "S4": [0.1, -0.7, 1.74], "S5": [0.1, -1.0, 1.74], "S6": [0.1, -0.7, 1.74], "S7": [0.1, -0.4, 1.74], "S8": [0.1, -0.1, 1.74]}
        self.names = ["RShoulderPitch", "RShoulderRoll", "RWristYaw"]

    def run(self):
        # Connect to python 3 script
        self.socket.connect((HOST, CONNPORT))
        self.socket.settimeout(10)
        print("Connected")

        lock = self.touchData.getLock()
        
        for _ in range(60):  
            lock.acquire()
            # Read whether robot has been touched
            touchVal = self.touchData.readAndReset(1.0)
            if touchVal == 0.0:
                # Let environment know that the robot felt something by saying "Ooh"
                self.tts.post.say("Ooh")
            # Send value to python3 script
            self.socket.sendall(str(touchVal))
            # Receive action from python3 script
            data = self.socket.recv(1024)
            # Print information about joint positions and action
            print(data, "Joint positions:", self.map["S{}".format(int(data)+1)])
            jointPositions = self.map["S{}".format(int(data)+1)]
            # Move to the next state
            self.motionProxy.angleInterpolation(self.names, jointPositions, [1, 1, 1], True)
            lock.release()
            # Move up and down again to sense in the state
            jointPositions[0] += 0.1
            self.motionProxy.angleInterpolation(self.names, jointPositions, [0.8, 0.8, 0.8], True)
            jointPositions[0] -= 0.1
            self.motionProxy.angleInterpolation(self.names, jointPositions, [0.8, 0.8, 0.8], True)

        self.tts.say("Moving down")
        # End connection with script
        self.socket.sendall(b"end")
        self.socket.close()

class Sense(Thread):
    ''' This class is used to sense in the environment and update the shared variable if touched

    It displays the following behaviour:
        - Read sensor data from the touch sensor on the back of the right hand
        - Update shared variable when touched
        - Check whether act thread finished and stop thread accordingly
    '''
    def __init__(self, args, touchInstance):
        # call the parent constructor
        super(Sense, self).__init__()

        # Initiate shared touch variable
        self.touchData = touchInstance

        # Get access to robot memory to read sensorvalues
        self.memoryProxy = ALProxy("ALMemory", args.ip, args.port)  

        # Create event to stop thread
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        lock = self.touchData.getLock()

        while True:
            lock.acquire()
            # Read the touch sensor value on the back of the robot's right hand
            touchVal = self.memoryProxy.getData("Device/SubDeviceList/RHand/Touch/Back/Sensor/Value")
            # If the value is bigger than 0.0, this indicates a touch
            if touchVal > 0.0:
                self.touchData.readAndReset(0.0)
            lock.release()
            # Check whether other thread finished
            if self.stopped():
                # If so, break and stop thread
                break
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default=IP,
                        help="Robot IP address. If unsure, press the button on the robot chest to get the IP address.")
    parser.add_argument("--port", type=int, default=PORT,
                        help="Naoqi port number. Standard port number is 9559.")
    args = parser.parse_args()

    main(args)