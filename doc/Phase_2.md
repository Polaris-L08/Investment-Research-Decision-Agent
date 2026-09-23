# Phase 2 — LLM + Structured Output

## Lesson 1 — LLM Node

这一课只做一件事：

> **把一个真正的 LLM 调用放进我们已经存在的 LangGraph 中。**

Phase 1 我们已经解决了：

```text
Graph 怎么运行？
State 怎么传递？
Node 怎么更新 State？
```

Phase 2 开始解决：

```text
Agent 怎么通过 LLM 产生结果？
```

本 Lesson 暂时**不做 Structured Output**，也不做 Tool Calling。Structured Output 会在后面的 Lesson 单独引入。交接文档也明确要求 Phase 2 Lesson 1 先建立最简单的 LLM Node。

---

### 1. 本 Lesson 的目标

完成之后，我们希望 Graph 变成：

```text
InputState
    │
    ▼
initialize_state
    │
    ▼
LLM Node
    │
    ▼
GraphState
    │
    ▼
prepare_output
    │
    ▼
OutputState
```

其中：

```text
LLM Node
    │
    ├── 读取 GraphState
    │
    ├── 调用 LLM
    │
    └── 把 LLM response 写回 GraphState
```

---

### 2. 为什么现在学习这个

Phase 1 的 `create_research_plan()` 是硬编码的：

```python
def create_research_plan(state: GraphState) -> GraphState:
    return {
        "research_plan": [
            "Analyze company fundamentals",
            "Review financial performance",
            ...
        ],
    }
```

这虽然可以学习 LangGraph，但是它还不是 Agent。

真正的 Agent 应该逐渐变成：

```text
User Query
    ↓
LLM
    ↓
Research Plan
```

所以这一课的第一步就是把：

```text
Python function
```

替换成：

```text
LLM-powered Node
```

---

### 3. 核心概念：LLM 本身不是 Node

这是今天最重要的概念之一。

不要把：

```text
LLM
```

和：

```text
LangGraph Node
```

理解成同一个东西。

它们职责不同：

```text
LangGraph Node
    ↓
负责 Workflow / State

LLM
    ↓
负责生成模型响应
```

因此：

```python
def llm_node(state: GraphState) -> GraphState:
    response = llm.invoke(...)
    return {
        ...
    }
```

这里真正的 Node 是：

```python
llm_node
```

而：

```python
llm
```

只是 Node 使用的一个外部能力。

这和我们之后的 Tool Calling 架构是一致的：

```text
Graph Node
    ↓
LLM
    ↓
Tool
    ↓
External Provider
```

---

### 4. 本 Lesson 的一个重要设计选择

我们现在**不直接让 LLM 生成完整 `research_plan: list[str]`**。

原因很简单：

后面 Lesson 3 才学习：

```text
LLM
 ↓
Pydantic
 ↓
Structured Output
```

如果现在就让模型输出复杂结构，我们会同时遇到：

* Prompt
* JSON
* Parsing
* Validation
* Structured Output

这样会把多个概念混在一起。

所以 Lesson 1 故意保持简单：

```text
LLM → string
```

然后把这个 string 暂时写入一个 State 字段。

到了 Lesson 3，再正式升级成：

```text
LLM → Pydantic object
```

这是刻意的教学拆分，而不是最终架构。

---

### 5. Provider 怎么处理？

这里需要先做一个实际工程决定：

**我们需要一个可以调用的 LLM Provider。**

为了保持 Phase 2 和金融数据完全解耦，本阶段只需要一个普通 LLM。

如果你当前项目已经配置了 OpenAI API，那么我们直接使用 LangChain 的 OpenAI integration。

安装：

```bash
pip install -U langchain-openai
```

如果你的虚拟环境就是项目当前的 `.venv`，请确保这个命令是在项目虚拟环境中执行。

然后设置：

```text
OPENAI_API_KEY
```

例如 Windows PowerShell：

```powershell
$env:OPENAI_API_KEY="your-api-key"
```

或者使用项目自己的 `.env` 配置方式。

> **注意：不要把真实 API Key 写进代码，也不要把 API Key 提交到 Git。**

---

### 6. 第一个版本的 State

这里有一个实际问题。

当前 `GraphState` 没有专门存储 LLM response 的字段。

目前只有：

```python
research_plan
company_research
financial_research
market_research
industry_research
valuation_summary
...
```

Lesson 1 如果直接把 LLM response 塞进 `research_plan`，语义上是不太好的。

因此我们增加一个非常明确的字段：

```python
llm_response: str
```

这不是大规模重构，只是为了让 Lesson 1 有一个明确的实验输出位置。

---

### 7. 修改 `app/graph/state.py`

请将当前文件完整修改为：

```python
from typing import Literal, TypedDict


Recommendation = Literal[
    "Strong Buy",
    "Buy",
    "Hold",
    "Reduce",
    "Sell",
]


InvestmentHorizon = Literal[
    "Short Term",
    "Medium Term",
    "Long Term",
]


class InputState(TypedDict):
    user_query: str
    ticker: str


class GraphState(TypedDict):
    user_query: str
    ticker: str
    research_plan: list[str]
    company_research: str
    financial_research: str
    market_research: str
    industry_research: str
    valuation_summary: str
    current_price: float
    target_price: float
    risk_factors: list[str]
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    investment_thesis: str
    llm_response: str


class OutputState(TypedDict):
    ticker: str
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    current_price: float
    target_price: float
    investment_thesis: str
```

这里我们**没有把 `llm_response` 暴露到 `OutputState`**。

原因：

```text
llm_response
```

现在只是内部教学/中间状态。

未来真正的 Output 应该是结构化的业务结果，而不是把原始 LLM response 直接暴露给 API 用户。

这也符合 Phase 1 已经确定的：

```text
InputState
    ↓
GraphState
    ↓
OutputState
```

三层职责分离。

---

### 8. 修改 `app/graph/graph.py`

现在进入真正的 LLM Node。

完整文件：

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState, InputState, OutputState


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)


def initialize_state(state: InputState) -> GraphState:
    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
    }


def llm_node(state: GraphState) -> GraphState:
    prompt = (
        "You are an investment research assistant.\n"
        f"User question: {state['user_query']}\n"
        f"Ticker: {state['ticker']}\n\n"
        "In one concise paragraph, explain what should be researched "
        "about this company before making an investment decision."
    )

    response = llm.invoke(prompt)

    return {
        "llm_response": response.content,
    }


def prepare_output(state: GraphState) -> OutputState:
    return {
        "ticker": state["ticker"],
        "recommendation": state["recommendation"],
        "investment_horizon": state["investment_horizon"],
        "current_price": state["current_price"],
        "target_price": state["target_price"],
        "investment_thesis": state["investment_thesis"],
    }


