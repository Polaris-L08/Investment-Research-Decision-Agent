# Phase 12 Lesson 8 — Final Acceptance

## 课程目标

Lesson 8 是 Phase 12 的最终验收课。它不再新增错误恢复策略，而是从真实生产入口运行工作流，检查前七课的契约是否在一次实际执行中保持一致。

本项目新增的 [scripts/smoke_test_application.py](../scripts/smoke_test_application.py) 会构建 `app.application.graph`，使用真实 HITL interrupt、SQLite Checkpoint 和实际配置的 Provider/LLM。脚本不会替换 Research、Valuation、Risk、Decision 或 Report 阶段。

## 运行方式

先复制 `.env.example` 为 `.env`，根据运行模式配置 Provider 和 LLM。

### 1. Mock Provider + 真实 LLM

```powershell
python scripts/smoke_test_application.py --provider-mode mock --ticker AAPL
```

这仍然是真实 Application Graph 运行；`mock` 只表示数据 Provider 使用项目已有的确定性 Provider。Research Agent、LLM structured output、HITL、checkpoint、valuation、risk、decision 和 report 节点仍按生产图执行。

### 2. 真实 Provider + 真实 LLM

```powershell
python scripts/smoke_test_application.py `
  --provider-mode real `
  --ticker AAPL `
  --eps 6.0 `
  --multiple 20 `
  --rationale "Manual assumption for smoke test"
```

真实 Provider 当前是 partial integration。某些 source 只能提供报价、公司资料或财务数据，缺失的 market/industry/macro 能力会按既定契约失败或降级；脚本会把这些状态打印出来，不会用默认值伪造完整结论。

### 3. 验证 HITL 拒绝路径

```powershell
python scripts/smoke_test_application.py --provider-mode mock --approval reject
```

预期结果是 `approval_status=rejected` 和 `execution_status=rejected`，Research 不应执行。

### 4. 诊断预期失败

如果只想查看真实 Provider 覆盖不足造成的失败，而不让脚本以进程错误退出，可增加：

```powershell
python scripts/smoke_test_application.py --provider-mode real --allow-failed
```

`--allow-failed` 只改变脚本退出码，不改变 Graph 状态，也不会把失败转换成成功。

## 输出证据

脚本会输出：

- Provider mode、source、ticker、thread ID、checkpoint 数据库；
- 初始调用后的审批中断和 checkpoint 摘要；
- 恢复后的终态 `execution_status`；
- `research_data_status`、失败/降级研究区域；
- `stage_errors`、`error_details`、`application_error`；
- Memory capture 决策；
- 生成的最终 Markdown 报告（如果存在）。

这些输出分别对应 Phase 12 的错误分类、状态传播、失败路由、降级诚实性和 Memory 保护要求。

## Phase 12 验收矩阵

| 验收项 | 证据 | 状态 |
|---|---|---|
| 正常流程 | Lesson 7 生产 Graph 集成测试；本课 smoke script | 已实现，需在配置好的环境运行确认 |
| 可重试错误和调用次数 | `tests/test_llm_retry_policy.py`、`tests/test_tool_failure_routing.py` | 有测试证据 |
| 重试耗尽明确终止 | LLM retry policy 与 tool retry tests | 有测试证据 |
| Timeout 边界 | `tests/test_application_timeout_boundaries.py`、provider isolation tests | 有测试证据 |
| Cancellation 传播 | Application timeout boundary tests | 有测试证据 |
| Fallback / degraded | `tests/test_research_fallbacks.py`、`tests/test_application_degraded_status.py` | 有测试证据 |
| Partial research | `tests/test_application_degraded_status.py`、生产路由测试 | 有测试证据 |
| 关键数据缺失不伪造估值 | valuation input boundary tests | 有测试证据 |
| 关键阶段失败路由 | Lesson 7 integration tests | 有测试证据 |
| 失败不写入成功 Memory | `tests/test_memory_workflow.py`、Lesson 7 integration tests | 有测试证据 |
| 真实生产入口运行 | `scripts/smoke_test_application.py` | 脚本已提供，运行结果取决于环境配置 |
| 全量测试在当前环境通过 | pytest 启动器和临时目录此前存在环境阻塞 | 未验证 |

## 当前限制

1. 生产 Graph 是同步 `invoke()` 流程；项目没有阶段级硬截止时间或同步任务的强制取消机制。
2. LLM 请求 timeout 和 Provider worker timeout 只约束各自边界；不能据此声称整条工作流有端到端 deadline。
3. 真实 Provider factory 当前明确标记为 partial；`APP_ENV=production` 会拒绝不完整的 real provider 覆盖。
4. 真实运行仍需要配置 LLM 凭据。没有 LLM 配置时，脚本应输出结构化失败状态，而不会伪装成成功。

## 关闭结论

Phase 12 只有在以下证据齐备后才能关闭：

- Lesson 7 集成测试通过；
- 本课 smoke script 在实际项目 Python 环境至少完成一次正常路径和一次代表性故障路径；
- 全部必需验收项都有测试或明确限制说明；
- 未验证项目被记录为未通过，而不是按代码存在直接视为通过。

当前提交完成了 Lesson 8 的真实运行工具和验收教学文档，但是否关闭 Phase 12 仍取决于用户环境中实际运行脚本和全量测试的结果。
