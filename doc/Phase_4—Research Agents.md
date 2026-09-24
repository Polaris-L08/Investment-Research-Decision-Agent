# Phase 4 —— Research Agents

## Lesson 1: First Research Agent：Company Research Agent

### 1. 本课目标

这一课只建立一个最小但完整的 **Company Research Agent**。

我们要完成：

> **Ticker → Company Research Agent → Tools → Mock Providers → Structured Research Result**

例如：

```text
AAPL
 ↓
Company Research Agent
 ↓
get_company_info
get_stock_price
 ↓
MockCompanyInfoProvider
MockStockPriceProvider
 ↓
CompanyResearchResult
```

最终得到：

```python
CompanyResearchResult(
    ticker="AAPL",
    company_name="Apple Inc.",
    sector="Technology",
    current_price=200.0,
    summary="..."
)
```

---

### 2. 为什么现在做这个

Phase 3 解决的是：

> **Agent 如何调用 Tool？**

现在开始解决：

> **一个具有明确业务职责的 Agent，如何利用 Tool 完成一项完整的研究任务？**

这是一个非常重要的抽象变化。

Phase 3：

```text
LLM
 ↓
Tool Calling
 ↓
Tool
 ↓
Provider
```

Phase 4：

```text
Research Agent
 ↓
LLM
 ↓
Tool Calling
 ↓
Tool
 ↓
Provider
 ↓
Research Result
```

也就是说，**Tool Calling 不再是我们学习的终点，而变成 Research Agent 内部的执行机制。**

---

### 3. 本课暂时不做什么

这一点非常重要。

本课**不做**：

- Valuation
- Target Price
- Risk Analysis
- Investment Recommendation
- Supervisor
- Multi-Agent
- Parallel Research
- Research Planner
- Memory
- Checkpoint
- Human-in-the-loop

甚至不会修改你现有的主 Investment Decision Graph。

我们先建立一个干净的业务 Agent。

---

### 4. Agent 的业务边界

本课的 Agent 叫：

```text
Company Research Agent
```

它的职责只有：

1. 根据 ticker 获取公司信息
2. 获取当前股价
3. 形成基本公司研究结果

它**不负责**：

```text
"这家公司值多少钱？"
"应该买还是卖？"
"风险有多高？"
"目标价是多少？"
```

所以 Agent 的职责边界是：

```text
Company Research
    ├── Company Name
    ├── Sector
    ├── Current Price
    └── Basic Summary
```

---

### 5. Graph Topology

本课的外部 Graph 非常简单：

```text
START
  │
  ▼
company_research_agent
  │
  ▼
 END
```

但不要被这个 Graph 的简单程度误导。

`company_research_agent` 内部实际上会执行：

```text
             Company Research Agent
                       │
                       ▼
                      LLM
                       │
                Tool Calling
                       │
                       ▼
                   Tool Loop
                  /         \
                 ▼           ▼
      get_company_info   get_stock_price
                 │           │
                 ▼           ▼
       CompanyInfoProvider  StockPriceProvider
                 │           │
                 └─────┬─────┘
                       ▼
                Tool Results
                       │
                       ▼
              Structured Output LLM
                       │
                       ▼
             CompanyResearchResult
```

所以要理解一个非常关键的概念：

> **Agent Graph 和 Tool Loop Graph 是两个不同层级的 Graph。**

外层：

```text
Business Workflow
```

内层：

```text
Tool Execution Workflow
```

本课暂时不把它们强行合并。

---

### 6. State Design

这里第一次正式体现我们之前强调的：

> Input State / Internal State / Output State 分离。

#### Input State

用户真正需要提供的只有：

```python
class CompanyResearchInputState(TypedDict):
    ticker: str
```

例如：

```python
{
    "ticker": "AAPL"
}
```

---

#### Internal State

Agent 内部：

```python
class CompanyResearchState(TypedDict):
    ticker: str
    research_result: CompanyResearchResult | None
    research_error: str
```

