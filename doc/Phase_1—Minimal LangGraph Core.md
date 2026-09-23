
# Phase 1 — Minimal LangGraph Core

这一阶段我们严格遵守之前确定的路线：**先学习 LangGraph 本身，不引入 Investment Agent 的业务复杂度，不提前设计 Supervisor、Memory、Checkpoint 等高级能力。**

## Phase 1 目标

我们只解决一个问题：

> **一个 LangGraph Graph 到底是如何运行的？**

最终建立：

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

并通过一个最小但完整的 Application 验证它。

---

## Lesson 1 — StateGraph 的最小闭环

### 学习目标

本课结束后，你应该能够解释：

1. 什么是 Graph State
2. 什么是 Node
3. 什么是 Edge
4. `StateGraph` 在做什么
5. `compile()` 在做什么
6. `invoke()` 在做什么
7. Graph 执行过程中 State 如何变化

本课**暂时不涉及 LLM**。

这是故意的。

如果第一课就加入 LLM，我们很容易把：

```text
LangGraph
```

和：

```text
LLM Agent
```

混为一谈。

---

### Step 1 — 创建项目

建议项目名称：

```text
investment-agent
```

第一阶段先保持非常简单：

```text
investment-agent/
│
├── app/
│   ├── __init__.py
│   └── graph/
│       ├── __init__.py
│       ├── state.py
│       └── graph.py
│
├── tests/
│   └── test_graph.py
│
└── pyproject.toml
```

**暂时不要创建：**

```text
agents/
tools/
memory/
persistence/
evaluation/
config/
```

因为这些目前都还没有实际职责。

这也符合我们之前确定的：

> 不要为了满足最终目录结构提前创建大量空模块。

---

### Step 2 — `pyproject.toml`

创建：

```text
pyproject.toml
```

完整内容：

```toml
[project]
name = "investment-agent"
version = "0.1.0"
description = "Investment Research and Decision Agent built with LangGraph"
requires-python = ">=3.12"
dependencies = [
    "langgraph",
    "pydantic>=2.0",
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

这里暂时只安装：

```text
langgraph
pydantic
pytest
pytest-asyncio
```

**暂时不安装 LangChain、FastAPI、LangSmith 等。**

原因很简单：

> 我们现在学习的是 LangGraph Core，而不是整个生态。

---

### Step 3 — 定义 State

创建：

```text
app/graph/state.py
```

完整代码：

```python
from typing import TypedDict


class GraphState(TypedDict):
    message: str
```

这里非常重要。

我们现在有一个 State：

```text
GraphState
└── message: str
```

可以把它理解成：

```text
Graph State
     │
     └── 当前 Graph 执行过程中共享的数据
```

---

### Step 4 — 创建第一个 Node

创建：

```text
app/graph/graph.py
```

完整代码：

```python
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState


def process_message(state: GraphState) -> GraphState:
    return {
        "message": f"Processed: {state['message']}",
    }


builder = StateGraph(GraphState)

builder.add_node("process_message", process_message)

builder.add_edge(START, "process_message")
builder.add_edge("process_message", END)

graph = builder.compile()
```

现在我们第一次真正使用 LangGraph。

---

### Step 5 — 理解这段代码

核心结构：

```text
StateGraph
    │
    ▼
GraphState
    │
    ▼
process_message
    │
    ▼
END
```

对应代码：

```python
builder = StateGraph(GraphState)
```

表示：

> 创建一个以 `GraphState` 为 State Schema 的 Graph Builder。

---

然后：

```python
builder.add_node(
    "process_message",
    process_message,
)
```

注册一个 Node。

这里：

```text
"process_message"
```

是 Graph 中 Node 的名字。

而：

```python
process_message
```

是实际执行的 Python 函数。

---

然后：

```python
builder.add_edge(START, "process_message")
```

表示：

```text
START
  ↓
process_message
```

---

再：

```python
builder.add_edge("process_message", END)
```

表示：

```text
process_message
  ↓
END
```

所以整个 Graph 是：

```text
START
  │
  ▼
process_message
  │
  ▼
 END
```

---

### Step 6 — Compile

这一行：

```python
graph = builder.compile()
```

非常重要。

前面：

```python
builder
```

还是在**构建 Graph**。

而：

```python
graph
```

是已经编译好的、可以执行的 Graph。

可以先简单理解成：

```text
Graph Definition
       ↓
    compile()
       ↓
Executable Graph
```

这和你过去设计 Runtime 时的：

```text
Definition
    ↓
Build
    ↓
Executable Runtime
```

会有一点相似。

但这里先不要急着把它类比到 AgentOS。

后面我们会专门讨论这种相似性到底意味着什么。

---

### Step 7 — 第一次 Invoke

现在创建：

```text
tests/test_graph.py
```

完整代码：

```python
from app.graph.graph import graph


def test_graph_processes_message() -> None:
    result = graph.invoke(
        {
            "message": "Hello LangGraph",
        }
    )

    assert result["message"] == "Processed: Hello LangGraph"
```

运行：

```bash
uv run pytest
```

预期：

```text
1 passed
```

---

### Step 8 — 第一次真正执行 Graph

我们也可以直接运行：

```python
from app.graph.graph import graph


result = graph.invoke(
    {
        "message": "Hello LangGraph",
    }
)

print(result)
```

预期：

```python
{
    "message": "Processed: Hello LangGraph"
}
```

整个执行过程：

```text
Input

{
    "message": "Hello LangGraph"
}

        │
        ▼

START
        │
        ▼

process_message

        │
        │
        │
        ▼

{
    "message": "Processed: Hello LangGraph"
}

        │
        ▼

END
```

---

### Step 9 — 现在观察 State 的真正变化

我们输入：

```text
Hello LangGraph
```

Node：

```python
def process_message(state: GraphState) -> GraphState:
    return {
        "message": f"Processed: {state['message']}",
    }
```

实际上完成：

```text
Input State
────────────────────────

message
    │
    ▼
"Hello LangGraph"


Node
────────────────────────

process_message()


Output State
────────────────────────

message
    │
    ▼
"Processed: Hello LangGraph"
```

所以 Node 的基本职责可以先理解成：

> **读取 State → 执行逻辑 → 返回 State Update**

---

#### 一个非常重要的观察

注意我们的 Node：

```python
def process_message(state: GraphState) -> GraphState:
```

输入是：

```text
State
```

输出也是：

```text
State
```

因此可以抽象成：

```text
                 Node
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
     Read State        Return Update
```

这就是以后整个 Investment Agent 的基础。

例如未来：

```text
Company Research Agent
```

本质上也是：

```text
State
  ↓
Agent
  ↓
