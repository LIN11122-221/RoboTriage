# RoboTriage

RoboTriage is a ROS2-based decision-to-action framework developed as part of an MSc Robotics project at the University of Birmingham.

The project focuses on the software layer between a high-level battery-triage decision and downstream robotic execution. It converts structured triage decisions into symbolic tasks, manages execution attempts and retries, and records performance results for evaluation.

## System Overview

The ROS2 pipeline contains five main nodes:

- Decision Publisher
- Task Planner
- Execution Manager
- Evaluation Node
- Experiment Logger

The main ROS2 topics are:

- `/robotriage/decisions`
- `/robotriage/task_plan`
- `/robotriage/execution_feedback`
- `/robotriage/evaluation_summary`

## Repository Structure

```text
src/robotriage_core/
├── launch/
├── robotriage_core/
├── scripts/
├── docs/
├── package.xml
├── setup.py
└── setup.cfg

results_30_final/
├── CSV experiment results
└── plots
