"""Exercise the real ROS 2 pub/sub path with only fake nodes."""

import time
import unittest

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from robotics_sim.fake_base import FakeBaseNode
from robotics_sim.safety_gate import SafetyGateNode
from robotics_sim.sim_environment import SimEnvironmentNode
from std_srvs.srv import Trigger


def run_graph_scenario() -> None:
    rclpy.init()
    gate = SafetyGateNode()
    environment = SimEnvironmentNode()
    base = FakeBaseNode()
    probe = Node("sim_probe")
    executor = SingleThreadedExecutor()
    for node in (gate, environment, base, probe):
        executor.add_node(node)
    safe: list[Twist] = []
    odom: list[Odometry] = []
    probe.create_subscription(Twist, "cmd_safe", safe.append, 10)
    probe.create_subscription(Odometry, "odom", odom.append, 10)
    requests = probe.create_publisher(Twist, "cmd_request", 10)
    reset = probe.create_client(Trigger, "reset_estop")

    def pump(seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.02)

    def send_motion(linear: float = 0.2) -> None:
        message = Twist()
        message.linear.x = linear
        requests.publish(message)

    try:
        pump(0.35)
        assert safe and safe[-1].linear.x == 0.0
        assert reset.wait_for_service(timeout_sec=1.0)
        future = reset.call_async(Trigger.Request())
        pump(0.1)
        assert future.done() and future.result().success
        send_motion(0.7)
        pump(0.1)
        assert safe[-1].linear.x == 0.0
        send_motion()
        pump(0.15)
        assert safe[-1].linear.x == 0.2
        assert odom[-1].pose.pose.position.x > 0.0

        environment.status_timer.cancel()
        pump(0.35)
        assert safe[-1].linear.x == 0.0
        environment.status_timer.reset()
        pump(0.15)
        send_motion()
        pump(0.1)
        assert safe[-1].linear.x == 0.0
        future = reset.call_async(Trigger.Request())
        pump(0.1)
        assert future.done() and future.result().success
        send_motion()
        pump(0.1)
        assert safe[-1].linear.x == 0.2

        environment.set_parameters([Parameter("health_ok", value=False)])
        pump(0.2)
        assert safe[-1].linear.x == 0.0
        environment.set_parameters([Parameter("health_ok", value=True)])
        pump(0.15)
        assert safe[-1].linear.x == 0.0

        send_motion()
        pump(0.1)
        assert safe[-1].linear.x == 0.2
        environment.set_parameters([Parameter("obstacle_clear", value=False)])
        pump(0.15)
        assert safe[-1].linear.x == 0.0
        environment.set_parameters([Parameter("obstacle_clear", value=True)])
        pump(0.15)
        assert safe[-1].linear.x == 0.0

        send_motion()
        pump(0.1)
        assert safe[-1].linear.x == 0.2
        environment.set_parameters([Parameter("emergency_stop", value=True)])
        pump(0.15)
        assert safe[-1].linear.x == 0.0
        environment.set_parameters([Parameter("emergency_stop", value=False)])
        pump(0.15)
        send_motion()
        pump(0.1)
        assert safe[-1].linear.x == 0.0
        assert reset.wait_for_service(timeout_sec=1.0)
        future = reset.call_async(Trigger.Request())
        pump(0.1)
        assert future.done() and future.result().success
        send_motion()
        pump(0.1)
        assert safe[-1].linear.x == 0.2
        pump(0.35)
        assert safe[-1].linear.x == 0.0
        assert odom[-1].twist.twist.linear.x == 0.0
    finally:
        for node in (probe, base, environment, gate):
            executor.remove_node(node)
            node.destroy_node()
        executor.shutdown()
        rclpy.shutdown()


class SimGraphTest(unittest.TestCase):
    def test_faults_stop_and_require_fresh_motion(self) -> None:
        run_graph_scenario()

    def test_restart_requires_reset(self) -> None:
        rclpy.init()
        gate = SafetyGateNode()
        environment = SimEnvironmentNode()
        probe = Node("restart_probe")
        executor = SingleThreadedExecutor()
        for node in (gate, environment, probe):
            executor.add_node(node)
        safe: list[Twist] = []
        probe.create_subscription(Twist, "cmd_safe", safe.append, 10)
        requests = probe.create_publisher(Twist, "cmd_request", 10)
        reset = probe.create_client(Trigger, "reset_estop")

        def pump(seconds: float) -> None:
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                executor.spin_once(timeout_sec=0.02)

        def send_motion() -> None:
            request = Twist()
            request.linear.x = 0.2
            requests.publish(request)

        def safe_reset() -> None:
            self.assertTrue(reset.wait_for_service(timeout_sec=1.0))
            future = reset.call_async(Trigger.Request())
            pump(0.15)
            self.assertTrue(future.done() and future.result().success)

        try:
            pump(0.35)
            send_motion()
            pump(0.1)
            self.assertEqual(safe[-1].linear.x, 0.0)
            safe_reset()
            send_motion()
            pump(0.1)
            self.assertEqual(safe[-1].linear.x, 0.2)
            executor.remove_node(gate)
            gate.destroy_node()
            gate = SafetyGateNode()
            executor.add_node(gate)
            pump(0.35)
            send_motion()
            pump(0.1)
            self.assertEqual(safe[-1].linear.x, 0.0)
            safe_reset()
            send_motion()
            pump(0.1)
            self.assertEqual(safe[-1].linear.x, 0.2)
        finally:
            for node in (probe, environment, gate):
                executor.remove_node(node)
                node.destroy_node()
            executor.shutdown()
            rclpy.shutdown()
