# Evidence ladder / 证据阶梯

| Level / 层级 | Purpose / 目的 | Default backend / 默认后端 |
|---|---|---|
| Unit | Validate one contract or state transition | Deterministic local process |
| Integration | Exercise component boundaries | Fake transport |
| Simulation | Evaluate closed-loop behavior | Simulator with bounded scenario |
| Replay | Compare repeatable time-series behavior | Synthetic recorded scenario |
| Human review | Approve a physical trial procedure | Documented safety review |

Passing one level never replaces the next level.