这里：

```text
ticker
    ↓
research_result
```

同时保留：

```text
research_error
```

因为我们不允许 Agent 静默吞掉错误。

---

#### Output State

最终对外暴露：

```python
class CompanyResearchOutputState(TypedDict):
    research_result: CompanyResearchResult | None
    research_error: str
```

所以完整的数据边界：

```text
Input
  ↓
CompanyResearchState
  ↓
Output
```

---

### 7. Structured Result

我们新增：

```python
class CompanyResearchResult(BaseModel):
    ticker: str
    company_name: str
    sector: str
    current_price: float
    summary: str
```

它代表：

> **Company Research Agent 的业务结果**

注意这和 `Tool` 的返回值不是一回事。

Tool：

```python
{
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology",
}
```

另一个 Tool：

```python
{
    "ticker": "AAPL",
    "price": 200.0,
}
```

最终 Agent 将两个 Tool 的结果组合成：

```python
CompanyResearchResult(...)
```

这是 Phase 4 非常重要的一层：

```text
Tool Result
      ↓
Agent Research Result
```

---

### 8. 新增文件

按照当前项目的实际结构，我们现在只新增：

```text
app/
└── agents/
    ├── __init__.py
    └── company_research.py

tests/
└── test_company_research_agent.py
```

没有提前建立：

```text
supervisor/
research/
valuation/
risk/
decision/
```

避免过早架构化。

---

### 9. `app/agents/__init__.py`

完整内容：

```python
```

保持为空即可。

---

### 10. `app/agents/company_research.py`

完整内容如下：

```python
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.graph.graph import llm
from app.graph.tool_loop import build_tool_loop_graph


class CompanyResearchResult(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    company_name: str = Field(
        description="Legal or commonly used company name."
    )

    sector: str = Field(
        description="Primary business sector."
    )

    current_price: float = Field(
        description="Current stock price."
    )

    summary: str = Field(
        description="Concise factual company research summary."
    )


company_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Company Research Agent. "
            "Your responsibility is to research basic company information "
            "for the given stock ticker. "
            "Use the available tools to obtain company name, sector, and "
            "current stock price. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent financial data.",
        ),
        (
            "human",
            "Research the following company and return a concise company "
            "research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


structured_company_research_llm = llm.with_structured_output(
    CompanyResearchResult
)


class CompanyResearchInputState(TypedDict):
    ticker: str


class CompanyResearchState(TypedDict):
    ticker: str
    research_result: CompanyResearchResult | None
    research_error: str


class CompanyResearchOutputState(TypedDict):
    research_result: CompanyResearchResult | None
    research_error: str


def company_research_agent(
    state: CompanyResearchState,
) -> CompanyResearchState:
    ticker = state["ticker"]

    prompt_value = company_research_prompt.invoke(
        {
            "ticker": ticker,
        }
    )

    try:
        tool_loop = build_tool_loop_graph()

        tool_result = tool_loop.invoke(
            {
                "messages": [
                    *prompt_value.messages
                ]
            }
        )

        research_context = "\n".join(
            message.content
            for message in tool_result["messages"]
            if message.type == "tool"
        )

        structured_result = structured_company_research_llm.invoke(
            [
                *prompt_value.messages,
                HumanMessage(
                    content=(
                        "Tool results:\n"
                        f"{research_context}\n\n"
                        "Using only these tool results, produce the "
                        "structured company research result."
                    )
                ),
            ]
        )

    except Exception as exc:
        return {
            "research_result": None,
            "research_error": str(exc),
        }

    return {
        "research_result": structured_result,
        "research_error": "",
    }


def build_company_research_graph():
    builder = StateGraph(
        CompanyResearchState,
        input_schema=CompanyResearchInputState,
        output_schema=CompanyResearchOutputState,
    )

    builder.add_node(
        "company_research_agent",
        company_research_agent,
    )

    builder.add_edge(
        START,
        "company_research_agent",
    )

    builder.add_edge(
        "company_research_agent",
        END,
    )

    return builder.compile()
```

