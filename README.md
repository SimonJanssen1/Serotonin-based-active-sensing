# Serotonin-based active sensing

This repository is used for the project:

### Robotic active sensing inspired by serotonin modulation using active inference

The repository consists of several files which are used to evaluate a serotonin-based active sensing model in a humanoid (e.g. a Nao robot in this case). 

## Simulations

The program that is used in order to run simulation experiments can be found under the `Simulationscript_Heatmap.ipynb`. In this script, the active sensing model is run and the experiments are analyzed in simulation with a combination of 13 $\zeta$ values and 13 $\rho$ values (precision parameters used in the model). Hence, a total of 169 (13x13) experiments are run, 8 times each. All of the experiments took 40 time-steps, where after the 8th time step we simulated object appearance at arm position 4. As a final result, the heatmaps are generated which show:
- The time it takes to switch from one policy (movement with large amplitude) to another policy (movement with small amplitude).
- The time it takes to infer the correct context.
- The time period for performing the policy with the movement with small amplitude.

For an explanation of these results, we refer back to our project report.

## Nao experiments

The program that is used in order to run experiments on the Nao robot can be found in the following scripts: `main.py` (model), `model_definition.py` (initialization of matrices) and `RobotScript.py` (script communicating with Nao robot). For an explanation of the architecture and how these scripts work together, we refer back to our project report. Note that the `RobotScript.py` is written for Python 2.7 and the other scripts are written for Python 3.

In order to test whether the architecture is working correctly, we can simulate the script communicating with the Nao robot by replacing the `RobotScript.py` with the `simulationRunRobot.py` script. In this script, the general architecture is the same with an acting and sensing thread and some shared variables. However, instead of communication with the robot to sense the environment and execute actions, the script simulates these behaviours. For the simulation of touch, one can either choose to simulate touch randomly with a predefined probability, simulate touch at a specific arm position or simulate touch at specific time-steps in the experiment.
