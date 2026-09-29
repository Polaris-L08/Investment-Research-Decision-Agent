# Phase 5 — Multi-Agent Orchestration

## Lesson 1: Research Planner

本课只建立：

```text
User Query
    ↓
Research Planner
    ↓
ResearchPlan
```

**不执行任何 Research Agent。**

---

### 1. Goal

建立第一个真正的 Multi-Agent Orchestration 前置组件：

```text
User Query
    ↓
Research Planner
    ↓
ResearchPlan
```

Planner 的职责是回答：

> **“为了回答用户的问题，需要进行哪些类型的研究？”**

例如：

```text
Research AAPL as a long-term investment.
```

Planner 可以产生：

```text
ResearchPlan(
    research_areas=[
        company,
        financial,
        market,
        industry_macro
    ]
)
```

注意这里的关键区别：

```text
Planner
    ↓
决定研究什么

Research Agent
    ↓
真正进行研究
```

本课只做到前者。

---

### 2. Why Now

Phase 4 已经建立了四个独立 Research Agent：

```text
Company Research Agent
Financial Research Agent
Market Research Agent
Industry / Macro Research Agent
```

Phase 4 解决的是：

> 一个 Agent 应该负责什么？

Phase 5 开始解决：

> 多个 Agent 应该如何被选择、调度和协调？

因此第一步不能直接写：

```text
Supervisor
Parallel
Fan-out
Fan-in
```

而应该先建立：

```text
Research Planner
```

让系统第一次具有：

```text
User Request
      ↓
Research Plan
```

这一层。

---

### 3. Core Concepts

本课引入三个概念。

#### 3.1 ResearchArea

研究领域的有限集合：

```text
company
financial
market
industry_macro
```

对应：

```python
class ResearchArea(str, Enum):
    COMPANY = "company"
    FINANCIAL = "financial"
    MARKET = "market"
    INDUSTRY_MACRO = "industry_macro"
```

使用 Enum 而不是裸字符串，是为了让后面的 Router 可以基于稳定的结构进行判断。

---

#### 3.2 ResearchPlan

Planner 的结构化输出：

```python
class ResearchPlan(BaseModel):
    research_areas: list[ResearchArea]
```

因此 Planner 不再输出：

```text
"你应该研究公司、财务和市场……"
```

而是输出：

```python
ResearchPlan(
    research_areas=[
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
    ]
)
```

这也是后续 Routing 的输入基础。

---

#### 3.3 Planner ≠ Agent Executor

这是本课最重要的边界。

Planner：

```text
理解 Query
    ↓
选择 Research Areas
```

Planner **不能**：

```text
调用 Company Agent
调用 Financial Agent
调用 Market Agent
调用 Industry Agent
```

也不能：

```text
估值
风险分析
投资决策
```

所以本课 Graph 必须非常小。

---

### 4. Graph Topology

本课正式 Graph：

```text
START
  │
  ▼
research_planner
  │
  ▼
 END
```

也就是：

```text
START → research_planner → END
```

没有：

```text
Company Agent
Financial Agent
Market Agent
Industry Agent
```

这不是暂时没接，而是**本课明确不接**。

---

### 5. State Design

本课不修改整个 `GraphState` 来强行接入主图。

建立独立 Planner State：

```python
class ResearchPlannerInputState(TypedDict):
    user_query: str
```

内部 State：

```python
class ResearchPlannerState(TypedDict):
    user_query: str
    research_plan: ResearchPlan | None
    planning_error: str
```

Output：

```python
class ResearchPlannerOutputState(TypedDict):
    research_plan: ResearchPlan | None
    planning_error: str
```

因此：

```text
Input
    user_query

Internal
    user_query
    research_plan
    planning_error

Output
    research_plan
    planning_error
```

这里特意没有：

```text
company_research_result
financial_research_result
market_research_result
...
```

因为 Planner 还没有执行这些 Agent。

---

### 6. Exact Files

本课实际修改：

```text
app/agents/models.py
```

新增：

```text
app/agents/research_planner.py
```

新增：

```text
tests/test_research_planner.py
```

没有修改：

```text
app/graph/graph.py
```

这一点是有意的。

当前主 Graph 里的旧：

```python
create_research_plan()
```

仍然属于 Phase 4/早期主流程遗留逻辑。

**本课不把它直接改造成 Research Planner。**

原因是现在要先把新的 Planner 能力独立建立、测试，然后 Lesson 2 再进入 Routing。

---

### 7. Exact Changes

#### 7.1 `app/agents/models.py`

新增：

```python
from enum import Enum
```

并增加：

```python
class ResearchArea(str, Enum):
    COMPANY = "company"
    FINANCIAL = "financial"
    MARKET = "market"
    INDUSTRY_MACRO = "industry_macro"


class ResearchPlan(BaseModel):
    research_areas: list[ResearchArea] = Field(
        description=(
            "Research areas required to answer the user's request. "
            "Select only the areas that are relevant to the request."
        )
    )
```

因此现在 Model 层具有：

```text
ResearchArea
    ↓
ResearchPlan
```

以及原来的：

```text
CompanyResearchResult
FinancialResearchResult
MarketResearchResult
IndustryMacroResearchResult
```

---

#### 7.2 新增 `app/agents/research_planner.py`

当前实现：

```python
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agents.models import ResearchPlan
from app.llm.client import llm


class ResearchPlannerInputState(TypedDict):
    user_query: str


class ResearchPlannerState(TypedDict):
    user_query: str
    research_plan: ResearchPlan | None
    planning_error: str


class ResearchPlannerOutputState(TypedDict):
    research_plan: ResearchPlan | None
    planning_error: str


research_planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Research Planner for an investment research system. "
            "Your responsibility is only to determine which research areas "
            "are needed to answer the user's request. "
            "Available research areas are: company, financial, market, "
            "and industry_macro. "
            "Select only the relevant research areas. "
            "Do not execute any research agent. "
            "Do not perform valuation. "
            "Do not assess investment risk. "
            "Do not make an investment recommendation. "
            "Do not produce research findings or invent data.",
        ),
        (
            "human",
            "Create a research plan for the following user request.\n\n"
            "User request: {user_query}",
        ),
    ]
)


structured_research_planner_llm = (
    llm.with_structured_output(ResearchPlan)
)


def research_planner(
    state: ResearchPlannerState,
) -> ResearchPlannerState:

    prompt_value = research_planner_prompt.invoke(
        {
            "user_query": state["user_query"],
        }
    )

    try:
        research_plan = structured_research_planner_llm.invoke(
            prompt_value
        )
    except Exception as exc:
        return {
            "research_plan": None,
            "planning_error": str(exc),
        }

    return {
        "research_plan": research_plan,
        "planning_error": "",
    }


def build_research_planner_graph():
    builder = StateGraph(
        ResearchPlannerState,
        input_schema=ResearchPlannerInputState,
        output_schema=ResearchPlannerOutputState,
    )

    builder.add_node(
        "research_planner",
        research_planner,
    )

    builder.add_edge(
        START,
        "research_planner",
    )

    builder.add_edge(
        "research_planner",
        END,
    )

    return builder.compile()


research_planner_graph = build_research_planner_graph()
```

这里有一个值得注意的设计：

```python
llm.with_structured_output(ResearchPlan)
```

所以 Planner 并不是：

```text
LLM → 自由文本
```

而是：

```text
LLM
 ↓
Structured Output
 ↓
ResearchPlan
```

这与 Phase 2 学到的 Structured Output 能力保持一致。

---

### 8. Tests

新增：

```text
tests/test_research_planner.py
```

测试覆盖：

#### ResearchPlan Schema

验证：

```text
company
financial
market
industry_macro
```

能够进入结构化 Plan。

#### Graph Compilation

验证：

```text
research_planner_graph
```

可以正常构建。

#### Structured Output

使用 Mock LLM：

```python
fake_plan = ResearchPlan(
    research_areas=[
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
    ]
)
```

然后验证：

```python
output["research_plan"] == fake_plan
```

以及：

```python
fake_llm.invoke.assert_called_once()
```

