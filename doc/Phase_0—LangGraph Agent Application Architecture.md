
# Phase 0 — LangGraph Agent Application Architecture

## 0. Phase Goal

这一阶段的目标不是构建一个“能调用 LLM 的 Demo”。

而是回答一个更重要的问题：

> **我们到底要用 LangGraph 构建一个什么样的 Investment Agent Application？**

最终需要确定：

```text
Investment Application
        │
        ▼
LangGraph Workflow
        │
        ├── Agents
        ├── State
        ├── Tools
        ├── Checkpoint
        ├── Memory
        ├── Human-in-the-loop
        ├── Error Recovery
        ├── Observability
        └── Evaluation
```

同时始终保持一个原则：

> **这是一个 LangGraph Application，不是 AgentOS 的第二次实现。**

你的原始要求也明确指出，不应把 AgentOS Runtime、Tool Runtime、Memory Runtime、Event Bus 等抽象搬进这个项目。

---

# 1. 本项目最终目标

项目正式定义为：

# Investment Research & Decision Agent

它不是单纯的 Research Agent。

最终目标是：

> 用户提出一个投资研究请求，Agent 自主规划研究任务，调用不同的数据与研究工具，完成公司、财务、市场、行业/宏观、估值和风险分析，形成 Investment Thesis，并最终给出结构化投资建议。

最终 Recommendation 使用：

```text
Strong Buy
Buy
Hold
Reduce
Sell
```

同时允许：

```text
Investment Horizon
├── Short Term
├── Medium Term
└── Long Term
```

以及：

```text
Current Price
Target Price
Expected Upside / Downside
```

---

## 1.1 它不是什么

当前版本不是：

```text
High Frequency Trading System
Algorithmic Trading System
Real-time Trading Signal Engine
Automated Brokerage System
Automatic Order Execution System
```

因此：

```text
Research Frequency
        ≠
Trading Frequency
```

系统可以使用最新市场数据，但不会以秒级、分钟级交易决策为目标。

---

# 2. 为什么选择 Investment Research Application

这个项目非常适合用来学习 LangGraph，因为它天然具有：

```text
复杂 Workflow
      +
Multiple Agents
      +
Tool Calling
      +
Structured Output
      +
State
      +
Conditional Routing
      +
Parallel Research
      +
Checkpoint
      +
Human Approval
      +
Memory
      +
Error Recovery
      +
Evaluation
```

例如用户：

> 分析 NVIDIA，并判断未来 12–24 个月是否值得投资。

这并不是一个单一 LLM Call 可以可靠完成的问题。

它至少需要：

```text
理解任务
   ↓
规划研究
   ↓
获取公司资料
   ↓
获取财务数据
   ↓
获取市场数据
   ↓
分析行业
   ↓
进行估值
   ↓
识别风险
   ↓
形成 Investment Thesis
   ↓
形成 Recommendation
   ↓
生成报告
```

因此它天然适合验证：

> **LangGraph 如何把复杂 Agent Workflow 组织成一个可恢复、可观察、可测试的 Application。**

---

# 3. LangGraph 在系统中的位置

这是整个项目最重要的架构定位之一。

最终架构：

```text
                    User
                      │
                      ▼
              Application API
                  FastAPI
                      │
                      ▼
             Investment Agent
                      │
                      ▼
                LangGraph
          Workflow / Orchestration
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
    Agents          Tools          State
       │              │              │
       └──────────────┼──────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     Checkpointer              Store
          │                       │
          ▼                       ▼
   Thread / Run State       Long-term Memory
```

底层再连接：

```text
LLM Provider
Market APIs
Financial APIs
Search APIs
Database
```

---

## 3.1 LangGraph 的职责

LangGraph 主要承担：

```text
Workflow Orchestration
State Management
Node Execution
Conditional Routing
Parallel Execution
Persistence Integration
Interrupt / Resume
Agent Coordination
```

而不是：

```text
完整金融数据平台
完整量化计算平台
完整数据库系统
完整交易系统
```

这些属于 Application 或外部 Infrastructure。

