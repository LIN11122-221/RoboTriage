import csv
import json
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ExperimentLogger(Node):
    def __init__(self):
        super().__init__('experiment_logger_node')

        self.declare_parameter('output_csv', 'experiment_results.csv')
        self.declare_parameter('max_trials', 10)

        self.output_csv = str(self.get_parameter('output_csv').value)
        self.max_trials = int(self.get_parameter('max_trials').value)
        self.trials = []
        self.finished = False

        self.subscription = self.create_subscription(
            String,
            '/robotriage/evaluation_summary',
            self.evaluation_callback,
            10,
        )

        self.get_logger().info(
            f'Experiment Logger started with output_csv={self.output_csv}, '
            f'max_trials={self.max_trials}'
        )

    def evaluation_callback(self, message):
        if self.finished:
            return

        try:
            summary = json.loads(message.data)
        except json.JSONDecodeError:
            self.get_logger().warning('Received invalid evaluation summary JSON')
            return

        if not isinstance(summary, dict) or 'plan_id' not in summary:
            self.get_logger().warning('Evaluation summary must contain a plan_id')
            return

        metrics = summary.get('metrics')
        if not isinstance(metrics, dict):
            self.get_logger().warning('Evaluation summary must contain metrics')
            return

        average_retries = metrics.get('average_retries_per_task', 0.0)
        decisions = summary.get('decisions')
        if isinstance(decisions, list):
            valid_decisions = [
                decision for decision in decisions
                if isinstance(decision, dict)
            ]
            total_decisions = len(valid_decisions)
            successful_decisions = sum(
                decision.get('decision_success') is True
                for decision in valid_decisions
            )
            failed_decisions = total_decisions - successful_decisions
            total_attempts = sum(
                decision.get('total_attempts', 0)
                for decision in valid_decisions
            )
            total_duration = round(
                sum(
                    decision.get('total_duration_seconds', 0.0)
                    for decision in valid_decisions
                ),
                2,
            )
        else:
            total_decisions = ''
            successful_decisions = ''
            failed_decisions = ''
            total_attempts = ''
            total_duration = ''

        decision_type_metrics = summary.get('decision_type_metrics', {})
        if not isinstance(decision_type_metrics, dict):
            decision_type_metrics = {}

        trial = {
            'trial_id': len(self.trials) + 1,
            'plan_id': summary['plan_id'],
            'total_tasks': metrics.get('total_tasks', ''),
            'succeeded': metrics.get('successful_tasks', ''),
            'failed': metrics.get('failed_tasks', ''),
            'success_rate': metrics.get('success_rate_percent', ''),
            'average_attempts': round(average_retries + 1, 2),
            'average_duration_seconds': metrics.get(
                'average_duration_seconds',
                '',
            ),
            'task_success_rate_percent': metrics.get(
                'task_success_rate_percent',
                '',
            ),
            'decision_success_rate_percent': metrics.get(
                'decision_success_rate_percent',
                '',
            ),
            'plan_success': metrics.get('plan_success', ''),
            'total_decisions': total_decisions,
            'successful_decisions': successful_decisions,
            'failed_decisions': failed_decisions,
            'total_retries': metrics.get('total_retries', ''),
            'total_attempts': total_attempts,
            'total_duration_seconds': total_duration,
            'timestamp': datetime.now().isoformat(timespec='seconds'),
        }

        for decision_type in ('reuse', 'remanufacture', 'recycle'):
            type_metrics = decision_type_metrics.get(decision_type, {})
            if not isinstance(type_metrics, dict):
                type_metrics = {}
            trial[f'{decision_type}_total_decisions'] = type_metrics.get(
                'total_decisions',
                '',
            )
            trial[f'{decision_type}_successful_decisions'] = type_metrics.get(
                'successful_decisions',
                '',
            )
            trial[f'{decision_type}_failed_decisions'] = type_metrics.get(
                'failed_decisions',
                '',
            )
            trial[f'{decision_type}_success_rate_percent'] = type_metrics.get(
                'success_rate_percent',
                '',
            )

        self.trials.append(trial)
        self.save_results()

        self.get_logger().info(
            f'Recorded trial {len(self.trials)}/{self.max_trials}'
        )

        if len(self.trials) >= self.max_trials:
            self.finished = True
            self.get_logger().info(
                f'Saved experiment results to {self.output_csv}'
            )

    def save_results(self):
        fieldnames = [
            'trial_id',
            'plan_id',
            'total_tasks',
            'succeeded',
            'failed',
            'success_rate',
            'average_attempts',
            'average_duration_seconds',
            'task_success_rate_percent',
            'decision_success_rate_percent',
            'plan_success',
            'total_decisions',
            'successful_decisions',
            'failed_decisions',
            'total_retries',
            'total_attempts',
            'total_duration_seconds',
            'reuse_total_decisions',
            'reuse_successful_decisions',
            'reuse_failed_decisions',
            'reuse_success_rate_percent',
            'remanufacture_total_decisions',
            'remanufacture_successful_decisions',
            'remanufacture_failed_decisions',
            'remanufacture_success_rate_percent',
            'recycle_total_decisions',
            'recycle_successful_decisions',
            'recycle_failed_decisions',
            'recycle_success_rate_percent',
            'timestamp',
        ]

        with open(self.output_csv, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.trials)


def main(args=None):
    rclpy.init(args=args)
    node = ExperimentLogger()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