---

### 11. 这里最重要的代码

真正值得理解的是这一段：

```python
tool_loop = build_tool_loop_graph()
```

我们没有重新实现 Phase 3 的 Tool Calling。

这是有意的。

Phase 3 已经解决：

```text
LLM
 ↓
Tool Calling
 ↓
ToolNode
 ↓
Tool
 ↓
Provider
```

所以 Phase 4 应该**复用**这个能力。

---

然后：

```python
tool_result = tool_loop.invoke(
    {
        "messages": [
            *prompt_value.messages
        ]
    }
)
```

Agent 给 Tool Loop 一个明确的业务任务。

Tool Loop 自己负责：

```text
LLM
 ↓
Tool Calls
 ↓
Tools
 ↓
Tool Results
 ↓
LLM
```

---

最后：

```python
structured_result = structured_company_research_llm.invoke(...)
```

这里完成的是：

```text
Tool Results
      ↓
Research Result
```

这就是 Agent 层的核心价值。

---

### 12. 为什么还需要第二次 LLM？

这是本课一个非常重要的问题。

第一阶段：

```text
LLM #1
```

负责：

> **决定需要调用哪些 Tools。**

第二阶段：

```text
LLM #2
```

负责：

> **把 Tool Results 整理成业务层 Structured Result。**

因此：

```text
LLM #1
  ↓
Tool Selection / Tool Execution
  ↓
Raw Tool Results
  ↓
LLM #2
  ↓
CompanyResearchResult
```

这里并不是“为了多调用一次 LLM”。

而是两个不同职责：

| LLM | 职责 |
|---|---|
| Tool Loop LLM | Research execution |
| Structured LLM | Research result synthesis |

后续我们会继续优化这个模式，但 Lesson 1 不提前做复杂化。

---

### 13. Test

新增：

`tests/test_company_research_agent.py`

完整内容：

```python
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, ToolMessage

from app.agents.company_research import (
    CompanyResearchResult,
    build_company_research_graph,
    company_research_agent,
)


def test_company_research_result_model():
    result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    assert result.ticker == "AAPL"
    assert result.company_name == "Apple Inc."
    assert result.sector == "Technology"
    assert result.current_price == 200.0


def test_company_research_agent_uses_tool_results():
    tool_loop_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_company_info",
                        "args": {"ticker": "AAPL"},
                        "id": "call_company",
                        "type": "tool_call",
                    },
                    {
                        "name": "get_stock_price",
                        "args": {"ticker": "AAPL"},
                        "id": "call_price",
                        "type": "tool_call",
                    },
                ],
            ),
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"company_name": "Apple Inc.", '
                    '"sector": "Technology"}'
                ),
                tool_call_id="call_company",
            ),
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"price": 200.0}'
                ),
                tool_call_id="call_price",
            ),
            AIMessage(
                content="Apple Inc. is a technology company."
            ),
        ]
    }

    fake_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = tool_loop_result

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_result

    with (
        patch(
            "app.agents.company_research.build_tool_loop_graph",
            return_value=fake_tool_loop,
        ),
        patch(
            "app.agents.company_research.structured_company_research_llm",
            fake_structured_llm,
        ),
    ):
        result = company_research_agent(
            {
                "ticker": "AAPL",
                "research_result": None,
                "research_error": "",
            }
        )

    assert result["research_result"] == fake_result
    assert result["research_error"] == ""

    fake_tool_loop.invoke.assert_called_once()
    fake_structured_llm.invoke.assert_called_once()


def test_company_research_graph_topology_is_single_business_agent():
    graph = build_company_research_graph()

    node_names = set(
        graph.get_graph().nodes
    )

    assert "company_research_agent" in node_names
    assert "__start__" in node_names
    assert "__end__" in node_names

    assert node_names == {
        "__start__",
        "company_research_agent",
        "__end__",
    }
```