#### Planner Failure

验证 LLM 失败时：

```python
research_plan is None
planning_error != ""
```

而不是静默吞掉异常。

#### Planner Boundary

验证 Graph 中不存在：

```text
company_research
financial_research
market_research
industry_macro_research
```

因此 Planner 当前没有偷偷执行 Research Agent。

---

### 9. Acceptance Criteria

| Criteria                                 | 当前状态                       |
|------------------------------------------|--------------------------------|
| `ResearchPlan` 有明确 Schema             | ✅                             |
| `ResearchArea` 有明确枚举                | ✅                             |
| Planner 使用 Structured Output           | ✅                             |
| Planner 可以选择 Research Areas          | ✅                             |
| Planner 不执行 Research Agent            | ✅                             |
| Planner 不进行 Valuation                 | ✅                             |
| Planner 不进行 Risk Analysis             | ✅                             |
| Planner 不产生 Investment Recommendation | ✅                             |
| Graph = `START → research_planner → END` | ✅                             |
| 新增 Planner 测试                        | ✅                             |
| Python 静态编译                          | ✅                             |
| 实际 pytest                              | ⚠️ 当前环境缺少 LangGraph 依赖 |

因此代码实现本身已经完成 Lesson 1，但**正式 Lesson Acceptance 还需要你本地 pytest 跑通**。

---

### 10. Key Understanding

这一课真正要掌握的不是 `ResearchPlan` 这个 Pydantic Model，而是：

```text
User Query
     │
     ▼
Research Planner
     │
     ▼
ResearchPlan
```

Planner 做的是：

```text
WHAT should be researched?
```

而不是：

```text
HOW to research?
```

更不是：

```text
DO the research
```

因此现在：

```text
Planner
  ↓
ResearchPlan
```

而下一课才会出现：

```text
ResearchPlan
  ↓
Router
  ↓
Company / Financial / Market / Industry-Macro Agent
```

这就是 Phase 5 的第一个真正分界线：

```text
Planner = 决定研究范围
Router  = 决定执行路径
Agent   = 执行具体研究
```

后面再逐步进入：

```text
Sequential
    ↓
Parallel
    ↓
Fan-out
    ↓
Fan-in
    ↓
Supervisor
```

而不是现在一步跳过去。

---


## Lesson 2：Agent Routing

### 1. 本课目标

Lesson 1 建立了：

```text
User Query
    ↓
Research Planner
    ↓
ResearchPlan
```

现在我们增加：

```text
ResearchPlan
    ↓
Router
    ↓
指定 Research Agent
```

最终形成：

```text
User Query
    ↓
Research Planner
    ↓
ResearchPlan
    ↓
Deterministic Router
    ↓
┌─────────────────────┐
│ Company Research    │
│ Financial Research  │
│ Market Research     │
│ Industry/Macro      │
└─────────────────────┘
```

但是**本课仍然只执行一个当前指定的 Research Area**。

例如：

```text
ResearchPlan:
    company
    financial
    market

next_research_area:
    financial
```

那么：

```text
Router
   ↓
Financial Research Agent
```

而不是：

```text
Company
   ↓
Financial
   ↓
Market
```

后者属于 **Lesson 4 — Sequential Multi-Agent Orchestration**。

---

### 2. Why Now

现在系统已经能够回答：

> “需要研究什么？”

但还不能回答：

> “现在应该把任务交给哪个 Agent？”

这就是 Router 的职责。

因此职责链现在变成：

```text
Planner
    │
    │ What?
    ▼
ResearchPlan
    │
    │ Which?
    ▼
Router
    │
    ▼
Research Agent
```

这是 Phase 5 非常重要的一层职责分离。

---

### 3. 最重要的概念：Router ≠ LLM

本课最重要的原则：

> **Router 不应该再次调用 LLM。**

例如下面这种设计，本课明确不采用：

```python
router_llm = llm.with_structured_output(...)
```

然后让 LLM 决定：

```text
"应该调用 financial agent"
```

这是错误的方向。

因为 Planner 已经负责：

```text
LLM
 ↓
ResearchPlan
```

Router 只需要执行：

```python
if research_area == ResearchArea.COMPANY:
    return "company_research"
```

因此：

```text
Planner
    = LLM reasoning

Router
    = deterministic control flow
```

这两个职责必须分开。

---

### 4. Graph Topology

本课的 Graph：

```text
                    ┌──→ Company Research ──→ END
                    │
START → Router ─────┼──→ Financial Research → END
                    │
                    ├──→ Market Research ───→ END
                    │
                    ├──→ Industry/Macro ────→ END
                    │
                    └──→ Routing Error ─────→ END
```

也可以抽象成：

```text
START
  ↓
Router
  │
  ├── company
  ├── financial
  ├── market
  ├── industry_macro
  └── error
```

这里第一次真正使用了 LangGraph 的：

```python
add_conditional_edges()
```

---

### 5. 为什么增加 `next_research_area`

这是本课特别需要理解的设计。

`ResearchPlan` 可能是：

```python
ResearchPlan(
    research_areas=[
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
    ],
    rationale="..."
)
```

但 Router 一次只负责：

> **把当前要执行的 Research Area 路由到对应 Agent。**

因此 State 中增加：

```python
next_research_area: ResearchArea
```

例如：

```text
ResearchPlan
    ├── company
    ├── financial
    └── market

next_research_area
    ↓
financial
```

Router 只负责：

```text
financial
    ↓
Financial Research Agent
```

这样以后 Lesson 4 才可以做：

```text
company
    ↓
financial
    ↓
market
    ↓
industry_macro
```

而 Lesson 5 才进一步变成：

```text
       ┌── company ───────┐
       ├── financial ─────┤
       ├── market ────────┤
       └── industry_macro ┘
```

因此这个设计实际上是在为后面的 Orchestration 铺路。

---

### 6. State Design

新增：

```python
class ResearchRouterInputState(TypedDict):
    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea
```

内部 State：

```python
class ResearchRouterState(TypedDict):
    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea

    routed_area: ResearchArea | None
    research_result: object | None
    research_error: str
    routing_error: str
```

Output：

```python
class ResearchRouterOutputState(TypedDict):
    routed_area: ResearchArea | None
    research_result: object | None
    research_error: str
    routing_error: str
```

这里的：

```python
research_result: object | None
```

是**暂时性的 Lesson 2 设计**。

因为四个 Agent 的结果类型不同：

```text
CompanyResearchResult
FinancialResearchResult
MarketResearchResult
IndustryMacroResearchResult
```

本课还没有建立统一的 Multi-Agent Shared State。

那个问题属于：

> **Lesson 3 — Multi-Agent Shared State**

所以现在不提前设计复杂的统一 Result 类型。

---

### 7. Router 的核心逻辑

实际 Router 是：

```python
def route_research_area(
    state: ResearchRouterState,
) -> str:

    research_area = state["next_research_area"]

    if research_area not in state["research_plan"].research_areas:
        return "routing_error"

    routes = {
        ResearchArea.COMPANY: "company_research",
        ResearchArea.FINANCIAL: "financial_research",
        ResearchArea.MARKET: "market_research",
        ResearchArea.INDUSTRY_MACRO: "industry_macro_research",
    }

    return routes[research_area]
```

这段代码非常值得掌握。

它没有：

```text
LLM
Prompt
Structured Output
Tool Calling
```

只有：

```text
State
 ↓
Enum
 ↓
Dictionary
 ↓
Graph Route
```

所以它是一个真正的 **deterministic router**。

---

### 8. 一个额外的重要保护

Router 不仅判断：

```python
next_research_area == financial
```

还判断：

```python
financial in research_plan.research_areas
```

例如：

```python
ResearchPlan(
    research_areas=[
        ResearchArea.COMPANY
    ],
    rationale="Only company research is required."
)
```

却要求：

```python
next_research_area = ResearchArea.FINANCIAL
```

这是非法路由。

系统不会偷偷执行 Financial Agent，而是：

```text
Router
  ↓
Routing Error
```

结果：

```python
routing_error = (
    "Research area is not included in the research plan: financial"
)
```