builder = StateGraph(
    GraphState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node("initialize_state", initialize_state)
builder.add_node("llm_node", llm_node)
builder.add_node("prepare_output", prepare_output)

builder.add_edge(START, "initialize_state")
builder.add_edge("initialize_state", "llm_node")
builder.add_edge("llm_node", "prepare_output")
builder.add_edge("prepare_output", END)

graph = builder.compile()
```

---

### 9. 仔细理解这个 Node

核心代码只有：

```python
def llm_node(state: GraphState) -> GraphState:
```

它仍然是一个普通的 LangGraph Node。

所以它首先获得：

```python
state
```

然后从 State 中拿数据：

```python
state["user_query"]
state["ticker"]
```

构造 Prompt：

```python
prompt = (...)
```

然后：

```python
response = llm.invoke(prompt)
```

这一步才是真正发生 LLM 调用的地方。

最后：

```python
return {
    "llm_response": response.content,
}
```

把结果写回 State。

因此整个过程实际上是：

```text
GraphState
    │
    │ user_query
    │ ticker
    ▼
llm_node
    │
    ▼
Prompt
    │
    ▼
ChatOpenAI
    │
    ▼
AIMessage
    │
    ▼
response.content
    │
    ▼
llm_response
```

---

### 10. 一个非常重要的 LangGraph 原则再次出现

注意我们没有这样写：

```python
return {
    "user_query": state["user_query"],
    "ticker": state["ticker"],
    "llm_response": response.content,
}
```

而是：

```python
return {
    "llm_response": response.content,
}
```

原因和 Phase 1 Lesson 4 学到的一样：

> **Node 只返回自己负责更新的字段。**

交接文档中特别强调过，并且这个原则已经在并行 Node 的实践中验证过。

所以：

```text
initialize_state
    → 初始化 State

llm_node
    → 更新 llm_response

prepare_output
    → 构造 OutputState
```

职责非常清楚。

---

### 11. 为什么 `temperature=0`

这里：

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)
```

现在主要是为了教学和测试。

我们希望同样的输入尽可能得到稳定的输出。

目前我们不是在追求：

```text
creative writing
```

而是在测试：

```text
Graph
→ LLM
→ State
```

因此尽量减少不必要的随机性。

后续真正做 Investment Research 时，再讨论不同 Agent 是否应该采用不同模型参数。

---

### 12. 修改测试

现在测试不能再只验证：

```text
Graph 能运行
```

而要验证：

```text
Graph 确实调用了 LLM
```

但是这里有一个非常重要的工程原则：

> **单元测试不要因为外部 LLM API 不稳定而变得不可重复。**

所以我们这一步先使用 Mock。

这也符合项目已经确定的原则：

```text
先 Mock
↓
再接真实 Provider
```



---

### 13. `tests/test_graph.py`

完整测试文件：

```python
from unittest.mock import patch

from app.graph.graph import graph


def test_graph_calls_llm_and_returns_output():
    fake_response = type(
        "FakeResponse",
        (),
        {
            "content": (
                "Research the company's revenue growth, profitability, "
                "competitive position, balance sheet, valuation, and risks."
            )
        },
    )()

    with patch("langchain_openai.ChatOpenAI.invoke", return_value=fake_response) as mock_invoke:
        result = graph.invoke(
            {
                "user_query": "Research Apple as a long-term investment.",
                "ticker": "AAPL",
            }
        )

    mock_invoke.assert_called_once()

    assert result["ticker"] == "AAPL"
    assert result["recommendation"] == "Hold"
    assert result["investment_horizon"] == "Long Term"
    assert result["current_price"] == 0.0
    assert result["target_price"] == 0.0
    assert result["investment_thesis"] == ""
```

---

### 14. 为什么这个测试没有验证 `llm_response`

这里有一个非常值得注意的地方。

我们的：

```python
OutputState
```

目前没有：

```python
llm_response
```

所以：

```python
result = graph.invoke(...)
```

拿到的是：

```text
OutputState
```

而不是完整的内部 `GraphState`。

这正是我们在 Lesson 7 学到的：

```text
InputState
    ↓
GraphState
    ↓
OutputState
```

因此当前测试验证的是：

```text
LLM Node 被调用
        ↓
Graph 正常完成
        ↓
OutputState 正确产生
```

而不是直接暴露内部 State。

---

### 15. 但我们还需要测试 LLM Node 自身

否则：

```python
mock_invoke.assert_called_once()
```

只能证明它调用了 LLM。

我们还应该验证：

```text
Prompt
```

里面确实包含 State 数据。

因此再增加一个测试。

完整 `tests/test_graph.py`：

```python
from unittest.mock import patch

from app.graph.graph import graph


def test_graph_calls_llm_and_returns_output():
    fake_response = type(
        "FakeResponse",
        (),
        {
            "content": (
                "Research the company's revenue growth, profitability, "
                "competitive position, balance sheet, valuation, and risks."
            )
        },
    )()

    with patch("langchain_openai.ChatOpenAI.invoke", return_value=fake_response) as mock_invoke:
        result = graph.invoke(
            {
                "user_query": "Research Apple as a long-term investment.",
                "ticker": "AAPL",
            }
        )

    mock_invoke.assert_called_once()

    prompt = mock_invoke.call_args.args[0]

    assert "Research Apple as a long-term investment." in prompt
    assert "AAPL" in prompt

    assert result["ticker"] == "AAPL"
    assert result["recommendation"] == "Hold"
    assert result["investment_horizon"] == "Long Term"
    assert result["current_price"] == 0.0
    assert result["target_price"] == 0.0
    assert result["investment_thesis"] == ""


def test_graph_uses_llm_response():
    fake_response = type(
        "FakeResponse",
        (),
        {
            "content": "This is a mocked LLM response.",
        },
    )()

    with patch("langchain_openai.ChatOpenAI.invoke", return_value=fake_response):
        result = graph.invoke(
            {
                "user_query": "Analyze Microsoft as a long-term investment.",
                "ticker": "MSFT",
            }
        )

    assert result["ticker"] == "MSFT"
```

这里第二个测试看起来没有直接验证：

```python
"This is a mocked LLM response."
```

这是因为当前 `OutputState` 没有暴露：

```python
llm_response
```

**这是刻意的。**

我们暂时不为了测试方便破坏 State 分层。

---

### 16. 运行测试

在项目根目录执行：

```bash
pytest -q
```

预期：

```text
2 passed
```

如果你 Phase 1 原来的测试还保留在项目中，那么实际数量应该会高于 2。

例如：

```text
9 passed
```

或者：

```text
10 passed
```

都没有问题。

真正的 Acceptance Criteria 是：

```text
所有现有测试通过
+
新增 LLM Node 测试通过
```

---

### 17. 再做一次真实 LLM 手工运行

测试使用 Mock。

但我们还需要确认：

> **真实 Provider 到底能不能工作。**

这一步不是单元测试，而是 Integration Smoke Test。

可以临时在项目根目录创建：

```text
test_llm_manual.py
```

内容：

```python
from app.graph.graph import graph


result = graph.invoke(
    {
        "user_query": "Research Apple as a long-term investment.",
        "ticker": "AAPL",
    }
)

print(result)
```

然后：

```bash
python test_llm_manual.py
```

如果 API Key 和模型配置正确，Graph 应该成功执行。

输出应该至少包含类似：

```python
{
    "ticker": "AAPL",
    "recommendation": "Hold",
    "investment_horizon": "Long Term",
    "current_price": 0.0,
    "target_price": 0.0,
    "investment_thesis": ""
}
```

注意：

**当前输出看不到 `llm_response` 是正常的。**

因为：

```text
llm_response
```

是：

```text
GraphState internal field
```

而：

```text
OutputState
```

没有暴露它。

这正是我们设计 State 分层的意义。

---

### 18. 一个值得你现在理解的架构变化

Phase 1：

```text
START
  ↓
initialize_state
  ↓
create_research_plan
  ↓
prepare_output
  ↓
END
```

现在：

```text
START
  ↓
initialize_state
  ↓
llm_node
  ↓
prepare_output
  ↓
END
```

变化看起来非常小。

但是系统能力发生了关键变化：

#### Phase 1

```text
Python
    ↓
固定结果
```

#### Phase 2

```text
State
    ↓
Prompt
    ↓
LLM
    ↓
Response
    ↓
State
```

这才是我们真正开始进入 Agent 的地方。

---

### 19. 当前还没有解决的问题

这一课故意留下几个问题。

#### 问题 1：LLM 返回的是自由文本

现在：

```text
LLM
 ↓
str
```

所以模型完全可能返回：

```text
I think Apple is interesting...
```

甚至返回：

```text
123456
```

我们没有严格约束。

---

#### 问题 2：没有 Pydantic

现在还没有：

```python
BaseModel
```

所以没有真正的 Schema Validation。

---

#### 问题 3：没有 Enum Validation

未来我们要求：

```text
Strong Buy
Buy
Hold
Reduce
Sell
```

但现在 LLM 根本没有机会生成：

```text
Recommendation
```

所以也还不存在这个问题。

---

#### 问题 4：没有 Retry

如果：

```text
LLM API failure
```

当前 Graph 会直接失败。

我们暂时不处理。

因为：

```text
Invalid Output Handling
Retry / Recovery
```

属于后面的 Lesson。

这正符合当前 Phase 2 的渐进式路线。

---

### 20. Acceptance Criteria

Lesson 1 完成的标准：

#### 必须满足

```text
☑ ChatOpenAI 可以初始化
☑ Graph 中存在 llm_node
☑ llm_node 可以读取 GraphState
☑ llm_node 可以构造 Prompt
☑ llm_node 可以调用 LLM
☑ LLM response 可以写回 GraphState
☑ Node 只更新自己负责的字段
☑ OutputState 没有被内部 llm_response 污染
☑ LLM 调用可以通过 Mock 测试
☑ 所有 Phase 1 测试继续通过
☑ 真实 LLM Smoke Test 可以运行
```

---

### 21. 本 Lesson 最重要的 5 个理解

#### ① LLM 不是 LangGraph Node

```text
Node = Workflow / State operation

LLM = Node 使用的能力
```

---

#### ② Node 是 LLM 和 State 之间的桥梁

```text
State
 ↓
Node
 ↓
Prompt
 ↓
LLM
 ↓
Response
 ↓
Node
 ↓
State
```

---

#### ③ 当前先接受自由文本

现在：

```text
LLM → str
```

后面才升级：

```text
LLM → Pydantic
```

---

#### ④ Mock 和真实 LLM 是两件事

单元测试：

```text
Mock LLM
```

验证：

```text
Graph logic
```

Smoke Test：

```text
Real LLM
```

验证：

```text
Provider integration
```

这是后续工程化测试非常重要的基础。

---

#### ⑤ OutputState 不是“所有 State 的副本”

它是：

```text
对外 API contract
```

内部可以有：

```text
llm_response
research_plan
raw research
intermediate data
```

但不代表这些东西都应该暴露给最终用户。

---

### 22. 现在执行

按顺序执行：

```bash
pip install -U langchain-openai
```

配置：

```text
OPENAI_API_KEY
```

然后：

```bash
pytest -q
```

最后运行真实 LLM Smoke Test：

```bash
python test_llm_manual.py
```


## Lesson 2：Prompt + LLM Node

这一课我们不引入新的架构，也不接真实金融数据。目标非常明确：

> 把 Lesson 1 中“直接拼接字符串”的 LLM 调用，升级成 **Prompt Template → LLM** 的标准链路。

### 一、先明确本课要解决什么问题

Lesson 1 的 `llm_node` 大致是：

```python
prompt = f"""
Analyze the company {state["ticker"]}.
User request: {state["user_query"]}
"""

response = llm.invoke(prompt)
```

它可以工作，但存在一个明显问题：

**Prompt 和业务代码混在一起。**

随着项目发展，我们会出现：

```text
Company Research Prompt
Financial Research Prompt
Market Research Prompt
Industry Research Prompt
Valuation Prompt
Risk Prompt
Investment Decision Prompt
Report Prompt
```

如果每个 Node 都自己：

```python
prompt = f"""..."""
```

很快就会变得难以维护。

所以这一课开始把：

```text
Prompt
```

作为一个独立概念处理。

---

### 二、这一课的核心结构

我们希望形成：

```text
GraphState
    │
    ├── ticker
    └── user_query
          │
          ▼
   Prompt Template
          │
          ▼
      formatted prompt
          │
          ▼
      ChatOpenAI
          │
          ▼
      AI response
          │
          ▼
    llm_response
```

注意：

**Prompt Template 不是 LLM。**

它只是负责：

> 把变量填入 Prompt。

例如：

```text
Ticker: AAPL
User request: Analyze Apple as a long-term investment
```

---

### 三、第一步：安装 Prompt 相关组件

如果你已经安装了 `langchain-openai`，通常不需要额外安装。

LangChain 的 Prompt Template 在核心包中。

可以先确认：

```bash
pip show langchain-core
```

你之前的 traceback 已经显示：

```text
langchain-core 1.6.4
```

所以当前环境已经具备所需组件。

---

### 四、第二步：创建 Prompt Template

我们先修改：

```text
app/graph/graph.py
```

增加：

```python
from langchain_core.prompts import ChatPromptTemplate
```

然后定义 Prompt：

```python
llm_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment research assistant. "
            "Provide concise and factual research guidance.",
        ),
        (
            "human",
            "Analyze the following investment research request.\n\n"
            "Ticker: {ticker}\n"
            "User request: {user_query}",
        ),
    ]
)
```

这里出现了两个变量：

```text
{ticker}
{user_query}
```

它们不是 Python f-string。

这是 **Prompt Template 的变量占位符**。

---

### 五、这里一定要理解 `system` 和 `human`

我们现在使用：

```python
ChatPromptTemplate.from_messages(...)
```

里面有：

```python
("system", ...)
("human", ...)
```

对应的是 Chat Model 的消息结构：

```text
System Message
    ↓
定义模型角色、行为、规则

Human Message
    ↓
具体用户任务
```

例如：

```text
SYSTEM:
You are an investment research assistant.

HUMAN:
Ticker: AAPL
User request: Analyze Apple as a long-term investment.
```

然后：

```python
llm.invoke(...)
```

接收到的是一组结构化消息，而不是简单的一段字符串。

这是后面做 Agent Prompt 时非常重要的基础。

---

### 六、第三步：修改 `llm_node`

原来的逻辑大概是：

```python
def llm_node(state: GraphState) -> GraphState:
    prompt = f"""
    ...
    """

    response = llm.invoke(prompt)

    return {
        "llm_response": response.content,
    }
```

现在改成：

```python
def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = llm.invoke(prompt_value)

    return {
        "llm_response": response.content,
    }
```

这里发生了两个动作。

第一步：

```python
prompt_value = llm_prompt.invoke(...)
```

是：

```text
变量
 ↓
Prompt Template
 ↓
Prompt Value
```

第二步：

```python
response = llm.invoke(prompt_value)
```

是：

```text
Prompt Value
 ↓
LLM
 ↓
Response
```

---

### 七、为什么不是直接 `.format()`？

你可能会想到：

```python
prompt = llm_prompt.format(
    ticker=state["ticker"],
    user_query=state["user_query"],
)
```

这不是不能用。

但是对于 Chat Prompt，我们现在更希望保留：

```text
system message
human message
```

这样的消息结构。

因此使用：

```python
llm_prompt.invoke(...)
```

更符合我们现在的 LangChain Chat Model 工作方式。

最终：

```python
prompt_value
```

里面仍然保留：

```text
SystemMessage
HumanMessage
```

这样的结构。

这对后面：

```text
Tool Calling
Structured Output
Agent
Multi-Agent
```

都非常重要。

---

### 八、第四步：给你一份完整的 `graph.py`

为了避免你局部修改时遗漏，我建议 Lesson 2 直接把当前文件整理成下面这个完整版本。

```python
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState, InputState, OutputState


load_dotenv()


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0,
)


llm_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment research assistant. "
            "Provide concise and factual research guidance.",
        ),
        (
            "human",
            "Analyze the following investment research request.\n\n"
            "Ticker: {ticker}\n"
            "User request: {user_query}",
        ),
    ]
)


def initialize_state(state: InputState) -> GraphState:
    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
    }


def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = llm.invoke(prompt_value)

    return {
        "llm_response": response.content,
    }


def create_research_plan(state: GraphState) -> GraphState:
    return {
        "research_plan": [
            "Analyze company fundamentals",
            "Review financial performance",
            "Analyze market conditions",
            "Analyze industry conditions",
            "Perform valuation analysis",
            "Identify major risks",
        ],
    }


def prepare_output(state: GraphState) -> OutputState:
    return {
        "ticker": state["ticker"],
        "recommendation": state["recommendation"],
        "investment_horizon": state["investment_horizon"],
        "current_price": state["current_price"],
        "target_price": state["target_price"],
        "investment_thesis": state["investment_thesis"],
    }


builder = StateGraph(
    GraphState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node("initialize_state", initialize_state)
builder.add_node("llm_node", llm_node)
builder.add_node("create_research_plan", create_research_plan)
builder.add_node("prepare_output", prepare_output)

builder.add_edge(START, "initialize_state")
builder.add_edge("initialize_state", "llm_node")
builder.add_edge("llm_node", "create_research_plan")
builder.add_edge("create_research_plan", "prepare_output")
builder.add_edge("prepare_output", END)

graph = builder.compile()
```

---

### 九、这里有一个重要的架构细节

你可能注意到：

```text
initialize_state
       ↓
   llm_node
       ↓
create_research_plan
```

现在我们的 LLM Response 仍然只是：

```python
llm_response: str
```

它没有进入：

```python
OutputState
```

这是**故意的**。

因为现在我们只是学习：

> LLM 如何进入 Graph。

还没有进入：

> LLM 如何产生可靠的业务结构化数据。

后面 Lesson 3 才开始：

```text
LLM
 ↓
Structured Output
 ↓
Pydantic
```

所以现在不要急着把 `llm_response` 改成复杂对象。

---

### 十、第五步：测试 Prompt Template

Lesson 1 我们测试的是：

```text
LLM 有没有被调用？
```

Lesson 2 增加一个新的问题：

> Prompt 中的 `ticker` 和 `user_query` 是否真的被正确注入？

这一次测试非常重要。

修改：

```text
tests/test_graph.py
```

建议使用：

```python
from unittest.mock import MagicMock, patch

from app.graph.graph import graph


def test_graph_calls_llm_with_formatted_prompt():
    fake_response = MagicMock()
    fake_response.content = "Mocked investment research response."

    with patch(
        "langchain_openai.ChatOpenAI.invoke",
        return_value=fake_response,
    ) as mock_invoke:

        result = graph.invoke(
            {
                "user_query": "Analyze Apple as a long-term investment",
                "ticker": "AAPL",
            }
        )

    mock_invoke.assert_called_once()

    prompt_value = mock_invoke.call_args.args[0]

    prompt_text = "\n".join(
        message.content
        for message in prompt_value.messages
    )

    assert "AAPL" in prompt_text
    assert "Analyze Apple as a long-term investment" in prompt_text

    assert result["ticker"] == "AAPL"
```

---

### 十一、这段测试值得认真理解

尤其是：

```python
prompt_value = mock_invoke.call_args.args[0]
```

你已经学过：

```python
mock_invoke.assert_called_once()
```

现在进一步学习：

```python
mock_invoke.call_args
```

它可以让我们看到：

> Mock 到底收到了什么参数。

我们的实际调用：

```python
llm.invoke(prompt_value)
```

因此：

```python
mock_invoke.call_args.args[0]
```

就是：

```python
prompt_value
```

---

### 十二、为什么不能直接这样？

你可能会写：

```python
assert "AAPL" in mock_invoke.call_args.args[0]
```

不建议。

因为：

```python
prompt_value
```

不是普通字符串。

它是一个：

```text
ChatPromptValue
```

里面包含多个 message。

所以我们转换成：

```python
prompt_text = "\n".join(
    message.content
    for message in prompt_value.messages
)
```

之后再：

```python
assert "AAPL" in prompt_text
```

这才是在检查：

```text
System Message
+
Human Message
```

里面的实际内容。

---

### 十三、再增加一个更直接的 Prompt 单元测试

我建议 Lesson 2 再单独测试 Prompt。

在：

```text
tests/test_graph.py
```

增加：

```python
from app.graph.graph import llm_prompt
```

然后：

```python
def test_llm_prompt_injects_variables():
    prompt_value = llm_prompt.invoke(
        {
            "ticker": "AAPL",
            "user_query": "Evaluate Apple's competitive position.",
        }
    )

    prompt_text = "\n".join(
        message.content
        for message in prompt_value.messages
    )

    assert "AAPL" in prompt_text
    assert "Evaluate Apple's competitive position." in prompt_text
```

于是我们有两层测试：

#### Prompt 层

```text
Prompt Template
      ↓
变量正确注入？
```

#### Graph 层

```text
Graph
 ↓
Prompt
 ↓
LLM Mock
 ↓
State
```

这是非常好的测试边界。

---

### 十四、现在运行测试

执行：

```bash
pytest -v
```

你应该看到类似：

```text
tests/test_graph.py::test_graph_calls_llm_with_formatted_prompt PASSED
tests/test_graph.py::test_llm_prompt_injects_variables PASSED
```

以及你之前已有的 Phase 1 测试全部保持通过。

---

### 十五、本课验收标准

Lesson 2 只有在下面全部满足后才算完成：

#### A. Prompt

* [ ] 使用 `ChatPromptTemplate`
* [ ] 有 `system` message
* [ ] 有 `human` message
* [ ] 使用 `{ticker}`
* [ ] 使用 `{user_query}`

#### B. LLM Node

* [ ] Node 从 `GraphState` 获取变量
* [ ] Prompt Template 注入变量
* [ ] Prompt Value 传给 `llm.invoke()`
* [ ] LLM Response 写入 `llm_response`

#### C. Testing

* [ ] 不调用真实 LLM
* [ ] 使用 `patch`
* [ ] 使用 `MagicMock`
* [ ] 验证 LLM 被调用
* [ ] 验证 ticker 被注入
* [ ] 验证 user query 被注入
* [ ] Prompt 可以独立测试

#### D. Architecture

最终链路应该是：

```text
InputState
    │
    ▼
initialize_state
    │
    ▼
GraphState
    │
    ▼
llm_prompt
    │
    ├── ticker
    └── user_query
    │
    ▼
ChatOpenAI
    │
    ▼
llm_response
    │
    ▼
create_research_plan
    │
    ▼
prepare_output
    │
    ▼
OutputState
```

---

### 本课最重要的三个知识点

你这一次不要只记代码，重点理解这三个东西：

**① Prompt Template**

```python
ChatPromptTemplate
```

负责：

> **把业务变量组织成模型输入。**

**② Chat Prompt 的 Message Structure**

```text
system
human
```

负责：

> **区分模型行为规则和具体任务。**

**③ Mock 的 `call_args`**

```python
mock_invoke.call_args
```

负责：

> **验证测试中的 LLM 实际收到了什么。**

---


## Lesson 3：Pydantic Structured Output

这一课是整个 Phase 2 的关键转折点。

到 Lesson 2 为止，我们得到的是：

```text
User Request
    ↓
Prompt Template
    ↓
LLM
    ↓
普通字符串
```

但我们的最终产品是 **Investment Decision Agent**。

我们最终需要的不是：

```text
"Apple looks attractive because..."
```

而是类似：

```text
{
    "summary": "...",
    "key_factors": [...],
    "risk_level": "Medium",
    "investment_horizon": "Long Term"
}
```

所以这一课开始进入：

```text
LLM
 ↓
Structured Output
 ↓
Pydantic Model
```

---

### 一、为什么需要 Structured Output？

这是我们项目中一个非常重要的工程问题。

假设我们让 LLM 返回：

```text
Apple has strong revenue growth.
Its services business remains attractive.
However, valuation is relatively high.
The major risks are...
```

人可以理解。

但是 Python 很难可靠地处理：

```python
response.content
```

因为它只是：

```python
str
```

如果下一步要做：

```text
Risk Agent
    ↓
Valuation Agent
    ↓
Investment Decision Agent
```

我们希望程序能够明确知道：

```text
summary       → str
key_factors   → list[str]
risk_level    → 某几个允许值
```

这就是 Structured Output 的价值。

---

### 二、Pydantic 在这里负责什么？

我们先定义一个 Python 数据模型：

```python
class ResearchSummary(BaseModel):
    summary: str
    key_factors: list[str]
```

那么：

```text
LLM
 ↓
Structured Output
 ↓
ResearchSummary
```

之后 Python 得到的就不是任意字符串，而是一个结构化对象。

例如：

```python
result.summary
result.key_factors
```

而不是：

```python
result.content
```

---

### 三、为什么选择 Pydantic？

因为我们的项目后面会大量依赖：

* 类型约束
* 字段定义
* 数据验证
* Enum / Literal
* Nested Model
* Structured Output
* 最终投资决策 Schema

而 Pydantic 正好适合做这一层。

所以 Phase 2 后面的路线实际上会逐渐变成：

```text
Pydantic Model
      ↓
LLM Structured Output
      ↓
GraphState
      ↓
Validation
      ↓
Investment Decision
```

---

### 四、Lesson 3 的目标

这一课我们暂时**不修改整个 GraphState 的业务结构**。

只做一件事情：

> 创建第一个 Pydantic Structured Output Model，并让 ChatOpenAI 返回这个结构。

我们先定义：

```python
ResearchSummary
```

它代表：

> LLM 对投资研究请求产生的基础研究摘要。

---

### 五、第一步：创建 Pydantic Model

建议在：

```text
app/
└── graph/
    ├── __init__.py
    ├── graph.py
    └── state.py
```

中新增：

```text
app/graph/models.py
```

暂时不要建立更多目录。

---

#### `app/graph/models.py`

完整内容：

```python
from pydantic import BaseModel, Field


class ResearchSummary(BaseModel):
    summary: str = Field(
        description="A concise summary of the investment research."
    )

    key_factors: list[str] = Field(
        description="The key factors that materially affect the investment analysis."
    )
```

现在我们有了：

```text
ResearchSummary
├── summary: str
└── key_factors: list[str]
```

---

### 六、理解 `BaseModel`

这一行：

```python
class ResearchSummary(BaseModel):
```

意味着：

```text
ResearchSummary
```

是一个 Pydantic Model。

例如：

```python
research = ResearchSummary(
    summary="Strong business fundamentals.",
    key_factors=[
        "Revenue growth",
        "Profitability",
        "Competitive position",
    ],
)
```

之后：

```python
research.summary
```

得到：

```text
Strong business fundamentals.
```

而：

```python
research.key_factors
```

得到：

```python
[
    "Revenue growth",
    "Profitability",
    "Competitive position",
]
```

---

### 七、`Field(description=...)` 是干什么的？

你现在看到：

```python
summary: str = Field(
    description="A concise summary of the investment research."
)
```

不要把它理解成普通注释。

它是 Schema 的一部分。

最终 Pydantic 可以表达类似：

```text
summary
    type: string
    description: A concise summary...

key_factors
    type: array
    items: string
```

这对 LLM Structured Output 非常重要。

因为模型需要知道：

> 你希望它输出什么结构。

所以：

```text
Pydantic Model
        ↓
Schema
        ↓
LLM
```

这是后面 Structured Output 的核心机制之一。

---

### 八、第二步：让 LLM 使用 Structured Output

现在回到：

```text
app/graph/graph.py
```

原来：

```python
llm = ChatOpenAI(...)
```

之后直接：

```python
response = llm.invoke(prompt_value)
```

现在我们创建一个 Structured LLM：

```python
structured_llm = llm.with_structured_output(ResearchSummary)
```

所以需要增加：

```python
from app.graph.models import ResearchSummary
```

然后：

```python
structured_llm = llm.with_structured_output(ResearchSummary)
```

---

### 九、这里非常重要：`llm` 和 `structured_llm` 不一样

现在代码里会同时存在：

```python
llm
```

和：

```python
structured_llm
```

理解它们的区别：

#### 普通 LLM

```python
response = llm.invoke(prompt_value)
```

返回：

```text
AIMessage
```

通常：

```python
response.content
```

是字符串。

---

#### Structured LLM

```python
response = structured_llm.invoke(prompt_value)
```

返回：

```text
ResearchSummary
```

也就是：

```python
response.summary
response.key_factors
```

所以：

```text
普通：

LLM
 ↓
AIMessage
 ↓
content: str


Structured：

LLM
 ↓
ResearchSummary
 ↓
summary
key_factors
```

这就是本课最核心的变化。

---

### 十、修改 `llm_node`

原来的：

```python
def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = llm.invoke(prompt_value)

    return {
        "llm_response": response.content,
    }
```

改成：

```python
def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = structured_llm.invoke(prompt_value)

    return {
        "llm_response": response.summary,
    }
```

注意：

我们现在**仍然把 `llm_response` 定义为 `str`**。

这是刻意的。

Lesson 3 的重点是：

```text
LLM → Pydantic
```

而不是现在就把整个 GraphState 重构掉。

---

### 十一、完整 `graph.py`

为了保持我们之前的教学方式，这里给你当前 Lesson 3 的完整文件。

```python
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.graph.models import ResearchSummary
from app.graph.state import GraphState, InputState, OutputState


load_dotenv()


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0,
)


structured_llm = llm.with_structured_output(ResearchSummary)


llm_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment research assistant. "
            "Provide concise and factual research guidance.",
        ),
        (
            "human",
            "Analyze the following investment research request.\n\n"
            "Ticker: {ticker}\n"
            "User request: {user_query}",
        ),
    ]
)


def initialize_state(state: InputState) -> GraphState:
    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
    }


def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = structured_llm.invoke(prompt_value)

    return {
        "llm_response": response.summary,
    }


def create_research_plan(state: GraphState) -> GraphState:
    return {
        "research_plan": [
            "Analyze company fundamentals",
            "Review financial performance",
            "Analyze market conditions",
            "Analyze industry conditions",
            "Perform valuation analysis",
            "Identify major risks",
        ],
    }


def prepare_output(state: GraphState) -> OutputState:
    return {
        "ticker": state["ticker"],
        "recommendation": state["recommendation"],
        "investment_horizon": state["investment_horizon"],
        "current_price": state["current_price"],
        "target_price": state["target_price"],
        "investment_thesis": state["investment_thesis"],
    }


builder = StateGraph(
    GraphState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node("initialize_state", initialize_state)
builder.add_node("llm_node", llm_node)
builder.add_node("create_research_plan", create_research_plan)
builder.add_node("prepare_output", prepare_output)

builder.add_edge(START, "initialize_state")
builder.add_edge("initialize_state", "llm_node")
builder.add_edge("llm_node", "create_research_plan")
builder.add_edge("create_research_plan", "prepare_output")
builder.add_edge("prepare_output", END)

graph = builder.compile()
```

---

### 十二、现在遇到一个非常重要的测试问题

Lesson 2 我们测试：

```python
ChatOpenAI.invoke
```

但现在：

```python
llm_node
```

调用的是：

```python
structured_llm.invoke()
```

而：

```python
structured_llm
```

是：

```python
llm.with_structured_output(ResearchSummary)
```

产生的 Runnable。

所以我们**不能简单地继续 patch：**

```python
langchain_openai.ChatOpenAI.invoke
```

来模拟最终结果。

这是一个非常值得你理解的变化：

```text
Lesson 2:

ChatOpenAI
    ↓
invoke()
    ↓
AIMessage


Lesson 3:

ChatOpenAI
    ↓
with_structured_output()
    ↓
Runnable
    ↓
invoke()
    ↓
ResearchSummary
```

因此测试策略也需要随之变化。

---

### 十三、Lesson 3 的测试重点

我们现在需要测试：

#### 测试 1：Pydantic Model 本身

确认：

```python
ResearchSummary(...)
```

能够正常创建。

#### 测试 2：Structured LLM

确认：

```python
structured_llm
```

被调用，并返回：

```python
ResearchSummary
```

#### 测试 3：Graph

确认：

```text
Graph
 ↓
llm_node
 ↓
structured output
 ↓
llm_response
```

最终仍然正常工作。

---

### 十四、先写 Pydantic Model 单元测试

在：

```text
tests/test_models.py
```

创建：

```python
from app.graph.models import ResearchSummary


def test_research_summary_model():
    research = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
            "Competitive position",
        ],
    )

    assert research.summary == "Strong business fundamentals."

    assert research.key_factors == [
        "Revenue growth",
        "Profitability",
        "Competitive position",
    ]
```

这个测试完全不涉及 LLM。

这是一个纯粹的：

```text
Pydantic Model Test
```

---

### 十五、再测试 Structured Output

这里我们不调用真实 LLM。

我们直接 Mock：

```python
structured_llm.invoke
```

因此：

```text
Graph
 ↓
llm_node
 ↓
Mock structured_llm
 ↓
ResearchSummary
```

我们可以直接测试 `llm_node`。

测试文件：

```text
tests/test_graph.py
```

增加：

```python
from unittest.mock import MagicMock, patch

from app.graph.graph import graph, llm_node
from app.graph.models import ResearchSummary
```

然后增加：

```python
def test_llm_node_uses_structured_output():
    fake_response = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
            "Competitive position",
        ],
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_response

    state = {
        "user_query": "Analyze Apple as a long-term investment",
        "ticker": "AAPL",
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
    }

    with patch(
        "app.graph.graph.structured_llm",
        fake_structured_llm,
    ):
        result = llm_node(state)

    fake_structured_llm.invoke.assert_called_once()

    assert result["llm_response"] == "Strong business fundamentals."
```

---

### 十六、这里出现了一个新的 Mock 技巧

这次我们不再：

```python
patch("某个类的方法")
```

而是：

```python
patch(
    "app.graph.graph.structured_llm",
    fake_structured_llm,
)
```

为什么？

因为：

```python
structured_llm
```

是我们 `graph.py` 模块中的一个变量。

测试时我们直接把它替换成：

```python
fake_structured_llm
```

而：

```python
fake_structured_llm
```

是：

```python
MagicMock()
```

它拥有：

```python
fake_structured_llm.invoke
```

于是：

```python
fake_structured_llm.invoke.return_value = fake_response
```

意味着：

```text
调用：

structured_llm.invoke(...)

实际上：

fake_structured_llm.invoke(...)
        ↓
ResearchSummary(...)
```

---

### 十七、为什么这里比 Lesson 1 更值得注意？

因为现在你已经开始接触真正的 LangChain Runnable 抽象。

Lesson 1：

```text
ChatOpenAI
```

直接调用：

```python
invoke()
```

Lesson 3：

```text
ChatOpenAI
   ↓
with_structured_output()
   ↓
Runnable
```

所以以后你看到：

```python
something.invoke(...)
```

不要自动认为：

> `something` 一定是 ChatOpenAI。

它可能是：

* Chat Model
* PromptValue
* Runnable
* RunnableSequence
* Structured Output Runnable
* Tool
* Agent
* Graph

这正是 LangChain/LangGraph 中 `Runnable` 抽象非常重要的原因。

---

### 十八、现在运行测试

先执行：

```bash
pytest -v
```

目标是：

```text
tests/test_models.py
    PASSED

tests/test_graph.py
    PASSED
```

以及 Phase 1 / Lesson 2 的原有测试继续通过。

---

### 十九、Lesson 3 暂时不要做的事情

这一课我们**刻意不做**：

 - ❌ 不把 `llm_response` 改成 `ResearchSummary`

    暂时保持：
    
    ```python
    llm_response: str
    ```

 - ❌ 不修改 OutputState

 - ❌ 不增加 Recommendation Schema

 - ❌ 不增加投资决策字段

 - ❌ 不连接金融数据 API

 - ❌ 不做 Tool Calling

 - ❌ 不做 Retry

这些分别属于后续 Lesson。

---

### 二十、本课真正要建立的认知

到现在，你的 Agent 已经从：

```text
Lesson 1

Graph
 ↓
LLM
 ↓
String
```

升级成：

```text
Lesson 2

Graph
 ↓
Prompt Template
 ↓
LLM
 ↓
String
```

再升级成：

```text
Lesson 3

Graph
 ↓
Prompt Template
 ↓
Structured LLM
 ↓
Pydantic Model
```

这就是我们 Phase 2 的核心主线。

---

### Lesson 3 验收标准

运行 `pytest -v` 后，需要满足：

* [ ] `ResearchSummary` Pydantic Model 创建成功
* [ ] `summary` 是 `str`
* [ ] `key_factors` 是 `list[str]`
* [ ] `structured_llm = llm.with_structured_output(ResearchSummary)`
* [ ] `llm_node` 调用 `structured_llm.invoke()`
* [ ] 单元测试不调用真实 LLM
* [ ] Mock 返回的是 `ResearchSummary`
* [ ] `llm_response` 能正确获得 `ResearchSummary.summary`
* [ ] 所有已有测试继续通过

**先完成这一步并运行 `pytest -v`。测试通过后，我们直接进入 Lesson 4：`LLM → Structured Graph State`。**

这一课会真正解决一个重要问题：

> 现在 Pydantic 对象已经产生了，**如何让它进入 LangGraph 的 State，而不是又被压缩回一个字符串？**


## Lesson 4：LLM → Structured Graph State

这一课是 Phase 2 中非常关键的一步：我们不再满足于“LLM 能输出 Pydantic 对象”，而是让**结构化结果真正成为 LangGraph State 的一部分**。

### 一、先看我们现在的问题

Lesson 3 已经完成：

```text
Prompt
  ↓
Structured LLM
  ↓
ResearchSummary
```

目前 `llm_node()` 最后却还是：

```python
return {
    "llm_response": response.summary,
}
```

也就是说：

```text
ResearchSummary
    │
    ├── summary
    └── key_factors
           ↓
      只取 summary
           ↓
     llm_response: str
```

**Pydantic 结构又被我们丢掉了。**

这不是我们最终想要的。

---

### 二、Lesson 4 的目标

我们要把：

```text
ResearchSummary
```

直接放进：

```text
GraphState
```

最终变成：

```text
GraphState
├── ...
└── research_summary
      ├── summary
      └── key_factors
```

完整链路：

```text
InputState
    ↓
initialize_state
    ↓
Prompt
    ↓
Structured LLM
    ↓
ResearchSummary
    ↓
GraphState.research_summary
    ↓
后续 Node
```

这一步完成之后，后面的 Agent 就可以直接读取：

```python
state["research_summary"]
```

而不是解析字符串。

---

### 三、第一件事情：修改 `GraphState`

打开：

```text
app/graph/state.py
```

现在你应该已经有：

```python
class GraphState(TypedDict):
    ...
    llm_response: str
```

我们这次增加：

```python
research_summary: ResearchSummary
```

但是这里有一个非常重要的问题：

> `GraphState` 怎么引用 `ResearchSummary`？

所以首先：

```python
from app.graph.models import ResearchSummary
```

然后：

```python
class GraphState(TypedDict):
    ...
    research_summary: ResearchSummary
```

---

### 四、完整的 `state.py`

为了避免遗漏，当前版本建议整理成：

```python
from typing import Literal, TypedDict

from app.graph.models import ResearchSummary


Recommendation = Literal[
    "Strong Buy",
    "Buy",
    "Hold",
    "Reduce",
    "Sell",
]

InvestmentHorizon = Literal[
    "Short Term",
    "Medium Term",
    "Long Term",
]


class InputState(TypedDict):
    user_query: str
    ticker: str


class GraphState(TypedDict):
    user_query: str
    ticker: str

    research_plan: list[str]

    company_research: str
    financial_research: str
    market_research: str
    industry_research: str

    valuation_summary: str

    current_price: float
    target_price: float

    risk_factors: list[str]

    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    investment_thesis: str

    llm_response: str
    research_summary: ResearchSummary


class OutputState(TypedDict):
    ticker: str
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    current_price: float
    target_price: float
    investment_thesis: str
```

这里暂时**保留 `llm_response: str`**。

但注意：

> Lesson 4 开始，`llm_response` 已经不是我们的核心数据了。

真正的结构化结果是：

```python
research_summary: ResearchSummary
```

---

### 五、为什么 `ResearchSummary` 应该进入 State？

这是 LangGraph 项目中一个非常重要的设计原则。

假设：

```text
llm_node
```

得到：

```python
ResearchSummary(
    summary="Strong fundamentals",
    key_factors=[
        "Revenue growth",
        "High margins",
        "Strong balance sheet",
    ],
)
```

下一节点：

```text
risk_node
```

可能需要：

```python
state["research_summary"].key_factors
```

再下一节点：

```text
decision_node
```

可能需要：

```python
state["research_summary"].summary
```

所以：

```text
LLM Output
     ↓
Graph State
     ↓
Multiple Nodes
```

而不是：

```text
LLM Output
     ↓
字符串
     ↓
后面重新解析
```

---

### 六、第二件事情：初始化 State

现在 `initialize_state()` 必须给：

```python
research_summary
```

提供初始值。

但是我们遇到了一个问题：

```python
ResearchSummary
```

需要：

```python
summary
key_factors
```

所以初始化：

```python
ResearchSummary(
    summary="",
    key_factors=[],
)
```

即可。

修改：

```python
def initialize_state(state: InputState) -> GraphState:
    return {
        ...
        "research_summary": ResearchSummary(
            summary="",
            key_factors=[],
        ),
    }
```

---

### 七、这里再次复习 Phase 1 的一个关键概念

你之前已经学过：

> TypedDict 不会自动创建默认值。

所以：

```python
class GraphState(TypedDict):
    research_summary: ResearchSummary
```

**不会**自动产生：

```python
research_summary = ResearchSummary(...)
```

必须由：

```text
initialize_state
```

显式初始化。

这就是我们 Phase 1 专门建立 `initialize_state` 的原因。

---

### 八、第三件事情：修改 `llm_node`

Lesson 3：

```python
response = structured_llm.invoke(prompt_value)

return {
    "llm_response": response.summary,
}
```

Lesson 4：

```python
response = structured_llm.invoke(prompt_value)

return {
    "research_summary": response,
}
```

这一步非常关键。

因为：

```python
response
```

本身就是：

```python
ResearchSummary
```

所以我们不需要：

```python
response.summary
```

而是直接：

```python
"research_summary": response
```

---

### 九、完整 `llm_node`

现在：

```python
def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = structured_llm.invoke(prompt_value)

    return {
        "research_summary": response,
    }
```

注意这里体现了一个非常重要的 State 设计原则：

> **Node 返回它负责更新的字段。**

Lesson 3：

```text
structured_llm
      ↓
llm_response
```

Lesson 4：

```text
structured_llm
      ↓
research_summary
```

以后我们会有：

```text
Company Research Node
      ↓
company_research

Financial Research Node
      ↓
financial_research

Valuation Node
      ↓
valuation_summary

Risk Node
      ↓
risk_factors
```

这就是 State 的模块化。

---

### 十、第四件事情：现在 `llm_response` 还要不要？

这是一个值得讨论的设计问题。

现在：

```python
llm_response: str
```

实际上已经失去了核心意义。

但我建议：

**本课暂时保留它。**

原因不是它以后一定有用，而是我们现在正在学习从：

```text
String Output
```

迁移到：

```text
Structured Output
```

保留它一课，可以让迁移过程非常清楚：

```text
Lesson 3:

ResearchSummary
      ↓
summary
      ↓
llm_response


Lesson 4:

ResearchSummary
      ↓
research_summary
```

到后面的 Lesson 5，我们再处理：

```text
Schema Validation
```

届时可以正式清理不再需要的字段。

这比现在顺手大改 State 更适合我们的学习节奏。

---

### 十一、完整 `graph.py`

当前 Lesson 4 可以整理成：

```python
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.graph.models import ResearchSummary
from app.graph.state import GraphState, InputState, OutputState


load_dotenv()


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0,
)


structured_llm = llm.with_structured_output(ResearchSummary)


llm_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment research assistant. "
            "Provide concise and factual research guidance.",
        ),
        (
            "human",
            "Analyze the following investment research request.\n\n"
            "Ticker: {ticker}\n"
            "User request: {user_query}",
        ),
    ]
)


def initialize_state(state: InputState) -> GraphState:
    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
        "research_summary": ResearchSummary(
            summary="",
            key_factors=[],
        ),
    }


def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = structured_llm.invoke(prompt_value)

    return {
        "research_summary": response,
    }


def create_research_plan(state: GraphState) -> GraphState:
    return {
        "research_plan": [
            "Analyze company fundamentals",
            "Review financial performance",
            "Analyze market conditions",
            "Analyze industry conditions",
            "Perform valuation analysis",
            "Identify major risks",
        ],
    }


def prepare_output(state: GraphState) -> OutputState:
    return {
        "ticker": state["ticker"],
        "recommendation": state["recommendation"],
        "investment_horizon": state["investment_horizon"],
        "current_price": state["current_price"],
        "target_price": state["target_price"],
        "investment_thesis": state["investment_thesis"],
    }


builder = StateGraph(
    GraphState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node("initialize_state", initialize_state)
builder.add_node("llm_node", llm_node)
builder.add_node("create_research_plan", create_research_plan)
builder.add_node("prepare_output", prepare_output)

builder.add_edge(START, "initialize_state")
builder.add_edge("initialize_state", "llm_node")
builder.add_edge("llm_node", "create_research_plan")
builder.add_edge("create_research_plan", "prepare_output")
builder.add_edge("prepare_output", END)

graph = builder.compile()
```

---

### 十二、测试也要跟着改变

Lesson 3 的测试：

```python
assert result["llm_response"] == ...
```

现在我们应该测试：

```python
assert result["research_summary"] == ...
```

但这里有一个细节：

我们的最终：

```python
graph.invoke(...)
```

返回的是：

```python
OutputState
```

而 `OutputState` 目前没有：

```python
research_summary
```

所以：

```python
graph.invoke(...)
```

的最终结果**看不到**这个内部字段。

这正好再次体现：

```text
InputState
     ↓
GraphState
     ↓
OutputState
```

三者不是一回事。

---

### 十三、所以 Lesson 4 的核心测试应该直接测试 `llm_node`

我们已经有：

```python
fake_structured_llm = MagicMock()
```

现在只需要把断言从：

```python
assert result["llm_response"] == ...
```

改成：

```python
assert result["research_summary"] == fake_response
```

完整测试：

```python
from unittest.mock import MagicMock, patch

from app.graph.graph import llm_node
from app.graph.models import ResearchSummary


def test_llm_node_writes_structured_output_to_state():
    fake_response = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
            "Competitive position",
        ],
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_response

    state = {
        "user_query": "Analyze Apple as a long-term investment",
        "ticker": "AAPL",
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
        "research_summary": ResearchSummary(
            summary="",
            key_factors=[],
        ),
    }

    with patch(
        "app.graph.graph.structured_llm",
        fake_structured_llm,
    ):
        result = llm_node(state)

    fake_structured_llm.invoke.assert_called_once()

    assert result["research_summary"] == fake_response
    assert result["research_summary"].summary == (
        "Strong business fundamentals."
    )
    assert result["research_summary"].key_factors == [
        "Revenue growth",
        "Profitability",
        "Competitive position",
    ]
```

---

### 十四、这里出现一个非常重要的 LangGraph State 原则

注意：

```python
return {
    "research_summary": response,
}
```

而不是：

```python
return {
    "research_summary": response.model_dump(),
}
```

也不是：

```python
return {
    "research_summary": response.json(),
}
```

我们现在**直接把 Pydantic 对象放进 State**。

为什么？

因为当前 State 定义就是：

```python
research_summary: ResearchSummary
```

所以：

```text
State
    ↓
ResearchSummary
```

类型是匹配的。

---

### 十五、这和以后持久化有什么关系？

你可能会想到：

> Pydantic 对象直接放 State，以后 checkpoint 能保存吗？

这是后面 Phase 9 才需要深入讨论的问题。

现在我们先建立一个原则：

```text
GraphState 是应用内部的数据契约。
```

在当前阶段，我们首先关心：

```text
类型正确
↓
Node 之间可以可靠传递
↓
后续节点可以直接使用
```

到了 Checkpoint/Persistence 阶段，我们再专门讨论：

```text
serialization
deserialization
checkpoint
storage
```

所以现在**不要为了未来的持久化提前把 Pydantic 转成 dict/string**。

---

### 十六、还有一个非常重要的概念：State 是“共享数据契约”

现在我们的数据流开始变得清晰：

```text
                    ┌──────────────────────┐
                    │      GraphState      │
                    │                      │
Input ─────────────►│ ticker               │
                    │ user_query           │
                    │                      │
LLM ──────────────►│ research_summary     │
                    │                      │
Research Planner ─►│ research_plan        │
                    │                      │
Valuation ────────►│ valuation_summary     │
                    │                      │
Risk ─────────────►│ risk_factors         │
                    │                      │
Decision ─────────►│ recommendation        │
                    │ investment_horizon    │
                    │ investment_thesis     │
                    └──────────────────────┘
```

这实际上已经开始接近我们最终的 Investment Decision Agent 架构。

---

### 十七、为什么这一课对后面的 Multi-Agent 很重要？

未来我们会有：

```text
                    Supervisor
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
Company Agent     Financial Agent   Market Agent
        │               │               │
        └───────────────┼───────────────┘
                        ↓
                     State
                        ↓
                  Valuation Agent
                        ↓
                    Risk Agent
                        ↓
                 Decision Agent
```

每个 Agent 都不能随便返回一坨字符串。

我们最终希望：

```text
Company Agent
    ↓
CompanyResearch

Financial Agent
    ↓
FinancialResearch

Valuation Agent
    ↓
ValuationResult

Risk Agent
    ↓
RiskAnalysis

Decision Agent
    ↓
InvestmentDecision
```

然后这些结构化对象进入 Graph State。

**Lesson 4 正是在建立这个模式。**

---

### 十八、现在运行测试

执行：

```bash
pytest -v
```

这一次重点看：

```text
test_research_summary_model
```

以及：

```text
test_llm_node_writes_structured_output_to_state
```

同时确保之前所有测试仍然通过。

---

### 十九、本课验收标准

Lesson 4 完成的标准：

* [ ] `ResearchSummary` 成为 `GraphState` 字段
* [ ] `initialize_state()` 初始化 `ResearchSummary`
* [ ] `llm_node()` 返回完整的 `ResearchSummary`
* [ ] 没有把结构化对象重新转换成字符串
* [ ] Mock 的 Structured LLM 返回 `ResearchSummary`
* [ ] 测试验证 `summary`
* [ ] 测试验证 `key_factors`
* [ ] 原有测试全部通过
* [ ] `OutputState` 暂时保持不变

最终链路：

```text
InputState
    ↓
initialize_state
    ↓
Prompt Template
    ↓
Structured LLM
    ↓
ResearchSummary
    ↓
GraphState.research_summary
    ↓
后续 Nodes
```

---

### 本课你真正需要掌握的三个概念

#### ① Structured Output 不应该马上变回字符串

错误思路：

```text
LLM
 ↓
Pydantic
 ↓
String
```

正确方向：

```text
LLM
 ↓
Pydantic
 ↓
GraphState
```

#### ② GraphState 是 Node 之间的数据契约

```text
Node A
 ↓
State
 ↓
Node B
```

而不是：

```text
Node A
 ↓
Node B 直接互相调用
```

#### ③ Node 只返回自己负责更新的 State 字段

本课：

```python
return {
    "research_summary": response,
}
```

不要顺手返回整个 State。

---


## Lesson 5：Enum / Schema Validation

这一课非常关键：前面 Lesson 3/4 已经解决了“LLM 输出必须符合结构”的问题，但现在还存在一个更深层的问题：

> **结构正确 ≠ 业务语义正确。**

例如：

```text
recommendation = "Maybe Buy"
```

它可能完全是一个合法的字符串，但对我们的投资系统来说是非法值。

所以这一课要把约束从：

```text
str
```

提升为：

```text
有限、明确、可验证的业务值集合
```

### 1. 本课目标

本课完成以后，我们希望得到这样的数据模型：

```text
ResearchSummary
    ├── summary: str
    └── key_factors: list[str]

InvestmentDecision
    ├── recommendation: Strong Buy | Buy | Hold | Reduce | Sell
    ├── investment_horizon: Short Term | Medium Term | Long Term
    └── investment_thesis: str
```

其中：

#### Recommendation

只允许：

```text
Strong Buy
Buy
Hold
Reduce
Sell
```

#### Investment Horizon

只允许：

```text
Short Term
Medium Term
Long Term
```

而不是：

```text
recommendation: str
investment_horizon: str
```

---

### 2. 为什么不能继续使用 `str`

假设我们现在写：

```python
class InvestmentDecision(BaseModel):
    recommendation: str
    investment_horizon: str
    investment_thesis: str
```

那么下面这些全部可能通过：

```python
InvestmentDecision(
    recommendation="Strong Buy",
    investment_horizon="Long Term",
    investment_thesis="..."
)
```

也可能：

```python
InvestmentDecision(
    recommendation="Maybe Buy",
    investment_horizon="Forever",
    investment_thesis="..."
)
```

甚至：

```python
InvestmentDecision(
    recommendation="banana",
    investment_horizon="unknown",
    investment_thesis="..."
)
```

从 Pydantic 的角度，它们都是 `str`。

但是从**投资业务领域模型**的角度，它们显然不是同一种情况。

所以我们需要：

> Schema 不仅描述数据长什么样，还要描述数据允许取什么值。

---

### 3. Enum 是什么

Python 的 `Enum` 可以理解成：

> **一个字段只能从预先定义好的有限集合中选择。**

例如：

```python
from enum import Enum

class Recommendation(str, Enum):
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    REDUCE = "Reduce"
    SELL = "Sell"
```

那么：

```python
Recommendation.BUY
```

对应的实际值是：

```text
"Buy"
```

而：

```python
Recommendation("Buy")
```

是合法的。

但是：

```python
Recommendation("Maybe Buy")
```

会失败。

这就是我们想要的**业务层 validation**。

---

### 4. 为什么使用 `str, Enum`

我们这里使用：

```python
class Recommendation(str, Enum):
```

而不是：

```python
class Recommendation(Enum):
```

原因是我们的系统最终还需要：

* JSON
* Pydantic
* Structured Output
* API
* Report
* LangGraph State

这些地方都非常依赖字符串形式。

因此：

```python
class Recommendation(str, Enum):
```

非常适合作为 API / LLM / Pydantic 之间的业务枚举。

---

### 5. 第一处修改：`models.py`

打开：

```text
app/graph/models.py
```

现在我们把投资决策模型加入进去。

完整文件修改为：

```python
from enum import Enum

from pydantic import BaseModel, Field


class Recommendation(str, Enum):
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    REDUCE = "Reduce"
    SELL = "Sell"


class InvestmentHorizon(str, Enum):
    SHORT_TERM = "Short Term"
    MEDIUM_TERM = "Medium Term"
    LONG_TERM = "Long Term"


class ResearchSummary(BaseModel):
    summary: str = Field(
        description="A concise summary of the investment research."
    )

    key_factors: list[str] = Field(
        description="The key factors that materially affect the investment analysis."
    )


class InvestmentDecision(BaseModel):
    recommendation: Recommendation = Field(
        description="The investment recommendation."
    )

    investment_horizon: InvestmentHorizon = Field(
        description="The expected investment horizon."
    )

    investment_thesis: str = Field(
        description="The concise investment thesis supporting the recommendation."
    )
```

---

### 6. 这里发生了什么？

现在：

```python
recommendation: Recommendation
```

已经不再是：

```python
recommendation: str
```

而是：

```text
Recommendation
```

它的合法值只有：

```text
Strong Buy
Buy
Hold
Reduce
Sell
```

同理：

```python
investment_horizon: InvestmentHorizon
```

只有：

```text
Short Term
Medium Term
Long Term
```

---

### 7. 第二处修改：`state.py`

现在 GraphState 中已经存在：

```python
recommendation: Recommendation
investment_horizon: InvestmentHorizon
```

但之前这两个类型是直接从 `typing.Literal` 定义的。

我们现在把业务枚举统一放到 `models.py`。

打开：

```text
app/graph/state.py
```

完整修改为：

```python
from typing import TypedDict

from app.graph.models import (
    InvestmentDecision,
    InvestmentHorizon,
    Recommendation,
    ResearchSummary,
)


class InputState(TypedDict):
    user_query: str
    ticker: str


class GraphState(TypedDict):
    user_query: str
    ticker: str
    research_plan: list[str]
    company_research: str
    financial_research: str
    market_research: str
    industry_research: str
    valuation_summary: str
    current_price: float
    target_price: float
    risk_factors: list[str]
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    investment_thesis: str
    llm_response: str
    research_summary: ResearchSummary
    investment_decision: InvestmentDecision


class OutputState(TypedDict):
    ticker: str
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    current_price: float
    target_price: float
    investment_thesis: str
```

这里有一个重要变化：

```python
investment_decision: InvestmentDecision
```

我们开始让最终投资决策成为一个**结构化业务对象**。

---

### 8. 修改 `initialize_state`

打开：

```text
app/graph/graph.py
```

在：

```python
"research_summary": ResearchSummary(
    summary="",
    key_factors=[],
),
```

下面增加：

```python
"investment_decision": InvestmentDecision(
    recommendation=Recommendation.HOLD,
    investment_horizon=InvestmentHorizon.LONG_TERM,
    investment_thesis="",
),
```

因此需要修改 import：

```python
from app.graph.models import (
    InvestmentDecision,
    InvestmentHorizon,
    Recommendation,
    ResearchSummary,
)
```

---

### 9. 完整的 `initialize_state`

为了避免局部修改遗漏，你现在的函数应该是：

```python
def initialize_state(state: InputState) -> GraphState:
    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
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
    }
```

---

### 10. 为什么这里使用 `Recommendation.HOLD`

注意我们没有写：

```python
"recommendation": "Hold"
```

而是：

```python
"recommendation": Recommendation.HOLD
```

这是为了让内部业务状态从一开始就使用类型安全的值。

也就是说：

```text
GraphState
   ↓
Recommendation Enum
   ↓
Pydantic
   ↓
Structured Output
```

而不是整个系统到处都是裸字符串。

---

### 11. 一个非常重要的细节

这里需要区分：

```python
Recommendation.HOLD
```

和：

```python
"Hold"
```

前者是：

```text
Recommendation Enum member
```

后者是：

```text
str
```

但是由于：

```python
class Recommendation(str, Enum)
```

它在很多序列化场景中可以表现为对应字符串：

```text
"Hold"
```

这正是我们需要的效果：

> **内部有强约束，外部容易序列化。**

---

### 12. Lesson 5 的核心测试

现在创建/修改：

```text
tests/test_models.py
```

完整内容：

```python
import pytest
from pydantic import ValidationError

from app.graph.models import (
    InvestmentDecision,
    InvestmentHorizon,
    Recommendation,
)


def test_recommendation_accepts_valid_values():
    decision = InvestmentDecision(
        recommendation=Recommendation.BUY,
        investment_horizon=InvestmentHorizon.LONG_TERM,
        investment_thesis="Strong long-term business fundamentals.",
    )

    assert decision.recommendation == Recommendation.BUY
    assert decision.investment_horizon == InvestmentHorizon.LONG_TERM


def test_recommendation_rejects_invalid_value():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            recommendation="Maybe Buy",
            investment_horizon=InvestmentHorizon.LONG_TERM,
            investment_thesis="Test thesis.",
        )


def test_investment_horizon_rejects_invalid_value():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            recommendation=Recommendation.HOLD,
            investment_horizon="Forever",
            investment_thesis="Test thesis.",
        )


def test_all_recommendation_values_are_defined():
    assert {item.value for item in Recommendation} == {
        "Strong Buy",
        "Buy",
        "Hold",
        "Reduce",
        "Sell",
    }


def test_all_investment_horizon_values_are_defined():
    assert {item.value for item in InvestmentHorizon} == {
        "Short Term",
        "Medium Term",
        "Long Term",
    }
```

---

### 13. 再增加一个 Graph State 测试

创建：

```text
tests/test_graph_state.py
```

内容：

```python
from app.graph.graph import initialize_state
from app.graph.models import InvestmentHorizon, Recommendation


def test_initialize_state_uses_valid_business_enums():
    state = initialize_state(
        {
            "user_query": "Analyze Apple as a long-term investment",
            "ticker": "AAPL",
        }
    )

    assert state["recommendation"] == Recommendation.HOLD
    assert state["investment_horizon"] == InvestmentHorizon.LONG_TERM
```

这个测试和前面的 Pydantic 测试关注点不同。

前面的测试：

```text
Pydantic 是否拒绝非法业务值？
```

这个测试：

```text
Graph 初始化出来的 State 是否使用合法业务值？
```

这两个都重要。

---

### 14. 运行测试

在项目根目录：

```bash
pytest -q
```

本课应该至少覆盖：

```text
tests/test_models.py
tests/test_graph_state.py
```

以及之前 Phase 2 的所有测试。

---

### 15. 本课 Acceptance Criteria

Lesson 5 通过的标准：

#### Schema

* [ ] `Recommendation` 是 `str, Enum`
* [ ] 包含五个值：

  * [ ] `Strong Buy`
  * [ ] `Buy`
  * [ ] `Hold`
  * [ ] `Reduce`
  * [ ] `Sell`
* [ ] `InvestmentHorizon` 是 `str, Enum`
* [ ] 包含：

  * [ ] `Short Term`
  * [ ] `Medium Term`
  * [ ] `Long Term`

#### Pydantic

* [ ] `InvestmentDecision` 使用 Enum
* [ ] 非法 recommendation 会触发 `ValidationError`
* [ ] 非法 investment horizon 会触发 `ValidationError`

#### GraphState

* [ ] `GraphState` 使用 Enum 类型
* [ ] `investment_decision` 已进入 GraphState
* [ ] `initialize_state()` 使用合法默认值
* [ ] 没有重新引入裸字符串作为业务状态的默认值

#### Regression

* [ ] Lesson 1–4 测试全部通过
* [ ] 没有破坏 `ResearchSummary`
* [ ] `OutputState` 的外部接口暂时保持不变

---

### 16. 本课最重要的概念

这一课真正要理解的不是 Python Enum 语法，而是：

```text
LLM 输出
    ↓
结构约束
    ↓
业务值约束
    ↓
Graph State
```

前面的 Lesson 3：

```text
Pydantic
```

解决：

> **数据结构是什么？**

例如：

```json
{
  "summary": "...",
  "key_factors": ["...", "..."]
}
```

Lesson 5 的 Enum 解决：

> **字段允许出现哪些业务值？**

例如：

```text
recommendation
        ↓
┌─────────────────┐
│ Strong Buy      │
│ Buy             │
│ Hold            │
│ Reduce          │
│ Sell            │
└─────────────────┘
```

这就是从：

```text
Schema Validation
```

进一步进入：

```text
Domain Validation
```

---

### 17. 为什么这对后面的 Investment Decision 极其重要

我们的最终投资决策节点以后会产生类似：

```python
InvestmentDecision(
    recommendation=Recommendation.BUY,
    investment_horizon=InvestmentHorizon.LONG_TERM,
    investment_thesis="..."
)
```

然后后面的节点可以安全地假设：

```python
decision.recommendation
```

只可能是五种合法状态之一。

这样我们以后做：

```text
Decision
   ↓
Risk
   ↓
Report
   ↓
API
```

时，就不会出现：

```text
"buy"
"BUY"
"Buy"
"Strongly Buy"
"Maybe Buy"
"Potential Buy"
```

这种 LLM 自由发挥导致的业务状态污染。

**这就是 Structured Output 真正的价值：不是让 JSON 看起来漂亮，而是让 Agent 的输出逐渐变成可以被程序可靠消费的业务对象。**

---