---

# 4. Overall Architecture

我建议第一版整体架构采用：

```text
┌──────────────────────────────────────────────┐
│                  User / Client               │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              FastAPI Application             │
│                                              │
│  Research Request                            │
│  Thread ID                                   │
│  Human Approval                              │
│  Result / Report                             │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              LangGraph Application           │
│                                              │
│                 Supervisor                   │
│                      │                       │
│       ┌──────────────┼──────────────┐        │
│       ▼              ▼              ▼        │
│   Company         Financial       Market     │
│   Research        Research       Research    │
│       │              │              │        │
│       └──────────────┼──────────────┘        │
│                      ▼                       │
│              Industry / Macro                │
│                 Research                     │
│                      │                       │
│                      ▼                       │
│                Valuation                     │
│                      │                       │
│                      ▼                       │
│                Risk Analysis                 │
│                      │                       │
│                      ▼                       │
│             Investment Decision              │
│                      │                       │
│                      ▼                       │
│                 Report Agent                 │
│                                              │
└──────────────┬───────────────┬───────────────┘
               │               │
               ▼               ▼
        Checkpointer          Store
               │               │
               ▼               ▼
        Thread State      Long-term Memory
```

这就是我们后续实现的**目标架构**。

但注意：

> 这是最终目标架构，不意味着 Phase 1 就要把所有节点全部实现。

---

# 5. Agent Design

最终至少包含以下 Agent。

## 5.1 Supervisor / Research Planner

职责：

```text
理解用户请求
      ↓
确定研究目标
      ↓
确定 Investment Horizon
      ↓
决定需要哪些 Research Agent
      ↓
分配研究任务
      ↓
检查研究完整性
      ↓
决定是否需要补充研究
```

它不是负责写最终报告的。

它更接近：

```text
Planner
+
Coordinator
+
Research Quality Controller
```

---

# 5.2 Company Research Agent

研究：

```text
Company Profile
Business Model
Products
Revenue Segments
Competitive Position
Management
Corporate Events
Company News
```

主要使用：

```text
Search Tool
Company Information Tool
Filing / Announcement Tool
```

输出结构化 Company Research Result。

---

# 5.3 Financial Research Agent

这是根据你新增的 Valuation 要求，我建议独立增加的 Agent。

研究：

```text
Revenue
Revenue Growth
Gross Margin
Operating Margin
Net Income
EPS
Cash Flow
Free Cash Flow
Debt
Cash
Balance Sheet
Capital Allocation
```

并负责准备：

```text
Financial Metrics
Historical Trends
Financial Quality
```

它不直接做最终 Recommendation。

---

# 5.4 Market Research Agent

研究：

```text
Current Price
Historical Price
Market Capitalization
Trading Volume
Volatility
Price Performance
Market Context
```

如果数据源允许，也可以加入：

```text
Beta
Drawdown
Relative Performance
```

---

# 5.5 Industry / Macro Research Agent

这一部分原始 Prompt 中没有单独拆出来，但随着最终要形成投资建议，我认为它值得进入正式架构。

研究：

```text
Industry Structure
Industry Growth
Competitors
Market Share
Cyclicality
Regulatory Environment
Macro Factors
Interest Rates
Demand Environment
```

不是每个任务都必须执行全部内容。

由 Supervisor 根据任务决定。

---

# 5.6 Valuation Agent

这是本项目新增的核心 Agent。

输入：

```text
Financial Research
Market Research
Company Research
Industry Research
```

输出：

```text
Valuation Assessment
```

可能包含：

```text
P/E
Forward P/E
EV/EBITDA
PEG
DCF
FCF Yield
Peer Comparison
Historical Valuation
```

第一版不要求所有模型同时实现。

更重要的是先建立：

```text
Valuation Provider
        ↓
Valuation Result
```

的结构。

---

# 5.7 Risk Analysis Agent

输入：

```text
Company Research
Financial Research
Market Research
Industry Research
Valuation
```

分析：