State Update
```

只是 Node 内部复杂很多。

---

### Step 10 — 第一个实验

现在不要马上进入下一课。

请自己修改：

```python
def process_message(state: GraphState) -> GraphState:
```

让它把消息转换成：

```text
Research request: <原始消息>
```

例如：

输入：

```text
Analyze NVIDIA
```

输出：

```text
Research request: Analyze NVIDIA
```

然后修改测试：

```python
def test_graph_processes_message() -> None:
    result = graph.invoke(
        {
            "message": "Analyze NVIDIA",
        }
    )

    assert result["message"] == "Research request: Analyze NVIDIA"
```

再次运行：

```bash
uv run pytest
```

确保：

```text
1 passed
```

---

### Lesson 1 Acceptance Criteria

完成本课必须满足：

```text
[ ] Python 3.12 环境可用

[ ] LangGraph 安装成功

[ ] StateGraph 创建成功

[ ] GraphState 定义成功

[ ] 至少一个 Node

[ ] START → Node → END

[ ] compile() 成功

[ ] invoke() 成功

[ ] State 能够经过 Node 发生变化

[ ] pytest 测试通过

[ ] 能够解释 State / Node / Edge / Compile / Invoke
```

---

### 本课暂时不要做

不要提前加入：

```text
❌ LLM
❌ LangChain Agent
❌ Tool Calling
❌ Supervisor
❌ Multi-Agent
❌ Checkpoint
❌ Memory
❌ FastAPI
❌ LangSmith
❌ Investment Recommendation
```

我们刻意把第一课压缩到：

```text
State
+
Node
+
Edge
+
Execution
```

这是后面所有东西的基础。

---

### Phase 1 的学习路线

完成 Lesson 1 后，我们继续：

```text
Phase 1
│
├── Lesson 1
│   └── StateGraph 最小闭环       ← 当前
│
├── Lesson 2
│   └── State Update 与多个 Node
│
├── Lesson 3
│   └── Conditional Edge / Routing
│
├── Lesson 4
│   └── Graph Execution Model
│
└── Phase 1 Acceptance
```

**现在先完成 Lesson 1，不要继续往后写。**

你运行完：

```bash
uv run pytest
```

把**终端实际输出**贴给我。如果出现错误，把完整 traceback 一并贴过来。

我们下一步就从实际运行结果开始，而不是假设环境一定正确。


## Lesson 2：Conditional Edge（条件路由）。

这一课非常重要，因为它是后面 **Supervisor / Planner 动态决定研究路径** 的基础。

### 1. 本课目标

Lesson 1 是固定路径：

```text
START
  ↓
process_message
  ↓
END
```

Lesson 2 改成：

```text
START
  ↓
process_message
  ↓
route_message
  ├── simple
  │    ↓
  │   END
  │
  └── detailed
       ↓
      END
```

核心变化只有一个：

> **下一步不再写死，而是由当前 State 决定。**

---

### 2. 先理解 Conditional Edge

LangGraph 中可以把它理解成：

```python
builder.add_conditional_edges(
    "process_message",
    route_message,
    {
        "simple": "simple_response",
        "detailed": "detailed_response",
    },
)
```

这里：

* `process_message`：当前 Node
* `route_message`：路由函数
* `"simple"`：路由函数可能返回的结果
* `"simple_response"`：真正要执行的 Node

所以：

```text
process_message
      ↓
 route_message
      ↓
  返回 "simple"
      ↓
simple_response
```

或者：

```text
process_message
      ↓
 route_message
      ↓
 返回 "detailed"
      ↓
detailed_response
```

注意一个非常重要的概念：

> **Router 决定去哪，不负责完成主要业务工作。**

这一区分以后会非常重要。

---

### 3. 修改 State

现在我们需要让 State 里面有一个字段表示请求类型。

把：

`app/graph/state.py`

完整修改为：

```python
from typing import Literal, TypedDict


class GraphState(TypedDict):
    message: str
    request_type: Literal["simple", "detailed"]
```

这里的：

```python
Literal["simple", "detailed"]
```

表示：

`request_type` 只能是这两个值。

这是我们第一次让 State 开始承载**控制流程信息**。

最终投资 Agent 中会出现类似：

```text
research_type
company
research_depth
valuation_required
risk_analysis_required
```

等等。

但现在只学习最简单的情况。

---

### 4. 修改 Graph

打开：

`app/graph/graph.py`

完整替换为：

```python
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState


def process_message(state: GraphState) -> GraphState:
    message = state["message"]

    if len(message) <= 20:
        request_type = "simple"
    else:
        request_type = "detailed"

    return {
        "message": message,
        "request_type": request_type,
    }


def route_message(
    state: GraphState,
) -> Literal["simple", "detailed"]:
    return state["request_type"]


def simple_response(state: GraphState) -> GraphState:
    return {
        "message": f"Simple: {state['message']}",
        "request_type": state["request_type"],
    }


def detailed_response(state: GraphState) -> GraphState:
    return {
        "message": f"Detailed: {state['message']}",
        "request_type": state["request_type"],
    }


builder = StateGraph(GraphState)

builder.add_node("process_message", process_message)
builder.add_node("simple_response", simple_response)
builder.add_node("detailed_response", detailed_response)

builder.add_edge(START, "process_message")

builder.add_conditional_edges(
    "process_message",
    route_message,
    {
        "simple": "simple_response",
        "detailed": "detailed_response",
    },
)

builder.add_edge("simple_response", END)
builder.add_edge("detailed_response", END)

graph = builder.compile()
```

---

### 5. 仔细看执行过程

现在如果输入：

```text
Hello
```

执行：

```text
START
  ↓
process_message
  ↓
len("Hello") <= 20
  ↓
request_type = "simple"
  ↓
route_message
  ↓
"simple"
  ↓
simple_response
  ↓
END
```

最终：

```python
{
    "message": "Simple: Hello",
    "request_type": "simple",
}
```

---

如果输入：

```text
Please research Apple financial performance
```

由于字符串长度超过 20：

```text
START
  ↓
process_message
  ↓
request_type = "detailed"
  ↓
route_message
  ↓
"detailed"
  ↓
detailed_response
  ↓
END
```

最终：

```python
{
    "message": "Detailed: Please research Apple financial performance",
    "request_type": "detailed",
}
```

---

### 6. 修改测试

现在把：

`tests/test_graph.py`

完整替换成：

```python
from app.graph.graph import graph


def test_graph_routes_simple_request() -> None:
    result = graph.invoke(
        {
            "message": "Hello",
            "request_type": "simple",
        }
    )

    assert result["request_type"] == "simple"
    assert result["message"] == "Simple: Hello"


def test_graph_routes_detailed_request() -> None:
    message = "Please research Apple financial performance"

    result = graph.invoke(
        {
            "message": message,
            "request_type": "simple",
        }
    )

    assert result["request_type"] == "detailed"
    assert result["message"] == f"Detailed: {message}"
