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