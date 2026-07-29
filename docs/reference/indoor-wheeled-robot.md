# Indoor wheeled robot reference / 室内轮式机器人参考

## Scope / 范围

This repository supports controlled indoor research and logistics robots with a wheeled base. It assumes a ROS 2 reference architecture, restricted access during autonomous trials, and simulation before physical testing.

本仓库面向受控研发和物流场景下的室内轮式机器人，采用 ROS 2 参考架构，要求自主试验期间限制人员进入，并坚持先仿真、后实机。

## Functional architecture / 功能架构

```text
mission manager -> navigation -> safety gate -> base interface
                         ^             ^
                    localization    diagnostics
```

Keep mission, navigation, safety, diagnostics, and hardware transport responsibilities separate. The safety gate is the only owner allowed to pass bounded motion requests to the base interface.

任务、导航、安全、诊断和硬件传输必须职责分离。安全门是唯一可向底盘接口传递有界运动请求的组件。

## Model-free hardware vocabulary / 型号无关硬件术语

Describe hardware as functional blocks: motion feedback, inertial motion observation, obstacle observation, compute, power, communication, diagnostics, and mechanical installation. State required performance, interface, health signal, environment, and degradation behavior. Do not add a product recommendation or bill of materials.

硬件只应描述为功能模块：运动反馈、惯性运动观测、障碍物观测、计算、电源、通信、诊断和机械安装。必须说明性能、接口、健康状态、环境与降级行为；不得给出产品推荐或物料清单。
