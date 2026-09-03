# RoboTriage

RoboTriage is a ROS2-based decision-to-action framework developed for an MSc Robotics project at the University of Birmingham.

The framework connects high-level battery-triage decisions with symbolic task planning, execution management, retry-based recovery, feedback and evaluation.

## System Architecture

The ROS2 pipeline contains five main nodes:

- Decision Publisher
- Task Planner
- Execution Manager
- Evaluation Node
- Experiment Logger

Main ROS2 topics:

- `/robotriage/decisions`
- `/robotriage/task_plan`
- `/robotriage/execution_feedback`
- `/robotriage/evaluation_summary`

## Execution Model

Execution uncertainty is represented using:

- `success_probability`: probability that an individual execution attempt succeeds
- `max_retries`: maximum number of additional attempts after the initial attempt

The framework evaluates the trade-off between task reliability and execution cost under different parameter settings.

## Experiments

The final parameter sweep used:

- Success probabilities: `0.1, 0.3, 0.5, 0.7, 0.9`
- Maximum retries: `0, 1, 2, 4`
- 30 repeated trials per configuration
- 3 battery tasks per trial
- 600 experimental trials
- 1800 task-level outcomes

## Environment

- Ubuntu 22.04
- ROS2 Humble
- Python

## Project Scope

This prototype focuses on the decision-to-action software layer. Battery perception, physical battery disassembly and low-level robot control are outside the scope of the current implementation.