```text
Company Risk
Operational Risk
Financial Risk
Market Risk
Valuation Risk
Industry Risk
Macro Risk
Regulatory Risk
Data Uncertainty
```

同时需要回答：

> 哪些风险可能使 Investment Thesis 失效？

---

# 5.8 Investment Decision Agent

这是新的最终决策层。

输入：

```text
All Research
+
Valuation
+
Risk
```

输出：

```text
Investment Recommendation
Investment Horizon
Target Price
Expected Upside / Downside
Investment Thesis
Key Catalysts
Key Risks
Invalidation Conditions
Conviction
```

Recommendation：

```text
Strong Buy
Buy
Hold
Reduce
Sell
```

这里要特别强调：

> **Investment Decision Agent 不应该重新“搜索世界”。**

它主要应该基于前面已经完成并结构化的研究结果进行综合判断。

这样后续 Evaluation 才能检查：

```text
Evidence
   ↓
Analysis
   ↓
Valuation
   ↓
Risk
   ↓
Recommendation
```

是否逻辑一致。

---

# 5.9 Report Agent

最后才是：

```text
Research
+
Analysis
+
Decision
```

→ Final Report。

最终报告：

```text
Executive Summary

Investment Recommendation

Investment Horizon

Target Price

Expected Upside / Downside

Investment Thesis

Company Overview

Business Analysis

Financial Analysis

Market Analysis

Industry / Macro Analysis

Valuation Analysis

Risk Analysis

Key Catalysts

Thesis Invalidation Conditions

Evidence

Data Sources

Data Uncertainty

Conclusion
```

---

# 6. Agent Workflow

最终 Graph 不应该是简单的：

```text
A → B → C → D
```

而应该具备动态 routing。

目标结构：

```text
                    User Request
                         │
                         ▼
                 Research Planner
                         │
                  ┌──────┴──────┐
                  │             │
                  ▼             ▼
              Required      Optional
              Research       Research
                  │             │
          ┌───────┼─────────────┤
          ▼       ▼       ▼     ▼
       Company Financial Market Industry
          │       │       │     │
          └───────┴───────┴─────┘
                      │
                      ▼
                  Valuation
                      │
                      ▼
                  Risk Analysis
                      │
                      ▼
              Research Sufficiency?
                  │       │
                 No      Yes
                  │       │
                  └───┐   │
                      ▼   ▼
                 More Research
                      │
                      ▼
              Investment Decision
                      │
                      ▼
                 Report Agent
                      │
                      ▼
                 Final Report
```

---

# 7. Parallel Research

这里是 LangGraph 非常值得学习的地方。

例如：

```text
Supervisor
    │
    ├──────────────┐
    │              │
    ▼              ▼
Company        Financial
Research       Research
    │              │
    ├──────────────┤
    │              │
    ▼              ▼
Market         Industry
Research       Research
```

这些任务之间在第一阶段通常没有强依赖关系。

因此可以考虑：

> **Parallel Fan-out → Fan-in**

最后：

```text
Research Results
       ↓
Aggregation
       ↓
Valuation
       ↓
Risk
```

这比简单串行：

```text
Company
 ↓
Financial
 ↓
Market
 ↓
Industry
```

更符合真实研究 Workflow。

---

# 8. State Design

State 是这个项目的核心。

第一版概念模型：

```text
InvestmentState
```

包含：

```text
request
research_plan

company_research
financial_research
market_research
industry_research

valuation_analysis
risk_analysis

investment_thesis
investment_decision

final_report

evidence
sources

errors
warnings

research_status
```

同时还有：

```text
metadata
thread_id
timestamps
```

---

## 8.1 State 不等于 Memory

这一点必须从 Phase 0 就明确。

```text
Current State
      │
      ▼
Current Research Execution
```

例如：

```text
正在研究 NVIDIA
```

属于当前 Thread State。

而：

```text
用户过去研究过 NVIDIA
用户关注半导体
用户过去要求重点关注估值
```

属于 Long-term Memory。

---

# 9. Checkpoint / Persistence

LangGraph 的：

