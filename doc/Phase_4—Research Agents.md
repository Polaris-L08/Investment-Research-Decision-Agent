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


## Lesson 2: Graph Composition：让 Research Agent 正式组合 Tool Loop

这一课我们不再增加业务能力，而是把 Lesson 1 的结构进一步规范化：**Research Agent 负责业务职责，Tool Loop 负责工具执行，两者通过明确的 State 边界连接。**

### 本课目标

完成后，结构应当是：

```text
Company Research Graph
        │
        ▼
company_research_agent
        │
        ▼
   Tool Loop Graph
        │
        ├── LLM
        ├── ToolNode
        └── LLM ...
        │
        ▼
   Tool Results
        │
        ▼
CompanyResearchResult
```

核心认知：

> **Agent 不应该重新实现 Tool Calling；Graph 也不应该把所有 State 混在一起。**

---

### 1. 先明确本课的 State 边界

Company Research 层：

```python
class CompanyResearchState(TypedDict):
    ticker: str
    research_result: CompanyResearchResult | None
    research_error: str
```

Tool Loop 层：

```python
class ToolLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

两者之间只有一个明确的转换：

```text
CompanyResearchState
        │
        │ ticker + prompt
        ▼
ToolLoopState
        │
        ▼
Tool Loop
        │
        ▼
ToolLoop Result
        │
        ▼
CompanyResearchState
```

这就是我们本课要建立的 **State Boundary**。

---

### 2. Graph Topology

外层：

```text
START
  │
  ▼
company_research_agent
  │
  ▼
 END
```

Node 内部：

```text
company_research_agent
        │
        ▼
   Tool Loop Graph
        │
        ▼
      Result
        │
        ▼
Structured Output
        │
        ▼
CompanyResearchResult
```

因此不要把它理解成：

```text
Company Research Graph
    =
Tool Loop Graph
```

而是：

```text
Company Research Graph
    └── company_research_agent Node
             └── Tool Loop Graph
```

---

### 3. 先重构 Tool Loop

我们不再让 Agent 每次执行时：

```python
build_tool_loop_graph()
```

而是：

```text
build
  ↓
compile
  ↓
reuse
```

这是一个很自然的重构。

#### `app/graph/tool_loop.py`

把 Tool Loop 的 Graph 构建改成模块级 compiled graph。

核心结构：

```python
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.graph.graph import llm
from app.tools.registry import TOOLS


class ToolLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm_with_tools = llm.bind_tools(TOOLS)

tool_node = ToolNode(TOOLS)


def tool_loop_llm_node(state: ToolLoopState):
    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }


def route_after_llm(state: ToolLoopState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


builder = StateGraph(ToolLoopState)

builder.add_node(
    "llm",
    tool_loop_llm_node,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_edge(
    START,
    "llm",
)

builder.add_conditional_edges(
    "llm",
    route_after_llm,
    {
        "tools": "tools",
        "end": END,
    },
)

builder.add_edge(
    "tools",
    "llm",
)

tool_loop_graph = builder.compile()
```

这里最重要的变化只有：

```python
tool_loop_graph = builder.compile()
```

而不是：

```python
def build_tool_loop_graph():
    ...
```

然后每次调用。

---

### 4. 为什么这次重构是合理的？

Graph 的构建属于：

> **Configuration / Composition**

Graph 的 `invoke()` 属于：

> **Execution**

因此应该：

```text
Application startup
      ↓
Build Graph
      ↓
Compile Graph
      ↓
Repeated Invocation
```

而不是：

```text
Every invocation
      ↓
Build Graph
      ↓
Compile Graph
      ↓
Invoke
```

这也是后面我们构建：

```text
Research Agent Graph
Financial Agent Graph
Risk Agent Graph
Decision Graph
```

时非常重要的习惯。

---

### 5. 修改 Company Research Agent

现在：

```python
from app.graph.tool_loop import tool_loop_graph
```

然后：

```python
tool_result = tool_loop_graph.invoke(
    {
        "messages": prompt_value.messages
    }
)
```

所以 Agent 的职责变得非常清楚：

```text
Agent
 ├── 创建业务 Prompt
 ├── 调用 Tool Loop
 ├── 提取 Tool Result
 └── 生成 Research Result
```

而：

```text
Tool Loop
 ├── LLM
 ├── 判断 Tool Call
 ├── ToolNode
 └── 循环
```

完全由 Tool Loop 自己负责。

---

### 6. 一个重要的边界

Agent 不应该出现：

```python
llm_with_tools = llm.bind_tools(...)
```

也不应该出现：

```python
ToolNode(...)
```

更不应该出现：

```python
if last_message.tool_calls:
    ...
```

这些都属于：

> **Tool Execution Layer**

所以未来如果我们把 Tool Loop 换成另外一种执行机制：

```text
Agent
   ↓
Tool Execution Layer
```

Agent 本身不应该受到影响。

---

### 7. Company Research Agent 的完整逻辑

现在可以把它抽象成：

```python
def company_research_agent(state):
    ticker = state["ticker"]

    prompt = build_research_prompt(ticker)

    tool_result = tool_loop_graph.invoke(
        {
            "messages": prompt
        }
    )

    research_context = extract_tool_results(
        tool_result
    )

    result = structured_llm.invoke(
        build_structured_prompt(
            ticker,
            research_context,
        )
    )

    return {
        "research_result": result,
        "research_error": "",
    }
```

这里已经开始出现一个非常重要的架构趋势：

```text
Business Logic
      ↓
Execution Logic
```

逐渐分离。

---

### 8. 测试应该怎么改？

这一次我们**不重复测试 Tool Loop 内部的所有行为**。

因为 Phase 3 已经完成了：

```text
Tool Calling
ToolNode
Routing
Retry
Multiple Tools
Tool Loop
```

Lesson 2 只验证 Composition Boundary。

#### Test 1：Tool Loop 是 compiled graph

验证：

```python
tool_loop_graph is not None
```

---

#### Test 2：Agent 调用了 Tool Loop

Mock：

```python
with patch(
    "app.agents.company_research.tool_loop_graph"
) as mock_tool_loop:
```

然后：

```python
mock_tool_loop.invoke.assert_called_once()
```

---

#### Test 3：State Boundary

检查：

```python
call_args = mock_tool_loop.invoke.call_args

tool_loop_input = call_args.args[0]

assert "messages" in tool_loop_input
assert "ticker" not in tool_loop_input
assert "research_result" not in tool_loop_input
```

这条测试非常有价值。

因为它不是在测试“代码有没有运行”。

它是在测试：

> **业务 State 没有泄漏进 Tool Loop State。**

---

### 9. Lesson 2 的完整验收标准

测试通过后，我们应该能够画出：

```text
                  Application
                       │
                       ▼
             Company Research Graph
                       │
                       ▼
          company_research_agent
                       │
                       ▼
                Tool Loop Graph
                  │         │
                  ▼         ▼
                 LLM      ToolNode
                             │
                             ▼
                          Tools
                             │
                             ▼
                         Providers
```

并且每一层都有自己的职责。

| Layer                  | Responsibility            |
| ---------------------- | ------------------------- |
| Company Research Agent | 公司研究业务职责                  |
| Tool Loop              | Tool Calling 执行           |
| Tool                   | Capability Boundary       |
| Provider               | Data Source               |
| Structured LLM         | Research Result synthesis |
| Graph                  | Workflow composition      |

---

### 10. 关于真正的 Subgraph

这里我要特别把 Lesson 2 的目标说清楚。

我们现在做的是：

```text
Node
  ↓
compiled Graph.invoke()
```

也就是：

> **Graph inside Node**

它已经是 Graph Composition 的一种形式。

但 LangGraph 更进一步的能力是：

```text
Parent Graph
      │
      ▼
Subgraph Node
```

也就是把一个 compiled graph **直接作为另一个 Graph 的 node/subgraph**。

这个我们不会现在为了“炫技”马上塞进 Company Research Agent。

因为下一步真正需要它的地方是：

```text
Research Pipeline
    │
    ├── Company Research Agent
    ├── Financial Research Agent
    ├── Market Research Agent
    └── Industry Research Agent
```

届时 Subgraph 的 State Mapping、Graph Composition、并行执行才会真正产生价值。

---

### 11. 现在还不要动 `graph.py`

你刚才说：

> `graph.py` 未来一定要重构。

我完全同意。

但我们现在不做一次性的“大爆炸重构”。

原因是 Phase 4 正好会暴露出 `graph.py` 中哪些东西应该属于：

```text
LLM
Prompt
Agent
Graph
State
Routing
```

等 Lesson 3/4 再逐渐明确这些边界后，重构才有实际依据。

最终目标不是：

> “把旧 graph.py 改得更漂亮。”

而是：

> **让 Graph 层只负责 Graph Composition。**

也就是说最终我们希望逐渐接近：

```text
app/
├── agents/
│   ├── company_research.py
│   ├── financial_research.py
│   └── ...
│
├── graph/
│   ├── graph.py
│   ├── tool_loop.py
│   └── state.py
│
├── tools/
├── providers/
└── ...
```

而不是继续把所有业务逻辑堆进 `graph.py`。

---

### 12. Lesson 2 的学习重点

这一课你真正需要掌握的是四句话：

#### ① Graph 可以调用 Graph

```text
Graph
  ↓
Node
  ↓
Graph
```

---

#### ② Graph 的 State 不需要相同

```text
CompanyResearchState
        ↓
      Adapter
        ↓
ToolLoopState
```

---

#### ③ Agent 不应该知道 Tool Loop 的内部实现

Agent 只知道：

```text
“我需要研究公司”
        ↓
“调用 Tool Execution”
```

而不知道：

```text
ToolNode
conditional_edges
tool_calls
```

---

#### ④ Graph 是可以组合的

这会成为后面整个项目架构的基础：

```text
Investment Research Graph
       │
       ├── Research Graph
       │      ├── Company Agent
       │      ├── Financial Agent
       │      └── Market Agent
       │
       ├── Valuation Graph
       │
       ├── Risk Graph
       │
       └── Decision Graph
```

---

### 13. Lesson 2 的最终Graph

```angular2html
┌──────────────────────────────────────────────┐
│ Company Research Graph                       │
│                                              │
│  START                                       │
│    │                                         │
│    ▼                                         │
│  company_research_agent                      │
│    │                                         │
│    │  CompanyResearchState                   │
│    │                                         │
│    └──────────────┐                          │
│                   ▼                          │
│          ┌─────────────────┐                 │
│          │ tool_loop_graph │                 │
│          │                 │                 │
│          │ ToolLoopState   │                 │
│          │                 │                 │
│          │      LLM        │                 │
│          │       │         │                 │
│          │       ▼         │                 │
│          │   ToolNode      │                 │
│          │       │         │                 │
│          │       ▼         │                 │
│          │      LLM        │                 │
│          └───────┬─────────┘                 │
│                  │                           │
│                  ▼                           │
│          Tool Results                        │
│                  │                           │
│                  ▼                           │
│          Structured LLM                      │
│                  │                           │
│                  ▼                           │
│        CompanyResearchResult                 │
│                  │                           │
│                  ▼                           │
│                 END                          │
└──────────────────────────────────────────────┘
```


## Lesson 3: Research Agent 正式进入 Parent Graph

### 1. 本课目标

前两课我们已经有：

```text
Company Research Graph
        │
        ▼
company_research_agent
        │
        ▼
tool_loop_graph
```

但是它目前还是一个**孤立的 Research Agent**。

而整个 Investment Research Agent 的主 Graph 还不知道它的存在。

本课开始把它接入真正的上层 Workflow：

```text
Investment Research Graph
        │
        ▼
Company Research Agent
        │
        ▼
Tool Loop
        │
        ▼
CompanyResearchResult
        │
        ▼
Parent Graph State
```

也就是说，本课解决一个非常重要的问题：

> **一个独立 Research Agent 产生的结果，如何成为上层 LangGraph 的正式 State？**

---

### 2. 为什么现在做这个

现在有两个 Graph：

#### Company Research Graph

```text
START
  ↓
company_research_agent
  ↓
END
```

#### Investment Research Graph

你 Phase 3 已经有：

```text
START
  ↓
initialize_state
  ↓
llm_node
  ↓
create_research_plan
  ↓
investment_decision_node
  ↓
prepare_output
  ↓
END
```

现在它们是两套互相独立的 Graph。

这不符合最终目标。

最终应该是：

```text
Investment Research Graph
        │
        ▼
Company Research
        │
        ▼
Financial Research
        │
        ▼
Market Research
        │
        ▼
Industry Research
        │
        ▼
Valuation
        │
        ▼
Risk
        │
        ▼
Decision
```

所以 Lesson 3 是第一次真正建立：

> **Agent Graph → Parent Graph**

---

### 3. 本课最重要的新概念：State Ownership

现在有两个 State：

```text
CompanyResearchState
```

和：

```text
GraphState
```

我们不能简单粗暴地把所有字段塞进一起。

Company Research Agent 自己拥有：

```text
ticker
research_result
research_error
```

Parent Graph 则拥有：

```text
ticker
company_research
financial_research
...
```

所以我们需要一个明确的转换：

```text
CompanyResearchResult
        │
        ▼
Parent Graph State
```

---

### 4. 这里顺便解决一个之前留下的问题

你现在 Phase 3 的 `GraphState` 有：

```python
company_research: str
```

但 Phase 4 的 Agent 已经产生：

```python
CompanyResearchResult
```

这两个类型实际上已经不匹配。

继续使用：

```python
company_research: str
```

会导致 Agent 结果被压扁成字符串。

这不是我们想要的架构。

所以本课第一次正式修改 Parent State。

---

### 5. State Design

我们新增：

```python
company_research_result: CompanyResearchResult | None
```

因此：

```text
GraphState
│
├── ticker
├── research_plan
│
├── company_research_result
├── financial_research
├── market_research
├── industry_research
│
├── valuation_summary
├── current_price
│
└── ...
```

这里：

```python
company_research: str
```

暂时保留。

为什么？

因为你的 Phase 3 State 还有旧的 research pipeline 字段，而我们现在不应该为了一个 Agent 就一次性把整个 `GraphState` 清空重构。

所以本课采用：

```text
旧 State
 +
新 Agent State
```

的渐进式演进。

后面等 Research Agents 全部建立之后，再统一重构 `GraphState`。

这也正好符合你刚才强调的：

> 前面的代码可以修改，不需要为了保留 Phase 1/2/3 的代码而冻结架构。

---

### 6. Graph Topology

本课的 Parent Graph：

```text
START
  │
  ▼
initialize_state
  │
  ▼
company_research
  │
  ▼
create_research_plan
  │
  ▼
investment_decision_node
  │
  ▼
prepare_output
  │
  ▼
END
```

其中：

```text
company_research
```

内部：

```text
Company Research Graph
        │
        ▼
Company Research Agent
        │
        ▼
Tool Loop Graph
        │
        ▼
CompanyResearchResult
```

因此完整拓扑：

```text
Investment Research Graph
│
├── initialize_state
│
├── company_research
│       │
│       └── Company Research Graph
│               │
│               └── Tool Loop Graph
│
├── create_research_plan
│
├── investment_decision_node
│
└── prepare_output
```

---

### 7. 这一次是真正的 Graph Composition

前面 Lesson 1/2 是：

```python
tool_loop_graph.invoke(...)
```

属于：

```text
Node
 ↓
Graph.invoke()
```

现在 Parent Graph：

```text
Parent Graph
    ↓
company_research node
    ↓
Company Research Graph
```

我们开始形成：

```text
Graph
 └── Agent Graph
       └── Tool Loop Graph
```

这才真正进入**分层 Graph Composition**。

---

### 8. 修改文件一：`app/graph/state.py`

这是基于：

> Phase 3 源码 + Lesson 1 + Lesson 2

继续修改。

完整内容建议改成：

```python
from typing import TypedDict

from app.graph.models import (
    ResearchSummary,
    Recommendation,
    InvestmentHorizon,
    InvestmentDecision,
)
from app.agents.company_research import CompanyResearchResult


class InputState(TypedDict):
    user_query: str
    ticker: str


class GraphState(TypedDict):
    # User request
    user_query: str
    ticker: str

    # Research planning
    research_plan: list[str]

    # Research results
    company_research: str
    company_research_result: CompanyResearchResult | None
    financial_research: str
    market_research: str
    industry_research: str

    # Valuation
    valuation_summary: str
    current_price: float | None
    target_price: float
    investment_thesis: str

    # Risk analysis
    risk_factors: list[str]

    # Investment decision
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    investment_thesis: str

    llm_response: str
    research_summary: ResearchSummary
    investment_decision: InvestmentDecision

    llm_error: str
    failure_reason: str
    retry_count: int

    tool_error: str | None
    tool_retry_count: int
    tool_retryable: bool


class OutputState(TypedDict):
    ticker: str
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    current_price: float
    target_price: float
    investment_thesis: str
    failure_reason: str
```

---

### 9. 为什么是 `company_research_result`

而不是直接修改成：

```python
company_research: CompanyResearchResult
```

因为当前 Phase 3 的：

```python
company_research: str
```

还有历史语义。

我们现在不急着覆盖它。

于是暂时：

```text
company_research
        ↓
旧字段

company_research_result
        ↓
Phase 4 新字段
```

这实际上是一个非常典型的**渐进式架构迁移**。

后面我们会逐步淘汰旧字段。

---

### 10. 修改文件二：`app/graph/graph.py`

这是本课最关键的修改。

我们首先增加：

```python
from app.agents.company_research import (
    CompanyResearchResult,
    build_company_research_graph,
)
```

然后创建：

```python
company_research_graph = build_company_research_graph()
```

---

#### 新增 Parent Graph Node

增加：

```python
def company_research_node(
    state: GraphState,
) -> GraphState:
    result = company_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    if result["research_error"]:
        return {
            "company_research_result": None,
            "failure_reason": (
                "Company research failed: "
                f"{result['research_error']}"
            ),
        }

    return {
        "company_research_result": result["research_result"],
        "failure_reason": "",
    }
```

这就是我们的 State Adapter。

---

### 11. 为什么不能直接：

```python
company_research_graph.invoke(state)
```

因为 Parent State 是：

```text
GraphState
```

而 Company Research Graph 的 Input State 是：

```text
CompanyResearchInputState
```

后者只有：

```python
{
    "ticker": str
}
```

所以 Parent Graph 只应该向它提供：

```python
{
    "ticker": state["ticker"]
}
```

而不是：

```python
state
```

否则：

```text
Parent Graph State
```

会泄漏到：

```text
Company Research Graph
```

这就是我们之前 Lesson 2 学到的 State Boundary。

---

### 12. `initialize_state()` 必须修改

这是我们之前反复强调的一个原则：

> **每一个新增的 GraphState 字段，都必须检查 `initialize_state()`。**

所以增加：

```python
"company_research_result": None,
```

最终：

```python
def initialize_state(state: InputState) -> GraphState:
    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],

        "research_plan": [],

        "company_research": "",
        "company_research_result": None,
        "financial_research": "",
        "market_research": "",
        "industry_research": "",

        "valuation_summary": "",
        "current_price": None,
        "target_price": 0.0,
        "risk_factors": [],

        "recommendation": Recommendation.HOLD,
        "investment_horizon": InvestmentHorizon.LONG_TERM,
        "investment_thesis": "",

        "llm_response": "",
        "research_summary": ResearchSummary(
            summary="",
            key_factors=[],
        ),
        "investment_decision": InvestmentDecision(
            recommendation=Recommendation.HOLD,
            investment_horizon=InvestmentHorizon.LONG_TERM,
            investment_thesis="",
        ),

        "llm_error": "",
        "failure_reason": "",
        "retry_count": 0,

        "tool_error": None,
        "tool_retry_count": 0,
        "tool_retryable": False,
    }