这体现了一个重要的工程原则：

> **Routing Failure 必须显式存在，而不是静默执行错误路径。**

---

### 9. Agent 与 Router 的关系

本课第一次把两者真正连接起来。

例如 Company：

```text
Router
   │
   ▼
company_research
   │
   ▼
company_research_graph
```

Router 自己不研究公司。

它只负责：

```text
“把任务交给谁？”
```

真正的：

```text
Tool Calling
Provider
Structured Output
CompanyResearchResult
```

仍然完全由 Phase 4 的 Company Agent 负责。

因此我们没有重新实现 Company Agent。

这非常重要。

---

### 10. Exact Files

本课新增：

```text
app/agents/research_router.py
```

新增：

```text
tests/test_research_router.py
```

同时修正：

```text
app/agents/models.py
```

使 `ResearchPlan` 与你定义的正式 Schema 完全一致：

```python
class ResearchPlan(BaseModel):
    research_areas: list[ResearchArea] = Field(
        description=(
            "The research areas required to answer the "
            "user's research request."
        )
    )

    rationale: str = Field(
        description=(
            "A concise explanation of why these research "
            "areas are required."
        )
    )
```

同时更新了 Lesson 1 Planner prompt：

```text
Select only the relevant research areas.
Provide a concise rationale explaining why the selected
research areas are required.
```

因此 Planner 现在真正负责产生：

```text
Research Areas
+
Rationale
```

---

### 11. Router Graph

新增文件：

```text
app/agents/research_router.py
```

核心结构：

```python
builder.add_node("router", lambda state: {})

builder.add_node(
    "company_research",
    _run_company_research,
)

builder.add_node(
    "financial_research",
    _run_financial_research,
)

builder.add_node(
    "market_research",
    _run_market_research,
)

builder.add_node(
    "industry_macro_research",
    _run_industry_macro_research,
)

builder.add_node(
    "routing_error",
    handle_routing_error,
)
```

然后：

```python
builder.add_conditional_edges(
    "router",
    route_research_area,
    {
        "company_research": "company_research",
        "financial_research": "financial_research",
        "market_research": "market_research",
        "industry_macro_research": "industry_macro_research",
        "routing_error": "routing_error",
    },
)
```

这就是本课最核心的 LangGraph 代码。

---

### 12. 为什么四个 Agent 都仍然是独立 Graph

例如：

```text
research_router
      │
      ▼
company_research
      │
      ▼
company_research_graph
```

而不是：

```python
financial_agent.call(company_agent)
```

或者：

```python
company_agent -> financial_agent
```

永远保持：

```text
                 ┌── Company Agent
                 │
Router ──────────┼── Financial Agent
                 │
                 ├── Market Agent
                 │
                 └── Industry/Macro Agent
```

**Agent 不知道其他 Agent 的存在。**

Orchestrator / Graph 才负责协调。

这正是 Phase 5 的核心架构原则。

---

### 13. Tests

新增：

```text
tests/test_research_router.py
```

主要测试四类。

#### 13.1 Company Routing

```text
ResearchArea.COMPANY
        ↓
company_research
```

#### 13.2 Financial Routing

```text
ResearchArea.FINANCIAL
        ↓
financial_research
```

#### 13.3 Market Routing

```text
ResearchArea.MARKET
        ↓
market_research
```

#### 13.4 Industry/Macro Routing

```text
ResearchArea.INDUSTRY_MACRO
        ↓
industry_macro_research
```

---

#### 13.5 不允许调用 LLM

Router 本身没有：

```python
llm.invoke(...)
```

测试重点是：

```text
Router
 ↓
deterministic mapping
```

而不是：

```text
Router
 ↓
LLM
 ↓
route
```

---

#### 13.6 非法 Route

测试：

```text
Plan:
    company

Requested:
    financial
```

必须得到：

```text
routing_error
```

不能执行 Financial Agent。

---

### 14. 当前测试状态

我已经对当前累积代码执行：

```bash
python -m compileall -q app tests
```

结果：

```text
compileall: PASS
```

你本地环境已经在刚才确认：

```text
Lesson 1 tests: PASS
```

本课请运行：

```bash
pytest tests/test_research_router.py -q
```

然后运行：

```bash
pytest tests/test_research_planner.py tests/test_research_router.py -q
```

建议再跑：

```bash
pytest tests/test_models.py -q
```

---

### 15. Lesson 2 Acceptance Criteria

本课完成的判断标准：

| 项目                              | 要求            |
|-----------------------------------|-----------------|
| Router 存在                       | ✅              |
| Router 使用 deterministic routing | ✅              |
| Router 不调用 LLM                 | ✅              |
| Company route                     | ✅              |
| Financial route                   | ✅              |
| Market route                      | ✅              |
| Industry/Macro route              | ✅              |
| 非 Plan 中的 Area 被拒绝          | ✅              |
| Agent 本身保持独立                | ✅              |
| Agent 不直接调用其他 Agent        | ✅              |
| 没有并行执行                      | ✅              |
| 没有 Fan-out/Fan-in               | ✅              |
| 没有 Supervisor                   | ✅              |
| `ResearchPlan.rationale` 保留     | ✅              |
| Python compile                    | ✅              |
| Router tests                      | ⏳ 等你本地运行 |

---

### 16. 本课最重要的理解

到这里，系统第一次形成了明确的三层职责：

```text
┌─────────────────────────────┐
│ Research Planner            │
│                             │
│ “需要研究什么？”             │
└──────────────┬──────────────┘
               │
               ▼
        ResearchPlan
               │
               ▼
┌─────────────────────────────┐
│ Research Router             │
│                             │
│ “当前应该交给谁？”           │
└──────────────┬──────────────┘
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
    Company Financial Market ...
```

所以：

```text
Planner = WHAT
Router  = WHERE / WHICH
Agent   = DO
```

这三个职责不能混在一起。

---

### 17. 为什么现在还不能叫 Multi-Agent Orchestration 完成

目前我们只能做到：

```text
Plan
  ↓
选择一个 Area
  ↓
执行一个 Agent
```

还不能做到：

```text
Plan
  ↓
Company
  ↓
Financial
  ↓
Market
  ↓
Industry/Macro
```

也不能：

```text
             ┌→ Company
Plan → Fan-out ┼→ Financial
             ├→ Market
             └→ Industry
```

更不能：

```text
Supervisor
    ↓
观察 State
    ↓
决定下一步
```

所以现在只是建立了：

> **Agent Routing**

而不是提前实现整个 Multi-Agent Orchestration。

---

### 18. Phase 5 当前进度

现在已经是：

```text
Phase 5 — Multi-Agent Orchestration

Lesson 1
Research Planner
        ↓
ResearchPlan
        ✅

Lesson 2
Agent Routing
        ↓
Research Agent
        ✅

Lesson 3
Multi-Agent Shared State
        ↓
下一课
```

Lesson 3 的核心问题将变成：

> **多个 Agent 的结果，应该如何进入同一个共享 State？**

届时我们会正式解决：

```text
company_research
financial_research
market_research
industry_research
```

以及：

```text
Input State
Internal State
Output State
```

但仍然**不会**进入 Parallel。

Parallel 要等 Shared State 稳定之后，再在 Lesson 5 引入。

---


## Lesson 3：Multi-Agent Shared State

Lesson 3 已完成实现，核心变化是：

```text
Lesson 2

Router
  ↓
research_result
```

变为：

```text
Lesson 3

Router
  ↓
Shared Research State
  ├── company_research
  ├── financial_research
  ├── market_research
  └── industry_macro_research
```

### 本课新增

```text
app/agents/research_state.py
tests/test_research_state.py
```

`ResearchState` 当前定义了：

```python
class ResearchState(TypedDict, total=False):
    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: dict[str, str]
```

### Router 的变化

例如 Financial Agent 现在不再：

```python
"research_result": result["research_result"]
```

而是：

```python
"financial_research": result["research_result"]
```

因此不同 Agent 可以把结果放入不同的 State 字段，而不会互相覆盖。

同时保留：