```text
Thread
Checkpoint
Checkpointer
```

需要在本项目中真正使用。

基本生命周期：

```text
User Request
      │
      ▼
Thread
      │
      ▼
Graph Run
      │
      ▼
State
      │
      ▼
Checkpoint
      │
      ▼
Interrupt / Failure
      │
      ▼
Resume
      │
      ▼
Continue Graph
```

最终必须能够验证：

```text
Run 1
 ↓
Checkpoint
 ↓
Application stopped
 ↓
Restart
 ↓
Resume
 ↓
Run 2
 ↓
Final Result
```

这对应你原 Prompt 中要求的：

> 第一次执行 → 中断 → 读取 checkpoint → 恢复 → 继续执行 → 最终正确结果。

---

# 10. Human-in-the-loop

这里我建议不要做一个没有意义的：

> “是否继续？”

而选择一个真正具有 Application 意义的场景。

例如：

```text
Research
   ↓
准备执行高成本数据获取 / 深度研究
   ↓
interrupt()
   ↓
Human
   ├── Approve
   └── Reject
   ↓
Command(resume=...)
   ↓
Continue
```

后续还可以用于：

```text
Approve Final Investment Recommendation
```

但第一阶段 HITL 最好先用于**研究流程控制**，不要一开始就把它和投资决策审批混在一起。

---

# 11. Memory Architecture

明确分成两个层次。

## Short-term

```text
Thread
   │
   ▼
Graph State
   │
   ▼
Checkpoint
```

用于：

```text
当前 Research Execution
```

---

## Long-term

```text
Store
 │
 ├── User Preferences
 ├── Research History
 ├── Areas of Interest
 └── Previous Research Context
```

例如：

```text
User previously researched NVIDIA.
```

下一次：

```text
Analyze NVIDIA again.
```

Agent 可以知道之前研究过什么。

但：

> **不能把历史 Research State 当成当前事实直接使用。**

历史信息必须区分：

```text
Historical Memory
vs
Current Market Data
```

这是投资 Application 特别重要的设计。

---

# 12. Tool Architecture

Tool 不直接散落在 Agent 中。

逻辑上：

```text
Agent
  │
  ▼
Tool
  │
  ▼
Provider
  │
  ▼
External API
```

例如：

```text
SearchTool
    ↓
SearchProvider

MarketDataTool
    ↓
MarketDataProvider

FinancialDataTool
    ↓
FinancialDataProvider

CompanyInfoTool
    ↓
CompanyInfoProvider
```

这样以后：

```text
Mock Provider
```

可以替换：

```text
Real Provider
```

测试不需要调用真实外部 API。

---

# 13. Evidence Architecture

因为最终要形成投资建议，所以 Evidence 不应该只是报告里的引用文本。

应该成为一等数据：

```text
Evidence
├── source
├── source_type
├── title
├── timestamp
├── claim
├── extracted_data
└── relevance
```

最终：

```text
Evidence
   ↓
Research Finding
   ↓
Analysis
   ↓
Investment Thesis
   ↓
Recommendation
```

这样 Evaluation 才能够检查：

> Recommendation 是否有足够证据支撑。

---

# 14. Investment Decision Schema

这是整个 Application 非常关键的 Structured Output。

概念上：

```text
InvestmentDecision

recommendation:
    Strong Buy | Buy | Hold | Reduce | Sell

investment_horizon:
    Short | Medium | Long

current_price

target_price

expected_return

conviction

investment_thesis

key_catalysts[]

key_risks[]

invalidation_conditions[]

supporting_evidence[]
```

这里的：

```text
expected_return
```

应该能够由：

```text
Target Price
+
Current Price
```

得到，而不是让 LLM 随便生成。

类似：

```text
Expected Upside
=
(Target Price - Current Price) / Current Price
```

具体实现阶段再决定是否加入股息、币种等因素。

---

# 15. Recommendation 与 Valuation 的关系

需要避免一个非常常见的问题：

```text
Valuation = $100

Recommendation = Strong Buy

```

但系统无法解释：

