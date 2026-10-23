# Phase 12 Lesson 7 — Production Error Recovery Integration

## 课程目标

本课把 Lesson 1–6 的错误分类、重试、超时、fallback、partial result 和恢复路由放到真正的生产入口 `app/application/graph.py` 中验证。

本课只验证生产 Graph 的组合行为，不重写教学用的 `app/graph/graph.py`，也不新增 Provider、FastAPI、Observability 或强制取消机制。

## 测试方法

测试通过 `build_application_graph(enable_default_memory=False)` 构建生产 Graph，并用可控的阶段替身注入故障。每个场景同时检查：

- 实际调用次数；
- 下游节点是否被跳过；
- `execution_status`、`stage_errors`、`application_error`；
- 仍然可公开返回的阶段结果；
- Memory capture 是否错误地记录失败执行。

## 已覆盖场景

- 正常流程：Research → Valuation → Risk → Decision → Report，每个阶段执行一次并进入 `completed`。
- Valuation、Risk、Investment Decision 失败：终止于失败阶段，依赖该阶段的下游节点不执行。
- Report 失败：保留已有报告内容和错误信息，不写入成功 Memory 历史。
- 输入校验失败：不执行审批和任何业务阶段。

研究 partial/degraded、HITL、checkpoint、取消传播、LLM retry 和 Provider fallback 由现有 Phase 12 测试继续覆盖；本课测试通过生产 Graph 将关键阶段路由串联起来。

## 当前限制

本课不声称实现阶段级硬截止时间、同步任务强制取消或失败后自动从中间阶段恢复。测试只验证这些边界不会被错误地包装成成功结果。

## Lesson 7 验收

- [x] 测试从生产 Application Graph 构建运行。
- [x] 正常路径检查调用次数和最终状态。
- [x] 关键阶段失败检查下游路由。
- [x] Report 失败检查报告保留和 Memory 保护。
- [x] 输入失败检查终止路径。
- [ ] 在项目实际 Python 环境中执行全量测试（当前环境的 pytest 启动器指向不存在的 Python 安装，需修复环境后执行）。

Lesson 7 完成后，应进入 Lesson 8 Final Acceptance；不能仅凭这些测试通过就宣布 Phase 12 关闭。