```

---

### 13. 修改 Graph Topology

现在原来：

```python
builder.add_edge(
    "initialize_state",
    "llm_node",
)
```

Lesson 3 改成：

```python
builder.add_edge(
    "initialize_state",
    "company_research",
)
```

然后：

```python
builder.add_edge(
    "company_research",
    "llm_node",
)
```

于是：

```text
START
  ↓
initialize_state
  ↓
company_research
  ↓
llm_node
```

---

### 14. 为什么暂时放在 `llm_node` 前面？

这是一个非常重要的教学决定。

Phase 3 的：

```text
llm_node
```

目前实际上承担的是：

```text
初步 Research Summary
```

而 Phase 4 的：

```text
company_research
```

已经开始产生真实的 Company Research Result。

所以先形成：

```text
Company Research
      ↓
Legacy Research Summary
```

下一步我们会逐渐把：

```text
Legacy Research Summary
```

替换掉。

这是一种**渐进式迁移**，而不是一次性重写整个系统。

---

### 15. 完整的 Graph 构建部分

因此 `graph.py` 后半部分应变成：

```python
company_research_graph = build_company_research_graph()


builder = StateGraph(
    GraphState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node(
    "initialize_state",
    initialize_state,
)

builder.add_node(
    "company_research",
    company_research_node,
)

builder.add_node(
    "llm_node",
    llm_node,
)

builder.add_node(
    "retry_llm",
    retry_llm,
)

builder.add_node(
    "handle_llm_failure",
    handle_llm_failure,
)

builder.add_node(
    "get_stock_price",
    get_stock_price_node,
)

builder.add_node(
    "create_research_plan",
    create_research_plan,
)

builder.add_node(
    "investment_decision_node",
    investment_decision_node,
)

builder.add_node(
    "prepare_output",
    prepare_output,
)

builder.add_node(
    "prepare_failure_output",
    prepare_failure_output,
)

builder.add_edge(
    START,
    "initialize_state",
)

builder.add_edge(
    "initialize_state",
    "company_research",
)

builder.add_edge(
    "company_research",
    "llm_node",
)

builder.add_conditional_edges(
    "llm_node",
    route_after_llm,
    {
        "continue": "create_research_plan",
        "retry": "retry_llm",
        "llm_failure": "handle_llm_failure",
    },
)

builder.add_conditional_edges(
    "investment_decision_node",
    route_after_decision,
    {
        "continue": "prepare_output",
        "llm_failure": "handle_llm_failure",
    },
)

builder.add_edge(
    "retry_llm",
    "llm_node",
)

builder.add_edge(
    "create_research_plan",
    "investment_decision_node",
)

builder.add_edge(
    "handle_llm_failure",
    "prepare_failure_output",
)

builder.add_edge(
    "prepare_output",
    END,
)

builder.add_edge(
    "prepare_failure_output",
    END,
)

graph = builder.compile()
```

注意：这只是 `graph.py` 的**修改部分**；你现有的 Phase 3 `llm_node`、retry、decision 等代码继续保留。

---

### 16. 新增 Test：Agent → Parent State

新建：

```text
tests/test_company_research_parent_graph.py
```

完整测试：

```python
from unittest.mock import MagicMock, patch

from app.agents.company_research import CompanyResearchResult
from app.graph.graph import graph


def test_company_research_result_is_written_to_parent_graph_state():
    fake_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": fake_result,
        "research_error": "",
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        result = graph.invoke(
            {
                "user_query": "Analyze Apple",
                "ticker": "AAPL",
            }
        )

    fake_company_research_graph.invoke.assert_called_once_with(
        {
            "ticker": "AAPL",
        }
    )

    assert result["company_research_result"] == fake_result


def test_company_research_failure_is_written_to_parent_failure_state():
    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": None,
        "research_error": "Tool execution failed",
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        result = graph.invoke(
            {
                "user_query": "Analyze Apple",
                "ticker": "AAPL",
            }
        )

    assert result["company_research_result"] is None

    assert (
        result["failure_reason"]
        == "Company research failed: Tool execution failed"
    )
```

---

### 17. 但是这里有一个测试设计问题

上面这个测试会继续执行：

```text
company_research
    ↓
llm_node
    ↓
...
```

所以如果我们只想测试：

```text
Company Research
    ↓
Parent State
```

其实不应该依赖后面的整个旧 Pipeline。

因此 Lesson 3 更合理的做法是：

> **直接测试 `company_research_node()`，而不是调用完整的 `graph`。**

所以我建议最终测试采用下面这个版本。

---

### 18. 推荐的 Lesson 3 测试

`tests/test_company_research_parent_graph.py`

完整版本：

```python
from unittest.mock import MagicMock, patch

from app.agents.company_research import CompanyResearchResult
from app.graph.graph import company_research_node


def test_company_research_node_maps_agent_result_to_parent_state():
    fake_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": fake_result,
        "research_error": "",
    }

    state = {
        "ticker": "AAPL",
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        result = company_research_node(state)

    fake_company_research_graph.invoke.assert_called_once_with(
        {
            "ticker": "AAPL",
        }
    )

    assert result["company_research_result"] == fake_result
    assert result["failure_reason"] == ""


def test_company_research_node_maps_agent_failure():
    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": None,
        "research_error": "Tool execution failed",
    }

    state = {
        "ticker": "AAPL",
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        result = company_research_node(state)

    assert result["company_research_result"] is None

    assert (
        result["failure_reason"]
        == "Company research failed: Tool execution failed"
    )


def test_company_research_node_only_passes_required_input_state():
    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": None,
        "research_error": "",
    }

    state = {
        "ticker": "AAPL",
        "user_query": "Analyze Apple",
        "research_plan": [],
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        company_research_node(state)

    fake_company_research_graph.invoke.assert_called_once_with(
        {
            "ticker": "AAPL",
        }
    )
```

这个测试组真正测试的是：

```text
Parent State
    ↓
State Adapter
    ↓
Company Research Graph
    ↓
Agent Result
    ↓
Parent State
```

---

### 19. 这里出现了一个非常重要的 LangGraph 模式

我们现在有：

```python
def company_research_node(state):
```

实际上它是一个：

> **Graph Adapter Node**

职责不是研究公司。

职责是：

```text
Parent Graph State
        ↓
Input Mapping
        ↓
Company Research Graph
        ↓
Output Mapping
        ↓
Parent Graph State
```

因此它是一个非常重要的架构边界。

---

### 20. 现在的完整 Graph Topology

Lesson 3 后：

```text
                         Investment Research Graph
                                  │
                                  ▼
                           initialize_state
                                  │
                                  ▼
                         company_research
                         Adapter Node
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ Company Research Graph │
                    │                         │
                    │ company_research_agent  │
                    │          │              │
                    │          ▼              │
                    │    tool_loop_graph      │
                    │          │              │
                    │          ▼              │
                    │ CompanyResearchResult   │
                    └──────────┬──────────────┘
                               │
                               ▼
                    company_research_result
                               │
                               ▼
                           llm_node
                               │
                               ▼
                     create_research_plan
                               │
                               ▼
                    investment_decision_node
                               │
                               ▼
                         prepare_output
                               │
                               ▼
                              END
```

这已经是我们整个项目第一次出现：

```text
Application Graph
    ↓
Agent Graph
    ↓
Tool Loop Graph
```

三级 Graph 层次。

---

### 21. 但是本课故意不做一件事

你可能会发现：

```python
company_research_result
```

进入 Parent State 之后：

```text
create_research_plan
investment_decision_node
```

还没有真正使用它。

这是**故意的**。

如果我们现在立刻修改 Decision Agent：

```text
CompanyResearchResult
    ↓
Investment Decision
```

那么 Lesson 3 会同时变成：

```text
Graph Composition
+
State Integration
+
Decision Refactoring
+
Prompt Refactoring
```

教学跨度太大。

本课只建立：

> **Agent Result → Parent State**

下一课再让上层 Research Workflow 真正消费这个结果。

---

### 22. Lesson 3 的 Acceptance Criteria

测试通过后，应该满足：

#### ① Company Research Graph 可以独立运行

```text
Company Research Graph
```

仍然可以独立工作。

---

#### ② Parent Graph 可以调用它

```text
Investment Research Graph
        ↓
company_research
        ↓
Company Research Graph
```

---

#### ③ State 不泄漏

Parent 只传：

```python
{
    "ticker": "AAPL"
}
```

而不是整个：

```python
GraphState
```

---

#### ④ Agent Result 成为 Parent State

最终：

```python
state["company_research_result"]
```

得到：

```python
CompanyResearchResult(...)
```

---

#### ⑤ Agent Failure 可以向上冒泡

```text
Tool Failure
    ↓
Tool Loop
    ↓
Company Research Agent
    ↓
research_error
    ↓
Parent Graph
    ↓
failure_reason
```

这正是我们 Phase 3 已经建立的 Error Boundary 在 Phase 4 的第一次真正应用。

---

### 23. 本课最重要的认知

到这里，你应该已经能区分四个层次：

```text
Provider
    ↓
Tool
    ↓
Tool Loop Graph
    ↓
Research Agent Graph
    ↓
Investment Research Graph
```

每往上一层，职责都发生变化：

| 层级             | 核心职责            |
| -------------- | --------------- |
| Provider       | 获取/提供数据         |
| Tool           | 暴露数据能力          |
| Tool Loop      | 执行 Tool Calling |
| Research Agent | 完成特定研究职责        |
| Parent Graph   | 编排多个业务步骤        |

所以我们现在真正开始从：

> **LangGraph Tool Calling**

进入：

> **LangGraph Agent Composition**

---

### Lesson 3 架构升级

llm和CompanyResearchResult独立声明，避免循环依赖

---


## Lesson 4 — Agent-Specific Tool Boundary

这一课我们解决一个非常关键的问题：

> **一个 Research Agent 是否应该看到系统里的所有 Tools？**

答案在架构上应该是：**不应该。**

Company Research Agent 的职责是：

```text
Company Research
    ↓
company information
current price
basic company facts
```

因此它应该只能使用完成这个职责所需要的 Tools，而不是整个系统的 Tool Registry。

这会是 Phase 4 从“一个 Agent 能运行”走向“多个 Agent 可以安全扩展”的第一个关键步骤。

---

### 1. 为什么现在学习这个

目前我们的结构实际上是：

```text
Company Research Agent
        ↓
tool_loop_graph
        ↓
TOOLS
        ↓
所有 Tools
```

而 `tool_loop.py` 中：

```python
llm_with_tools = llm.bind_tools(TOOLS)
```

这里的 `TOOLS` 是全局 Registry。

随着项目继续发展，未来很可能出现：

```text
Company Research Agent
    ├── get_company_info
    └── get_stock_price

Financial Research Agent
    ├── get_income_statement
    ├── get_balance_sheet
    └── get_cash_flow

Market Research Agent
    ├── get_market_index
    └── get_market_data

Industry Research Agent
    └── ...
```

如果所有 Agent 都看到：

```text
全部 Tools
```

就会出现职责泄漏：

```text
Company Research Agent
        ↓
看到 valuation tool
        ↓
看到 risk tool
        ↓
看到 market tool
        ↓
看到 financial tool
```

这会让 Agent 的 prompt 中：

```text
Do not perform valuation.
```

变成一种**软约束**。

更好的设计是：

```text
Company Research Agent
        ↓
只能看到 Company Research Tools
```

也就是：

> **职责边界不仅由 Prompt 定义，还应该由 Tool Availability 定义。**

---

### 2. Lesson 4 的目标

本课完成：

```text
Company Research Agent
        ↓
Company Research Tool Set
        ↓
Tool Loop
        ↓
CompanyResearchResult
```

具体来说：

```text
Company Research Agent
       │
       ├── get_company_info
       │
       └── get_stock_price
```

而不是：

```text
Company Research Agent
       │
       └── ALL TOOLS
```

---

### 3. Lesson 4 的 Graph Topology

这一课 Parent Graph 不需要改变。

仍然是：

```text
START
  ↓
initialize_state
  ↓
company_research
  ↓
llm_node
  ↓
create_research_plan
  ↓
investment_decision_node
  ↓
prepare_output
  ↓
END
```

变化发生在 Company Research Agent 内部。

之前：

```text
Company Research Agent
        ↓
tool_loop_graph
        ↓
ALL TOOLS
```

现在：

```text
Company Research Agent
        ↓
Company Research Tool Loop
        ↓
Company Research Tools
        ├── get_company_info
        └── get_stock_price
```

完整结构：

```text
Parent Research Graph
        │
        ▼
company_research
        │
        ▼
Company Research Graph
        │
        ▼
Company Research Agent
        │
        ▼
Company Research Tool Loop
        │
        ├───────────────┐
        ▼               ▼
get_company_info   get_stock_price
        │               │
        └───────┬───────┘
                ▼
             Provider
                │
                ▼
     CompanyResearchResult
```

---

### 4. State Design

这一课**不新增 Parent Graph State 字段**。

这是有意的。

Lesson 3 已经完成：

```text
Child Graph
    ↓
CompanyResearchResult
    ↓
Parent Graph State
```

Lesson 4 只改变：

```text
Agent
    ↓
Tool Availability
```

所以 State 保持：

```python
company_research_result: CompanyResearchResult | None
```

不变。

这是一个重要的工程习惯：

> **如果 Lesson 的目标不需要 State 变化，就不要为了“有代码改动”而修改 State。**

---

### 5. 先检查当前 Tool Registry

当前 Phase 3 已经有：

```text
app/tools/registry.py
```

其职责是：

```text
系统级 Tool Registry
```

我们不删除它。

它仍然应该存在：

```text
TOOLS
```

因为未来可能有：

```text
ALL_TOOLS
```

但是 Agent 不应该直接使用它。

---

### 6. 新增 Agent Tool Registry

新建：

```text
app/agents/tool_sets.py
```

完整代码：

```python
from app.tools.financial import (
    get_company_info,
    get_stock_price,
)


COMPANY_RESEARCH_TOOLS = [
    get_company_info,
    get_stock_price,
]
```

这里的意义非常明确：

```text
System Tool Registry
        ↓
所有系统能力

Agent Tool Set
        ↓
某个 Agent 被允许使用的能力
```

因此：

```python
COMPANY_RESEARCH_TOOLS
```

不是新的 Tool。

它只是：

> **Tool Capability Boundary**

---

### 7. 修改 `app/graph/tool_loop.py`

这里需要做一个重要改变。

之前：

```python
llm_with_tools = llm.bind_tools(TOOLS)
tool_node = ToolNode(TOOLS)
```

这意味着 Tool Loop 和具体 Tool Set 强绑定。

Lesson 4 开始，我们把 Tool Loop 变成：

> **可复用的 Tool Loop Factory**

也就是：

```text
build_tool_loop_graph(tools)
```

给它什么 Tools，它就构建一个使用这些 Tools 的 Tool Loop。

---

#### 完整 `app/graph/tool_loop.py`

```python
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.llm.client import llm


class ToolLoopState(TypedDict):
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]