```text
Agent Failure
    ↓
research_errors
```

的显式错误信息。

---

### 本课没有做的事情

严格保持 Lesson 边界：

* ❌ 没有 Sequential Orchestration
* ❌ 没有 Parallel Execution
* ❌ 没有 Fan-out
* ❌ 没有 Fan-in
* ❌ 没有 Reducer
* ❌ 没有 Supervisor
* ❌ 没有修改 Phase 4 Research Agent 的内部结构

特别是 **Reducer 不在本课引入**。

现在仍然只有一个 Agent 分支执行，因此 `research_errors` 使用普通 `dict` 即可。到了 Lesson 5 真正进入并行执行时，再解决多个分支如何安全合并 State 的问题。

---

### 验证

当前新增代码已经通过：

```bash
python -m compileall -q app tests
```

你本地已经验证 Lesson 2：

```text
tests/test_research_router.py → PASS
```

Lesson 3 请运行：

```bash
pytest tests/test_research_state.py tests/test_research_router.py -q
```

再运行：

```bash
pytest tests/test_models.py tests/test_research_planner.py tests/test_research_router.py tests/test_research_state.py -q
```

---

### Lesson 3 的核心理解

现在我们正式拥有了：

```text
                    ┌── company_research
                    │
ResearchPlan → Router ── financial_research
                    │
                    ├── market_research
                    │
                    └── industry_macro_research
                             
                              ↓

                       ResearchState
```

这意味着：

> **State 开始成为多个 Agent 之间真正的共享边界。**

Agent 仍然不知道其他 Agent 的存在；它只负责产生自己的结果，而 Orchestrator/Graph 负责把结果放入共享 State。

下一课才会利用这个 Shared State 构建：

```text
Planner
   ↓
Company Agent
   ↓
Financial Agent
   ↓
Market Agent
   ↓
Industry/Macro Agent
   ↓
Research State
```

也就是 **Lesson 4 — Sequential Multi-Agent Orchestration**。


## Lesson 4：Sequential Multi-Agent Orchestration

这一课的目标非常明确：

> **把 Planner、Router、Shared State 和已有的四个 Research Agent 串成一个确定性的 Sequential Orchestrator。**

---

### 1. Lesson 4 解决什么问题

Lesson 3 之后，我们已经有：

```text
User Query
    ↓
Research Planner
    ↓
ResearchPlan
    ↓
Router
    ↓
一个 Research Agent
    ↓
ResearchState
```

但仍然只能执行一次 Agent。

Lesson 4 将它扩展为：

```text
User Query
    ↓
Research Planner
    ↓
ResearchPlan
    ↓
Sequential Orchestrator
    │
    ├── Company Research
    │
    ├── Financial Research
    │
    ├── Market Research
    │
    └── Industry / Macro Research
    │
    ↓
ResearchState
```

但有一个重要规则：

**只有 ResearchPlan 中选择的 Agent 才执行。**

例如：

```text
ResearchPlan:
    company
    market
    industry_macro
```

实际执行：

```text
Company
   ↓
Market
   ↓
Industry/Macro
```

不会执行 Financial。

---

### 2. Graph Topology

本课最终 Graph 是：

```text
START
  │
  ▼
research_planner
  │
  ▼
prepare_next_research
  │
  ▼
route_and_execute
  │
  ▼
mark_completed
  │
  ▼
prepare_next_research
  │
  ▼
route_and_execute
  │
  ▼
mark_completed
  │
  ▼
    ...
  │
  ▼
END
```

因此它实际上是一个**确定性的 Sequential Loop**：

```text
Planner
   ↓
找到下一个需要执行的 Research Area
   ↓
Router
   ↓
Agent
   ↓
记录完成
   ↓
寻找下一个 Research Area
   ↓
...
```

注意：

这虽然存在 Graph loop，但它**不是 Supervisor Loop**。

因为这里没有：

```text
LLM
 ↓
观察 State
 ↓
自主决定下一步
```

而是固定规则：

```text
COMPANY
    ↓
FINANCIAL
    ↓
MARKET
    ↓
INDUSTRY_MACRO
```

然后根据 `ResearchPlan` 跳过未选择的 Area。

---

### 3. 为什么不把四个 Agent 直接硬编码成固定执行

例如不采用：

```text
Company
 ↓
Financial
 ↓
Market
 ↓
Industry
```

无条件执行。

因为那样就意味着：

```text
ResearchPlan
```

实际上没有控制 Orchestration。

Planner 说：

```text
只需要 Market + Financial
```

Orchestrator 却执行：

```text
Company
Financial
Market
Industry
```

这是架构错误。

因此本课采用：

```text
ResearchPlan
      ↓
selected areas
      ↓
固定顺序遍历
      ↓
只执行 selected areas
```

这同时满足：

```text
Planner = 决定 WHAT
Orchestrator = 决定 HOW / ORDER
Agent = 执行 DO
```

---

### 4. 新增文件

本课新增：

```text
app/agents/research_orchestrator.py
```

以及：

```text
tests/test_research_orchestrator.py
```

没有重新实现任何 Research Agent。

---

### 5. Sequential Orchestrator State

使用现有：

```python
ResearchState
```

并增加：

```python
user_query: str
completed_research_areas: list[ResearchArea]
current_research_area: ResearchArea | None
planning_error: str
orchestration_error: str
```

因此运行中的 State 可以理解为：

```text
ResearchState
├── ticker
├── research_plan
├── next_research_area
│
├── company_research
├── financial_research
├── market_research
├── industry_macro_research
│
├── research_errors
│
├── completed_research_areas
├── current_research_area
│
├── planning_error
└── orchestration_error
```

其中：

```text
completed_research_areas
```

记录已经执行过的研究领域。

例如：

```python
[
    ResearchArea.COMPANY,
    ResearchArea.FINANCIAL,
]
```

那么下一次只会寻找：

```text
MARKET
```

或者：

```text
INDUSTRY_MACRO
```

---

### 6. 固定 Research Order

本课明确建立：

```python
RESEARCH_ORDER = [
    ResearchArea.COMPANY,
    ResearchArea.FINANCIAL,
    ResearchArea.MARKET,
    ResearchArea.INDUSTRY_MACRO,
]
```

这代表的是：

> **Sequential Orchestration 的执行顺序。**

它不是 Planner 的职责。

Planner 决定：

```text
哪些需要研究
```

Orchestrator 决定：

```text
这些需要研究的内容按照什么顺序执行
```

例如 Planner：

```text
financial
market
company
```

即使 LLM 输出顺序是：

```text
financial
market
company
```

Orchestrator 仍然按照：

```text
company
financial
market
```

执行。

这使执行顺序成为确定性的工程规则，而不是 LLM 的随机行为。

---

### 7. `prepare_next_research`

核心逻辑：

```python
for research_area in RESEARCH_ORDER:
    if (
        research_area in plan.research_areas
        and research_area not in completed
    ):
        return {
            "current_research_area": research_area
        }
```

因此：

```text
Plan
    ↓
[Company, Market, Industry]
    ↓
固定 Order
    ↓
Company
    ↓
Market
    ↓
Industry
```

而不是依赖：

```text
LLM 输出 list 的顺序
```

---

### 8. Router 与 Orchestrator 的关系

这里非常重要。

我们没有删除 Lesson 2 的 Router。

现在：

```text
Sequential Orchestrator
          ↓
    current_research_area
          ↓
        Router
          ↓
       Agent
```

也就是说：

```text
Orchestrator
```

决定：

> 下一步要研究哪个 Area。

然后：

```text
Router
```

负责：

> 把这个 Area 映射到具体 Agent。

例如：

```text
current_research_area
        ↓
FINANCIAL
        ↓
Research Router
        ↓
financial_research_graph
```

所以职责仍然非常清晰：

```text
Planner
  ↓
ResearchPlan

Orchestrator
  ↓
Next Area

Router
  ↓
Agent Node

Agent
  ↓
Research Result

Shared State
  ↓
保存结果
```

---

### 9. 为什么这是 Sequential，而不是 Parallel

当前执行路径永远是：

