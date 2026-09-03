import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


TASK_SEQUENCES = {
    'reuse': ['pick_battery', 'inspect_battery', 'isolate_for_reuse'],
    'remanufacture': [
        'pick_battery',
        'inspect_battery',
        'remove_component',
        'route_for_remanufacture',
    ],
    'recycle': [
        'pick_battery',
        'complete_disassembly',
        'separate_components',
        'route_for_recycling',
    ],
}

class TaskPlanner(Node):
    def __init__(self):
        super().__init__('task_planner_node')

        self.subscription = self.create_subscription(
            String,
            '/robotriage/decisions',
            self.decision_callback,
            10,
        )
        self.publisher = self.create_publisher(
            String,
            '/robotriage/task_plan',
            10,
        )

    def decision_callback(self, message):
        try:
            decision = json.loads(message.data)
        except json.JSONDecodeError:
            self.get_logger().warning('Received invalid decision JSON')
            return

        batteries = decision.get('batteries')
        if not isinstance(batteries, list):
            self.get_logger().warning('Decision payload must contain a batteries list')
            return

        required_fields = {
            'id', 'risk_level', 'target_bin', 'priority', 'decision_type'
        }
        for battery in batteries:
            if not isinstance(battery, dict):
                self.get_logger().warning('Each battery must be a JSON object')
                return

            missing_fields = required_fields - battery.keys()
            if missing_fields:
                missing = ', '.join(sorted(missing_fields))
                self.get_logger().warning(
                    f'Battery is missing required fields: {missing}'
                )
                return

            if battery['decision_type'] not in TASK_SEQUENCES:
                self.get_logger().warning(
                    'Battery has unsupported decision_type: '
                    f"{battery['decision_type']}"
                )
                return

        sorted_batteries = sorted(
            batteries,
            key=lambda battery: battery['priority'],
        )

        tasks = []
        for battery in sorted_batteries:
            for action in TASK_SEQUENCES[battery['decision_type']]:
                task = {
                    'task_id': f'task_{len(tasks) + 1:03d}',
                    'object_id': battery['id'],
                    'action': action,
                    'source_location': 'sorting_area',
                    'target_bin': battery['target_bin'],
                    'decision_type': battery['decision_type'],
                    'risk_level': battery['risk_level'],
                    'priority': battery['priority'],
                    'status': 'pending',
                }
                tasks.append(task)

        task_plan = {
            'plan_id': decision.get('plan_id'),
            'tasks': tasks,
        }

        output_message = String()
        output_message.data = json.dumps(task_plan)
        self.publisher.publish(output_message)
        self.get_logger().info('Published task plan')


def main(args=None):
    rclpy.init(args=args)
    node = TaskPlanner()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