---

### 14. 测试策略

这里特意没有测试真实 LLM。

因为 Lesson 1 的重点不是：

> OpenAI API 能不能返回结果。

而是：

> Company Research Agent 是否正确编排 Tool Loop，并将 Tool Result 转换为 `CompanyResearchResult`。

因此：

```text
LLM
→ Mock

Tool Loop
→ Mock

Structured Output
→ Mock
```

这是我们一直保持的：

> **Real LLM + Mock Tools + Mock Providers**

与当前 Lesson 1 的单元测试职责并不冲突。

---

### 15. 我已经对当前实现做了基础检查

基于你上传的源码，我已经实际把 Lesson 1 的代码加入到一个工作副本中，并进行了 Python 语法编译检查：

```text
py_compile: PASS
```

我没有执行你明确说不需要的全量旧测试。

当前运行环境没有你项目虚拟环境中的 `langchain_core` 依赖，因此这里不能假装执行成功的 pytest。你的本地项目环境应直接使用项目已有 `.venv` 执行下面的命令。

---

### 16. Acceptance Criteria

Lesson 1 完成的标准不是“文件存在”，而是下面这些条件全部成立。

#### A. Agent 有明确业务职责

存在：

```python
company_research_agent
```

并且职责限定为：

```text
Company Name
Sector
Current Price
Basic Summary
```

---

#### B. Agent 使用 Phase 3 Tool Loop

不能重新实现：

```text
Tool Calling
ToolNode
Tool Routing
```

而是：

```python
build_tool_loop_graph()
```

复用 Phase 3 能力。

---

#### C. Tool 结果进入 Agent

Agent 能取得：

```text
get_company_info
get_stock_price
```

产生的 Tool Results。

---

#### D. Tool Results 转换为 Structured Result

最终形成：

```python
CompanyResearchResult
```

而不是返回普通字符串。

---

#### E. Graph Topology 正确

必须是：

```text
START
  ↓
company_research_agent
  ↓
END
```

---

#### F. 错误显式存在

Agent 失败时：

```python
{
    "research_result": None,
    "research_error": "..."
}
```

而不是：

```python
except Exception:
    pass
```

---

### 17. 本课真正需要掌握的三个概念

#### 第一：Agent ≠ Tool Loop

这是 Phase 4 最重要的认知。

```text
Agent
=
Business Responsibility
```

而：

```text
Tool Loop
=
Execution Mechanism
```

所以：

```text
Company Research Agent
        │
        ▼
   Tool Calling Loop
```

是合理的分层。

---

#### 第二：Tool Result ≠ Research Result

Tool 只是提供局部事实：

```text
CompanyInfo
StockPrice
```

Agent 才负责把这些事实组合成：

```text
CompanyResearchResult
```

因此：

```text
Provider
   ↓
Tool
   ↓
Tool Result
   ↓
Research Agent
   ↓
Research Result
```

这是我们整个项目从“Tool Calling Demo”走向“Research Agent”的关键一步。

---

#### 第三：业务边界必须先于能力扩张

现在：

```text
Company Research Agent
```

只做：

```text
公司基本信息
当前价格
基本摘要
```

下一阶段我们才逐渐增加：

```text
Financial Research
Market Research
Industry Research
Valuation
Risk
Decision
```

而不是第一步就造一个：

```text
UltimateInvestmentAgent
```

---

### 18. Phase 4 当前架构变化

Lesson 1 完成后，项目概念架构变成：

```text
Application
    ↓
Graph
    ↓
Research Agent
    ↓
LLM
    ↓
Tool
    ↓
Provider
```

具体到当前 Lesson：

```text
Company Research Agent
        │
        ├── get_company_info
        │       ↓
        │   CompanyInfoProvider
        │
        └── get_stock_price
                ↓
           StockPriceProvider
```

然后：

```text
Tool Results
      ↓
CompanyResearchResult
```

---