```text
Agent A
  ↓
Agent B
  ↓
Agent C
```

后一个 Agent 只有在前一个 Agent 完成之后才会开始。

例如：

```text
Company
  ↓
完成
  ↓
Financial
  ↓
完成
  ↓
Market
```

不存在：

```text
Company ─────┐
Financial ───┼── 同时
Market ──────┘
```

所以本课明确没有：

```text
Send
fan-out
parallel branches
reducer
join
```

这些内容留到后面的 Lesson 5/6。

---

### 10. Failure Handling

Planner 失败：

```text
Planner
   ↓
planning_error
   ↓
orchestration_error
   ↓
END
```

不会继续执行 Research Agent。

---

Router 失败：

```text
Router
   ↓
routing_error
   ↓
orchestration_error
   ↓
END
```

也不会继续执行后续 Agent。

---

而 Agent 自己的研究失败：

```text
Financial Agent
       ↓
research_error
       ↓
research_errors["financial"]
```

这个错误由现有 Router 写入 Shared State。

当前 Sequential Orchestrator **不会因为一个 Agent 的业务研究失败而自动变成 Supervisor**。

也就是说：

```text
Financial Agent
       ↓
failure
       ↓
record error
       ↓
continue to next selected area
```

这样可以保留：

```text
Partial Research
```

信息。

真正如何处理 Partial Failure，将在后续 Fan-out/Fan-in 阶段进一步讨论。

---

### 11. Tests

新增测试覆盖了几个非常重要的行为。

#### 11.1 Sequential Order

Plan：

```text
company
market
industry_macro
```

实际执行必须是：

```text
company
→ market
→ industry_macro
```

而不是：

```text
industry_macro
→ market
→ company
```

---

#### 11.2 Skip Unselected Agents

Plan：

```text
financial
```

只允许：

```text
Financial Agent
```

执行。

测试确保：

```text
Company ❌
Market ❌
Industry/Macro ❌
Financial ✅
```

---

#### 11.3 Planner Failure

模拟：

```text
Planner failed.
```

必须：

```text
planning_error
    ↓
orchestration_error
```

并且：

```text
Router.invoke()
```

不能被调用。

---

#### 11.4 Routing Failure

模拟 Router 返回：

```text
routing_error
```

Orchestrator 必须停止：

```text
routing_error
    ↓
orchestration_error
    ↓
END
```

不会继续执行剩余研究。

---

### 12. 当前代码检查

Lesson 4 新代码已经完成：

```bash
python -m compileall -q app tests
```

结果：

```text
PASS
```

我没有把当前执行环境无法运行完整 pytest 的问题伪装成测试通过；你本地环境已经具备 LangGraph 依赖，因此继续使用你之前的验证方式。

---

### 13. Lesson 4 Acceptance Criteria

| 项目                     | 状态            |
|--------------------------|-----------------|
| Planner → Orchestrator   | ✅              |
| 使用已有 ResearchPlan    | ✅              |
| 使用已有 Shared State    | ✅              |
| Sequential execution     | ✅              |
| 固定 Research Order      | ✅              |
| 未选择的 Agent 不执行    | ✅              |
| 使用已有 Router          | ✅              |
| Agent 保持独立           | ✅              |
| Agent 不调用 Agent       | ✅              |
| Agent failure 显式记录   | ✅              |
| Planner failure 显式处理 | ✅              |
| Routing failure 显式处理 | ✅              |
| Parallel                 | ❌ 本课不做     |
| Fan-out                  | ❌ 本课不做     |
| Fan-in                   | ❌ 本课不做     |
| Reducer                  | ❌ 本课不做     |
| Supervisor               | ❌ 本课不做     |
| Python compile           | ✅              |
| Lesson 4 pytest          | ⏳ 等你本地运行 |

---

### 14. 本课最重要的理解

Phase 5 到这里，架构已经从：

```text
Planner
   ↓
Router
   ↓
Agent
```

发展成：

```text
                  ┌──────────────┐
                  │    Planner   │
                  └──────┬───────┘
                         │
                         ▼
                  ResearchPlan
                         │
                         ▼
               Sequential Orchestrator
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     │
            Router                  │
              │                     │
              ▼                     │
             Agent                  │
              │                     │
              ▼                     │
        Shared Research State       │
              │                     │
              └────── next ─────────┘
```

而且三个层次的职责已经明确：

```text
Planner
    = WHAT

Orchestrator
    = WHEN / ORDER

Router
    = WHICH AGENT

Agent
    = DO THE RESEARCH

State
    = SHARED BOUNDARY
```

这是后面进入 Parallel 的基础。

---


## Lesson 5：Parallel Research Agents

### Part 1: Parallel Research Agents + Reducer

#### 1. Goal

本课只解决一个问题：

> **让多个 Research Agent 真正并行执行，并把各自结果安全地合并回 Shared State。**

上一课：

```text
Planner
   ↓
Orchestrator
   ↓
Company
   ↓
Financial
   ↓
Market
   ↓
Industry/Macro
```

是：

> **Sequential Multi-Agent Orchestration**

本课开始变成：

```text
                    ┌── Company ────────┐
                    │                   │
Planner → Fan-out ──┼── Financial ──────┼──→ Shared State
                    │                   │
                    ├── Market ─────────┤
                    │                   │
                    └── Industry/Macro ─┘
```

也就是：

> **多个 Agent 同时工作。**

---

#### 2. Why Now

Lesson 4 已经解决了：

```text
Planner
    ↓
ResearchPlan
    ↓
Orchestrator
    ↓
Router
    ↓
Agent
    ↓
Agent
    ↓
Agent
```

因此现在我们已经具备：

* Planner
* Router
* Shared State
* Dedicated research fields
* Sequential Orchestration

缺少的就是：

> **Parallel Execution**

而一旦进入 Parallel，就会产生一个 Lesson 4 中没有出现的新问题：

```text
Company Agent ──────┐
                    │
Financial Agent ────┼──→ 同一个 State
                    │
Market Agent ───────┤
                    │
Industry Agent ─────┘
```

多个节点可能同时产生 State Update。

因此我们必须回答：

> **多个并行节点写回同一个 State 时，LangGraph 应该如何合并这些 Update？**

这就是 **Reducer**。

---

#### 3. 本课核心概念

##### 3.1 Sequential State Update

上一课是：

```text
Company
   ↓
State Update

Financial
   ↓
State Update

Market
   ↓
State Update
```

每次只有一个 Agent 修改 State。

所以我们可以通过：

```python
return {
    "company_research": result,
}
```

这种方式自然完成更新。

---

##### 3.2 Parallel State Update

本课则可能出现：

```text
Company ───────→ {
    "company_research": ...
}

Financial ─────→ {
    "financial_research": ...
}

Market ────────→ {
    "market_research": ...
}
```

这些 Update 最终都要进入：

```text
ResearchState
```

所以 State 必须知道：

> 如果多个节点同时更新同一个字段，应该怎么处理？

---

#### 4. Reducer 是什么

可以先把 Reducer 理解成：

> **一个 State Field 的 Merge Policy。**

例如：

```python
research_errors: Annotated[
    dict[str, str],
    merge_dicts,
]
```

表示：

```text
旧值 + 新值
      ↓
 merge_dicts
      ↓
新 State
```

例如：

```python
old = {
    "company": "error A",
}

new = {
    "financial": "error B",
}
```

Reducer：

```python
{
    "company": "error A",
    "financial": "error B",
}
```

---

#### 5. 本课一个非常重要的边界

**不要把所有 State 字段都加 Reducer。**

这是本课非常重要的设计原则。

例如：

```python
company_research
```

理论上只有 Company Agent 写它。

```python
financial_research
```

理论上只有 Financial Agent 写它。

所以这些字段：

```text
company_research
financial_research
market_research
industry_macro_research
```

**暂时不需要 Reducer。**

真正需要 Reducer 的典型字段是：

```python
research_errors
```

因为多个并行 Agent 都可能产生 error：

```text
Company ──────→ research_errors
Financial ─────→ research_errors
Market ───────→ research_errors
```