> 为什么 $100 对应 Strong Buy？

所以后续需要建立一个明确的：

```text
Valuation
       +
Business Quality
       +
Growth
       +
Risk
       +
Catalysts
       ↓
Investment Decision
```

而不是：

```text
LLM 看完报告
      ↓
凭感觉输出 BUY
```

这也是 Evaluation 的重点。

---

# 16. Error Handling

我们不会使用：

```python
except Exception:
    pass
```

而会区分：

```text
Tool Failure
LLM Failure
Timeout
Invalid Structured Output
Missing Data
Partial Research Failure
Checkpoint Failure
```

对应策略：

```text
Retry
Fallback
Partial Result
Failure State
Recovery
Escalation
```

例如：

```text
Market API Failure
       │
       ▼
Retry
       │
    failure
       │
       ▼
Fallback Provider
       │
    failure
       │
       ▼
Partial Research
       │
       ▼
Risk / Data Uncertainty
```

系统不应该因为一个 Market API 暂时失败就把整个 Research 无条件判定为失败。

---

# 17. Observability

最终要能够观察：

```text
Application
    ↓
Graph Run
    ↓
Node
    ↓
Agent
    ↓
LLM
    ↓
Tool
```

至少记录：

```text
Run ID
Thread ID
Node
Start Time
End Time
Duration
Status
Error
Tool Calls
LLM Calls
Token Usage
```

如果使用 LangSmith，则需要单独理解：

```text
LangGraph
```

与：

```text
LangSmith
```

之间的关系。

不能把 LangSmith 当作 LangGraph 的 Runtime。

---

# 18. Evaluation Architecture

Evaluation 会分成多个层次。

## Level 1 — Tool Evaluation

例如：

```text
MarketDataTool
FinancialDataTool
SearchTool
```

验证：

```text
输入
 ↓
Tool
 ↓
Output
```

是否正确。

---

## Level 2 — Routing Evaluation

例如：

用户只问：

> NVIDIA 当前估值是否合理？

是否应该执行：

```text
Company Research
Financial Research
Market Research
Valuation
```

而不是无条件执行所有 Agent。

---

## Level 3 — Research Evaluation

检查：

```text
是否覆盖关键问题
是否找到足够证据
数据是否过期
是否存在明显缺失
```

---

## Level 4 — Analysis Evaluation

检查：

```text
Financial Analysis
Valuation Analysis
Risk Analysis
```

是否与输入证据一致。

---

## Level 5 — Investment Decision Evaluation

重点检查：

```text
Recommendation
Target Price
Horizon
Thesis
Risk
Evidence
```

是否逻辑一致。

---

## Level 6 — Report Evaluation

检查：

```text
Completeness
Evidence Grounding
Factual Consistency
Uncertainty
Recommendation Consistency
```

---

## Level 7 — Trajectory Evaluation

最终甚至可以检查：

```text
User Request
 ↓
Planner
 ↓
Tools
 ↓
Agents
 ↓
Research
 ↓
Decision
 ↓
Report
```

整个 Agent trajectory 是否合理。

这会成为后期非常重要的 LangGraph 学习内容。

---

# 19. Phase / Lesson Roadmap

接下来不会一次性把整个系统写出来。

按照你原始要求：

```text
Phase
 ↓
Lesson
 ↓
Step
 ↓
Code
 ↓
Test
 ↓
Run
 ↓
Acceptance
 ↓
Phase Closed
```

建议整个项目分成：

---

## Phase 0 — Architecture

当前阶段。

内容：

```text
Architecture
Boundaries
Agents
State
Tools
Persistence
Memory
HITL
Evaluation
```

### Acceptance

```text
[ ] Application boundary defined
[ ] Agent responsibilities defined
[ ] State boundary defined
[ ] Tool boundary defined
[ ] Memory boundary defined
[ ] Persistence strategy defined
[ ] Evaluation strategy defined
[ ] E2E scenario defined
```

---

# Phase 1 — Minimal LangGraph Core

学习：