def build_tool_loop_graph(tools):
    llm_with_tools = llm.bind_tools(tools)

    tool_node = ToolNode(tools)

    def tool_loop_llm_node(
        state: ToolLoopState,
    ) -> dict:

        response = llm_with_tools.invoke(
            state["messages"]
        )

        return {
            "messages": [response]
        }

    def route_after_llm(
        state: ToolLoopState,
    ) -> str:

        last_message = state["messages"][-1]

        if last_message.tool_calls:
            return "tools"

        return "end"

    builder = StateGraph(ToolLoopState)

    builder.add_node(
        "llm",
        tool_loop_llm_node,
    )

    builder.add_node(
        "tools",
        tool_node,
    )

    builder.add_edge(
        START,
        "llm",
    )

    builder.add_conditional_edges(
        "llm",
        route_after_llm,
        {
            "tools": "tools",
            "end": END,
        },
    )

    builder.add_edge(
        "tools",
        "llm",
    )

    return builder.compile()
```

注意这里我们**没有**再创建：

```python
tool_loop_graph = ...
```

因为现在 Tool Loop 不再只有一个版本。

它可以有：

```text
Company Research Tool Loop
Financial Research Tool Loop
Market Research Tool Loop
```

等等。

---

### 8. 修改 `company_research.py`

现在 Company Research Agent 不再使用一个默认 Tool Loop。

它明确创建自己的 Tool Loop：

```text
Company Research Tools
        ↓
build_tool_loop_graph()
        ↓
Company Research Tool Loop
```

---

#### 完整 `app/agents/company_research.py`

```python
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agents.models import CompanyResearchResult
from app.agents.tool_sets import COMPANY_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
from app.llm.client import llm


class CompanyResearchInputState(TypedDict):
    ticker: str


class CompanyResearchState(TypedDict):
    ticker: str
    research_result: CompanyResearchResult | None
    research_error: str


class CompanyResearchOutputState(TypedDict):
    research_result: CompanyResearchResult | None
    research_error: str


