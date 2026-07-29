# Navigation choice matrix / 导航选择矩阵

| Need / 需求 | Plan element / 方案元素 | Evidence to require / 所需证据 |
|---|---|---|
| Repeatable indoor route | Map-relative localization | Frame calibration and uncertainty trace |
| Changing obstacles | Local collision-aware tracking | Observation freshness and stopping envelope |
| Narrow passages | Kinematic feasibility and route clearance | Footprint, speed bound, and recovery rule |
| Localization uncertainty | Degraded navigation state | Stop threshold and operator handoff |

Keep global route planning separate from local tracking. Treat missing observations, stale timestamps, and blocked routes as explicit failure states.