```text
StateGraph
State
Node
Edge
Conditional Edge
Compile
Invoke
```

构建最小可运行 Graph。

### Acceptance

```text
[ ] Graph runs
[ ] State flows correctly
[ ] Conditional routing works
[ ] Tests pass
```

---

# Phase 2 — LLM + Structured Output

加入：

```text
LLM Provider
Pydantic
Structured Output
```

### Acceptance

```text
[ ] LLM provider works
[ ] Structured result validates
[ ] Invalid output handled
[ ] Provider can be replaced
```

---

# Phase 3 — Tool Calling

加入：

```text
Search
Market
Financial
Company
```

先 Mock Provider。

### Acceptance

```text
[ ] Tool schema works
[ ] Tool calling works
[ ] Tool result enters State
[ ] Tool failure handled
```

---

# Phase 4 — Research Agents

加入：

```text
Company
Financial
Market
Industry
```

### Acceptance

```text
[ ] Agents independently work
[ ] Structured research output
[ ] Evidence attached
[ ] Partial failure supported
```

---

# Phase 5 — Multi-Agent Orchestration

加入：

```text
Supervisor
Parallel Research
Aggregation
Routing
```

### Acceptance

```text
[ ] Supervisor plans
[ ] Parallel execution works
[ ] Results aggregate
[ ] Dynamic routing works
```

---

# Phase 6 — Valuation

加入：

```text
Valuation Agent
Valuation Models
Target Price
Expected Upside
```

### Acceptance

```text
[ ] Valuation executes
[ ] Assumptions explicit
[ ] Target price generated
[ ] Calculation test passes
```

---

# Phase 7 — Risk + Investment Decision

加入：

```text
Risk Agent
Investment Decision Agent
```

### Acceptance

```text
[ ] Risk assessment works
[ ] Recommendation generated
[ ] Horizon generated
[ ] Thesis generated
[ ] Evidence attached
[ ] Decision schema validates
```

---

# Phase 8 — Report Generation

加入：

```text
Report Agent
Evidence
Sources
Uncertainty
```

### Acceptance

```text
[ ] Complete report
[ ] Recommendation included
[ ] Target price included
[ ] Sources included
[ ] Uncertainty included
```

---

# Phase 9 — Checkpoint / Persistence

加入：

```text
Thread
Checkpointer
Interrupt
Resume
```

### Acceptance

```text
[ ] Execution checkpoints
[ ] Execution can stop
[ ] Application can restart
[ ] Thread resumes
[ ] Final state correct
```

---

# Phase 10 — Human-in-the-loop

加入：

```text
interrupt()
Command()
resume
```

### Acceptance

```text
[ ] Interrupt works
[ ] Human decision captured
[ ] Resume works
[ ] State preserved
```

---

# Phase 11 — Long-term Memory

加入：

```text
Store
User Preferences
Research History
```

### Acceptance

```text
[ ] Memory persisted
[ ] Memory retrieved
[ ] Current State separated from Memory
[ ] Historical information not mistaken for current data
```

---

# Phase 12 — Error Recovery

系统化处理：

```text
Retry
Fallback
Partial Result
Recovery
```

### Acceptance

```text
[ ] Tool failure tested
[ ] LLM failure tested
[ ] Timeout tested
[ ] Partial research works
[ ] Recovery works
```

---

# Phase 13 — Observability

加入：

```text
Tracing
Metrics
LangSmith
```

### Acceptance

```text
[ ] Graph execution observable
[ ] Node execution observable
[ ] Tool calls observable
[ ] LLM calls observable
[ ] Errors observable
```

---

# Phase 14 — Evaluation

建立：

```text
Dataset
Evaluator
LLM-as-Judge
Trajectory Evaluation
Regression Tests
```

### Acceptance

```text
[ ] Tool evaluation
[ ] Routing evaluation
[ ] Research evaluation
[ ] Decision evaluation
[ ] Report evaluation
[ ] Regression evaluation
```

---

# Phase 15 — FastAPI Application

最后形成真正 Application Interface：