```

这里有一个值得注意的地方。

我们虽然传入：

```python
"request_type": "simple"
```

但是 `process_message` 会重新计算它。

所以第二个测试实际上是在验证：

> **Node 可以根据当前 State 更新控制字段，然后 Conditional Edge 根据更新后的 State 进行路由。**

---

### 7. 现在运行测试

在 PyCharm 中运行：

```text
tests/test_graph.py
```

或者命令行：

```bash
uv run pytest
```

我们预期看到：

```text
2 passed
```

---

### 8. 这一课真正需要掌握的东西

不要只记住 API。

你现在应该建立下面这个模型：

```text
                    ┌── simple_response ──→ END
                    │
START → process → Router
                    │
                    └── detailed_response → END
```

其中：

#### State

保存当前执行状态：

```python
{
    "message": "...",
    "request_type": "simple",
}
```

#### Node

执行实际工作：

```python
process_message()
simple_response()
detailed_response()
```

#### Router

只负责判断：

```python
def route_message(state):
    return state["request_type"]
```

#### Conditional Edge

把 Router 的结果映射到具体 Node：

```python
{
    "simple": "simple_response",
    "detailed": "detailed_response",
}
```

---

### 9. 和最终 Investment Agent 的关系

这一课虽然只有几十行代码，但它实际上已经触碰到了最终架构的核心。

以后可能是：

```text
                         ┌→ Company Research
                         │
User Request
     ↓                   ├→ Financial Research
Supervisor / Planner ────┤
                         ├→ Market Research
                         │
                         └→ Industry Research
```

区别只是：

现在：

```python
request_type = "simple"
```

未来可能变成：

```text
research_plan
```

并且路由依据不再是字符串长度，而是：

* 用户研究目标
* 公司信息需求
* 财务分析需求
* 市场需求
* 行业/宏观需求
* 是否需要估值
* 是否需要风险分析

而这些复杂判断以后才会交给 **LLM + Structured Output + Supervisor**。

**现在绝对不要提前引入 LLM。**


## Lesson 3 — State Update 与多节点数据流

### 1. 本课目标

Lesson 2 我们学习的是：

```text
Node
 ↓
Router
 ↓
不同 Node
```

现在进一步学习：

```text
State
 ↓
Node A
 ↓
State Update
 ↓
Node B
 ↓
State Update
 ↓
Node C
 ↓
Final State
```

也就是：

> **多个 Node 如何通过 Graph State 协作完成一个任务。**

这是后面 Multi-Agent Workflow 的基础。

---

### 2. 先把投资 Agent 映射进来

最终我们希望出现类似这样的数据流：

```text
User Request
     ↓
Research Planner
     ↓
Company Research
     ↓
Financial Research
     ↓
Valuation
     ↓
Risk Analysis
     ↓
Investment Decision
```

每个节点都可能产生新的信息。

例如：

```text
Company Research
    ↓
company_facts

Financial Research
    ↓
financial_metrics

Valuation
    ↓
target_price

Risk Analysis
    ↓
risk_factors

Investment Decision
    ↓
recommendation
```

最后 State 可能变成：

```python
{
    "company": "Apple",
    "company_facts": "...",
    "financial_metrics": "...",
    "target_price": 280,
    "risk_factors": [...],
    "recommendation": "Buy",
}
```

**Lesson 3 暂时不做这些真实投资字段。**

我们先用一个极小的例子理解机制。

---

### 3. 修改 State

`app/graph/state.py`

完整替换：

```python
from typing import TypedDict


class GraphState(TypedDict):
    message: str
    processed_message: str
    analysis: str
```

现在 State 有三个字段：

```text
message
processed_message
analysis
```

可以理解成：

```text
原始输入
   ↓
processed_message
   ↓
analysis
```

---

### 4. 修改 Graph

`app/graph/graph.py`

完整替换：

```python
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState


def process_message(state: GraphState) -> GraphState:
    message = state["message"]

    return {
        "message": message,
        "processed_message": message.upper(),
        "analysis": "",
    }


def analyze_message(state: GraphState) -> GraphState:
    processed_message = state["processed_message"]

    return {
        "message": state["message"],
        "processed_message": processed_message,
        "analysis": f"Message length: {len(processed_message)}",
    }


builder = StateGraph(GraphState)

builder.add_node("process_message", process_message)
builder.add_node("analyze_message", analyze_message)

builder.add_edge(START, "process_message")
builder.add_edge("process_message", "analyze_message")
builder.add_edge("analyze_message", END)

graph = builder.compile()
```

现在 Graph 非常简单：

```text
START
  ↓
process_message
  ↓
analyze_message
  ↓
END
```

但是 State 在不断变化。

---

### 5. 观察 State 的变化

输入：

```python
{
    "message": "hello langgraph",
    "processed_message": "",
    "analysis": "",
}
```

经过 `process_message`：

```python
{
    "message": "hello langgraph",
    "processed_message": "HELLO LANGGRAPH",
    "analysis": "",
}
```

然后进入 `analyze_message`。

它读取：

```python
state["processed_message"]
```

得到：

```text
HELLO LANGGRAPH
```

然后产生：

```python
{
    "message": "hello langgraph",
    "processed_message": "HELLO LANGGRAPH",
    "analysis": "Message length: 15",
}
```

所以：

```text
Node A
  ↓
写入 processed_message
  ↓
Node B
  ↓
读取 processed_message
  ↓
写入 analysis
```

这就是最基本的**节点间数据流**。

---

### 6. 修改测试

`tests/test_graph.py`

完整替换：

```python
from app.graph.graph import graph


def test_graph_passes_state_between_nodes() -> None:
    result = graph.invoke(
        {
            "message": "hello langgraph",
            "processed_message": "",
            "analysis": "",
        }
    )

    assert result["message"] == "hello langgraph"
    assert result["processed_message"] == "HELLO LANGGRAPH"
    assert result["analysis"] == "Message length: 15"
```

运行：

```bash
pytest
```

预期：

```text
1 passed
```

如果通过，**Lesson 3 直接关闭，不需要再把测试结果贴给我**。

---

### 7. 一个重要概念：Node 为什么返回完整 State？

你现在可能会注意到：

```python
return {
    "message": state["message"],
    "processed_message": processed_message,
    "analysis": ...,
}
```

我们这里为了让 Lesson 3 简单，采用的是**完整 State 返回方式**。

但 LangGraph 中更重要的概念是：

> Node 可以返回 State Update，而不是每次都重新构造整个业务状态。

这个问题我们下一步会专门处理。

因为如果真正的投资 Agent 有几十个 State 字段，让每个 Node 都手工复制全部字段，会非常麻烦，也容易出错。

---

### 8. Lesson 3 的真正知识点

现在把三个 Lesson 串起来：

#### Lesson 1

学习：

```text
State
 ↓
