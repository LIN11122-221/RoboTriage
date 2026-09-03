# RoboTriage

RoboTriage is a ROS2-based decision-to-action framework developed as part of an MSc Robotics project at the University of Birmingham.

The project focuses on the software layer between a high-level battery-triage decision and downstream robotic execution. It converts structured triage decisions into symbolic manipulation tasks, manages execution attempts and retry-based recovery, and records performance data for evaluation.

The current implementation is a software prototype. Battery perception, physical battery disassembly and low-level robot control are outside the scope of the project.

## System Overview

The RoboTriage pipeline contains five main ROS2 nodes:

- **Decision Publisher**  
  Publishes structured battery-triage decisions.

- **Task Planner**  
  Converts the incoming decision into a symbolic pick-and-place task.

- **Execution Manager**  
  Simulates task execution and manages retry-based recovery.

- **Evaluation Node**  
  Processes execution feedback and calculates performance metrics.

- **Experiment Logger**  
  Records experimental parameters and results for later analysis.

The main ROS2 topics are:

- `/robotriage/decisions`
- `/robotriage/task_plan`
- `/robotriage/execution_feedback`
- `/robotriage/evaluation_summary`

The processing flow is:

```text
Upstream Triage Decision
        |
        v
Decision Publisher
        |
        v
Task Planner
        |
        v
Execution Manager
        |
        v
Evaluation Node
        |
        v
Experiment Logger
```

Retry behaviour is handled locally by the Execution Manager so that an execution failure does not require the original high-level triage decision to be changed.

## Decision Representation

The prototype uses JSON payloads to represent upstream battery-triage decisions.

A decision contains information such as:

- `battery_id`
- `risk_level`
- `priority`
- `target_bin`
- `timestamp`

The `target_bin` represents the downstream handling destination selected by the upstream triage system.

The RoboTriage framework does not determine the battery condition or decide which handling pathway should be selected. Its role is to translate the supplied decision into a task that can be passed to the execution layer.

## Repository Structure

```text
robotriage_ros2_ws/
|
├── src/
│   └── robotriage_core/
│       ├── launch/
│       │   └── robotriage_pipeline.launch.py
│       │
│       ├── robotriage_core/
│       │   ├── decision_publisher_node.py
│       │   ├── task_planner_node.py
│       │   ├── execution_manager_node.py
│       │   ├── evaluation_node.py
│       │   └── experiment_logger_node.py
│       │
│       ├── scripts/
│       │   ├── run_experiment_grid.py
│       │   └── plot_experiment_results.py
│       │
│       ├── docs/
│       │   ├── architecture.md
│       │   └── progress_log.md
│       │
│       ├── package.xml
│       ├── setup.py
│       └── setup.cfg
│
├── results_30_final/
│   ├── experiment_grid_summary.csv
│   ├── individual configuration CSV files
│   └── plots/
│
├── experiment_grid_summary_30_final.csv
├── README.md
└── .gitignore
```

## Execution Model

The current prototype does not use a physical robot or physics-based simulator.

Execution uncertainty is represented using a configurable probabilistic model with two main parameters:

- `success_probability` (`p`)  
  Probability that an individual execution attempt succeeds.

- `max_retries` (`r`)  
  Maximum number of additional execution attempts permitted after the initial attempt fails.

The initial attempt is not counted as a retry.

For example:

- `max_retries = 0` allows a maximum of 1 execution attempt.
- `max_retries = 1` allows a maximum of 2 execution attempts.
- `max_retries = 2` allows a maximum of 3 execution attempts.

In general, a retry limit of `r` allows up to `r + 1` execution attempts.

Assuming independent execution attempts with the same success probability, the theoretical probability that a task eventually succeeds is:

```text
P_task = 1 - (1 - p)^(r + 1)
```

This model is used to study retry behaviour under controlled execution uncertainty rather than to reproduce a particular physical robot failure mode.

## Building the ROS2 Workspace

The project was developed using ROS2 Humble on Ubuntu 22.04.

From the workspace directory:

```bash
cd ~/robotriage_ros2_ws
colcon build
source install/setup.bash
```

## Running the ROS2 Pipeline

The complete pipeline can be started using the ROS2 launch file:

```bash
ros2 launch robotriage_core robotriage_pipeline.launch.py
```

This starts the main RoboTriage nodes and allows the decision-to-action workflow to run through ROS2 topics.

## Experimental Evaluation

A parameter sweep was used to evaluate how execution reliability and retry limits affect task-level performance.

The final experiment used the following values:

### Per-attempt success probability

```text
p = {0.1, 0.3, 0.5, 0.7, 0.9}
```

### Maximum retries

```text
r = {0, 1, 2, 4}
```

This produced:

- 5 success-probability settings
- 4 retry settings
- 20 parameter configurations
- 30 repeated trials per configuration
- 3 battery tasks per trial
- 600 experimental trials
- 1800 task-level outcomes

The `r = 0` configuration was used as the no-retry baseline.

The experiment script is located at:

```text
src/robotriage_core/scripts/run_experiment_grid.py
```

The plotting script is located at:

```text
src/robotriage_core/scripts/plot_experiment_results.py
```

## Evaluation Metrics

Three main measures are used to evaluate the execution and recovery behaviour:

- **Task success rate**  
  Percentage of tasks successfully completed after all permitted retries.

- **Average execution attempts**  
  Mean number of attempts required for each task.

- **Average simulated execution duration**  
  Comparative measure of the software execution time associated with different retry settings.

The simulated execution duration should not be interpreted as a physical robot cycle time.

## Results

The experiments show that retry-based recovery can improve final task-level reliability, but the benefit depends on the underlying per-attempt execution probability.

For example, with:

```text
p = 0.7
```

the observed task success rate increased from:

```text
70.00% with no retries
```

to:

```text
93.33% with one retry
```

and:

```text
98.89% with two retries
```

At very low execution reliability, additional retries provide a smaller reliability improvement while increasing the number of attempts and simulated execution duration.

The results therefore illustrate a trade-off between task reliability and execution cost.

Final experimental data and plots are stored in:

```text
results_30_final/
```

## Environment

The project was developed using:

- Ubuntu 22.04
- WSL2
- ROS2 Humble
- Python
- ROS2 Python packages

## Project Scope

RoboTriage focuses specifically on the decision-to-action software layer.

The following areas are outside the scope of the current prototype:

- battery perception and condition estimation
- physical battery disassembly
- robot grasp generation
- geometric motion planning
- collision-free trajectory generation
- low-level robot control
- validation on a physical manipulator

The upstream battery-triage decision is assumed to have already been generated before entering the RoboTriage pipeline.

The current probabilistic execution layer could later be replaced by a physics-based simulator, motion-planning framework such as MoveIt, or a physical robotic platform while preserving the same high-level decision interface.

## Future Work

Possible extensions include:

- integration with a physics-based robot simulator
- integration with MoveIt for motion planning
- use of custom ROS2 message types instead of JSON string messages
- explicit execution-failure classification
- adaptive recovery instead of fixed retry behaviour
- alternative grasp or replanning strategies after repeated failures
- integration with a physical manipulator

## Project Status

The current repository contains the completed ROS2 prototype and the final parameter-sweep experiment results used for the MSc project evaluation.