```text
POST /research
GET /research/{thread_id}
POST /research/{thread_id}/resume
GET /research/{thread_id}/report
```

### Acceptance

```text
[ ] API works
[ ] Thread works
[ ] Resume works
[ ] Report retrievable
[ ] Error responses defined
```

---

# Phase 16 — End-to-End Production-style Application

最终把所有部分组合起来。

---

# 20. 最终 End-to-End Scenario

最终必须能够执行：

```text
User

"分析 NVIDIA，并判断未来投资价值。"
```

系统：

```text
                User
                  │
                  ▼
             FastAPI
                  │
                  ▼
             Supervisor
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
     Company   Financial   Market
        │         │         │
        └─────────┼─────────┘
                  │
                  ▼
              Industry
                  │
                  ▼
              Valuation
                  │
                  ▼
                Risk
                  │
                  ▼
          Investment Decision
                  │
                  ▼
              Report
```

最终得到：

```text
Recommendation:
Buy

Investment Horizon:
Medium Term

Current Price:
...

Target Price:
...

Expected Upside:
...

Investment Thesis:
...

Key Catalysts:
...

Key Risks:
...

Invalidation Conditions:
...

Evidence:
...

Data Limitations:
...
```

---

# 21. Phase 0 Acceptance Criteria

因此，现在正式定义：

## Phase 0 CLOSED 条件

```text
Architecture

[✓] 最终 Application 定位明确
[✓] Research → Analysis → Decision → Report 路径明确
[✓] Recommendation 五级体系确定
[✓] Valuation 纳入核心 Workflow
[✓] Target Price 纳入核心输出
[✓] Investment Horizon 支持 Short / Medium / Long
[✓] 非实时交易系统边界明确

Agents

[✓] Supervisor
[✓] Company Research
[✓] Financial Research
[✓] Market Research
[✓] Industry / Macro Research
[✓] Valuation
[✓] Risk Analysis
[✓] Investment Decision
[✓] Report

Core

[✓] State
[✓] Tools
[✓] Checkpoint
[✓] Persistence
[✓] Memory
[✓] HITL
[✓] Error Handling
[✓] Observability
[✓] Evaluation

Engineering

[✓] Phase roadmap
[✓] Acceptance criteria
[✓] E2E scenario
[✓] LangGraph / AgentOS boundary
```

---

# 22. 最重要的架构结论

经过 Phase 0，我们实际上已经把这个项目的核心定义压缩成一句话：

> **这是一个以 LangGraph 为 Workflow / Agent Orchestration 层，以结构化 Research、Valuation、Risk Analysis 为基础，最终生成带有 Investment Horizon、Target Price 和 Strong Buy / Buy / Hold / Reduce / Sell Recommendation 的 Investment Decision Agent Application。**

而 AgentOS 在这个项目中只作为**对照研究对象**存在。

不是：

```text
AgentOS
   ↓
LangGraph
```

而是：

```text
             Investment Application
                      │
                      ▼
                 LangGraph
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      Agent          Tool          State
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Checkpoint       Memory       External APIs
```

之后每一个重要 Phase 完成，我们再单独回答：

```text
LangGraph 是怎么解决这个问题的？

AgentOS 是怎么解决这个问题的？

为什么两者抽象边界不同？

这个能力到底属于：
Application？
Workflow？
Runtime？
Infrastructure？
```

这正是这次项目对你之前 AgentOS 开发最有价值的地方。

---

## Phase 0 状态：**CLOSED**

按照你之前制定的规则，Phase 0 已达到验收标准。

**下一阶段应该进入 Phase 1 — Minimal LangGraph Core。**

Phase 1 我们不会直接开始做 Investment Agent，而是先用一个**极小但真实可运行的 Graph**，逐步建立：

```text
State
 ↓
Node
 ↓
Edge
 ↓
Conditional Edge
 ↓
Compile
 ↓
Invoke
 ↓
Test
```

然后再逐步把它演化成 Investment Application。这样可以避免一开始就被业务复杂度掩盖 LangGraph 本身的核心机制。
