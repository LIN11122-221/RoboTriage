# RoboTriage Decision-to-Action Framework

## Current Development Status

RoboTriage has reached a functional minimum viable product (MVP) stage in both its original Python implementation and its ROS2 implementation. The current system demonstrates the complete decision-to-action workflow for mock battery-sorting tasks: decision generation, task planning, simulated execution, and performance evaluation.

The ROS2 version separates these responsibilities into modular nodes connected through topics. This provides a foundation for subsequent experimental evaluation, parameter configuration, custom ROS2 interfaces, and robot simulation integration.

## Completed Python MVP

The standalone Python MVP established and tested the core processing logic before migration to ROS2. Completed components include:

- Mock decision input representing battery risk classifications and sorting destinations.
- A task planner that converts decisions into prioritised manipulation tasks.
- An execution simulator that models task success, failure, retries, and duration.
- Evaluation metrics for measuring task outcomes and execution performance.
- A one-click Python pipeline for running the complete workflow.

## Completed ROS2 MVP

The Python workflow has been transferred into the `robotriage_core` ROS2 package. The completed ROS2 components are:

- `robotriage_core` package.
- `decision_publisher_node` for publishing mock battery decisions.
- `task_planner_node` for validating decisions and generating prioritised task plans.
- `execution_manager_node` for simulating task execution and retry behaviour.
- `evaluation_node` for calculating aggregate performance metrics.
- `robotriage_pipeline.launch.py` for starting the complete pipeline.

The launch file has been used successfully to start all four nodes together. This provides a single command for executing the complete ROS2 decision-to-action pipeline.

## Verified ROS2 Topics

Communication between the nodes has been verified using the following topics:

- `/robotriage/decisions`
- `/robotriage/task_plan`
- `/robotriage/execution_feedback`
- `/robotriage/evaluation_summary`

The current ROS2 MVP uses `std_msgs/msg/String` messages with JSON payloads. This approach supports rapid prototyping because messages are easy to generate, inspect, and debug using standard ROS2 command-line tools. It also allows the node responsibilities and data flow to be evaluated before committing to custom interface definitions.

## Evidence Collected

Evidence collected for the current implementation includes:

- Terminal output from `ros2 launch robotriage_core robotriage_pipeline.launch.py`, showing the four nodes starting and publishing data.
- Output from `ros2 topic echo /robotriage/evaluation_summary`, demonstrating the final evaluation data produced by the pipeline.
- The package `README.md`, documenting the architecture, build procedure, launch command, nodes, and topics.

These records provide evidence that the implemented ROS2 components communicate through the intended topic-based architecture and complete the end-to-end workflow.

## Next Development Steps

The next planned development activities are:

- Add configurable ROS2 parameters for simulation behaviour and publishing settings.
- Collect metrics across repeated trials to support quantitative evaluation.
- Consider integration with a simple robot simulation to connect planned tasks to visible actions.
- Later replace JSON strings with custom ROS2 message definitions for stronger typing and clearer interface contracts.

These steps will extend the current MVP towards a more configurable and experimentally rigorous robotics framework while preserving the modular architecture already established.