Node
 ↓
END
```

#### Lesson 2

学习：

```text
State
 ↓
Node
 ↓
Conditional Edge
 ↓
不同 Node
```

#### Lesson 3

学习：

```text
State
 ↓
Node A
 ↓
State Update
 ↓
Node B
 ↓
State Update
 ↓
END
```

因此到这里，你已经掌握了 LangGraph 最基本的三个骨架：

```text
① Node
② Edge / Conditional Edge
③ State Data Flow
```

---



## Lesson 4 — State Reducer

### 1. 为什么需要 Reducer？

前面我们一直是：

```text
Node A
  ↓
Node B
  ↓
Node C
```

所以 State 很简单：

```text
A 写入
 ↓
B 读取
 ↓
B 写入
 ↓
C 读取
```

但投资研究 Agent 最终会出现：

```text
                 ┌→ Company Research ──┐
                 │                     │
Supervisor ──────┼→ Financial Research ┼→ Aggregation
                 │                     │
                 ├→ Market Research ───┤
                 │                     │
                 └→ Industry Research ─┘
```

四个 Research Node 可以并行执行。

假设它们都产生：

```text
Company Research
    → evidence

Financial Research
    → evidence

Market Research
    → evidence

Industry Research
    → evidence
```

那么就出现一个问题：

> 四个 Node 都要向同一个 `evidence` 写数据，LangGraph 应该怎么合并？

这就是 **Reducer**。

---

### 2. 先理解普通 State

假设：

```python
class GraphState(TypedDict):
    messages: list[str]
```

如果：

```text
Node A → ["Company"]
Node B → ["Financial"]
```

我们希望最终得到：

```python
["Company", "Financial"]
```

而不是：

```python
["Financial"]
```

或者：

```python
["Company"]
```

Reducer 就负责定义：

> **同一个 State 字段收到多个更新时，如何合并这些更新。**

---

### 3. 最简单的 Reducer：`operator.add`

Python 本身已经提供了一个非常方便的函数：

```python
operator.add
```

对于 list：

```python
["Company"] + ["Financial"]
```

结果就是：

```python
["Company", "Financial"]
```

所以我们可以定义：

```python
from operator import add
from typing import Annotated
```

然后：

```python
messages: Annotated[list[str], add]
```

意思是：

> `messages` 字段发生多个更新时，使用 `add` 合并。

---

### 4. 修改 State

现在修改：

`app/graph/state.py`

完整内容：

```python
from operator import add
from typing import Annotated, TypedDict


class GraphState(TypedDict):
    message: str
    research_results: Annotated[list[str], add]
```

这里最重要的是：

```python
research_results: Annotated[list[str], add]
```

可以理解成：

```text
research_results
       +
    Reducer
       ↓
operator.add
```

---

### 5. 修改 Graph

这一次我们故意构造一个并行 Graph：

```text
                 ┌→ company_research ──┐
START →          │                     │
                 ├→ financial_research ┼→ END
                 │                     │
                 └→ market_research ───┘
```

修改：

`app/graph/graph.py`

完整内容：

```python
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState


def company_research(state: GraphState) -> GraphState:
    return {
        "message": state["message"],
        "research_results": ["Company research completed"],
    }


def financial_research(state: GraphState) -> GraphState:
    return {
        "message": state["message"],
        "research_results": ["Financial research completed"],
    }


def market_research(state: GraphState) -> GraphState:
    return {
        "message": state["message"],
        "research_results": ["Market research completed"],
    }


builder = StateGraph(GraphState)

builder.add_node("company_research", company_research)
builder.add_node("financial_research", financial_research)
builder.add_node("market_research", market_research)

builder.add_edge(START, "company_research")
builder.add_edge(START, "financial_research")
builder.add_edge(START, "market_research")

builder.add_edge("company_research", END)
builder.add_edge("financial_research", END)
builder.add_edge("market_research", END)

graph = builder.compile()
```

---

### 6. 现在 Graph 的结构非常重要

注意这里第一次出现了：

```python
builder.add_edge(START, "company_research")
builder.add_edge(START, "financial_research")
builder.add_edge(START, "market_research")
```

这意味着：

```text
              ┌── Company Research
              │
START ────────┼── Financial Research
              │
              └── Market Research
```

这就是最基础的 **Fan-out**。

---

### 7. State 如何汇聚？

初始 State：

```python
{
    "message": "Research Apple",
    "research_results": [],
}
```

三个 Node 分别产生：

```python
["Company research completed"]
```

```python
["Financial research completed"]
```

```python
["Market research completed"]
```

Reducer：

```python
add
```

负责把它们合并。

最终：

```python
{
    "message": "Research Apple",
    "research_results": [
        "Company research completed",
        "Financial research completed",
        "Market research completed",
    ],
}
```

这就是：

```text
                 ┌→ Company ─────┐
                 │               │
START ───────────┼→ Financial ───┼→ Shared State
                 │               │
                 └→ Market ──────┘
```

---

### 8. 修改测试

`tests/test_graph.py`

完整替换：

```python
from app.graph.graph import graph


def test_parallel_research_results_are_merged() -> None:
    result = graph.invoke(
        {
            "message": "Research Apple",
            "research_results": [],
        }
    )

    assert result["message"] == "Research Apple"

    assert sorted(result["research_results"]) == sorted(
        [
            "Company research completed",
            "Financial research completed",
            "Market research completed",
        ]
    )
```

这里使用：

```python
sorted(...)
```

而不是直接比较 list 顺序。

这是**故意的**。

因为三个并行节点的执行/合并顺序不应该成为我们这个测试的核心要求。

我们真正关心的是：

> 三个 Research Result 是否都进入了最终 State。

---

### 9. 运行测试

运行：

```bash
pytest
```

预期：

```text
1 passed
```

---

### 10. 这一课最重要的概念

现在你已经可以把 LangGraph 的数据流理解成两种模式。

#### Sequential

```text
A
↓
B
↓
C
```

State：

```text
A update
   ↓
B update
   ↓
C update
```

---

#### Parallel

```text
       ┌→ A ─┐
START ─┼→ B ─┼→ Shared State
       └→ C ─┘
```

State：

```text
A update ─┐
B update ─┼→ Reducer → Final State
C update ─┘
```

这就是后面 Research Agent 的核心机制。

---

### 11. 映射到 Investment Agent

最终我们可以做：

```text
                     ┌→ Company Research ────┐
                     │                        │
                     ├→ Financial Research ──┤
Supervisor ──────────┤                        ├→ Research Evidence
                     ├→ Market Research ─────┤
                     │                        │
                     └→ Industry Research ───┘