如果没有 Reducer，就可能发生：

```text
Company error
     ↓
Financial error
     ↓
Company error 消失
```

这与我们刚才解决的问题本质上类似。

---

#### 6. Graph Topology

Lesson 5 暂时先不要做 Fan-out / Fan-in 的完整动态模式。

本课第一步先建立一个**固定 Parallel Research Graph**。

目标拓扑：

```text
                         ┌── company_research ──────┐
                         │                          │
                         ├── financial_research ────┤
                         │                          │
START → parallel_research ┼── market_research ───────┼──→ END
                         │                          │
                         └── industry_macro ────────┘
```

更准确地说，LangGraph 的节点关系是：

```text
START
  │
  ├────────→ company_research ──────┐
  │                                 │
  ├────────→ financial_research ────┤
  │                                 │
  ├────────→ market_research ───────┤
  │                                 │
  └────────→ industry_macro ────────┘
                                    │
                                    ▼
                                   END
```

这一次我们第一次让：

```text
START
 ↓
多个节点
```

同时发生。

---

#### 7. State Design

当前：

```python
class ResearchState(TypedDict, total=False):
    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: dict[str, str]
```

本课重点修改：

```python
research_errors
```

因为它需要支持多个并行 Agent 的更新。

---

#### 8. Exact Files

本课建议：

##### 新增

```text
app/agents/research_parallel.py
tests/test_research_parallel.py
```

##### 修改

```text
app/agents/research_state.py
```

其他 Agent 暂时不要动。

---

#### 9. 第一步：定义 Reducer

在：

```text
app/agents/research_state.py
```

中增加：

```python
from typing import Annotated, TypedDict
```

然后定义：

```python
def merge_research_errors(
    existing: dict[str, str] | None,
    new: dict[str, str] | None,
) -> dict[str, str]:
    """Merge research errors from parallel research agents."""
    merged = dict(existing or {})
    merged.update(new or {})
    return merged
```

然后：

```python
research_errors: Annotated[
    dict[str, str],
    merge_research_errors,
]
```

所以最终：

```python
class ResearchState(TypedDict, total=False):
    """Shared state boundary for multi-agent research orchestration."""

    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: Annotated[
        dict[str, str],
        merge_research_errors,
    ]
```

---

#### 10. 为什么这里使用 `Annotated`

这里是 LangGraph State 的一个关键语法：

```python
Annotated[
    dict[str, str],
    merge_research_errors,
]
```

它表达的是：

```text
State Field
    │
    ├── Type
    │    ↓
    │  dict[str, str]
    │
    └── Reducer
         ↓
    merge_research_errors
```

也就是说：

```python
research_errors
```

不再是简单：

```text
new value replaces old value
```

而是：

```text
old value
    +
new value
    ↓
Reducer
    ↓
merged value
```

---

#### 11. 第二步：建立 Parallel Graph

新建：

```text
app/agents/research_parallel.py
```

第一版先不要把 Planner 和 Router 放进来。

我们专门学习：

> **Parallel Agent Execution**

可以使用现有四个 Agent Graph。

结构：

```python
from langgraph.graph import END, START, StateGraph

from app.agents.company_research import company_research_graph
from app.agents.financial_research import financial_research_graph
from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.market_research import market_research_graph
from app.agents.research_state import ResearchState
```

然后定义四个 wrapper。

例如：

