import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DecisionPublisherNode(Node):
    """Publish mock battery triage decisions for the RoboTriage ROS2 pipeline."""

    def __init__(self):
        super().__init__("decision_publisher_node")

        self.publisher = self.create_publisher(
            String,
            "/robotriage/decisions",
            10,
        )

        self.timer = self.create_timer(2.0, self.publish_decisions)

        self.decision_batch = {
            "plan_id": "plan_001",
            "batteries": [
                {
                    "id": "battery_001",
                    "risk_level": "high",
                    "target_bin": "hazardous_bin",
                    "priority": 1,
                    "decision_type": "recycle",
                },
                {
                    "id": "battery_002",
                    "risk_level": "low",
                    "target_bin": "reuse_bin",
                    "priority": 3,
                    "decision_type": "reuse",
                },
                {
                    "id": "battery_003",
                    "risk_level": "medium",
                    "target_bin": "remanufacturing_bin",
                    "priority": 2,
                    "decision_type": "remanufacture",
                },
            ],
        }

    def publish_decisions(self):
        msg = String()
        msg.data = json.dumps(self.decision_batch)

        self.publisher.publish(msg)
        self.get_logger().info("Published decision batch: plan_001")


def main(args=None):
    rclpy.init(args=args)
    node = DecisionPublisherNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