```

每个 Agent 都可以产生自己的结果：

```text
Company Research
    ↓
company_facts

Financial Research
    ↓
financial_metrics

Market Research
    ↓
market_context

Industry Research
    ↓
industry_context
```

然后进入：

```text
Research Evidence
        ↓
Valuation
        ↓
Risk Analysis
        ↓
Investment Decision
```

这就是为什么 **Reducer 不只是一个 API 技巧**。

它是后面多 Agent 并行研究能够成立的基础。

---

### 12. 一个非常重要的限制

这里暂时不要形成一个错误认识：

> “所有 State 字段都应该使用 Reducer。”

不是。

例如：

```python
current_price: float
```

通常并不希望：

```text
100
+
105
=
205
```

这显然没有意义。

所以不同 State 字段需要不同的语义。

例如未来：

```text
research_results → append / merge
evidence          → append / merge
risk_factors      → append / merge

current_price     → single value
target_price      → single value
recommendation    → single value
```

**Reducer 是字段级别的 State 合并规则。**

这一点后面设计正式 `GraphState` 时非常重要。

---

### Lesson 4 Acceptance

完成以下条件即可视为通过：

* [x] 理解 `Annotated`
* [x] 理解 Reducer
* [x] 理解 `operator.add`
* [x] 理解 Fan-out
* [x] 多个 Node 向同一 list State 写入
* [x] Reducer 合并并行结果
* [x] 测试验证三个结果全部存在

运行 `pytest` 没有问题后，**无需再贴结果，直接进入 Lesson 5**。

---



## Lesson 5：Fan-out / Fan-in

上一课我们完成了：

```text
                 ┌→ Company Research ──┐
                 │                     │
START ───────────┼→ Financial Research ┼→ END
                 │                     │
                 └→ Market Research ───┘
```

这解决了 **Fan-out + Reducer**。

但真正的研究工作流需要的是：

```text
                 ┌→ Company Research ──┐
                 │                     │
START ───────────┼→ Financial Research ─┼→ Aggregator → END
                 │                     │
                 └→ Market Research ────┘
```

也就是说：

* **Fan-out**：一个节点分发到多个节点
* **Fan-in**：多个节点完成后重新汇聚到一个节点

这就是今天的核心。

---

### 1. 修改 State

`app/graph/state.py`

完整内容：

```python
from operator import add
from typing import Annotated, TypedDict


class GraphState(TypedDict):
    message: str
    research_results: Annotated[list[str], add]
    research_summary: str
```

这里：

```python
research_results
```

负责收集并行 Research Node 的结果。

而：

```python
research_summary
```

由最后的 Aggregator Node 生成。

---

### 2. 修改 Graph

`app/graph/graph.py`

完整替换：

```python
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState


def company_research(state: GraphState) -> GraphState:
    return {
        "research_results": ["Company research completed"],
    }


def financial_research(state: GraphState) -> GraphState:
    return {
        "research_results": ["Financial research completed"],
    }


def market_research(state: GraphState) -> GraphState:
    return {
        "research_results": ["Market research completed"],
    }


def aggregate_research(state: GraphState) -> GraphState:
    results = state["research_results"]

    return {
        "research_summary": " | ".join(results),
    }


builder = StateGraph(GraphState)

builder.add_node("company_research", company_research)
builder.add_node("financial_research", financial_research)
builder.add_node("market_research", market_research)
builder.add_node("aggregate_research", aggregate_research)

builder.add_edge(START, "company_research")
builder.add_edge(START, "financial_research")
builder.add_edge(START, "market_research")

builder.add_edge("company_research", "aggregate_research")
builder.add_edge("financial_research", "aggregate_research")
builder.add_edge("market_research", "aggregate_research")

builder.add_edge("aggregate_research", END)

graph = builder.compile()
```

---

### 3. 现在 Graph 的拓扑

现在已经从上一课的：

```text
START
 ├── Company ──→ END
 ├── Financial → END
 └── Market ───→ END
```

变成：

```text
                 ┌→ Company Research ──┐
                 │                     │
START ───────────┼→ Financial Research ┼──→ Aggregator → END
                 │                     │
                 └→ Market Research ───┘
```

这里最重要的是：

```python
builder.add_edge("company_research", "aggregate_research")
builder.add_edge("financial_research", "aggregate_research")
builder.add_edge("market_research", "aggregate_research")
```

三个 Node 都指向同一个 Node。

这就是 **Fan-in**。

---

### 4. 修改测试

`tests/test_graph.py`

完整替换：

```python
from app.graph.graph import graph


def test_parallel_research_results_are_aggregated() -> None:
    result = graph.invoke(
        {
            "message": "Research Apple",
            "research_results": [],
            "research_summary": "",
        }
    )

    assert sorted(result["research_results"]) == sorted(
        [
            "Company research completed",
            "Financial research completed",
            "Market research completed",
        ]
    )

    summary_parts = result["research_summary"].split(" | ")

    assert sorted(summary_parts) == sorted(
        [
            "Company research completed",
            "Financial research completed",
            "Market research completed",
        ]
    )
```

运行：

```bash
pytest
```

---

### 5. 一个很重要的问题：为什么 Aggregator 不应该直接连 START？

我们现在故意使用：

```text
Company ──┐
Financial ─┼→ Aggregator
Market ───┘
```

而不是：

```text
START ──→ Aggregator
```

因为 Aggregator 的前提条件是：

> **三个 Research Node 的结果已经准备好。**

它需要读取：

```python
state["research_results"]
```

如果它在 Research 完成之前运行，就可能拿不到完整结果。

所以 Graph 的拓扑本身就在表达一个业务约束：

```text
Research
   ↓
全部完成
   ↓
Aggregation
```

这在我们的最终 Agent 中非常重要：

```text
Company Research ────────┐
Financial Research ──────┤
Market Research ─────────┼→ Research Aggregator
Industry/Macro Research ─┘
                              ↓
                          Valuation
```

不能让 Valuation 在 Research 数据尚未汇聚完成的时候就执行。

---

### 6. 这里有一个 LangGraph 的关键机制

你现在可能会发现：

```python
builder.add_edge(
    "company_research",
    "aggregate_research",
)
```

```python
builder.add_edge(
    "financial_research",
    "aggregate_research",
)
```

```python
builder.add_edge(
    "market_research",
    "aggregate_research",
)
```

为什么不会导致：

```text
Company 完成
   ↓
Aggregator 执行

Financial 完成
   ↓
Aggregator 又执行

Market 完成
   ↓
