# Source

Organize implementation by stable subsystem boundaries. Keep hardware transports behind interfaces so simulation and fake backends can exercise control logic without physical actuation.

`robotics_sim/` is a ROS 2 Jazzy `ament_python` package. It contains a pure Python motion gate, ROS adapters, a fake base, synthetic fault inputs, a launch file, and a ROS graph test. No hardware transport is implemented.
