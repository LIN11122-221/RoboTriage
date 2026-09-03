import json
import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ExecutionManager(Node):
    def __init__(self):
        super().__init__('execution_manager_node')

        self.declare_parameter('success_probability', 0.85)
        self.declare_parameter('max_retries', 2)

        self.success_probability = float(
            self.get_parameter('success_probability').value
        )
        self.max_retries = int(self.get_parameter('max_retries').value)

        self.get_logger().info(
            'Execution Manager started with '
            f'success_probability={self.success_probability}, '
            f'max_retries={self.max_retries}'
        )

        self.subscription = self.create_subscription(
            String,
            '/robotriage/task_plan',
            self.task_plan_callback,
            10,
        )
        self.publisher = self.create_publisher(
            String,
            '/robotriage/execution_feedback',
            10,
        )

    def task_plan_callback(self, message):
        try:
            task_plan = json.loads(message.data)
        except json.JSONDecodeError:
            self.get_logger().warning('Received invalid task plan JSON')
            return

        if not isinstance(task_plan, dict) or 'plan_id' not in task_plan:
            self.get_logger().warning('Task plan must contain a plan_id')
            return

        tasks = task_plan.get('tasks')
        if not isinstance(tasks, list):
            self.get_logger().warning('Task plan must contain a tasks list')
            return

        results = []
        required_fields = {
            'task_id', 'object_id', 'action', 'target_bin', 'decision_type'
        }

        for task in tasks:
            if not isinstance(task, dict):
                self.get_logger().warning('Each task must be a JSON object')
                return

            missing_fields = required_fields - task.keys()
            if missing_fields:
                missing = ', '.join(sorted(missing_fields))
                self.get_logger().warning(
                    f'Task is missing required fields: {missing}'
                )
                return

            results.append(self.execute_task(task))

        feedback = {
            'plan_id': task_plan['plan_id'],
            'results': results,
        }

        output_message = String()
        output_message.data = json.dumps(feedback)
        self.publisher.publish(output_message)

        successful_tasks = sum(
            result['status'] == 'success' for result in results
        )
        failed_tasks = len(results) - successful_tasks
        self.get_logger().info(
            f'Published execution feedback: {successful_tasks} succeeded, '
            f'{failed_tasks} failed'
        )

    def execute_task(self, task):
        attempts = 0
        duration = 0.0
        succeeded = False

        while attempts <= self.max_retries and not succeeded:
            attempts += 1
            duration += random.uniform(0.5, 2.0)
            succeeded = random.random() < self.success_probability

        status = 'success' if succeeded else 'failed'
        retry_count = attempts - 1

        return {
            'task_id': task['task_id'],
            'action': task['action'],
            'decision_type': task['decision_type'],
            'target_box': task['target_bin'],
            'status': status,
            'attempts': attempts,
            'max_retries': self.max_retries,
            'success_probability': self.success_probability,
            'object_id': task['object_id'],
            'target_bin': task['target_bin'],
            'final_status': status,
            'retry_count': retry_count,
            'simulated_duration_seconds': round(duration, 2),
        }


def main(args=None):
    rclpy.init(args=args)
    node = ExecutionManager()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