Aggregator 又执行
```

？

LangGraph 会根据 Graph 的依赖关系处理这种汇聚。

这里的核心不是简单的：

> “三个 Node 都调用了 Aggregator。”

而是：

> **Aggregator 位于多个上游节点的汇聚位置。**

这正是我们学习 Graph topology 的原因。

---

### 7. 映射到投资 Agent

现在可以把我们的 Lesson 5 直接映射到最终系统：

```text
                         ┌→ Company Research ──────┐
                         │                         │
                         ├→ Financial Research ────┤
Supervisor / Planner ────┤                         ├→ Research Aggregator
                         ├→ Market Research ───────┤
                         │                         │
                         └→ Industry / Macro ──────┘
                                                       ↓
                                                   Valuation
                                                       ↓
                                                   Risk Analysis
                                                       ↓
                                                Investment Decision
                                                       ↓
                                                     Report
```

这里已经开始出现最终产品真正的骨架了。

---

### 8. Lesson 5 Acceptance

测试通过后，本课即完成：

* [ ] 理解 Fan-out
* [ ] 理解 Fan-in
* [ ] 多个 Research Node 汇聚到 Aggregator
* [ ] Reducer 收集并行结果
* [ ] Aggregator 消费汇聚后的 State
* [ ] 理解 Graph topology 对执行顺序的约束

仍然按照新的节奏：

**测试通过 → 不需要贴结果 → 我们直接进入 Lesson 6。**

---



## Lesson 6：State Schema 设计与业务状态建模。

从这一课开始，我们逐渐从“LangGraph API Demo”切换到 **Investment Research & Decision Agent 的真实业务模型**。

前 5 课解决的是：

```text
Node
Edge
Conditional Edge
State Update
Reducer
Fan-out / Fan-in
```

Lesson 6 要解决的是：

> **一个真正的 Investment Agent，到底应该把什么放进 Graph State？**

---

### 1. 为什么 State Schema 很重要？

后面的整个系统都会围绕 State 运转：

```text
User
 ↓
Supervisor
 ↓
Research Agents
 ↓
Valuation
 ↓
Risk
 ↓
Investment Decision
 ↓
Report
```

这些 Node 之间需要共享数据。

如果 State 设计混乱，后面会出现：

```text
Node A 不知道 Node B 需要什么
Node B 不知道数据从哪里来
Checkpoint 无法有效保存
HITL 无法恢复
Memory 和 State 混在一起
Report 不知道应该读取哪些字段
```

所以我们现在先建立一个清晰的边界。

---

### 2. State 的三个基本原则

我们的 Graph State 主要保存：

#### ① 当前 Run 的输入

例如：

```text
用户要研究谁？
研究什么？
```

#### ② 当前 Run 中产生的中间结果

例如：

```text
公司研究
财务研究
市场研究
估值
风险
```

#### ③ 当前 Run 的最终结果

例如：

```text
Investment Recommendation
Target Price
Investment Horizon
```

---

### 3. 什么暂时不要放进 State？

这同样重要。

#### 不要把长期 Memory 直接当 State

例如：

```text
用户历史投资偏好
过去研究过哪些公司
用户长期关注行业
```

这些属于后面：

```text
Memory / Store
```

不是当前 Graph Run 的核心 State。

---

#### 不要把工具客户端放进 State

例如：

```python
yfinance_client
database_connection
llm_client
http_client
```

这些属于：

```text
Tool / Infrastructure
```

不属于业务 State。

---

#### 不要把整个 LLM 对话历史无脑塞进业务 State

后面会有：

```text
messages
```

但我们会单独讨论 Message State，而不是现在把所有东西混进去。

---

### 4. 开始建立 Investment Agent State

这一课先建立一个**第一版业务 State**。

我们不引入 Pydantic，不引入 LLM，不引入 Tool。

只使用：

```python
TypedDict
Annotated
Literal
```

---

### 5. 修改 `state.py`

`app/graph/state.py`

完整替换为：

```python id="4u1p2w"
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


class GraphState(TypedDict):
    # User request
    user_query: str
    ticker: str

    # Research planning
    research_plan: list[str]

    # Research results
    company_research: str
    financial_research: str
    market_research: str
    industry_research: str

    # Valuation
    valuation_summary: str
    current_price: float
    target_price: float

    # Risk analysis
    risk_factors: list[str]

    # Investment decision
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    investment_thesis: str
```

这里已经开始体现最终产品的核心结构。

---

### 6. 为什么使用 Literal？

这里：

```python id="75p52u"
Recommendation = Literal[
    "Strong Buy",
    "Buy",
    "Hold",
    "Reduce",
    "Sell",
]
```

直接对应我们之前确定的五档投资建议：

```text
Strong Buy
Buy
Hold
Reduce
Sell
```

而不是随便定义一个：

```text
recommendation: str
```

因为：

```python
recommendation: str
```

理论上允许：

```text
"Maybe Buy"
"Very Strong Buy"
"Don't Know"
"XYZ"
```

这会让下游系统很难保证数据一致性。

使用 `Literal` 后，State Schema 明确表达：

> Investment Decision 的合法输出集合就是这五个等级。

---

### 7. Investment Horizon

同样：

```python id="e8x0ru"
InvestmentHorizon = Literal[
    "Short Term",
    "Medium Term",
    "Long Term",
]
```

对应我们之前确定的：

```text
Short Term
Medium Term
Long Term
```

这里特别注意：

**不是让用户必须指定 Horizon。**

最终系统可以由 Agent 根据研究结论自主选择。

现在 State 只是定义：

> 如果 Agent 最终产生 Horizon，那么合法值是什么。

后面的 Decision Agent 才负责决定具体是哪一个。

---

### 8. 为什么 `target_price` 和 `current_price` 都放 State？

因为我们的投资决策需要一个非常重要的关系：

```text
Current Price
      ↓
Target Price
      ↓
Expected Upside / Downside
```

例如：

```text
Current Price = 200
Target Price = 240
```

那么：

```text
Expected Return
= (240 - 200) / 200
= 20%
```

未来这个计算应该由**明确的计算逻辑**完成，而不是让 LLM 随意生成。

所以我们现在先把：

```python
current_price: float
target_price: float
```

作为独立 State 字段。

---

### 9. 为什么没有 `expected_return`？

这是故意的。

我们现在没有：

```python
expected_return: float
```

因为它是一个**派生数据**：

```text
expected_return
=
(target_price - current_price) / current_price
```

原则是：

> **能够可靠计算得到的数据，不应该让 LLM 自由生成。**

以后我们可以让：

```text
Valuation
    ↓
current_price
target_price
    ↓
Calculation Node
    ↓
