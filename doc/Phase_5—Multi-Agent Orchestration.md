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