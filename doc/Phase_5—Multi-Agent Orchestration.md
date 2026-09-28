# Phase 5 — Multi-Agent Orchestration

## Lesson 1 — Research Planner

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