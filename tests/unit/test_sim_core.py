"""Offline regression checks for the simulation motion path."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "robotics_sim"))

from robotics_sim.core import FakeBase, SafetyGate  # noqa: E402


class SafetyGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = SafetyGate()
        self.gate.receive_estop(False, 1.0)
        self.gate.receive_health(True, 1.0)
        self.gate.receive_obstacle(True, 1.0)

    def test_requires_fresh_status_and_command(self) -> None:
        self.assertEqual(self.gate.output(1.0), (0.0, 0.0))
        self.assertTrue(self.gate.receive_command(0.3, 0.2, 1.0))
        self.assertEqual(self.gate.output(1.1), (0.3, 0.2))
        self.assertEqual(self.gate.output(1.26), (0.0, 0.0))
        self.gate.receive_command(0.3, 0.2, 1.31)
        self.assertEqual(self.gate.output(1.31), (0.0, 0.0))

    def test_rejects_invalid_or_unbounded_request(self) -> None:
        for linear, angular in ((0.61, 0), (0, 1.01), (math.nan, 0), (0, math.inf)):
            self.gate.receive_command(0.2, 0.0, 1.0)
            self.assertFalse(self.gate.receive_command(linear, angular, 1.01))
            self.assertEqual(self.gate.output(1.01), (0.0, 0.0))

    def test_estop_latches_and_reset_requires_new_command(self) -> None:
        self.gate.receive_command(0.2, 0.0, 1.0)
        self.gate.receive_estop(True, 1.01)
        self.gate.receive_estop(False, 1.02)
        self.assertEqual(self.gate.output(1.02), (0.0, 0.0))
        self.assertTrue(self.gate.reset_estop(1.03))
        self.assertEqual(self.gate.output(1.03), (0.0, 0.0))
        self.gate.receive_command(0.2, 0.0, 1.04)
        self.assertEqual(self.gate.output(1.04), (0.2, 0.0))

    def test_reset_refused_while_fault_active_or_stale(self) -> None:
        self.gate.receive_estop(True, 1.01)
        self.assertFalse(self.gate.reset_estop(1.02))
        self.gate.receive_estop(False, 1.03)
        self.gate.receive_obstacle(False, 1.03)
        self.assertFalse(self.gate.reset_estop(1.04))
        self.gate.receive_obstacle(True, 1.05)
        self.assertFalse(self.gate.reset_estop(1.4))

    def test_fault_clears_previous_command(self) -> None:
        for fault in (self.gate.receive_health, self.gate.receive_obstacle):
            self.gate.receive_command(0.2, 0.0, 1.0)
            fault(False, 1.01)
            fault(True, 1.02)
            self.assertEqual(self.gate.output(1.02), (0.0, 0.0))


class FakeBaseTests(unittest.TestCase):
    def test_motion_and_independent_timeout(self) -> None:
        base = FakeBase()
        base.step(1.0)
        base.receive_command(0.2, 0.0, 1.0)
        self.assertEqual(base.step(1.1), (0.2, 0.0))
        self.assertAlmostEqual(base.x, 0.02)
        self.assertEqual(base.step(1.21), (0.0, 0.0))
        self.assertAlmostEqual(base.x, 0.02)


if __name__ == "__main__":
    unittest.main()
