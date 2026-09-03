# RoboTriage Core

RoboTriage is a ROS2-based Decision-to-Action Framework for battery triage simulation. The package demonstrates how decision outputs can be converted into ordered robot-style tasks, executed by a configurable simulator, evaluated, and logged for repeated experiments.

The current implementation is intentionally scoped as a framework and experiment pipeline. It is not a computer-vision system, it does not perform physical battery disassembly, and it does not implement complex decision-making algorithms. The decision input is mocked so that the implemented contribution can focus on the integration path from decisions to task planning, execution feedback, logging, and evaluation.

## Implemented Package

The implemented ROS2 package is:

```text
robotriage_core
```

Main package structure:

```text
src/robotriage_core/
|-- launch/
|   `-- robotriage_pipeline.launch.py
|-- robotriage_core/
|   |-- decision_publisher_node.py
|   |-- task_planner_node.py
|   |-- execution_manager_node.py
|   |-- evaluation_node.py
|   `-- experiment_logger_node.py
|-- scripts/
|   |-- run_experiment_grid.py
|   `-- plot_experiment_results.py
|-- docs/
|   |-- architecture.md
|   `-- progress_log.md
|-- package.xml
|-- setup.py
|-- setup.cfg
`-- README.md
```

## Pipeline

The core pipeline contains five ROS2 nodes:

| Node | Role |
| --- | --- |
| `decision_publisher_node` | Publishes a mock batch of battery triage decisions. |
| `task_planner_node` | Validates the decision JSON and converts it into priority-ordered pick-and-place tasks. |
| `execution_manager_node` | Simulates task execution with configurable success probability and retry behaviour. |
| `evaluation_node` | Computes aggregate metrics from execution feedback. |
| `experiment_logger_node` | Optionally records evaluation summaries to CSV for repeated trials. |

The topic pipeline is:

```text
/robotriage/decisions
/robotriage/task_plan
/robotriage/execution_feedback
/robotriage/evaluation_summary
```

All topics currently use `std_msgs/msg/String` with JSON payloads. This keeps the prototype easy to inspect with standard ROS2 tools while preserving clear boundaries between decision, planning, execution, evaluation, and logging.

## Build

From a ROS2-enabled terminal:

```bash
cd ~/robotriage_ros2_ws
colcon build
source install/setup.bash
```

Source the workspace again in each new terminal:

```bash
cd ~/robotriage_ros2_ws
source install/setup.bash
```

## Run the Pipeline

Launch the full pipeline:

```bash
ros2 launch robotriage_core robotriage_pipeline.launch.py
```

The launch file starts the decision publisher, task planner, execution manager, and evaluation node. The experiment logger is disabled by default.

## Launch Parameters

`robotriage_pipeline.launch.py` supports:

| Parameter | Default | Purpose |
| --- | ---: | --- |
| `success_probability` | `0.85` | Probability that one execution attempt succeeds. |
| `max_retries` | `2` | Maximum number of retries after a failed attempt. |
| `enable_experiment_logger` | `false` | Enables CSV logging of evaluation summaries. |
| `experiment_output_csv` | `experiment_results.csv` | CSV path used by the experiment logger. |
| `max_trials` | `10` | Number of evaluation summaries to record. |

Example launch with experiment logging enabled:

```bash
ros2 launch robotriage_core robotriage_pipeline.launch.py \
  enable_experiment_logger:=true \
  experiment_output_csv:=experiment_results.csv \
  max_trials:=10 \
  success_probability:=0.85 \
  max_retries:=2
```

## Inspect Topics

In another sourced terminal:

```bash
ros2 topic echo /robotriage/decisions
ros2 topic echo /robotriage/task_plan
ros2 topic echo /robotriage/execution_feedback
ros2 topic echo /robotriage/evaluation_summary
```

The final summary includes metrics such as total tasks, successful tasks, failed tasks, success rate, retries, average simulated duration, and longest simulated task duration.

## Experiment Grid

The experiment grid script runs the ROS2 launch file repeatedly across combinations of execution parameters:

```bash
python3 src/robotriage_core/scripts/run_experiment_grid.py
```

Useful options:

```bash
python3 src/robotriage_core/scripts/run_experiment_grid.py \
  --success-probabilities 0.1 0.3 0.5 0.7 0.9 \
  --max-retries-values 0 1 2 4 \
  --max-trials 30 \
  --output-dir results_30_final
```

The script uses a separate `ROS_DOMAIN_ID` for each parameter combination and performs process group cleanup for launched ROS2 child processes.

To rebuild only the summary CSV from existing per-condition CSV files:

```bash
python3 src/robotriage_core/scripts/run_experiment_grid.py \
  --success-probabilities 0.1 0.3 0.5 0.7 0.9 \
  --max-retries-values 0 1 2 4 \
  --max-trials 30 \
  --output-dir results_30_final \
  --summarise-only
```

## Final 600-Trial Experiment

The final clean experiment output is stored in:

```text
results_30_final/
```

It contains 20 parameter combinations:

- `success_probability`: `0.1`, `0.3`, `0.5`, `0.7`, `0.9`
- `max_retries`: `0`, `1`, `2`, `4`
- `30` trials per combination
- `600` total trials

The summary file:

```text
results_30_final/experiment_grid_summary.csv
```

shows all 20 runs completed successfully. The highest measured success rates reached `100.0%` for `success_probability=0.7, max_retries=4`, `success_probability=0.9, max_retries=2`, and `success_probability=0.9, max_retries=4`.

Generated plots are stored in:

```text
results_30_final/plots/
```

Generated plot files:

- `success_probability_vs_success_rate.png`
- `retries_vs_success_rate.png`
- `retries_vs_average_attempts.png`
- `retries_vs_average_duration.png`

The plot script currently contains default paths for `results_30`. To regenerate plots for the final directory without changing source code:

```bash
python3 -c "from pathlib import Path; import sys; sys.path.insert(0, 'src/robotriage_core/scripts'); import plot_experiment_results as p; p.INPUT_CSV = Path('results_30_final/experiment_grid_summary.csv'); p.OUTPUT_DIR = Path('results_30_final/plots'); p.main()"
```

## Documentation

Architecture details and Mermaid diagrams are in:

```text
src/robotriage_core/docs/architecture.md
```

The architecture document covers the component architecture, topic flow, single-trial sequence, retry state machine, launch configuration, and final experiment outputs.