expected_return
```

这比让 LLM 输出：

```text
Expected return: approximately 17.3%
```

更加可靠。

这一原则以后会贯穿整个投资 Agent。

---

### 10. 为什么 Research 使用不同字段？

我们目前定义：

```python id="a8y1h7"
company_research: str
financial_research: str
market_research: str
industry_research: str
```

因为这四个领域最终可能来自不同 Agent：

```text
Company Research Agent
Financial Research Agent
Market Research Agent
Industry/Macro Research Agent
```

所以 State 要能够明确知道：

```text
这条信息属于什么研究领域？
```

而不是全部塞成：

```python
research: str
```

否则后面：

```text
Valuation
Risk
Decision
Report
```

很难知道应该从哪里读取信息。

---

### 11. Risk 为什么是 list？

我们定义：

```python id="cy36t2"
risk_factors: list[str]
```

因为风险天然是多项：

```text
[
    "Revenue concentration",
    "Margin pressure",
    "Regulatory risk",
    "Valuation risk",
]
```

后面 Risk Agent 可以不断产生多个风险因素。

这也会和上一课的 Reducer 产生联系：

```text
Risk Agent A ──┐
Risk Agent B ──┼→ risk_factors
Risk Agent C ──┘
```

未来可能会使用：

```python
Annotated[list[str], add]
```

但**这一课暂时不加 Reducer**。

因为我们现在首先建立业务 Schema，不急着把所有机制都混在一起。

---

### 12. Research Plan 为什么也是 list？

现在：

```python
research_plan: list[str]
```

例如：

```python
[
    "Analyze company fundamentals",
    "Review recent financial performance",
    "Analyze industry conditions",
    "Estimate intrinsic value",
    "Identify major risks",
]
```

后面的 Supervisor / Planner 会负责生成这个计划。

于是：

```text
User Query
     ↓
Supervisor
     ↓
Research Plan
     ↓
Research Agents
```

这会成为后面 Multi-Agent Orchestration 的重要输入。

---

### 13. 现在 Graph 也要切换到新的 State

因为 Lesson 5 的测试 Graph 已经完成使命。

现在让 Graph 做一个非常简单的：

```text
User Query
    ↓
Research Planner
    ↓
Research State
```

修改：

`app/graph/graph.py`

完整内容：

```python id="1g3t9k"
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState


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


builder = StateGraph(GraphState)

builder.add_node("create_research_plan", create_research_plan)

builder.add_edge(START, "create_research_plan")
builder.add_edge("create_research_plan", END)

graph = builder.compile()
```

这里我们暂时不需要真正的 LLM。

Planner 先用固定数据模拟。

---

### 14. 测试

`tests/test_graph.py`

完整替换：

```python id="2g49ap"
from app.graph.graph import graph


def test_research_plan_is_created() -> None:
    result = graph.invoke(
        {
            "user_query": "Research Apple as a long-term investment",
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
        }
    )

    assert result["ticker"] == "AAPL"

    assert result["research_plan"] == [
        "Analyze company fundamentals",
        "Review financial performance",
        "Analyze market conditions",
        "Analyze industry conditions",
        "Perform valuation analysis",
        "Identify major risks",
    ]
```

运行：

```bash
pytest
```

---

### 15. 这里有一个非常重要的 State 设计问题

你可能已经发现：

我们现在 invoke 的时候需要传：

```python
{
    "user_query": "...",
    "ticker": "...",
    "research_plan": [],
    ...
}
```

这意味着：

> **TypedDict 本身并不会自动给字段提供默认值。**

也就是说：

```python
class GraphState(TypedDict):
    ticker: str
```

并不意味着：

```python
ticker = ""
```

自动存在。

这也是为什么我们现在必须显式初始化 State。

---

### 16. 这会在下一阶段发生变化

等我们进入更真实的 Application Architecture 后，我们会逐步讨论：

```text
Input State
↓
Internal State
↓
Output State
```

以及：

```text
Required
Optional
Default
Derived
Reducer
```

甚至最终可能把复杂业务对象进一步拆成：

```text
ResearchRequest
ResearchPlan
ResearchEvidence
ValuationResult
RiskAnalysis
InvestmentDecision
```

而不是让一个巨大的 `GraphState` 无限膨胀。

**但现在不要过早设计。**

Lesson 6 的目的只是让你开始建立正确的 State 建模意识。

---

### 17. 当前 State 的业务结构

现在可以把它画成：

```text
GraphState
│
├── User Request
│   ├── user_query
│   └── ticker
│
├── Research Planning
│   └── research_plan
│
├── Research
│   ├── company_research
│   ├── financial_research
│   ├── market_research
│   └── industry_research
│
├── Valuation
│   ├── valuation_summary
│   ├── current_price
│   └── target_price
│
├── Risk
│   └── risk_factors
│
└── Investment Decision
    ├── recommendation
    ├── investment_horizon
    └── investment_thesis
```

这已经开始成为我们的真正业务 State。

---

### 18. Lesson 6 Acceptance

运行：

```bash
pytest
```

通过即可继续。

这一课重点不是 LangGraph API，而是掌握：

* State 是**当前 Run 的共享业务上下文**
* State 字段应该有明确业务语义
* `Literal` 可以约束有限业务枚举
* 派生值应该尽可能通过确定性计算产生
* Research / Valuation / Risk / Decision 应该在 State 中有清晰边界
* State 不应该混入 Tool Client、数据库连接等基础设施对象
* 长期 Memory 不等于当前 Graph State
* 不要为了“未来可能用到”而无限扩张 State

---


## Lesson 7 — Input / Internal / Output State

这一课完成后，Phase 1 的核心 State 建模就基本完整。我们会开始解决一个真实应用里非常重要的问题：

> **用户输入的数据，和 Graph 内部运行过程中需要的数据，不应该是同一个概念。**

### 1. 当前的问题

上一课我们的 `GraphState` 已经比较接近业务模型：

```text
GraphState
├── user_query
├── ticker
├── research_plan
├── company_research
├── financial_research
├── market_research
├── industry_research
├── valuation_summary
├── current_price
├── target_price
├── risk_factors
├── recommendation
├── investment_horizon
└── investment_thesis
```

但如果用户调用我们的 Agent，实际上用户只需要提供：

```python
{
    "ticker": "AAPL",
    "user_query": "Research Apple as a long-term investment",
}
```

用户不应该知道：

```text
research_plan
company_research
financial_research
target_price
risk_factors
recommendation
...
```

这些是 **Graph 内部执行状态**。

所以我们需要把三种概念分开：

```text
User Input
     ↓
Internal Graph State
     ↓
Final Output
```

---

### 2. 为什么要分离？

假设未来 FastAPI 接收到：

```json
{
  "ticker": "AAPL",
  "query": "Research Apple"
}
```

Graph 内部可能经历：

```text
Research Planner
      ↓
Company Research
      ↓
Financial Research
      ↓
Market Research
      ↓
Valuation
      ↓
Risk Analysis
      ↓
Investment Decision
      ↓