```python
def _run_company(
    state: ResearchState,
) -> ResearchState:
    result = company_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "company_research": result.get("company_research"),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

Financial：

```python
def _run_financial(
    state: ResearchState,
) -> ResearchState:
    result = financial_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "financial_research": result.get(
            "financial_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

Market：

```python
def _run_market(
    state: ResearchState,
) -> ResearchState:
    result = market_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "market_research": result.get(
            "market_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

Industry/Macro：

```python
def _run_industry_macro(
    state: ResearchState,
) -> ResearchState:
    result = industry_macro_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "industry_macro_research": result.get(
            "industry_macro_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

---

#### 12. 构建 Graph

```python
def build_parallel_research_graph():
    builder = StateGraph(ResearchState)

    builder.add_node("company_research", _run_company)
    builder.add_node("financial_research", _run_financial)
    builder.add_node("market_research", _run_market)
    builder.add_node(
        "industry_macro_research",
        _run_industry_macro,
    )

    builder.add_edge(
        START,
        "company_research",
    )
    builder.add_edge(
        START,
        "financial_research",
    )
    builder.add_edge(
        START,
        "market_research",
    )
    builder.add_edge(
        START,
        "industry_macro_research",
    )

    builder.add_edge(
        "company_research",
        END,
    )
    builder.add_edge(
        "financial_research",
        END,
    )
    builder.add_edge(
        "market_research",
        END,
    )
    builder.add_edge(
        "industry_macro_research",
        END,
    )

    return builder.compile()


research_parallel_graph = build_parallel_research_graph()
```

这里非常值得你注意：

```python
builder.add_edge(START, "company_research")
builder.add_edge(START, "financial_research")
builder.add_edge(START, "market_research")
builder.add_edge(START, "industry_macro_research")
```

这四条 Edge 是并行拓扑的核心。

---

#### 13. 第一组测试：四个 Agent 都执行

新建：

```text
tests/test_research_parallel.py
```

先测试 Graph 是否真正启动四个 Agent。

可以 monkeypatch 四个 graph：

```python
def test_parallel_research_executes_all_agents(monkeypatch):
    executed = []

    def mock_company(state):
        executed.append("company")
        return {
            "company_research": None,
            "research_errors": {},
        }

    def mock_financial(state):
        executed.append("financial")
        return {
            "financial_research": None,
            "research_errors": {},
        }

    def mock_market(state):
        executed.append("market")
        return {
            "market_research": None,
            "research_errors": {},
        }

    def mock_industry_macro(state):
        executed.append("industry_macro")
        return {
            "industry_macro_research": None,
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_parallel.company_research_graph.invoke",
        mock_company,
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.financial_research_graph.invoke",
        mock_financial,
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.market_research_graph.invoke",
        mock_market,
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.industry_macro_research_graph.invoke",
        mock_industry_macro,
    )

    result = research_parallel_graph.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert set(executed) == {
        "company",
        "financial",
        "market",
        "industry_macro",
    }
```

注意这里**不要断言执行顺序**。

这是 Parallel Graph。

我们关心：

```text
全部执行
```

而不是：

```text
谁先执行
```

---

#### 14. 第二组测试：四个 Dedicated Fields 都保留

这是本课非常重要的测试。

```python
def test_parallel_research_preserves_all_results(monkeypatch):
    company_result = object()
    financial_result = object()
    market_result = object()
    industry_macro_result = object()

    monkeypatch.setattr(
        "app.agents.research_parallel.company_research_graph.invoke",
        lambda state: {
            "company_research": company_result,
            "research_errors": {},
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.financial_research_graph.invoke",
        lambda state: {
            "financial_research": financial_result,
            "research_errors": {},
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.market_research_graph.invoke",
        lambda state: {
            "market_research": market_result,
            "research_errors": {},
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.industry_macro_research_graph.invoke",
        lambda state: {
            "industry_macro_research": industry_macro_result,
            "research_errors": {},
        },
    )

    result = research_parallel_graph.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result["company_research"] is company_result
    assert result["financial_research"] is financial_result
    assert result["market_research"] is market_result
    assert (
        result["industry_macro_research"]
        is industry_macro_result
    )
```

这个测试与刚才 Lesson 4 的 bug 有一个非常重要的区别：

Lesson 4：

```text
Sequential
→ 后一个 update 覆盖前一个错误 update
```

Lesson 5：

```text
Parallel
→ 多个 update 同时进入 State
→ Dedicated fields 独立保存
```

---

#### 15. 第三个测试：Reducer

这是本课最关键的测试。

直接测试：

```python
def test_research_errors_reducer_merges_errors():
    existing = {
        "company": "Company research failed.",
    }

    new = {
        "financial": "Financial research failed.",
    }

    merged = merge_research_errors(
        existing,
        new,
    )

    assert merged == {
        "company": "Company research failed.",
        "financial": "Financial research failed.",
    }
```

然后再测试真正的 Graph：

```python
def test_parallel_research_merges_errors(monkeypatch):
    monkeypatch.setattr(
        "app.agents.research_parallel.company_research_graph.invoke",
        lambda state: {
            "company_research": None,
            "research_errors": {
                "company": "Company failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.financial_research_graph.invoke",
        lambda state: {
            "financial_research": None,
            "research_errors": {
                "financial": "Financial failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.market_research_graph.invoke",
        lambda state: {
            "market_research": None,
            "research_errors": {
                "market": "Market failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.industry_macro_research_graph.invoke",
        lambda state: {
            "industry_macro_research": None,
            "research_errors": {
                "industry_macro": "Industry/macro failed.",
            },
        },
    )

    result = research_parallel_graph.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result["research_errors"] == {
        "company": "Company failed.",
        "financial": "Financial failed.",
        "market": "Market failed.",
        "industry_macro": "Industry/macro failed.",
    }
```

这个测试才真正证明：

```text
                    company error
                         │
                         ▼
                    ┌─────────┐
                    │ Reducer │
                    └────┬────┘
                         │
financial error ─────────┤
                         │
market error ────────────┤
                         │
industry error ──────────┘
                         ↓
              merged research_errors
```

---

#### 16. 本课暂时不要做的事情

Lesson 5 第一阶段先**不要**加入：

* Research Planner
* Router
* 动态 ResearchPlan
* Fan-out / Fan-in
* Supervisor
* Reducer for every field
* 新 Agent
* 新 ResearchArea
* 复杂错误恢复

本课只学习：

> **Parallel execution + State Reducer**

---

#### 17. Acceptance Criteria

完成后必须满足：

##### Graph

```text
START
 ├── Company
 ├── Financial
 ├── Market
 └── Industry/Macro
```

四个 Agent 可以并行执行。

##### State

最终：

```text
company_research       ✓
financial_research     ✓
market_research        ✓
industry_macro_research ✓
```

不会因为并行更新而互相覆盖。

##### Reducer

多个 Agent：

```text
research_errors
```

可以合并：

```text
company
financial
market
industry_macro
```

而不是只保留最后一个。

##### Tests

至少通过：

```text
test_parallel_research_executes_all_agents
test_parallel_research_preserves_all_results
test_research_errors_reducer_merges_errors
test_parallel_research_merges_errors
```

---

#### 本课最重要的理解

到这里，你应该能明确区分：

```text
Lesson 4
Sequential
    ↓
一个 Agent 更新 State
    ↓
下一个 Agent 更新 State
```

和：

```text
Lesson 5
Parallel
    ↓
多个 Agent 同时更新 State
    ↓
Reducer 负责定义如何合并
```

以及：

```text
Dedicated Field
    ↓
company_research
financial_research
market_research
industry_macro_research
```

与：

```text
Shared Field
    ↓
research_errors
    ↓
需要 Reducer
```


## Lesson 6：Dynamic Fan-out / Fan-in

Lesson 5 的 Parallel Graph 是：

> **固定的四路并行。**

Lesson 6 要解决的是：

> **根据 Planner 的 `ResearchPlan.research_areas` 动态决定到底启动哪些 Agent。**

---

### 1. Goal

假设 Planner 返回：

```python
[
    ResearchArea.COMPANY,
    ResearchArea.FINANCIAL,
    ResearchArea.MARKET,
]
```

我们不应该再固定启动：

```text
Company
Financial
Market
Industry/Macro
```

而应该动态产生：

```text
          ┌── Company
          ├── Financial
START ────┼── Market
          └── 不启动 Industry/Macro
```

如果 Planner 返回：

```python
[
    ResearchArea.COMPANY,
    ResearchArea.INDUSTRY_MACRO,
]
```

则：

```text
          ┌── Company
START ────┤
          └── Industry/Macro
```

这就是 **Dynamic Fan-out**。

---

### 2. Why Now

目前我们的系统存在两个并行 Graph：

#### Lesson 4

Sequential：

```text
COMPANY
   ↓
FINANCIAL
   ↓
MARKET
   ↓
INDUSTRY_MACRO
```

#### Lesson 5

Fixed Parallel：

```text
       Company
       Financial
START  Market
       Industry/Macro
```

但真正的 Research Planner 已经能够产生：

```python
research_plan.research_areas
```

例如：

```text
[COMPANY, MARKET]
```

所以如果我们始终启动四个 Agent：

```text
Planner 说只需要 Company + Market
                ↓
却执行四个 Agent
```

那么 Planner 的决策就没有真正控制执行图。

Lesson 6 要建立：

```text
Planner
   │
   ▼
ResearchPlan
   │
   │ selected areas
   ▼
Dynamic Fan-out
   │
   ├── selected Agent
   ├── selected Agent
   └── selected Agent
```

---

### 3. 核心概念：Send

这一课第一次正式引入 LangGraph 的：

```python
Send
```

它的用途正是：

> **在运行时动态创建并行任务。**

概念上：

```python
Send(
    "research_agent",
    {
        "research_area": ResearchArea.COMPANY,
        ...
    },
)
```

可以理解成：

```text
“请启动一个 research_agent，
并给它这一份独立的任务输入。”
```

如果有三个 ResearchArea：

```text
[
    COMPANY,
    FINANCIAL,
    MARKET,
]
```

Fan-out 可以动态生成：

```text
Send("research_agent", COMPANY)
Send("research_agent", FINANCIAL)
Send("research_agent", MARKET)
```

形成：

```text
             ┌── research_agent(COMPANY)
             │
START ───────┼── research_agent(FINANCIAL)
             │
             └── research_agent(MARKET)
```

---

### 4. 为什么这是真正的 Fan-out

Lesson 5：

```text
START
 ├→ company_research
 ├→ financial_research
 ├→ market_research
 └→ industry_macro_research
```

Graph topology 在代码里是**静态写死的**。

Lesson 6：

```text
ResearchPlan
     │
     │ runtime data
     ▼
[COMPANY, FINANCIAL, MARKET]
     │
     ▼
动态生成三个 Send
```

因此：

> **Fan-out 的数量由运行时 State 决定。**

这才是 Dynamic Fan-out。

---

### 5. Graph Topology

这一课建议建立一个独立 Graph：

```text
START
  │
  ▼
prepare_research_tasks
  │
  │ conditional Send
  ├──────────────┐
  ▼              ▼
research_agent  research_agent
(COMPANY)       (FINANCIAL)
  │              │
  └──────┬───────┘
         │
         ▼
       END
```

如果运行时有三个 area：

```text
prepare_research_tasks
        │
        ├──→ COMPANY Agent
        ├──→ FINANCIAL Agent
        └──→ MARKET Agent
```

---

### 6. 一个重要设计选择

这里我们**不再使用 Lesson 5 的四个固定 Agent Node**：

```python
company_research
financial_research
market_research
industry_macro_research
```

而建立一个统一的：

```text
research_agent
```

它收到：

```python
research_area
```

然后决定调用哪个已有 Agent Graph。

注意：

> 这个 `research_agent` 不是新的业务 Agent。

它只是一个 **dynamic dispatch node**。

真正的研究仍然由：

```text
Company Research Agent
Financial Research Agent
Market Research Agent
Industry/Macro Research Agent
```

完成。

---

### 7. State Design

这一课需要引入一个非常小的 task state。

建议：

```python
class ResearchTask(TypedDict):
    research_area: ResearchArea
```

然后动态 Agent 的输入：

```python
class DynamicResearchState(ResearchState):
    research_area: ResearchArea
```

这里要注意：

```text
ResearchPlan
    │
    │ list[ResearchArea]
    ▼
Fan-out
    │
    ├── ResearchTask(COMPANY)
    ├── ResearchTask(FINANCIAL)
    └── ResearchTask(MARKET)
```

---

### 8. Exact Files

新增：

```text
app/agents/research_fanout.py
tests/test_research_fanout.py
```

暂时不要修改：

```text
research_orchestrator.py
research_parallel.py
research_router.py
```

因为我们仍然是逐课学习。

---

### 9. `research_fanout.py`

首先：

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agents.company_research import company_research_graph
from app.agents.financial_research import financial_research_graph
from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.market_research import market_research_graph
from app.agents.models import ResearchArea, ResearchPlan
from app.agents.research_state import ResearchState
```

定义输入：

```python
class ResearchFanoutInputState(TypedDict):
    ticker: str
    research_plan: ResearchPlan
```

动态 Agent State：

```python
class ResearchFanoutState(ResearchState, total=False):
    research_area: ResearchArea
```

---

### 10. Dynamic Fan-out Function

核心函数：

```python
def fan_out_research(
    state: ResearchFanoutState,
) -> list[Send]:
    plan = state["research_plan"]

    return [
        Send(
            "research_agent",
            {
                "ticker": state["ticker"],
                "research_area": research_area,
            },
        )
        for research_area in plan.research_areas
    ]
```

这里就是本课最核心的代码。

例如：

```python
plan.research_areas = [
    COMPANY,
    FINANCIAL,
    MARKET,
]
```

那么返回：

```text
[
    Send(... COMPANY),
    Send(... FINANCIAL),
    Send(... MARKET),
]
```

LangGraph 会根据这些 `Send` 创建并行执行。

---

### 11. Dynamic Research Agent

然后：

```python
def _run_research_agent(
    state: ResearchFanoutState,
) -> ResearchFanoutState:
    research_area = state["research_area"]
```

根据 Area dispatch：

```python
if research_area == ResearchArea.COMPANY:
    result = company_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "company_research": result.get(
            "company_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

Financial：

```python
if research_area == ResearchArea.FINANCIAL:
    result = financial_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "financial_research": result.get(
            "financial_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

Market：

```python
if research_area == ResearchArea.MARKET:
    result = market_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "market_research": result.get(
            "market_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

Industry/Macro：

```python
if research_area == ResearchArea.INDUSTRY_MACRO:
    result = industry_macro_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "industry_macro_research": result.get(
            "industry_macro_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }
```

最后：

```python
raise ValueError(
    f"Unsupported research area: {research_area}"
)
```

---

### 12. Build Graph

```python
def build_research_fanout_graph():
    builder = StateGraph(
        ResearchFanoutState,
        input_schema=ResearchFanoutInputState,
    )

    builder.add_node(
        "research_agent",
        _run_research_agent,
    )

    builder.add_conditional_edges(
        START,
        fan_out_research,
    )

    builder.add_edge(
        "research_agent",
        END,
    )

    return builder.compile()


research_fanout_graph = build_research_fanout_graph()
```

这里有一个非常值得注意的变化：

之前：

```python
builder.add_edge(START, ...)
```

现在：

```python
builder.add_conditional_edges(
    START,
    fan_out_research,
)
```

因为返回值不再是：

```text
一个固定 node name
```

而是：

```text
多个 Send
```

---

### 13. 测试一：只执行 Planner 选择的 Agent

这是本课最重要的测试。

```python
def test_fanout_executes_only_selected_research_areas(
    monkeypatch,
):
    executed = []

    monkeypatch.setattr(
        "app.agents.research_fanout.company_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.COMPANY)
            or {
                "company_research": None,
                "research_errors": {},
            }
        ),
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.financial_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.FINANCIAL)
            or {
                "financial_research": None,
                "research_errors": {},
            }
        ),
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.market_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.MARKET)
            or {
                "market_research": None,
                "research_errors": {},
            }
        ),
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.industry_macro_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.INDUSTRY_MACRO)
            or {
                "industry_macro_research": None,
                "research_errors": {},
            }
        ),
    )

    plan = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.MARKET,
        ],
        rationale="Only company and market research are required.",
    )

    research_fanout_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": plan,
        }
    )

    assert set(executed) == {
        ResearchArea.COMPANY,
        ResearchArea.MARKET,
    }
```

尤其要确认：

```text
FINANCIAL
INDUSTRY_MACRO
```

没有执行。

---

### 14. 测试二：不同 ResearchPlan 产生不同 Fan-out

再测试：

```python
def test_fanout_respects_research_plan(
    monkeypatch,
):
    executed = []

    def mock_company(state):
        executed.append(ResearchArea.COMPANY)
        return {
            "company_research": None,
            "research_errors": {},
        }

    def mock_financial(state):
        executed.append(ResearchArea.FINANCIAL)
        return {
            "financial_research": None,
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_fanout.company_research_graph.invoke",
        mock_company,
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.financial_research_graph.invoke",
        mock_financial,
    )

    plan = ResearchPlan(
        research_areas=[
            ResearchArea.FINANCIAL,
        ],
        rationale="Financial research is sufficient.",
    )

    research_fanout_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": plan,
        }
    )

    assert executed == [
        ResearchArea.FINANCIAL,
    ]
```

这里体现：

```text
ResearchPlan
     ↓
决定 fan-out 数量
     ↓
决定哪些 Agent 被启动
```

---

### 15. 测试三：Reducer 仍然有效

由于现在可能产生多个动态 `Send`，必须确认前一课的 Reducer 没有被破坏。

```python
def test_fanout_merges_research_errors(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.agents.research_fanout.company_research_graph.invoke",
        lambda state: {
            "company_research": None,
            "research_errors": {
                "company": "Company failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.market_research_graph.invoke",
        lambda state: {
            "market_research": None,
            "research_errors": {
                "market": "Market failed.",
            },
        },
    )

    plan = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.MARKET,
        ],
        rationale="Company and market research are required.",
    )

    result = research_fanout_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": plan,
        }
    )

    assert result["research_errors"] == {
        "company": "Company failed.",
        "market": "Market failed.",
    }
```

---

### 16. 一个关键理解：Fan-out 和 Router 的区别

现在系统中已经出现两个很容易混淆的概念。

#### Router

上一课：

```text
next_research_area
       ↓
Router
       ↓
Company Agent
```

Router 的问题是：

> **这一次应该去哪一个 Agent？**

它是：

```text
1 → 1
```

---

#### Fan-out

本课：

```text
ResearchPlan
    ↓
[Company, Financial, Market]
    ↓
Fan-out
    ├── Company
    ├── Financial
    └── Market
```

Fan-out 的问题是：

> **这一次应该同时启动哪些 Agent？**

它是：

```text
1 → N
```

这两个概念不能混为一谈。

---

### 17. 本课暂时不把 Planner 接进来

虽然真实架构最终应该是：

```text
User Query
    ↓
Planner
    ↓
ResearchPlan
    ↓
Dynamic Fan-out
    ↓
Research Agents
```

但 Lesson 6 先把：

```text
ResearchPlan
    ↓
Dynamic Fan-out
```

独立验证。

原因是教学上要把两个问题拆开：

#### Planner

```text
WHAT
```

#### Fan-out

```text
HOW MANY / WHICH IN PARALLEL
```

后面再组合。

---

### 18. Acceptance Criteria

Lesson 6 当前阶段完成标准：

* `Send` 能够根据 `ResearchPlan.research_areas` 动态创建并行任务
* 不再固定启动四个 Agent
* Planner 选择两个 Area，就只执行两个 Agent
* Planner 选择三个 Area，就只执行三个 Agent
* 每个动态任务只写自己的 Dedicated State Field
* `research_errors` Reducer 可以正确合并多个动态 Agent 的结果
* 不引入 Supervisor
* 不修改现有 Planner
* 不修改现有 Router
* 不接真实金融 API

最终概念模型：

```text
                ResearchPlan
                     │
                     │
              [A, B, C]
                     │
                     ▼
                 Fan-out
               /    |    \
              /     |     \
             ▼      ▼      ▼
            A       B       C
             \      |      /
              \     |     /
               \    |    /
                Shared State
```

这里的 **Fan-in 可以是隐式的**：如果这些动态分支全部直接结束 Graph，就不需要人为增加一个空节点；只有在并行分支之后存在实际的后续计算节点时，才需要显式汇合到那个节点。
