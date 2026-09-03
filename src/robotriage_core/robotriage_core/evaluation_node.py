import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class EvaluationNode(Node):
    def __init__(self):
        super().__init__('evaluation_node')

        self.subscription = self.create_subscription(
            String,
            '/robotriage/execution_feedback',
            self.feedback_callback,
            10,
        )
        self.publisher = self.create_publisher(
            String,
            '/robotriage/evaluation_summary',
            10,
        )

    def feedback_callback(self, message):
        try:
            feedback = json.loads(message.data)
        except json.JSONDecodeError:
            self.get_logger().warning('Received invalid execution feedback JSON')
            return

        if not isinstance(feedback, dict) or 'plan_id' not in feedback:
            self.get_logger().warning('Feedback must contain a plan_id')
            return

        results = feedback.get('results')
        if not isinstance(results, list):
            self.get_logger().warning('Feedback must contain a results list')
            return

        required_fields = {
            'object_id',
            'decision_type',
            'final_status',
            'attempts',
            'retry_count',
            'simulated_duration_seconds',
        }
        for result in results:
            if not isinstance(result, dict):
                self.get_logger().warning('Each result must be a JSON object')
                return

            missing_fields = required_fields - result.keys()
            if missing_fields:
                missing = ', '.join(sorted(missing_fields))
                self.get_logger().warning(
                    f'Result is missing required fields: {missing}'
                )
                return

        total_tasks = len(results)
        successful_tasks = sum(
            result['final_status'] == 'success' for result in results
        )
        failed_tasks = sum(
            result['final_status'] == 'failed' for result in results
        )
        total_retries = sum(result['retry_count'] for result in results)
        total_duration = sum(
            result['simulated_duration_seconds'] for result in results
        )

        if total_tasks > 0:
            success_rate = successful_tasks / total_tasks * 100
            average_retries = total_retries / total_tasks
            average_duration = total_duration / total_tasks
            longest_duration = max(
                result['simulated_duration_seconds'] for result in results
            )
        else:
            success_rate = 0.0
            average_retries = 0.0
            average_duration = 0.0
            longest_duration = 0.0

        results_by_object = {}
        for result in results:
            results_by_object.setdefault(result['object_id'], []).append(result)

        decisions = []
        for object_id, object_results in results_by_object.items():
            object_successful_tasks = sum(
                result['final_status'] == 'success'
                for result in object_results
            )
            object_total_tasks = len(object_results)
            decision = {
                'object_id': object_id,
                'decision_type': object_results[0]['decision_type'],
                'total_tasks': object_total_tasks,
                'successful_tasks': object_successful_tasks,
                'failed_tasks': object_total_tasks - object_successful_tasks,
                'decision_success': (
                    object_successful_tasks == object_total_tasks
                ),
                'total_attempts': sum(
                    result['attempts'] for result in object_results
                ),
                'total_retries': sum(
                    result['retry_count'] for result in object_results
                ),
                'total_duration_seconds': round(
                    sum(
                        result['simulated_duration_seconds']
                        for result in object_results
                    ),
                    2,
                ),
            }
            decisions.append(decision)

        total_decisions = len(decisions)
        successful_decisions = sum(
            decision['decision_success'] for decision in decisions
        )
        if total_decisions > 0:
            decision_success_rate = successful_decisions / total_decisions * 100
        else:
            decision_success_rate = 0.0

        decision_type_metrics = {}
        for decision_type in ('reuse', 'remanufacture', 'recycle'):
            matching_decisions = [
                decision for decision in decisions
                if decision['decision_type'] == decision_type
            ]
            type_total = len(matching_decisions)
            type_successful = sum(
                decision['decision_success'] for decision in matching_decisions
            )
            type_success_rate = (
                type_successful / type_total * 100 if type_total > 0 else 0.0
            )
            decision_type_metrics[decision_type] = {
                'total_decisions': type_total,
                'successful_decisions': type_successful,
                'failed_decisions': type_total - type_successful,
                'success_rate_percent': round(type_success_rate, 2),
            }

        metrics = {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate_percent': round(success_rate, 2),
            'task_success_rate_percent': round(success_rate, 2),
            'decision_success_rate_percent': round(
                decision_success_rate,
                2,
            ),
            'plan_success': (
                total_decisions > 0
                and successful_decisions == total_decisions
            ),
            'total_retries': total_retries,
            'average_retries_per_task': round(average_retries, 2),
            'average_duration_seconds': round(average_duration, 2),
            'longest_task_duration_seconds': round(longest_duration, 2),
        }
        summary = {
            'plan_id': feedback['plan_id'],
            'metrics': metrics,
            'decisions': decisions,
            'decision_type_metrics': decision_type_metrics,
        }

        output_message = String()
        output_message.data = json.dumps(summary)
        self.publisher.publish(output_message)
        self.get_logger().info(
            f'Published evaluation for {total_tasks} tasks: '
            f'{metrics["success_rate_percent"]}% success rate'
        )


def main(args=None):
    rclpy.init(args=args)
    node = EvaluationNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()