Report
```

内部 State 会越来越丰富。

但 API 不应该要求用户传：

```json
{
  "ticker": "AAPL",
  "query": "...",
  "research_plan": [],
  "company_research": "",
  "financial_research": "",
  "current_price": 0,
  "target_price": 0,
  "risk_factors": [],
  ...
}
```

这违反了一个基本的 Application Architecture 原则：

> **输入契约和内部执行状态应该解耦。**

---

### 3. LangGraph 提供的能力

我们现在开始使用：

```python
TypedDict
```

定义不同的 State Schema。

结构：

```text
InputState
     ↓
Graph
     ↓
Internal State
     ↓
OutputState
```

我们会让 Graph 明确知道：

* 什么字段允许作为输入
* 什么字段只属于内部运行
* 什么字段允许作为最终输出

---

### 4. 修改 State

打开：

`app/graph/state.py`

完整替换为：

```python id="0abz7j"
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


class OutputState(TypedDict):
    ticker: str
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    current_price: float
    target_price: float
    investment_thesis: str
```

现在我们明确有三个 Schema：

#### InputState

```text
用户真正需要提供的东西
```

#### GraphState

```text
Graph 内部执行需要的完整上下文
```

#### OutputState

```text
最终对用户暴露的结果
```

---

### 5. 修改 Graph

现在需要告诉 `StateGraph`：

> 输入是什么？

> 内部状态是什么？

> 输出是什么？

修改：

`app/graph/graph.py`

完整内容：

```python id="2s8x0y"
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState, InputState, OutputState


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

builder.add_node("create_research_plan", create_research_plan)
builder.add_node("prepare_output", prepare_output)

builder.add_edge(START, "create_research_plan")
builder.add_edge("create_research_plan", "prepare_output")
builder.add_edge("prepare_output", END)

graph = builder.compile()
```

这里第一次出现：

```python id="xk1j4a"
StateGraph(
    GraphState,
    input_schema=InputState,
    output_schema=OutputState,
)
```

它表达的是：

```text
InputState
    ↓
GraphState
    ↓
OutputState
```

---

### 6. 现在的问题：GraphState 还有很多字段

注意我们现在的 `create_research_plan()` 只返回：

```python id="t7g2k6"
{
    "research_plan": [...]
}
```

这其实就是我们前面纠正过的原则：

> **Node 返回它实际更新的字段即可。**

Graph 会继续维护 State。

这也是为什么以后我们不会让每一个 Node 都复制几十个字段。

---

### 7. Output Node

最后：

```python id="04e6f4"
def prepare_output(state: GraphState) -> OutputState:
```

只选择最终需要暴露的数据：

```text id="oxzj4f"
ticker
recommendation
investment_horizon
current_price
target_price
investment_thesis
```

例如内部可能存在：

```text id="9byb4g"
research_plan
company_research
financial_research
market_research
industry_research
valuation_summary
risk_factors
```

但这些不会出现在最终 `OutputState`。

这是非常重要的边界。

---

### 8. 修改测试

`tests/test_graph.py`

完整替换：

```python id="zfl7ma"
from app.graph.graph import graph


def test_graph_separates_input_internal_state_and_output() -> None:
    result = graph.invoke(
        {
            "user_query": "Research Apple as a long-term investment",
            "ticker": "AAPL",
        }
    )

    assert result == {
        "ticker": "AAPL",
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "current_price": 0.0,
        "target_price": 0.0,
        "investment_thesis": "",
    }
```

运行：

```bash
pytest
```

预期：

```text
1 passed
```

---

### 9. 这里有一个值得特别注意的地方

你可能会问：

> `create_research_plan` 产生了 `research_plan`，为什么最终结果里没有它？

因为：

```text
research_plan
```

属于：

**Internal State**

而不是：

**Output State**

Graph 的内部状态可以比最终 API 返回的数据丰富很多。

这会让我们的最终架构更加干净：

```text
                    ┌──────────────────────┐
                    │     Internal State   │
                    │                      │
InputState ───────→ │ Research             │
                    │ Valuation            │
                    │ Risk                 │
                    │ Decision             │
                    │ Report               │
                    └──────────┬───────────┘
                               ↓
                         OutputState
```

---

### 10. 这对最终 FastAPI 非常重要

未来我们的 API 大致会变成：

```text
POST /research
```

输入：

```json
{
  "ticker": "AAPL",
  "query": "Research Apple as a long-term investment"
}
```

而最终输出可能是：

```json
{
  "ticker": "AAPL",
  "recommendation": "Buy",
  "investment_horizon": "Long Term",
  "current_price": 245.50,
  "target_price": 290.00,
  "investment_thesis": "..."
}
```

中间经历多少 Agent、Tool、Research Node、Valuation Node、Risk Node：

**API 调用者不需要知道。**

这就是 Application Layer 和 Graph Internal State 的边界。

---

### 11. 一个重要架构原则

现在可以正式确定：

```text
InputState
```

代表：

> **用户/API → Graph 的契约**

```text
GraphState
```

代表：

> **Graph 内部执行上下文**

```text
OutputState
```

代表：

> **Graph → 用户/API 的契约**

这三个概念以后会一直保留。

---

### 12. Lesson 7 Acceptance

测试通过即可认为 Lesson 7 完成。

你需要确认的不是 API 细节，而是这个模型：

```text
                ┌─────────────────────┐
                │    InputState       │
                │ ticker               │
                │ user_query           │
                └──────────┬──────────┘
                           ↓
                    LangGraph Run
                           ↓
                ┌─────────────────────┐
                │     GraphState      │
                │                     │
                │ Plan                │
                │ Research            │
                │ Valuation           │
                │ Risk                │
                │ Decision            │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │    OutputState      │
                │ Recommendation      │
                │ Horizon             │
                │ Price               │
                │ Thesis              │
                └─────────────────────┘
```

---

### Phase 1 即将结束

到这里我们已经完成：

```text
Phase 1 — Minimal LangGraph Core

Lesson 1  State / Node / Edge              ✅
Lesson 2  Conditional Edge                 ✅
Lesson 3  State Update / Data Flow         ✅
Lesson 4  Reducer / Parallel State         ✅
Lesson 5  Fan-out / Fan-in                 ✅
Lesson 6  Business State Schema             ✅
Lesson 7  Input / Internal / Output State  ← 当前
```

Lesson 7 测试通过后，**Phase 1 可以正式关闭**。

### Phase 1 最终架构

目前项目核心已经可以抽象成：

```text
Investment Research & Decision Agent
                │
                ▼
            InputState
                │
                ▼
          LangGraph Workflow
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    Node A    Node B    Node C
       │        │        │
       └────────┼────────┘
                ▼
           GraphState
                │
                ▼
          Decision Logic
                │
                ▼
           OutputState
```

下一阶段才开始真正引入 LLM。