company_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Company Research Agent. "
            "Your responsibility is to research basic company "
            "information for the given stock ticker. "
            "Use the available tools to obtain company name, "
            "sector, and current stock price. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent financial data.",
        ),
        (
            "human",
            "Research the following company and return a concise "
            "company research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


structured_company_research_llm = (
    llm.with_structured_output(
        CompanyResearchResult
    )
)


company_research_tool_loop = build_tool_loop_graph(
    COMPANY_RESEARCH_TOOLS
)


def extract_tool_results(
    tool_result: dict,
) -> str:

    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(
        message.content
        for message in tool_messages
    )


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
        tool_result = company_research_tool_loop.invoke(
            {
                "messages": prompt_value.messages,
            }
        )

        research_context = extract_tool_results(
            tool_result
        )

        structured_result = (
            structured_company_research_llm.invoke(
                [
                    *prompt_value.messages,
                    HumanMessage(
                        content=(
                            "Tool results:\n"
                            f"{research_context}\n\n"
                            "Using only these tool results, "
                            "produce the structured company "
                            "research result."
                        )
                    ),
                ]
            )
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


company_research_graph = (
    build_company_research_graph()
)
```

---

### 9. 一个重要的架构变化

之前：

```text
company_research.py
       ↓
tool_loop_graph
       ↓
TOOLS
```

现在：

```text
company_research.py
       ↓
COMPANY_RESEARCH_TOOLS
       ↓
build_tool_loop_graph()
       ↓
company_research_tool_loop
```

因此 Agent 自己声明：

> “我需要哪些工具。”

而不是 Tool Loop 决定：

> “所有 Agent 都可以使用哪些工具。”

这两者的职责完全不同。

---

### 10. 为什么不直接修改 `registry.py`

这是一个很重要的问题。

我们当然可以写：

```python
COMPANY_RESEARCH_TOOLS = [
    ...
]
```

放进：

```text
app/tools/registry.py
```

但是现在不这样做。

因为：

```text
app/tools/registry.py
```

表达的是：

> **系统有哪些 Tools。**

而：

```text
app/agents/tool_sets.py
```

表达的是：

> **某个 Agent 被授权使用哪些 Tools。**

这是两个不同的概念。

最终可能形成：

```text
tools/
    registry.py
        ↓
    ALL_TOOLS

agents/
    tool_sets.py
        ↓
    COMPANY_RESEARCH_TOOLS
    FINANCIAL_RESEARCH_TOOLS
    MARKET_RESEARCH_TOOLS
```

这为 Phase 4 后面的多个 Research Agents 留出了自然扩展空间。

---

### 11. 测试设计

这一课测试的重点不是再次测试：

```text
Tool 能不能调用 Provider
```

Phase 3 已经完成这个学习目标。

Lesson 4 要测试：

> **Company Research Agent 是否真的被限制在自己的 Tool Set 中。**

所以新增：

```text
tests/test_agent_tool_boundary.py
```

---

#### 完整测试代码

```python
from unittest.mock import patch

from app.agents.company_research import (
    company_research_tool_loop,
)
from app.agents.tool_sets import (
    COMPANY_RESEARCH_TOOLS,
)
from app.graph.tool_loop import (
    build_tool_loop_graph,
)


def test_company_research_tool_set_contains_company_tools():
    tool_names = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    assert tool_names == {
        "get_company_info",
        "get_stock_price",
    }


def test_company_research_tool_loop_is_compiled():
    assert company_research_tool_loop is not None


def test_build_tool_loop_graph_accepts_custom_tool_set():
    graph = build_tool_loop_graph(
        COMPANY_RESEARCH_TOOLS
    )

    assert graph is not None


def test_company_research_tool_loop_contains_only_allowed_tools():
    graph = company_research_tool_loop

    graph_nodes = graph.get_graph().nodes

    assert "llm" in graph_nodes
    assert "tools" in graph_nodes


def test_company_research_tool_set_does_not_include_unrelated_tools():
    tool_names = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    assert "get_stock_price" in tool_names
    assert "get_company_info" in tool_names

    assert "get_income_statement" not in tool_names
    assert "get_balance_sheet" not in tool_names
```

---

### 12. 这里为什么没有 Mock LLM

因为这组测试主要验证：

```text
Tool Set
    ↓
Tool Loop Construction
```

而不是：

```text
LLM
    ↓
Tool Call
```

Phase 3 已经覆盖后者。

我们应该避免每一个 Lesson 都重新测试之前已经验证过的能力。

---

### 13. 再增加一个更重要的测试

我们还要验证：

> Company Research Agent 使用的确实是自己的 Tool Loop，而不是旧的 global Tool Loop。

增加：

```python
def test_company_research_agent_uses_company_research_tool_loop():
    from app.agents import company_research

    assert (
        company_research.company_research_tool_loop
        is company_research_tool_loop
    )
```

不过这个测试实际上比较弱，因为只是验证模块对象引用。

更有价值的是直接检查构建时传入的 Tool Set。

因此我更推荐下面这个测试：

```python
def test_company_research_tool_loop_uses_expected_tool_set():
    tool_names = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    assert set(
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    ) == tool_names
```

这其实还是比较弱。

因此这里需要明确一个测试原则：

> **不要为了测试而制造没有业务价值的测试。**

前面的四个测试已经足够证明 Lesson 4 的核心概念。

---

### 14. 需要修改的旧测试

因为 Lesson 2 时：

```python
from app.graph.tool_loop import tool_loop_graph
```

是合法的。

Lesson 4 之后：

```text
tool_loop_graph
```

不再是模块级单例。

因此，如果旧测试里有：

```python
from app.graph.tool_loop import tool_loop_graph
```

必须改成：

```python
from app.graph.tool_loop import build_tool_loop_graph
```

然后：

```python
graph = build_tool_loop_graph(
    TOOLS
)
```

注意这里需要导入：

```python
from app.tools.registry import TOOLS
```

这是因为旧测试的目标仍然是：

> 用全部 Tools 测试 Tool Loop。

而不是 Company Research Agent。

---

### 15. `test_tool_calling_loop.py` 的调整原则

如果当前测试中存在：

```python
tool_loop_graph.invoke(...)
```

修改成：

```python
tool_loop_graph = build_tool_loop_graph(
    TOOLS
)

tool_loop_graph.invoke(...)
```

或者更简洁：

```python
graph = build_tool_loop_graph(TOOLS)

graph.invoke(...)
```

这里**不要修改测试的业务场景**。

它仍然测试 Phase 3：

```text
LLM
 ↓
Tool
 ↓
Tool Loop
```

只是 Tool Loop 从：

```text
Singleton
```

变成：

```text
Factory-created graph
```

---

### 16. 这次修改之后的最终架构

现在：

```text
app/
│
├── agents/
│   ├── models.py
│   ├── tool_sets.py
│   └── company_research.py
│
├── graph/
│   ├── graph.py
│   ├── models.py
│   ├── state.py
│   ├── tool_loop.py
│   └── nodes/
│       └── tool_node.py
│
├── llm/
│   ├── __init__.py
│   └── client.py
│
├── tools/
│   ├── financial.py
│   └── registry.py
│
└── providers/
    ├── financial.py
    └── exceptions.py
```

逻辑关系：

```text
                         LLM Client
                            │
              ┌─────────────┴─────────────┐
              │                           │
           Graph                        Agent
              │                           │
              │                  Company Research
              │                           │
              │                    Tool Set
              │                           │
              │                           ▼
              │                    Tool Loop Factory
              │                           │
              │                           ▼
              │                         Tools
              │                           │
              │                           ▼
              │                       Providers
              │
              ▼
        Parent State
```

---

### 17. Lesson 4 的核心思想

到现在为止，我们已经完成了三个不同层次：

#### Lesson 1

```text
Agent
```

第一次出现。

#### Lesson 2

```text
Agent
 ↓
Compiled Tool Loop
```

把 Agent 内部执行结构固定下来。

#### Lesson 3

```text
Parent Graph
 ↓
Agent
 ↓
Result
 ↓
Parent State
```

让 Agent 真正成为整个 Application Graph 的业务组件。

#### Lesson 4

现在进一步：

```text
Agent
 ↓
Agent-specific Tool Set
 ↓
Tool Loop
```

于是：

> **Agent 的 Business Responsibility 开始通过 Tool Boundary 被真正落实。**

这非常重要，因为到了后面的：

```text
Financial Research Agent
Market Research Agent
Industry Research Agent
```

我们就可以自然得到：

```text
Company Agent
    ↓
Company Tools

Financial Agent
    ↓
Financial Tools

Market Agent
    ↓
Market Tools
```

而不是：

```text
所有 Agent
    ↓
所有 Tools
```

---

### 18. 本课 Acceptance Criteria

#### Architecture

* [ ] `build_tool_loop_graph(tools)` 可以接受任意 Tool Set
* [ ] `tool_loop.py` 不再依赖全局 `TOOLS`
* [ ] `Company Research Agent` 有自己的 Tool Set
* [ ] `COMPANY_RESEARCH_TOOLS` 包含 `get_company_info`
* [ ] `COMPANY_RESEARCH_TOOLS` 包含 `get_stock_price`
* [ ] Company Research Agent 不直接使用全局 `TOOLS`

#### Graph

* [ ] Parent Graph topology 不发生变化
* [ ] Company Research Graph topology 不发生变化
* [ ] Agent 内部 Tool Loop 改为 Agent-specific Tool Loop

#### Testing

运行：

```bash
pytest tests/test_agent_tool_boundary.py -v
```

然后：

```bash
pytest tests/test_company_research_agent.py -v
```

然后：

```bash
pytest tests/test_company_research_parent_graph.py -v
```

最后运行受影响的 Phase 3 Tool Loop 测试：

```bash
pytest tests/test_tool_calling_loop.py -v
```

---

### Lesson 4 完成后的关键理解

你现在应该能够清楚区分：

```text
Tool Registry
```

和：

```text
Agent Tool Set
```

前者回答：

> **系统有什么能力？**

后者回答：

> **这个 Agent 被允许使用哪些能力？**

这是后面进入 **多个 Research Agents** 前必须建立的边界。


## Lesson 5 — Financial Research Agent：第二个职责明确的 Research Agent

Lesson 4 我们解决了：

> **一个 Agent 应该使用哪些 Tools？**

现在进入 Lesson 5，解决下一个自然问题：

> **如果系统里出现第二个 Research Agent，它应该如何与 Company Research Agent 并存，同时保持职责、Tool Set、State 和输出彼此独立？**

这一课我们建立 **Financial Research Agent**。

但有一个边界必须先明确：

**本课不进入 Multi-Agent Orchestration。**

不会实现：

* Supervisor
* Agent Routing
* Parallel Agents
* Fan-out / Fan-in
* Agent-to-Agent communication

这些属于后续 Multi-Agent Orchestration 阶段。交接文档也明确将 Company、Financial、Market、Industry Research Agents 的组合协调放到后续阶段。

本课只是让第二个 Agent 独立成立。

---

### 一、Phase 4 到目前为止的演进

我们现在不是从零开始，而是：

```text
Phase 3
LLM
 ↓
Tool Calling
 ↓
Tool Loop
 ↓
Provider
```

↓

```text
Lesson 1
Company Research Agent
```

↓

```text
Lesson 2
Compiled Tool Loop
```

↓

```text
Lesson 3
Agent Result
 ↓
Parent Graph State
```

↓

```text
Lesson 4
Agent-specific Tool Set
```

现在：

```text
Lesson 5

Company Research Agent
        │
        └── Company Tools


Financial Research Agent
        │
        └── Financial Tools
```

这一步非常重要，因为我们第一次拥有了**两个具有不同业务职责的 Agent**。

---

### 二、为什么现在需要 Financial Research Agent

目前只有：

```text
CompanyResearchAgent
```

如果我们继续往里面塞功能，很容易变成：

```text
CompanyResearchAgent
    ├── company information
    ├── price
    ├── revenue
    ├── earnings
    ├── valuation
    ├── risk
    ├── market
    └── recommendation
```

最终又会退化成：

```text
Super Agent
```

而 Phase 4 的目标恰恰是避免这一点。

交接文档明确给出的后续方向是：

```text
Research Planner
        │
        ├── Company Research Agent
        ├── Financial Research Agent
        ├── Market Research Agent
        └── Industry / Macro Research Agent
```

然后在后续阶段才进入 Supervisor、Routing、Parallel Agents、Fan-out/Fan-in 等协调机制。

所以 Lesson 5 先只做：

```text
Financial Research Agent
```

---

### 三、Lesson 5 的业务职责

Financial Research Agent 的职责定义为：

> **研究公司的基础财务表现，并返回结构化的 Financial Research Result。**

本课只研究三个指标：

```text
ticker
 ↓
revenue
 ↓
net income
 ↓
profit margin
```

暂时不做：

```text
Valuation
Risk
Target Price
Expected Return
Investment Recommendation
```

因此：

```text
Company Research Agent
```

负责：

```text
Who is the company?
What sector?
What is current price?
```

而：

```text
Financial Research Agent
```

负责：

```text
How is the company performing financially?
```

---

### 四、Graph Topology

#### Parent Graph

本课**暂时不修改 Parent Graph**。

仍然：

```text
START
  ↓
initialize_state
  ↓
company_research
  ↓
llm_node
  ↓
create_research_plan
  ↓
investment_decision_node
  ↓
prepare_output
  ↓
END
```

为什么？

因为我们还没有进入 Multi-Agent Orchestration。

---

#### Financial Research Graph

新增：

```text
START
  ↓
financial_research_agent
  ↓
END
```

Agent 内部：

```text
Financial Research Agent
        ↓
Financial Tool Loop
        ↓
Financial Tools
        ├── get_revenue
        └── get_net_income
        ↓
Mock Provider
        ↓
FinancialResearchResult
```

因此现在系统有两个独立的 Agent Graph：

```text
Company Research Graph
        │
        └── Company Tool Loop
                ├── get_company_info
                └── get_stock_price


Financial Research Graph
        │
        └── Financial Tool Loop
                ├── get_revenue
                └── get_net_income
```

**它们现在彼此不调用。**

这点非常重要。

---

### 五、State Design

Financial Agent 不应该直接复用 Parent `GraphState`。

我们建立自己的：

```python
FinancialResearchInputState
FinancialResearchState
FinancialResearchOutputState
```

以及：

```python
FinancialResearchResult
```

结果模型：

```python
class FinancialResearchResult(BaseModel):
    ticker: str
    revenue: float
    net_income: float
    profit_margin: float
    summary: str
```

这样形成：

```text
Financial Agent
      ↓
FinancialResearchResult
```

而不是：

```text
Financial Agent
      ↓
GraphState
```

这是与 Lesson 3 非常重要的区别。

Lesson 3 学习的是：

```text
Child Agent Result
       ↓
Parent Graph State
```

Lesson 5 学习的是：

```text
Independent Agent
       ↓
Independent Domain Result
```

---

### 六、Step 1：新增 Financial Result Model

新建：

```text
app/agents/financial_research.py
```

不过为了与 Lesson 3 建立的结构保持一致，我们把 Domain Model 放在：

```text
app/agents/models.py
```

修改为：

```python
from pydantic import BaseModel, Field


class CompanyResearchResult(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    company_name: str = Field(
        description="Company name."
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


class FinancialResearchResult(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    revenue: float = Field(
        description="Company revenue."
    )

    net_income: float = Field(
        description="Company net income."
    )

    profit_margin: float = Field(
        description="Net income divided by revenue."
    )

    summary: str = Field(
        description="Concise factual financial research summary."
    )
```

这里暂时不引入：

```text
EPS
ROE
ROIC
Free Cash Flow
Debt
Growth
```

因为我们这一课的目标不是建立完整 Fundamental Analysis，而是建立**第二个独立 Research Agent**。

---

### 七、Step 2：新增 Financial Provider

目前项目的 Provider 抽象已经建立。

Lesson 5 继续遵循项目的：

> **Mock Provider → Agent Integration**

原则。

交接文档明确要求继续保持：

```text
Real LLM
+
Mock Tools
+
Mock Providers
```

这种测试方式，而不要现在把重点转移到真实金融 API、认证和网络问题。

修改：

```text
app/providers/financial.py
```

在现有内容中增加：

```python
def get_revenue(ticker: str) -> float:
    mock_revenue = {
        "AAPL": 100000.0,
        "MSFT": 80000.0,
    }

    try:
        return mock_revenue[ticker.upper()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported ticker: {ticker}"
        ) from exc


def get_net_income(ticker: str) -> float:
    mock_net_income = {
        "AAPL": 25000.0,
        "MSFT": 22000.0,
    }

    try:
        return mock_net_income[ticker.upper()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported ticker: {ticker}"
        ) from exc
```

这里的数字仍然只是 Mock Data。

不要把：

```text
100000
25000
```

理解成真实财务数据。

---

### 八、Step 3：新增 Financial Tools

修改：

```text
app/tools/financial.py
```

在现有 Company/Price Tools 之后增加：

```python
from app.providers.financial import (
    get_net_income as provider_get_net_income,
    get_revenue as provider_get_revenue,
)
```

然后：

```python
@tool
def get_revenue(ticker: str) -> float:
    """Get company revenue for the given stock ticker."""
    return provider_get_revenue(ticker)
```

以及：

```python
@tool
def get_net_income(ticker: str) -> float:
    """Get company net income for the given stock ticker."""
    return provider_get_net_income(ticker)
```

如果你当前 `financial.py` 已经有统一的 Provider import 结构，则**保持现有结构，只增加这两个 Tool**，不要为了这两个函数重构整个文件。

最终应该有：

```text
app.tools.financial
    ├── get_company_info
    ├── get_stock_price
    ├── get_revenue
    └── get_net_income
```

---

### 九、Step 4：扩展 Agent Tool Sets

Lesson 4 已经建立：

```text
app/agents/tool_sets.py
```

现在加入 Financial Tool Set。

完整文件变成：

```python
from app.tools.financial import (
    get_company_info,
    get_net_income,
    get_revenue,
    get_stock_price,
)


COMPANY_RESEARCH_TOOLS = [
    get_company_info,
    get_stock_price,
]


FINANCIAL_RESEARCH_TOOLS = [
    get_revenue,
    get_net_income,
]
```

现在终于形成非常清晰的边界：

```text
COMPANY_RESEARCH_TOOLS
    ├── get_company_info
    └── get_stock_price


FINANCIAL_RESEARCH_TOOLS
    ├── get_revenue
    └── get_net_income
```

---

### 十、Step 5：创建 Financial Research Agent

新建：

```text
app/agents/financial_research.py
```

完整代码：

```python
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agents.models import FinancialResearchResult
from app.agents.tool_sets import FINANCIAL_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
from app.llm.client import llm


class FinancialResearchInputState(TypedDict):
    ticker: str


class FinancialResearchState(TypedDict):
    ticker: str
    research_result: FinancialResearchResult | None
    research_error: str


class FinancialResearchOutputState(TypedDict):
    research_result: FinancialResearchResult | None
    research_error: str


financial_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Financial Research Agent. "
            "Your responsibility is to research basic financial "
            "performance for the given stock ticker. "
            "Use the available tools to obtain revenue and "
            "net income. "
            "Calculate profit margin as net income divided by "
            "revenue. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent financial data.",
        ),
        (
            "human",
            "Research the financial performance of the following "
            "company and return a concise financial research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


structured_financial_research_llm = (
    llm.with_structured_output(
        FinancialResearchResult
    )
)


financial_research_tool_loop = build_tool_loop_graph(
    FINANCIAL_RESEARCH_TOOLS
)


def extract_tool_results(
    tool_result: dict,
) -> str:

    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(
        message.content
        for message in tool_messages
    )


def financial_research_agent(
    state: FinancialResearchState,
) -> FinancialResearchState:

    ticker = state["ticker"]

    prompt_value = financial_research_prompt.invoke(
        {
            "ticker": ticker,
        }
    )

    try:
        tool_result = financial_research_tool_loop.invoke(
            {
                "messages": prompt_value.messages,
            }
        )

        research_context = extract_tool_results(
            tool_result
        )

        structured_result = (
            structured_financial_research_llm.invoke(
                [
                    *prompt_value.messages,
                    HumanMessage(
                        content=(
                            "Tool results:\n"
                            f"{research_context}\n\n"
                            "Using only these tool results, "
                            "produce the structured financial "
                            "research result."
                        )
                    ),
                ]
            )
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


def build_financial_research_graph():

    builder = StateGraph(
        FinancialResearchState,
        input_schema=FinancialResearchInputState,
        output_schema=FinancialResearchOutputState,
    )

    builder.add_node(
        "financial_research_agent",
        financial_research_agent,
    )

    builder.add_edge(
        START,
        "financial_research_agent",
    )

    builder.add_edge(
        "financial_research_agent",
        END,
    )

    return builder.compile()


financial_research_graph = (
    build_financial_research_graph()
)
```

---

### 十一、这里出现了一个非常值得注意的重复

现在：

```text
company_research.py
```

和：

```text
financial_research.py
```

有很多相似代码：

```text
Prompt
Tool Loop
extract_tool_results
structured output
State
Graph builder
```

**现在不要重构。**

这是刻意保留的。

为什么？

因为我们正在学习：

```text
两个独立的 Research Agents
```

如果现在立即抽象成：

```python
BaseResearchAgent
ResearchAgentFactory
GenericResearchGraph
AgentConfig
```

我们会把两个概念混在一起：

```text
Business Responsibility
```

和：

```text
Framework Abstraction
```

目前应该先让你清楚看到：

```text
Company Agent
```

和：

```text
Financial Agent
```

是两个独立业务组件。

等第三、第四个 Agent 出现后，再判断哪些重复是真正稳定的抽象。

---

### 十二、这里也再次体现 Lesson 4 的价值

Company Agent：

```text
Company Research Agent
        ↓
COMPANY_RESEARCH_TOOLS
        ↓
get_company_info
get_stock_price
```

Financial Agent：

```text
Financial Research Agent
        ↓
FINANCIAL_RESEARCH_TOOLS
        ↓
get_revenue
get_net_income
```

因此：

```text
Financial Research Agent
```

不会看到：

```text
get_company_info
get_stock_price
```

而：

```text
Company Research Agent
```

不会看到：

```text
get_revenue
get_net_income
```

这就是：

> **Business Responsibility → Tool Boundary**

真正落地后的效果。

---

### 十三、不要把两个 Agent 放进 Parent Graph

这是 Lesson 5 最容易犯的错误。

不要现在改成：

```text
START
  ↓
Company Research
  ↓
Financial Research
  ↓
LLM
```

也不要：

```text
START
  ↓
Company Research
  ↓
Financial Research
  ↓
END
```

因为这已经开始进入：

```text
Multi-Agent Orchestration
```

我们现在只需要让：

```text
Company Research Graph
```

和：

```text
Financial Research Graph
```

分别能够独立运行。

所以目前：

```text
Parent Graph
      │
      └── Company Research Agent
```

保持不变。

Financial Agent 作为新的独立能力存在：

```text
Financial Research Graph
      │
      └── Financial Research Agent
```

下一阶段再研究：

```text
谁决定什么时候调用 Company Agent？
谁决定什么时候调用 Financial Agent？
是否并行？
如何汇总？
```

那才是 Multi-Agent Orchestration。

---

### 十四、测试 1：Provider

新增：

```text
tests/test_financial_research_provider.py
```

```python
from app.providers.financial import (
    get_net_income,
    get_revenue,
)


def test_get_revenue_returns_mock_value():
    assert get_revenue("AAPL") == 100000.0


def test_get_net_income_returns_mock_value():
    assert get_net_income("AAPL") == 25000.0


def test_financial_provider_is_case_insensitive():
    assert get_revenue("aapl") == 100000.0
    assert get_net_income("aapl") == 25000.0


def test_financial_provider_rejects_unknown_ticker():
    try:
        get_revenue("UNKNOWN")
    except ValueError as exc:
        assert "UNKNOWN" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
```

---

### 十五、测试 2：Financial Tool

新增：

```text
tests/test_financial_research_tools.py
```

```python
from app.tools.financial import (
    get_net_income,
    get_revenue,
)


def test_get_revenue_tool_has_expected_name():
    assert get_revenue.name == "get_revenue"


def test_get_net_income_tool_has_expected_name():
    assert get_net_income.name == "get_net_income"


def test_get_revenue_tool_returns_provider_value():
    result = get_revenue.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result == 100000.0


def test_get_net_income_tool_returns_provider_value():
    result = get_net_income.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result == 25000.0
```

---

### 十六、测试 3：Financial Agent

新增：

```text
tests/test_financial_research_agent.py
```

```python
from unittest.mock import MagicMock, patch

from app.agents.financial_research import (
    FinancialResearchResult,
    build_financial_research_graph,
    financial_research_graph,
    financial_research_tool_loop,
)


def test_financial_research_result_model():
    result = FinancialResearchResult(
        ticker="AAPL",
        revenue=100000.0,
        net_income=25000.0,
        profit_margin=0.25,
        summary="Apple generated strong net income.",
    )

    assert result.ticker == "AAPL"
    assert result.revenue == 100000.0
    assert result.net_income == 25000.0
    assert result.profit_margin == 0.25


def test_financial_research_graph_is_compiled():
    assert financial_research_graph is not None


def test_build_financial_research_graph():
    graph = build_financial_research_graph()

    assert graph is not None


def test_financial_research_agent_uses_financial_tool_loop():
    assert financial_research_tool_loop is not None


def test_financial_research_agent_maps_tool_result():
    fake_result = FinancialResearchResult(
        ticker="AAPL",
        revenue=100000.0,
        net_income=25000.0,
        profit_margin=0.25,
        summary="Apple generated strong net income.",
    )

    fake_tool_loop = MagicMock()

    fake_tool_loop.invoke.return_value = {
        "messages": [],
    }

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_result

    with patch(
        "app.agents.financial_research.financial_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.financial_research.structured_financial_research_llm",
        fake_structured_llm,
    ):

        result = financial_research_graph.invoke(
            {
                "ticker": "AAPL",
            }
        )

    assert result["research_result"] == fake_result
    assert result["research_error"] == ""

    fake_tool_loop.invoke.assert_called_once()
```

这里测试的是：

```text
Financial Research Agent
        ↓
Financial Tool Loop
        ↓
Structured Financial Result
```

---

### 十七、测试 4：两个 Agent 的 Tool Boundary

修改 Lesson 4 的：

```text
tests/test_agent_tool_boundary.py
```

增加：

```python
from app.agents.tool_sets import (
    COMPANY_RESEARCH_TOOLS,
    FINANCIAL_RESEARCH_TOOLS,
)
```

然后增加：

```python
def test_financial_research_tool_set_contains_financial_tools():
    tool_names = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    assert tool_names == {
        "get_revenue",
        "get_net_income",
    }


def test_company_and_financial_tool_sets_are_separate():
    company_tools = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    financial_tools = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    assert company_tools.isdisjoint(
        financial_tools
    )


def test_financial_tool_set_does_not_include_company_tools():
    tool_names = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    assert "get_company_info" not in tool_names
    assert "get_stock_price" not in tool_names
```

这个测试实际上是在验证：

```text
Company Tool Set ∩ Financial Tool Set = ∅
```

即：

```text
Company Tools
       ∩
Financial Tools
       =
Empty Set
```

这不是数学炫技，而是在测试一个真正的架构约束：

> **两个 Agent 当前拥有独立的 Tool Capability Boundary。**

---

### 十八、为什么 Lesson 5 暂时不修改 GraphState

你可能会注意到：

```text
GraphState
```

目前没有：

```python
financial_research_result
```

这是**有意的**。

因为如果现在直接加入：

```python
financial_research_result: FinancialResearchResult | None
```

然后又把 Financial Agent 接进 Parent Graph，就会同时引入：

```text
第二 Agent
+
Parent Graph Integration
+
State Integration
+
Orchestration
```

一次学习太多概念。

Lesson 3 已经学习过：

```text
Agent Result → Parent State
```

Lesson 5 要学习的是：

```text
第二个独立 Research Agent
```

因此现在保持：

```text
Financial Agent
      ↓
FinancialResearchResult
      ↓
END
```

就足够。

---

### 十九、现在的整体架构

完成 Lesson 5 后：

```text
                         Parent Research Graph
                                  │
                                  ▼
                        Company Research Agent
                                  │
                         Company Tool Set
                           /            \
                          /              \
             get_company_info       get_stock_price
```

同时独立存在：

```text
                     Financial Research Graph
                              │
                              ▼
                    Financial Research Agent
                              │
                     Financial Tool Set
                         /          \
                        /            \
               get_revenue      get_net_income
```

二者现在：

```text
         Company Agent             Financial Agent
               │                         │
               ▼                         ▼
        Company Result            Financial Result
```

**没有 Agent-to-Agent communication。**

**没有 Supervisor。**

**没有 Parallel Execution。**

这正是我们希望 Lesson 5 达到的状态。

---

### 二十、测试运行顺序

不要跑全部历史测试。

先跑本课 Provider：

```bash
pytest tests/test_financial_research_provider.py -v
```

然后 Tool：

```bash
pytest tests/test_financial_research_tools.py -v
```

然后 Agent：

```bash
pytest tests/test_financial_research_agent.py -v
```

然后 Tool Boundary：

```bash
pytest tests/test_agent_tool_boundary.py -v
```

最后做一个 Lesson 4 回归：

```bash
pytest tests/test_company_research_agent.py -v
```

---

### 二十一、Lesson 5 Acceptance Criteria

#### Financial Domain

* [ ] `FinancialResearchResult` 存在
* [ ] 包含 `ticker`
* [ ] 包含 `revenue`
* [ ] 包含 `net_income`
* [ ] 包含 `profit_margin`
* [ ] 包含 `summary`

#### Financial Tools

* [ ] `get_revenue` 存在
* [ ] `get_net_income` 存在
* [ ] 两个 Tool 都通过 Provider 获取数据
* [ ] Provider 仍然是 Mock Provider
* [ ] 不引入真实金融 API

#### Financial Agent

* [ ] `FinancialResearchAgent` 独立存在
* [ ] 有自己的 Input State
* [ ] 有自己的 Internal State
* [ ] 有自己的 Output State
* [ ] 使用 `FINANCIAL_RESEARCH_TOOLS`
* [ ] 使用自己的 Tool Loop
* [ ] 可以返回 `FinancialResearchResult`

#### Agent Boundary

* [ ] Company Tool Set 与 Financial Tool Set 独立
* [ ] Financial Agent 不使用 Company Tools
* [ ] Company Agent 不使用 Financial Tools

#### Orchestration Boundary

* [ ] Parent Graph 不调用 Financial Agent
* [ ] 没有 Supervisor
* [ ] 没有 Parallel Agent
* [ ] 没有 Agent-to-Agent communication

---

### 二十二、Lesson 5 最重要的理解

现在你应该看到 Phase 4 的核心结构正在形成：

```text
                    Research Agents
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
 Company Research               Financial Research
      Agent                           Agent
          │                             │
          ▼                             ▼
 Company Tool Set              Financial Tool Set
          │                             │
          ▼                             ▼
 Company Result                Financial Result
```

这和 Phase 3 的根本区别是：

```text
Phase 3
```

关注：

> **LLM 如何调用 Tool？**

而 Phase 4 现在关注：

> **一个具有明确业务职责的 Agent，应该拥有哪些能力，并产生什么业务结果？**

这正是交接文档定义的 Phase 4 核心变化：从 `LLM → Tool → Provider` 进入 `Research Agent → LLM → Tools → Provider → Research Result`。

而 Lesson 5 完成之后，下一步才真正有条件讨论：

```text
Company Agent
      +
Financial Agent
      +
Market Agent
      +
Industry Agent
      ↓
如何协调？
```

这部分再进入后续 Multi-Agent Orchestration，而不是在本课提前实现。



## Lesson 6 — Market Research Agent

### 1. Goal

本课建立：

```text
Market Research Agent
```

它负责回答一个非常明确的问题：

> **当前这家公司所处的市场环境如何？**

但在当前阶段，我们只做一个**最小版本**。

本课最终形成：

```text
Company Research Agent
        │
        └── CompanyResearchResult

Financial Research Agent
        │
        └── FinancialResearchResult

Market Research Agent
        │
        └── MarketResearchResult
```

三个 Agent：

* 独立
* 独立 Tool Set
* 独立 State
* 独立 Research Result
* 独立 Tool Loop

**本课不做 Agent 之间的协调。**

---

### 2. Why Now

Phase 3 已经解决了：

```text
LLM
 ↓
Tool
 ↓
Provider
```

Lesson 1～5 又逐渐建立：

```text
Business Responsibility
        ↓
Research Agent
        ↓
Tool Set
        ↓
Tool Loop
        ↓
Research Result
```

现在已经有两个业务 Agent：

```text
Company
Financial
```

如果继续只增加 Company Agent 的功能，很容易重新变成一个：

```text
Super Company Agent
```

而我们的目标是建立真正的 **Domain-specific Research Agents**。

因此第三个 Agent 很重要：

```text
Company
Financial
Market
```

这三个职责开始出现明显的领域边界。

---

### 3. Core Concept

本课最重要的不是“再写一个 Agent”。

而是理解：

> **Research Agent 的边界由它负责产生的 Business Result 定义。**

三个 Agent 的职责可以这样划分：

| Agent              | 负责                               | 不负责        |
| ------------------ | -------------------------------- | ---------- |
| Company Research   | 公司身份、行业、当前价格                     | 财务分析、估值、推荐 |
| Financial Research | Revenue、Net Income、Profit Margin | 估值、推荐      |
| Market Research    | 市场环境、市场表现                        | 公司财务、估值、推荐 |

最终：

```text
Company Research
      ↓
"What is this company?"

Financial Research
      ↓
"How is this company performing financially?"

Market Research
      ↓
"What is happening in the market?"
```

这就是后面 Multi-Agent Architecture 的基础。

---

### 4. 本课业务范围

为了保持 Lesson 级别的小步推进，本课的 Market Research Agent 暂时只负责两个数据：

```text
market_index
market_return
```

例如：

```text
S&P 500
+8.5%
```

再由 Agent 生成：

```text
MarketResearchResult
```

建议 Schema：

```python
class MarketResearchResult(BaseModel):
    ticker: str
    market_index: str
    market_return: float
    summary: str
```

注意：

这里的 `ticker` 只是说明：

> 本次 Market Research 是针对哪个股票研究上下文执行的。

它并不意味着 Market Agent 已经在分析公司的财务表现。

---

### 5. Agent Boundary

Market Research Agent 的 Prompt 必须明确边界。

核心职责：

```text
You are a Market Research Agent.

Your responsibility is to research the current market environment
for the given stock research context.

You may use the available tools to obtain:
- market index
- market return

Return a concise market research result.

Do not perform company financial analysis.
Do not perform valuation.
Do not make an investment recommendation.
Do not assess investment risk.
Do not invent market data.
```

这里有一个很重要的设计思想：

```text
Prompt Boundary
        +
Tool Boundary
        +
Result Schema Boundary
        =
Agent Responsibility Boundary
```

所以不能只依赖 Prompt。

---

### 6. Graph Topology

本课仍然保持：

```text
START
  │
  ▼
market_research_agent
  │
  ▼
 END
```

Agent 内部：

```text
Market Research Agent
        │
        ▼
       LLM
        │
        ▼
   Tool Calling
        │
        ▼
    ToolNode
        │
        ▼
     Provider
        │
        ▼
Market Research Result
```

与前两个 Agent 对比：

```text
Company Research Agent
        ↓
Company Tool Set
        ↓
Company Research Result


Financial Research Agent
        ↓
Financial Tool Set
        ↓
Financial Research Result


Market Research Agent
        ↓
Market Tool Set
        ↓
Market Research Result
```

**三个 Graph 现在仍然互相独立。**

---

### 7. State Design

本课不要复用 Company / Financial Agent 的 State。

建立：

```python
class MarketResearchInputState(TypedDict):
    ticker: str
```

内部 State：

```python
class MarketResearchState(TypedDict):
    ticker: str
    research_result: MarketResearchResult | None
    research_error: str
```

Output：

```python
class MarketResearchOutputState(TypedDict):
    research_result: MarketResearchResult | None
    research_error: str
```

这里再次强化 Phase 3 已经建立的原则：

> **Agent 的 State 是 Agent 的执行边界，不应该把所有 Agent 的字段塞进一个万能 State。**

---

### 8. Exact Files

本课预计修改：

```text
app/
├── agents/
│   ├── __init__.py
│   ├── models.py                 ← 修改
│   ├── tool_sets.py              ← 修改
│   ├── company_research.py
│   ├── financial_research.py
│   └── market_research.py        ← 新建
│
├── providers/
│   └── financial.py              ← 修改
│
└── tools/
    └── financial.py              ← 修改

tests/
├── test_market_research_provider.py
├── test_market_research_tools.py
├── test_market_research_agent.py
└── test_agent_tool_boundary.py   ← 修改
```

**Parent Graph 不修改。**

也就是说：

```text
app/graph/graph.py
```

本课保持不动。

---

### 9. Step 1 — MarketResearchResult

在：

```text
app/agents/models.py
```

增加：

```python
class MarketResearchResult(BaseModel):
    ticker: str
    market_index: str
    market_return: float
    summary: str
```

例如：

```text
AAPL
S&P 500
8.5
Market conditions have been positive.
```

---

### 10. Step 2 — Mock Provider

在当前 Provider 层增加 Market 数据。

例如：

```python
def get_market_index(ticker: str) -> str:
    mock_market_index = {
        "AAPL": "S&P 500",
        "MSFT": "S&P 500",
    }

    try:
        return mock_market_index[ticker.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported ticker: {ticker}") from exc
```

以及：

```python
def get_market_return(ticker: str) -> float:
    mock_market_return = {
        "AAPL": 8.5,
        "MSFT": 8.5,
    }

    try:
        return mock_market_return[ticker.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported ticker: {ticker}") from exc
```

这里的数据仍然是：

```text
Mock Provider
```

不是现实市场数据。

这点和 Lesson 5 保持一致。

---

### 11. Step 3 — Market Tools

在：

```text
app/tools/financial.py
```

增加对应 Tool：

```python
@tool
def get_market_index(ticker: str) -> str:
    """Get the relevant market index for the given stock ticker."""
    return provider_get_market_index(ticker)
```

以及：

```python
@tool
def get_market_return(ticker: str) -> float:
    """Get the market return for the given stock ticker."""
    return provider_get_market_return(ticker)
```

注意这里仍然遵循：

```text
Tool
 ↓
Provider
```

Tool 不直接保存业务数据。

---

### 12. Step 4 — Agent Tool Set

在：

```text
app/agents/tool_sets.py
```

增加：

```python
MARKET_RESEARCH_TOOLS = [
    get_market_index,
    get_market_return,
]
```

现在 Tool Boundary 变成：

```text
COMPANY_RESEARCH_TOOLS
├── get_company_info
└── get_stock_price


FINANCIAL_RESEARCH_TOOLS
├── get_revenue
└── get_net_income


MARKET_RESEARCH_TOOLS
├── get_market_index
└── get_market_return
```

这时候我们已经可以清楚看到：

```text
Global Tool Registry
        │
        ├── Company Agent → Company Tool Set
        │
        ├── Financial Agent → Financial Tool Set
        │
        └── Market Agent → Market Tool Set
```

这正是 Lesson 4 Tool Boundary 的进一步应用。

---

### 13. Step 5 — Market Research Agent

新建：

```text
app/agents/market_research.py
```

整体结构保持和 Financial Agent 一致：

```text
MarketResearchInputState
        ↓
Market Research Agent
        ↓
Market Tool Loop
        ↓
Structured Output
        ↓
MarketResearchResult
```

核心代码结构：

```python
from typing import TypedDict

from app.agents.models import MarketResearchResult
from app.agents.tool_sets import MARKET_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
```

建立：

```python
class MarketResearchInputState(TypedDict):
    ticker: str
```

```python
class MarketResearchState(TypedDict):
    ticker: str
    research_result: MarketResearchResult | None
    research_error: str
```

```python
class MarketResearchOutputState(TypedDict):
    research_result: MarketResearchResult | None
    research_error: str
```

然后建立专属 Tool Loop：

```python
market_research_tool_loop = build_tool_loop_graph(
    MARKET_RESEARCH_TOOLS
)
```

Structured Output：

```python
structured_market_research_llm = llm.with_structured_output(
    MarketResearchResult
)
```

Agent 的基本执行流程保持：

```text
ticker
 ↓
Market Research Prompt
 ↓
Market Tool Loop
 ↓
Structured Market Research LLM
 ↓
MarketResearchResult
```

---

### 14. 一个重要设计点：不要复制粘贴错误

Lesson 5 的测试已经让我们发现了一个很典型的问题：

```python
patch("...structured_llm.invoke", ...)
```

不能直接这样 patch 当前 LangChain Runnable 的 `invoke`。

本课测试时继续使用：

```python
fake_structured_llm = MagicMock()
fake_structured_llm.invoke.return_value = fake_result
```

然后：

```python
patch(
    "...structured_market_research_llm",
    fake_structured_llm,
)
```

不要再使用：

```python
patch(
    "...structured_market_research_llm.invoke",
    ...
)
```

这个坑 Lesson 5 已经解决，本课不要重新踩。

---

### 15. Tests

本课测试分三个层次。

#### Test 1 — Provider

```text
tests/test_market_research_provider.py
```

验证：

```text
AAPL
 ↓
get_market_index
 ↓
"S&P 500"
```

以及：

```text
AAPL
 ↓
get_market_return
 ↓
8.5
```

同时测试 unsupported ticker。

---

#### Test 2 — Tools

```text
tests/test_market_research_tools.py
```

验证：

```text
Tool
 ↓
Provider
```

以及：

```text
Tool metadata
Tool name
Tool invocation
```

---

#### Test 3 — Agent

```text
tests/test_market_research_agent.py
```

至少覆盖：

##### Result Model

```text
MarketResearchResult
```

##### Agent Tool Loop

确认：

```text
Market Agent
        ↓
MARKET_RESEARCH_TOOLS
```

##### State Boundary

只向 Agent 提供：

```python
{
    "ticker": "AAPL"
}
```

##### Result Mapping

模拟：

```python
MarketResearchResult(...)
```

最终验证：

```python
result["research_result"] == fake_result
```

##### Error Mapping

验证：

```text
Tool Loop / structured research failure
        ↓
research_error
```

---

### 16. Tool Boundary Regression

继续修改：

```text
tests/test_agent_tool_boundary.py
```

最终应该明确验证：

```text
Company Tools
≠
Financial Tools
≠
Market Tools
```

例如：

```text
Company:
get_company_info
get_stock_price

Financial:
get_revenue
get_net_income

Market:
get_market_index
get_market_return
```

特别重要的是：

```text
Market Agent
```

**不能访问：**

```text
get_revenue
get_net_income
```

同样也不能访问：

```text
get_company_info
get_stock_price
```

除非未来业务需求明确改变其职责。

---

### 17. 本课暂时不要做什么

Lesson 6 做完以后，我们仍然**不要**：

```text
❌ 修改 Parent Graph
❌ Company + Financial + Market 串联
❌ Supervisor
❌ Router
❌ Parallel Agents
❌ Fan-out
❌ Fan-in
❌ Research Planner
❌ Investment Decision
❌ Valuation
❌ Risk Agent
```

当前架构应该保持：

```text
                    ┌─ Company Research Agent
                    │
START ──────────────┼─ Financial Research Agent
                    │
                    └─ Market Research Agent
```

但这三个 Agent **实际上还没有连接**。

这正是我们现在想要的状态。

---

### 18. Lesson 6 Acceptance Criteria

本课完成的标准：

#### Architecture

```text
Market Research Agent
        ↓
Market Tool Set
        ↓
Tool Loop
        ↓
Mock Provider
        ↓
MarketResearchResult
```

#### Isolation

```text
Company Agent
Financial Agent
Market Agent
```

三者 Tool Set 相互隔离。

#### State

Market Agent 只接受：

```text
ticker
```

并输出：

```text
research_result
research_error
```

#### Parent Graph

`app/graph/graph.py` **没有为了 Market Agent 被修改**。

#### Tests

本课新增/修改测试全部通过。

---

### 19. 当前 Phase 4 的架构位置

完成 Lesson 6 后，我们会得到：

```text
                    Research Agents
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
       Company         Financial        Market
       Research        Research        Research
          │               │               │
          ▼               ▼               ▼
       Company          Financial        Market
       Tools            Tools            Tools
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                    Tool / Provider
```

这一步非常关键。

我们现在已经从：

```text
"如何让 LLM 调 Tool？"
```

真正进入：

```text
"如何让多个职责明确的 Agent，各自完成自己的 Research Task？"
```

而**下一阶段真正值得研究的问题**才会变成：

```text
这些 Research Agents
如何被统一组织起来？
```

也就是后面的：

```text
Research Planner
        ↓
Company Research
Financial Research
Market Research
Industry / Macro Research
```

再之后才是 Phase 5 的 Multi-Agent Orchestration。

---


## Lesson 7：Industry / Macro Research Agent

Lesson 6（Market Research Agent）已经通过。现在继续按照 Phase 4 的主线，建立第四类独立 Research Agent。

这一步仍然**不进入 Supervisor、Multi-Agent、Parallel/Fan-out/Fan-in**，也不做 Research Data Normalization。我们继续练习一个核心能力：

> **一个具有明确业务职责的 Research Agent，如何拥有自己的 Tool Set，并完成独立的 Research Task。**

---

### 1. 本 Lesson 的目标

本 Lesson 建立：

```text
Industry / Macro Research Agent
```

它负责回答：

> “这家公司所处的行业以及宏观环境有哪些基础事实？”

例如：

```text
Ticker: AAPL

Industry: Technology
Industry Growth: 6.2%
Macro Environment: Expansion
Macro Growth: 2.8%
```

最终形成：

```text
Company Research Agent
Financial Research Agent
Market Research Agent
Industry / Macro Research Agent
```

四个相互独立的 Research Agent。

---

### 2. 为什么现在做 Industry / Macro Agent？

目前已经有：

```text
Company Agent
    ↓
公司是谁？

Financial Agent
    ↓
公司财务怎么样？

Market Agent
    ↓
市场表现怎么样？
```

还缺一个重要维度：

```text
Industry / Macro Agent
    ↓
公司所处的行业和宏观环境怎么样？
```

因此现在完成第四个独立 Research Agent 后，我们就拥有 Phase 4 中比较完整的基础 Research Agent 集合。

最终：

```text
                    Research
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Company        Financial       Market
        │              │              │
        └──────────────┼──────────────┘
                       │
                 Industry/Macro
```

**注意：现在仍然没有 Supervisor。**

---

### 3. 本 Lesson 不学习什么

这一点非常重要。

本 Lesson **不做**：

* Multi-Agent Supervisor
* Research Planner
* Agent Routing
* Parallel Research
* Fan-out / Fan-in
* Research Result Normalization
* Deterministic Computation
* Valuation
* Risk Analysis
* Investment Recommendation

这些属于后续阶段。

当前仍然是：

```text
一个 Agent
    ↓
自己的 Tool Set
    ↓
自己的 Research Result
```

---

### 4. Core Concept：Research Agent 的职责边界

现在四个 Agent 的职责应该越来越清楚。

| Agent                           | 负责什么       |
|---------------------------------|----------------|
| Company Research Agent          | 公司基本信息   |
| Financial Research Agent        | 财务数据       |
| Market Research Agent           | 市场表现       |
| Industry / Macro Research Agent | 行业与宏观环境 |

因此 Industry / Macro Agent **不能偷偷变成 Investment Agent**。

它可以：

```text
获取行业信息
获取宏观信息
总结行业/宏观环境
```

但不能：

```text
“因此应该买入”
“目标价是 $250”
“风险很低”
```

这些属于后面的研究/决策层。

---

### 5. Graph Topology

本 Lesson 的 Graph topology：

```text
START
  │
  ▼
industry_macro_research_agent
  │
  ▼
 END
```

Agent 内部：

```text
Industry / Macro Research Agent
            │
            ▼
       Research Prompt
            │
            ▼
        Tool Loop
        /        \
       /          \
Industry Tool   Macro Tool
      │              │
      ▼              ▼
Industry         Macro
Provider         Provider
      │              │
      └──────┬───────┘
             ▼
       Research Context
             │
             ▼
      Structured LLM
             │
             ▼
IndustryMacroResearchResult
```

这和前两个 Agent 的架构保持一致。

---

### 6. State Design

这里继续采用我们已经建立的：

```text
Input State
Internal State
Output State
```

#### Input

```python
class IndustryMacroResearchInputState(TypedDict):
    ticker: str
```

Agent 只需要：

```text
ticker
```

---

#### Internal State

```python
class IndustryMacroResearchState(TypedDict):
    ticker: str
    research_result: IndustryMacroResearchResult | None
    research_error: str
```

---

#### Output

```python
class IndustryMacroResearchOutputState(TypedDict):
    research_result: IndustryMacroResearchResult | None
    research_error: str
```

与 Company / Financial / Market Agent 保持统一。

---

### 7. Research Result

我们新增：

```python
IndustryMacroResearchResult
```

建议本 Lesson 使用：

```python
class IndustryMacroResearchResult(BaseModel):
    ticker: str
    industry: str
    industry_growth: float
    macro_environment: str
    macro_growth: float
    summary: str
```

这里的字段含义：

```text
ticker
    ↓
研究对象

industry
    ↓
行业名称

industry_growth
    ↓
行业增长率

macro_environment
    ↓
宏观环境描述

macro_growth
    ↓
宏观增长率

summary
    ↓
LLM 对上述事实的简洁总结
```

这里暂时**不要讨论这些数据应该由 Python 计算还是 LLM 计算**。本 Lesson 的重点依然是 Agent architecture。

---

### 8. Provider Layer

现在我们需要增加两个 Provider：

```text
IndustryInfoProvider
MacroEnvironmentProvider
```

继续使用 Mock Provider。

#### `app/providers/financial.py`

在现有 Provider 文件中增加：

```python
class IndustryInfoProvider(ABC):
    @abstractmethod
    def get_industry_info(self, ticker: str) -> dict:
        raise NotImplementedError


class MockIndustryInfoProvider(IndustryInfoProvider):
    def __init__(self):
        self.mock_industries = {
            "AAPL": {
                "ticker": "AAPL",
                "industry": "Consumer Electronics",
                "industry_growth": 6.2,
            },
            "MSFT": {
                "ticker": "MSFT",
                "industry": "Software",
                "industry_growth": 8.1,
            },
        }

    def get_industry_info(self, ticker: str) -> dict:
        if ticker not in self.mock_industries:
            raise ValueError(
                f"Industry information not found for ticker: {ticker}"
            )

        return self.mock_industries[ticker]


class MacroEnvironmentProvider(ABC):
    @abstractmethod
    def get_macro_environment(self, ticker: str) -> dict:
        raise NotImplementedError


class MockMacroEnvironmentProvider(MacroEnvironmentProvider):
    def __init__(self):
        self.mock_macro_environment = {
            "AAPL": {
                "ticker": "AAPL",
                "macro_environment": "Expansion",
                "macro_growth": 2.8,
            },
            "MSFT": {
                "ticker": "MSFT",
                "macro_environment": "Expansion",
                "macro_growth": 2.8,
            },
        }

    def get_macro_environment(self, ticker: str) -> dict:
        if ticker not in self.mock_macro_environment:
            raise ValueError(
                f"Macro environment not found for ticker: {ticker}"
            )

        return self.mock_macro_environment[ticker]
```

---

### 9. Tool Layer

然后在：

```text
app/tools/financial.py
```

增加两个 Tool。

```python
class IndustryInfoInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


industry_provider = MockIndustryInfoProvider()


@tool(args_schema=IndustryInfoInput)
def get_industry_info(ticker: str) -> dict:
    """Get basic industry information for a stock ticker."""
    try:
        return industry_provider.get_industry_info(ticker)
    except TransientProviderError as exc:
        raise TransientToolError(str(exc)) from exc
```

以及：

```python
class MacroEnvironmentInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


macro_environment_provider = MockMacroEnvironmentProvider()


@tool(args_schema=MacroEnvironmentInput)
def get_macro_environment(ticker: str) -> dict:
    """Get basic macroeconomic environment information for a stock ticker."""
    try:
        return macro_environment_provider.get_macro_environment(ticker)
    except TransientProviderError as exc:
        raise TransientToolError(str(exc)) from exc
```

---

### 10. Tool Set

然后修改：

```text
app/agents/tool_sets.py
```

增加：

```python
from app.tools.financial import (
    get_company_info,
    get_stock_price,
    get_revenue,
    get_net_income,
    get_market_index,
    get_market_return,
    get_industry_info,
    get_macro_environment,
)
```

并增加：

```python
INDUSTRY_MACRO_RESEARCH_TOOLS = [
    get_industry_info,
    get_macro_environment,
]
```

最终 Tool Set：

```text
COMPANY_RESEARCH_TOOLS
    ├── get_company_info
    └── get_stock_price

FINANCIAL_RESEARCH_TOOLS
    ├── get_revenue
    └── get_net_income

MARKET_RESEARCH_TOOLS
    ├── get_market_index
    └── get_market_return

INDUSTRY_MACRO_RESEARCH_TOOLS
    ├── get_industry_info
    └── get_macro_environment
```

这也是本 Lesson 一个非常重要的架构结果：

> **每一个 Research Agent 都有自己的 Tool Boundary。**

---

### 11. Model

修改：

```text
app/agents/models.py
```

增加：

```python
class IndustryMacroResearchResult(BaseModel):
    ticker: str = Field(description="Stock ticker symbol.")
    industry: str = Field(description="Industry associated with the company.")
    industry_growth: float = Field(
        description="Industry growth rate."
    )
    macro_environment: str = Field(
        description="Current macroeconomic environment."
    )
    macro_growth: float = Field(
        description="Macro-level growth rate."
    )
    summary: str = Field(
        description="Concise factual industry and macro research summary."
    )
```

---

### 12. Agent Prompt

新建：

```text
app/agents/industry_macro_research.py
```

核心 Prompt：

```python
industry_macro_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an Industry and Macro Research Agent. "
            "Your responsibility is to research the basic industry "
            "and macroeconomic environment for the given stock ticker. "
            "Use the available tools to obtain industry information "
            "and macroeconomic environment information. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent industry or macroeconomic data.",
        ),
        (
            "human",
            "Research the industry and macroeconomic environment "
            "for the following company and return a concise "
            "industry and macro research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)
```

---

### 13. 完整 Agent

完整文件：

```python
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.models import IndustryMacroResearchResult
from app.agents.tool_sets import INDUSTRY_MACRO_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
from app.llm.client import llm


class IndustryMacroResearchInputState(TypedDict):
    ticker: str


class IndustryMacroResearchState(TypedDict):
    ticker: str
    research_result: IndustryMacroResearchResult | None
    research_error: str


class IndustryMacroResearchOutputState(TypedDict):
    research_result: IndustryMacroResearchResult | None
    research_error: str


industry_macro_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an Industry and Macro Research Agent. "
            "Your responsibility is to research the basic industry "
            "and macroeconomic environment for the given stock ticker. "
            "Use the available tools to obtain industry information "
            "and macroeconomic environment information. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent industry or macroeconomic data.",
        ),
        (
            "human",
            "Research the industry and macroeconomic environment "
            "for the following company and return a concise "
            "industry and macro research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


industry_macro_research_tool_loop = build_tool_loop_graph(
    INDUSTRY_MACRO_RESEARCH_TOOLS
)


structured_industry_macro_research_llm = llm.with_structured_output(
    IndustryMacroResearchResult
)


def extract_tool_results(tool_result: dict) -> str:
    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(message.content for message in tool_messages)


def industry_macro_research_agent(
    state: IndustryMacroResearchState,
) -> IndustryMacroResearchState:
    ticker = state["ticker"]

    prompt_value = industry_macro_research_prompt.invoke(
        {"ticker": ticker}
    )

    try:
        tool_result = industry_macro_research_tool_loop.invoke(
            {"messages": prompt_value.messages}
        )

        research_context = extract_tool_results(tool_result)

        structured_result = (
            structured_industry_macro_research_llm.invoke(
                [
                    *prompt_value.messages,
                    HumanMessage(
                        content=(
                            "Tool results:\n"
                            f"{research_context}\n\n"
                            "Using only these tool results, "
                            "produce the structured industry and "
                            "macro research result."
                        )
                    ),
                ]
            )
        )

    except Exception as exc:
        return {
            "ticker": ticker,
            "research_result": None,
            "research_error": str(exc),
        }

    return {
        "ticker": ticker,
        "research_result": structured_result,
        "research_error": "",
    }


def build_industry_macro_research_graph():
    builder = StateGraph(
        IndustryMacroResearchState,
        input_schema=IndustryMacroResearchInputState,
        output_schema=IndustryMacroResearchOutputState,
    )

    builder.add_node(
        "industry_macro_research_agent",
        industry_macro_research_agent,
    )

    builder.add_edge(
        START,
        "industry_macro_research_agent",
    )

    builder.add_edge(
        "industry_macro_research_agent",
        END,
    )

    return builder.compile()


industry_macro_research_graph = build_industry_macro_research_graph()
```

---

### 14. 一个需要特别注意的地方

这里我们继续使用：

```python
llm.with_structured_output(
    IndustryMacroResearchResult
)
```

而不是：

```python
IndustryMacroResearchOutputState
```

这是上一 Lesson 已经踩过的坑，现在应该保持清晰：

```text
OutputState
    ↓
Graph 的边界

ResearchResult
    ↓
业务领域的数据结构
```

二者不是一回事。

---

### 15. Tests

本 Lesson 不跑整个历史测试套件。

按照我们之前约定，只测试：

1. Provider
2. Tool
3. Agent
4. Tool Boundary

---

#### Test 1 — Provider

新建：

```text
tests/test_industry_macro_research_provider.py
```

```python
import pytest

from app.providers.financial import (
    MockIndustryInfoProvider,
    MockMacroEnvironmentProvider,
)


def test_industry_info_provider_returns_mock_data():
    provider = MockIndustryInfoProvider()

    result = provider.get_industry_info("AAPL")

    assert result["industry"] == "Consumer Electronics"
    assert result["industry_growth"] == 6.2


def test_industry_info_provider_rejects_unknown_ticker():
    provider = MockIndustryInfoProvider()

    with pytest.raises(ValueError):
        provider.get_industry_info("UNKNOWN")


def test_macro_environment_provider_returns_mock_data():
    provider = MockMacroEnvironmentProvider()

    result = provider.get_macro_environment("AAPL")

    assert result["macro_environment"] == "Expansion"
    assert result["macro_growth"] == 2.8


def test_macro_environment_provider_rejects_unknown_ticker():
    provider = MockMacroEnvironmentProvider()

    with pytest.raises(ValueError):
        provider.get_macro_environment("UNKNOWN")
```

---

#### Test 2 — Tools

新建：

```text
tests/test_industry_macro_research_tools.py
```

```python
from app.tools.financial import (
    get_industry_info,
    get_macro_environment,
)


def test_get_industry_info_tool():
    result = get_industry_info.invoke(
        {"ticker": "AAPL"}
    )

    assert result["industry"] == "Consumer Electronics"
    assert result["industry_growth"] == 6.2


def test_get_macro_environment_tool():
    result = get_macro_environment.invoke(
        {"ticker": "AAPL"}
    )

    assert result["macro_environment"] == "Expansion"
    assert result["macro_growth"] == 2.8
```

---

#### Test 3 — Agent

新建：

```text
tests/test_industry_macro_research_agent.py
```

```python
from unittest.mock import MagicMock, patch

from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.models import IndustryMacroResearchResult


def test_industry_macro_research_graph_returns_expected_result():
    result = IndustryMacroResearchResult(
        ticker="AAPL",
        industry="Consumer Electronics",
        industry_growth=6.2,
        macro_environment="Expansion",
        macro_growth=2.8,
        summary=(
            "The company operates in a growing consumer "
            "electronics industry within an expansionary "
            "macro environment."
        ),
    )

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = {
        "messages": []
    }

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.industry_macro_research."
        "industry_macro_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.industry_macro_research."
        "structured_industry_macro_research_llm",
        fake_structured_llm,
    ):
        output = industry_macro_research_graph.invoke(
            {"ticker": "AAPL"}
        )

    assert output["research_result"] == result
    assert output["research_error"] == ""


def test_industry_macro_research_graph_maps_agent_failure():
    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.side_effect = RuntimeError(
        "Industry macro tool loop failed."
    )

    with patch(
        "app.agents.industry_macro_research."
        "industry_macro_research_tool_loop",
        fake_tool_loop,
    ):
        output = industry_macro_research_graph.invoke(
            {"ticker": "AAPL"}
        )

    assert output["research_result"] is None
    assert output["research_error"] == (
        "Industry macro tool loop failed."
    )


def test_industry_macro_research_agent_only_requires_ticker():
    result = IndustryMacroResearchResult(
        ticker="AAPL",
        industry="Consumer Electronics",
        industry_growth=6.2,
        macro_environment="Expansion",
        macro_growth=2.8,
        summary="Industry and macro conditions were positive.",
    )

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = {
        "messages": []
    }

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.industry_macro_research."
        "industry_macro_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.industry_macro_research."
        "structured_industry_macro_research_llm",
        fake_structured_llm,
    ):
        output = industry_macro_research_graph.invoke(
            {"ticker": "AAPL"}
        )

    assert output["research_result"].ticker == "AAPL"
```

这里继续使用上一 Lesson 已经验证过的正确 Mock 方法：

```python
fake_structured_llm = MagicMock()

with patch(
    "...structured_industry_macro_research_llm",
    fake_structured_llm,
):
```

而不是尝试直接 patch Runnable 的 `.invoke`。

---

#### Test 4 — Tool Boundary

继续修改：

```text
tests/test_agent_tool_boundary.py
```

增加：

```python
from app.agents.tool_sets import (
    COMPANY_RESEARCH_TOOLS,
    FINANCIAL_RESEARCH_TOOLS,
    MARKET_RESEARCH_TOOLS,
    INDUSTRY_MACRO_RESEARCH_TOOLS,
)


def test_industry_macro_research_tool_boundary():
    tool_names = {
        tool.name
        for tool in INDUSTRY_MACRO_RESEARCH_TOOLS
    }

    assert tool_names == {
        "get_industry_info",
        "get_macro_environment",
    }


def test_all_research_agent_tool_sets_are_disjoint():
    company_tools = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    financial_tools = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    market_tools = {
        tool.name
        for tool in MARKET_RESEARCH_TOOLS
    }

    industry_macro_tools = {
        tool.name
        for tool in INDUSTRY_MACRO_RESEARCH_TOOLS
    }

    tool_sets = [
        company_tools,
        financial_tools,
        market_tools,
        industry_macro_tools,
    ]

    for index, current_tools in enumerate(tool_sets):
        for other_tools in tool_sets[index + 1:]:
            assert current_tools.isdisjoint(other_tools)
```

---

### 16. 本 Lesson 的测试命令

只运行当前 Lesson：

```bash
pytest tests/test_industry_macro_research_provider.py -v
```

```bash
pytest tests/test_industry_macro_research_tools.py -v
```

```bash
pytest tests/test_industry_macro_research_agent.py -v
```

```bash
pytest tests/test_agent_tool_boundary.py -v
```

**暂时不要运行整个 `tests/`。**

---

### 17. Acceptance Criteria

本 Lesson 完成的判断标准：

#### Provider

* [ ] `MockIndustryInfoProvider` 工作
* [ ] `MockMacroEnvironmentProvider` 工作
* [ ] unknown ticker 正确失败

#### Tool

* [ ] `get_industry_info` 工作
* [ ] `get_macro_environment` 工作
* [ ] Tool 调用 Provider，而不是自己保存业务数据

#### Agent

* [ ] `IndustryMacroResearchAgent` 只需要 ticker
* [ ] Agent 拥有自己的 Tool Loop
* [ ] Agent 使用自己的 Tool Set
* [ ] Agent 输出 `IndustryMacroResearchResult`
* [ ] Agent 能正确映射失败
* [ ] 不进行 valuation / recommendation / risk analysis

#### Architecture

最终应该形成：

```text
Company Agent
    │
    └── Company Tools

Financial Agent
    │
    └── Financial Tools

Market Agent
    │
    └── Market Tools

Industry/Macro Agent
    │
    └── Industry/Macro Tools
```

---

### 18. 本 Lesson 最重要的理解

到 Lesson 7 为止，我们实际上完成了 Phase 4 一个非常重要的架构阶段：

```text
                    Research Agents
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
   Company            Financial           Market
   Agent               Agent              Agent
       │                  │                  │
       ▼                  ▼                  ▼
 Company Tools       Financial Tools    Market Tools
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
                 Industry / Macro
                      Agent
                          │
                          ▼
                Industry / Macro
                       Tools
```

现在的关键已经**不再是“LangGraph 怎么调用 Tool”**——Phase 3 已经解决了这个问题。

现在真正需要掌握的是：

> **如何把业务职责封装成独立 Research Agent，并让每个 Agent 拥有清晰、受约束的 Tool Boundary 和 Research Result。**

这正是 Phase 4 相对于 Phase 3 的核心变化。

**现在请按上面的修改完成 Lesson 7，然后只运行这 4 组测试。测试如果全部通过，我们直接进入下一 Lesson；如果失败，按照 `Error → Cause → Fix → Retest` 处理。**



## Lesson 8：Research Planner（已经废弃，在Phase 5中重新实现）

Lesson 7 完成后，我们已经拥有四个独立 Research Agent：

```text
Company Research Agent
Financial Research Agent
Market Research Agent
Industry / Macro Research Agent
```

现在开始 Phase 4 的下一层能力：

> **Research Planner：根据研究任务决定需要哪些 Research Agents。**

这一步非常重要，因为它是从：

```text
“我有几个独立 Agent”
```

进入：

```text
“我如何组织这些 Agent 完成一个 Research Task”
```

的第一步。

---

### 1. 本 Lesson 的目标

本 Lesson **只建立 Research Planner**。

Planner 的职责是：

```text
User Research Request
        │
        ▼
Research Planner
        │
        ▼
Research Plan
        │
        ├── Company Research
        ├── Financial Research
        ├── Market Research
        └── Industry / Macro Research
```

例如用户输入：

```text
Research AAPL for a long-term investment analysis.
```

Planner 可以生成：

```text
[
    "company",
    "financial",
    "market",
    "industry_macro"
]
```

但是：

> **Planner 本 Lesson 不执行这些 Agent。**

也就是说：

```text
Planner
   │
   └── 产生计划
```

而不是：

```text
Planner
   │
   ├── Company Agent
   ├── Financial Agent
   ├── Market Agent
   └── Industry Agent
```

后者属于下一阶段。

---

### 2. 为什么现在做 Planner？

到 Lesson 7 为止，我们的架构是：

```text
Company Agent
Financial Agent
Market Agent
Industry/Macro Agent
```

它们都是独立的。

问题来了：

> 如果用户提出一个完整的 Research Request，系统怎么知道应该调用哪些 Agent？

例如：

#### Request A

```text
“Tell me the basic information about Apple.”
```

可能只需要：

```text
Company Agent
```

#### Request B

```text
“Analyze Apple's financial condition.”
```

可能需要：

```text
Financial Agent
```

#### Request C

```text
“Research Apple comprehensively.”
```

可能需要：

```text
Company
Financial
Market
Industry/Macro
```

所以我们需要一个新的职责：

```text
Research Planner
```

它负责：

> **把自然语言 Research Request 转换成结构化 Research Plan。**

---

### 3. 本 Lesson 不做什么

这一步边界必须非常明确。

暂时不做：

* Supervisor
* Agent execution
* Parallel execution
* Fan-out
* Fan-in
* Agent result aggregation
* Research Data Normalization
* Deterministic Computation
* Investment Decision

所以：

```text
Planner ≠ Supervisor
```

这是本 Lesson 最重要的概念之一。

---

### 4. Planner 与 Supervisor 的区别

#### Research Planner

负责：

```text
“What research should be performed?”
```

也就是：

> **研究什么？**

例如：

```text
Company
Financial
Market
Industry/Macro
```

---

#### Supervisor

未来负责：

```text
“What should execute next?”
```

也就是：

> **现在让谁执行？**

甚至进一步：

```text
Company Agent
      ↓
Financial Agent
      ↓
Market Agent
      ↓
Industry Agent
      ↓
Aggregation
```

因此：

```text
Research Planner
    ↓
Research Plan

Supervisor
    ↓
Execution / Routing
```

两个职责必须分开。

---

### 5. Graph Topology

本 Lesson 的 Graph 非常简单：

```text
START
  │
  ▼
research_planner
  │
  ▼
 END
```

没有 Tool Loop。

没有 ToolNode。

没有 Research Agent。

因为 Planner 当前只是：

```text
User Request
    ↓
LLM
    ↓
Structured Research Plan
```

---

### 6. State Design

新增：

```text
app/agents/research_planner.py
```

我们采用和其他 Agent 一致的 Input / Internal / Output 分层。

#### Input State

```python
class ResearchPlannerInputState(TypedDict):
    user_query: str
```

---

#### Internal State

```python
class ResearchPlannerState(TypedDict):
    user_query: str
    research_plan: ResearchPlan | None
    research_error: str
```

---

#### Output State

```python
class ResearchPlannerOutputState(TypedDict):
    research_plan: ResearchPlan | None
    research_error: str
```

---

### 7. Research Plan Model

修改：

```text
app/agents/models.py
```

增加：

```python
from enum import Enum

class ResearchArea(str, Enum):
    COMPANY = "company"
    FINANCIAL = "financial"
    MARKET = "market"
    INDUSTRY_MACRO = "industry_macro"
```

然后：

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

这里的关键是：

```text
ResearchPlan
    ├── research_areas
    └── rationale
```

例如：

```python
ResearchPlan(
    research_areas=[
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
        ResearchArea.INDUSTRY_MACRO,
    ],
    rationale="A comprehensive company research requires..."
)
```

---

### 8. 为什么不用 `list[str]`？

我们当然可以：

```python
research_areas: list[str]
```

但这会允许：

```text
"company"
"financial"
"banana"
"random_agent"
```

进入系统。

而 Enum 将 Planner 的输出限制在：

```text
company
financial
market
industry_macro
```

因此：

```text
LLM
 ↓
Structured Output
 ↓
ResearchPlan
 ↓
Enum Validation
```

这就是我们已经在 Phase 3 / Phase 4 建立起来的：

> **让 LLM 输出受到业务 Schema 约束。**

---

### 9. Planner Prompt

新建：

```text
app/agents/research_planner.py
```

Prompt：

```python
research_planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Research Planning Agent for an "
            "investment research system. "
            "Your responsibility is to determine which "
            "research areas are required to answer the "
            "user's research request. "
            "Available research areas are: "
            "company, financial, market, and industry_macro. "
            "Select only the research areas that are relevant "
            "to the request. "
            "Do not perform the research yourself. "
            "Do not make an investment recommendation. "
            "Do not perform valuation or risk analysis.",
        ),
        (
            "human",
            "Create a research plan for the following request:\n\n"
            "{user_query}",
        ),
    ]
)
```

注意：

Planner 不需要任何 Tool。

---

### 10. Structured Output

继续使用我们已经验证过的模式：

```python
structured_research_planner_llm = llm.with_structured_output(
    ResearchPlan
)
```

因此：

```text
LLM
 ↓
ResearchPlan
```

而不是：

```text
LLM
 ↓
dict
```

---

### 11. 完整 `research_planner.py`

文件：

```text
app/agents/research_planner.py
```

完整代码：

```python
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.models import ResearchPlan
from app.llm.client import llm


class ResearchPlannerInputState(TypedDict):
    user_query: str


class ResearchPlannerState(TypedDict):
    user_query: str
    research_plan: ResearchPlan | None
    research_error: str


class ResearchPlannerOutputState(TypedDict):
    research_plan: ResearchPlan | None
    research_error: str


research_planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Research Planning Agent for an "
            "investment research system. "
            "Your responsibility is to determine which "
            "research areas are required to answer the "
            "user's research request. "
            "Available research areas are: "
            "company, financial, market, and industry_macro. "
            "Select only the research areas that are relevant "
            "to the request. "
            "Do not perform the research yourself. "
            "Do not make an investment recommendation. "
            "Do not perform valuation or risk analysis.",
        ),
        (
            "human",
            "Create a research plan for the following request:\n\n"
            "{user_query}",
        ),
    ]
)


