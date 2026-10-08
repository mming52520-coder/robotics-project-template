"""Smoke-test the installed launch and separate ROS 2 node processes."""

import os
import signal
import subprocess
import tempfile
import time
import unittest

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class InstalledLaunchTest(unittest.TestCase):
    def test_installed_graph_starts_at_zero(self) -> None:
        rclpy.init()
        probe = Node("installed_launch_probe")
        safe_commands: list[Twist] = []
        probe.create_subscription(Twist, "/sim/cmd_safe", safe_commands.append, 10)
        with tempfile.TemporaryFile(mode="w+t") as launch_log:
            process = subprocess.Popen(
                ["ros2", "launch", "robotics_sim", "sim.launch.py"],
                stdout=launch_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 10.0
                expected = {"safety_gate", "fake_base", "sim_environment"}
                while time.monotonic() < deadline:
                    rclpy.spin_once(probe, timeout_sec=0.1)
                    names = {
                        name for name, namespace in probe.get_node_names_and_namespaces()
                        if namespace == "/sim"
                    }
                    if expected <= names and safe_commands:
                        break
                    self.assertIsNone(
                        process.poll(), "installed launch exited before graph was ready"
                    )
                self.assertTrue(expected <= names, f"missing nodes: {expected - names}")
                self.assertTrue(safe_commands, "installed safety gate did not publish")
                self.assertEqual(safe_commands[-1].linear.x, 0.0)
                self.assertEqual(safe_commands[-1].angular.z, 0.0)
            except Exception:
                launch_log.seek(0)
                print(launch_log.read())
                raise
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                probe.destroy_node()
                rclpy.shutdown()
