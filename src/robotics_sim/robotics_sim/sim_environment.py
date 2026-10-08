"""Synthetic, switchable safety inputs for fault injection in simulation."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


class SimEnvironmentNode(Node):
    def __init__(self) -> None:
        super().__init__("sim_environment")
        self.declare_parameter("emergency_stop", False)
        self.declare_parameter("health_ok", True)
        self.declare_parameter("obstacle_clear", True)
        self.status_publishers = {
            name: self.create_publisher(Bool, name, 10)
            for name in ("emergency_stop", "health_ok", "obstacle_clear")
        }
        self.status_timer = self.create_timer(0.1, self._publish)

    def _publish(self) -> None:
        for name, publisher in self.status_publishers.items():
            message = Bool()
            message.data = self.get_parameter(name).value
            publisher.publish(message)


def main() -> None:
    rclpy.init()
    node = SimEnvironmentNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