structured_research_planner_llm = llm.with_structured_output(
    ResearchPlan
)


def research_planner(
    state: ResearchPlannerState,
) -> ResearchPlannerState:
    user_query = state["user_query"]

    prompt_value = research_planner_prompt.invoke(
        {"user_query": user_query}
    )

    try:
        research_plan = structured_research_planner_llm.invoke(
            prompt_value.messages
        )
    except Exception as exc:
        return {
            "user_query": user_query,
            "research_plan": None,
            "research_error": str(exc),
        }

    return {
        "user_query": user_query,
        "research_plan": research_plan,
        "research_error": "",
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

---

### 12. Tests

本 Lesson 我们重点测试三个东西：

```text
Model
Planner Success
Planner Failure
```

---

#### Test 1：Research Plan Model

新建：

```text
tests/test_research_planner_models.py
```

```python
from app.agents.models import ResearchArea, ResearchPlan


def test_research_plan_accepts_valid_research_areas():
    plan = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.FINANCIAL,
            ResearchArea.MARKET,
        ],
        rationale="A broad research request requires these areas.",
    )

    assert ResearchArea.COMPANY in plan.research_areas
    assert ResearchArea.FINANCIAL in plan.research_areas
    assert ResearchArea.MARKET in plan.research_areas


def test_research_plan_supports_industry_macro_area():
    plan = ResearchPlan(
        research_areas=[
            ResearchArea.INDUSTRY_MACRO,
        ],
        rationale="The request focuses on industry conditions.",
    )

    assert plan.research_areas == [
        ResearchArea.INDUSTRY_MACRO
    ]
```

---

#### Test 2：Planner

新建：

```text
tests/test_research_planner.py
```

```python
from unittest.mock import MagicMock, patch

from app.agents.models import (
    ResearchArea,
    ResearchPlan,
)
from app.agents.research_planner import (
    research_planner_graph,
)


def test_research_planner_returns_expected_plan():
    result = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.FINANCIAL,
            ResearchArea.MARKET,
            ResearchArea.INDUSTRY_MACRO,
        ],
        rationale=(
            "A comprehensive research request requires "
            "all available research areas."
        ),
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.research_planner."
        "structured_research_planner_llm",
        fake_structured_llm,
    ):
        output = research_planner_graph.invoke(
            {
                "user_query": (
                    "Conduct comprehensive research on AAPL."
                )
            }
        )

    assert output["research_plan"] == result
    assert output["research_error"] == ""


def test_research_planner_maps_llm_failure():
    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.side_effect = RuntimeError(
        "Research planner LLM failed."
    )

    with patch(
        "app.agents.research_planner."
        "structured_research_planner_llm",
        fake_structured_llm,
    ):
        output = research_planner_graph.invoke(
            {
                "user_query": "Research AAPL."
            }
        )

    assert output["research_plan"] is None
    assert output["research_error"] == (
        "Research planner LLM failed."
    )


def test_research_planner_accepts_only_user_query():
    result = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
        ],
        rationale="The request asks for basic company information.",
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.research_planner."
        "structured_research_planner_llm",
        fake_structured_llm,
    ):
        output = research_planner_graph.invoke(
            {
                "user_query": "Give me basic information about AAPL."
            }
        )

    assert output["research_plan"].research_areas == [
        ResearchArea.COMPANY
    ]
```

注意这里继续使用我们在 Lesson 5、6、7 已经验证过的：

```python
fake_structured_llm = MagicMock()

with patch(
    "...structured_research_planner_llm",
    fake_structured_llm,
):
```

不要直接 patch Runnable 对象的 `.invoke`。

---

### 13. Planner 的一个关键测试

我们还需要确认：

> Planner 本身不拥有 Research Tools。

新建：

```text
tests/test_research_planner_boundary.py
```

```python
from app.agents.research_planner import (
    research_planner_graph,
)


def test_research_planner_has_no_research_tool_loop():
    assert not hasattr(
        research_planner_graph,
        "tool_loop",
    )
```

不过这个测试对 LangGraph 编译后的对象来说比较弱。

因此更有价值的是直接检查源码级架构边界并保持设计：

```text
research_planner.py
    ↓
LLM
    ↓
ResearchPlan
```

而不是：

```text
research_planner.py
    ↓
Tool Loop
```

所以这里**不强制增加这个测试**。

当前 Lesson 的测试重点放在 Model + Planner 行为即可。

---

### 14. 测试命令

只运行当前 Lesson：

```bash
pytest tests/test_research_planner_models.py -v
```

```bash
pytest tests/test_research_planner.py -v
```

不要运行：

```bash
pytest
```

因为我们已经明确约定，不重复运行早期可能存在 obsolete assertion 的历史测试。

---

### 15. Acceptance Criteria

Lesson 8 完成条件：

#### Research Plan

* [ ] `ResearchArea` Enum 创建完成
* [ ] 支持四种 Research Area
* [ ] `ResearchPlan` Pydantic Model 创建完成
* [ ] Planner 只能产生定义好的 Research Area

#### Research Planner

* [ ] 只需要 `user_query`
* [ ] 使用真实 LLM 接口
* [ ] 使用 Structured Output
* [ ] 输出 `ResearchPlan`
* [ ] LLM failure 可以映射为 `research_error`
* [ ] 不调用任何 Research Tool
* [ ] 不执行任何 Research Agent

#### Architecture

必须保持：

```text
User Query
    │
    ▼
Research Planner
    │
    ▼
Research Plan
```

而不是：

```text
User Query
    │
    ▼
Research Planner
    │
    ├── Company Agent
    ├── Financial Agent
    ├── Market Agent
    └── Industry Agent
```

后者留到下一阶段。

---

### 16. 本 Lesson 最重要的理解

到这里，Phase 4 的架构开始发生第一次明显变化。

之前：

```text
User
 │
 ├── Company Agent
 ├── Financial Agent
 ├── Market Agent
 └── Industry/Macro Agent
```

现在增加：

```text
User
 │
 ▼
Research Planner
 │
 ▼
Research Plan
 │
 ├── Company
 ├── Financial
 ├── Market
 └── Industry/Macro
```

因此：

> **Research Planner 不是执行者，而是研究任务的结构化规划者。**

这为后续真正的 Multi-Agent Orchestration 铺路，但**本 Lesson 还没有进入 Multi-Agent Execution**。

---

### 当前 Phase 4 进度

```text
Phase 4 — Research Agents

Lesson 1  Company Research Agent          ✓
Lesson 2  Company Agent 深化              ✓
Lesson 3  Research Result / State         ✓
Lesson 4  Tool Set / Tool Loop Factory    ✓
Lesson 5  Financial Research Agent        ✓
Lesson 6  Market Research Agent           ✓
Lesson 7  Industry / Macro Agent         ✓
Lesson 8  Research Planner                ← 当前
```