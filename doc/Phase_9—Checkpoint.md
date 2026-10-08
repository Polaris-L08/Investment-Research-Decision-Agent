# Phase 9 — Checkpoint / Persistence

## Lesson 1 — Checkpoint / Thread / Persistence Concepts

这一课**暂时不写代码**。

这是有意的。

Phase 9 和前面最大的区别之一，就是如果没有先把下面几个概念分清楚：

```text
Thread
Run
State
Checkpoint
Checkpointer
Memory
```

后面非常容易写出“看起来能恢复，实际上没有真正恢复”的代码。

---

### 1. 为什么现在需要 Persistence？

先回到我们当前的 Agent。

现在的执行逻辑本质上是：

```text
User Request
      ↓
Graph
      ↓
State
      ↓
Nodes
      ↓
State
      ↓
...
      ↓
Final Output
```

例如：

```text
User:
分析 NVIDIA 的投资价值
```

Graph 开始执行：

```text
initialize_state
      ↓
company_research
      ↓
llm_node
      ↓
create_research_plan
      ↓
investment_decision
      ↓
prepare_output
      ↓
END
```

如果 Python Process 在：

```text
company_research
      ↓
llm_node
```

之间突然退出：

```text
Python Process
       X
      STOP
```

那么当前 Graph 的 State 也就随进程消失了。

下一次重新启动：

```text
Python Process
      ↓
new graph
      ↓
invoke(...)
```

默认只能重新开始。

这对于一个真正的 Application 是不够的。

---

### 2. Thread 是什么？

这是 Phase 9 最重要的概念之一。

可以先把：

```text
Thread
```

理解为：

> **一个持续存在的 Graph execution context。**

例如：

```text
thread_id = "research-nvda-001"
```

它不是简单的：

```text
HTTP Request ID
```

也不是：

```text
某一次 node execution ID
```

而是：

```text
一个持续的研究执行上下文
```

因此可以形成：

```text
Thread: research-nvda-001

    Run 1
       ↓
    Run 2
       ↓
    Run 3
```

也就是说，同一个 Thread 可以承载这个研究上下文的连续执行。

交接文档中也明确要求我们最终保持：

```text
Thread
 ├── Run 1
 ├── Run 2
 └── Run 3
```

而不是把 `thread_id` 简化成每次 API Request ID。

---

### 3. Run 是什么？

可以把：

```text
Run
```

理解为：

> **一次具体的 Graph execution。**

例如：

```text
Thread A
   │
   ├── Run 1
   │
   ├── Run 2
   │
   └── Run 3
```

这意味着：

```text
Thread
```

是较长期的 execution context，

而：

```text
Run
```

是其中一次具体执行。

但是这里需要一个很重要的 LangGraph 语义意识：

> **不要把 Run、Thread、Checkpoint 当成三个简单的数据库表，然后机械地认为它们是一一对应的。**

尤其是 Checkpoint。

---

### 4. State 是什么？

我们当前已经非常熟悉 State。

例如当前主 Graph 的：

```python
class GraphState(TypedDict):
```

里面包含：

```text
user_query
ticker

research_plan

company_research
financial_research
market_research
industry_research

valuation_summary
current_price
target_price

risk_factors

recommendation
investment_horizon
investment_thesis

research_summary
investment_decision

llm_error
failure_reason
retry_count

tool_error
tool_retry_count
tool_retryable
```

这就是 Graph execution 的状态数据。

所以可以简单理解：

```text
Graph
  ↓
State
```

State 回答的是：

> **“这个 Graph 当前执行到了什么状态？”**

例如：

```text
ticker = NVDA

company_research = ...

current_price = ...

research_summary = ...

investment_decision = ...

retry_count = 1
```

这些都是当前 execution context 的状态。

---

### 5. Checkpoint 是什么？

这是最关键的地方。

Checkpoint 可以理解为：

> **Graph execution 在某个执行节点/步骤上的持久化状态快照。**

也就是说：

```text
State
   ↓
Checkpoint
```

Checkpoint 的目的不是创建另一套业务 State。

而是：

```text
当前 Graph Execution State
        ↓
持久化
        ↓
以后可以恢复
```

例如：

```text
Run
 │
 ▼
Node A
 │
 ▼
Checkpoint
 │
 ▼
Node B
 │
 ▼
Checkpoint
 │
 ▼
Node C
```

所以：

```text
Checkpoint
```

的核心价值是：

> **让 Graph 不再完全依赖当前 Python Process 的内存。**

---

### 6. Checkpoint ≠ Memory

这个区别必须在 Phase 9 一开始就钉死。

我们项目后面还有：

```text
Phase 11 — Long-term Memory
```

所以现在绝对不能把两者混起来。

#### Checkpoint

回答：

> **当前这个 Graph Execution 到哪里了？**

例如：

```text
Thread: research-nvda-001

State:
    ticker = NVDA
    company_research = ...
    current_price = ...
    retry_count = 1
```

这是当前 execution context。

---

#### Long-term Memory

回答：

> **这个 Application / User / System 在过去积累了什么长期信息？**

例如未来可能是：

```text
User Preferences
Research History
Previous Research Context
```

这些属于 Phase 11。

交接文档已经明确要求：

```text
Checkpoint
    ≠
Long-term Memory
```

Checkpoint 是当前 Graph Execution State，而 Memory 是跨 Thread / 跨执行的长期信息。

---

### 7. 用我们的投资 Agent 举例

假设用户：

```text
分析 NVDA，判断未来投资价值。
```

创建：

```text
thread_id = research-nvda-001
```

然后开始执行。

---

#### 第一个阶段

```text
Thread
  ↓
Run 1
  ↓
initialize_state
  ↓
company_research
```

此时 State 可能已经变成：

```text
ticker = NVDA
company_research_result = {...}
current_price = 180.50
```

然后形成一个 checkpoint：

```text
Checkpoint A
```

---

#### 第二个阶段

继续：

```text
Checkpoint A
      ↓
llm_node
      ↓
research_summary
```

形成：

```text
Checkpoint B
```

---

#### 第三个阶段

继续：

```text
Checkpoint B
      ↓
investment_decision
```

形成：

```text
Checkpoint C
```

最终：

```text
Final State
```

---

### 8. 为什么 Application Restart 后还能恢复？

这就是 Checkpointer 的价值。

没有 Persistence：

```text
Python Process
      ↓
Graph
      ↓
State in RAM
      ↓
Process dies
      ↓
State lost
```

有 Persistence：

```text
Python Process
      ↓
Graph
      ↓
State
      ↓
Checkpointer
      ↓
Persistence Backend
```

然后：

```text
Python Process STOP
```

之后重新启动：

```text
New Python Process
      ↓
New Graph Instance
      ↓
Same Persistence Backend
      ↓
Same thread_id
      ↓
Load checkpoint
      ↓
Resume
```

这才是真正的 Persistence。

交接文档把这个定义得非常严格：

```text
旧 Application
    ↓
停止

新 Application
    ↓
读取持久化数据
    ↓
恢复旧 Thread
```

不能只是同一个 Python Process 连续调用两次 `invoke()`。

---

### 9. Checkpointer 是什么？

现在我们可以定义：

```text
Checkpointer
```

是：

> **负责 checkpoint 的保存、读取以及与 Graph execution 生命周期连接的 persistence infrastructure。**

于是架构关系应该是：

```text
             LangGraph
                 │
                 ▼
              State
                 │
                 ▼
            Checkpointer
                 │
                 ▼
       Persistence Backend
```

注意这个结构非常重要。

我们**不希望**：

```text
Agent Node
   ↓
SQLite
```

或者：

```text
Investment Decision Node
   ↓
PostgreSQL
```

这种业务节点直接操作 Persistence。

而应该：

```text
Business Logic
       │
       ▼
     Graph
       │
       ▼
 Checkpointer
       │
       ▼
 Persistence
```

这就是 Phase 9 后面 Lesson 5 要进一步建立的 Engineering Boundary。

---

### 10. Thread Isolation

这是另一个非常重要的生产级要求。

假设：

```text
Thread A
ticker = NVDA
```

和：

```text
Thread B
ticker = AAPL
```

那么必须：

```text
Thread A
    ↓
State A
    ↓
Checkpoint A
```

以及：

```text
Thread B
    ↓
State B
    ↓
Checkpoint B
```

绝不能：

```text
Thread A
    ↓
State A

Thread B
    ↓
读取 State A
```

否则我们会得到非常严重的金融应用数据污染：

```text
User A:
研究 NVDA

User B:
研究 AAPL

        ↓

AAPL Thread
读取了 NVDA 的 checkpoint
```

这是绝对不可接受的。

所以 Phase 9 不只是：

> “把 State 存下来。”

还必须证明：

> **不同 Thread 的 State 是严格隔离的。**

交接文档也把 Thread Isolation 单独列成 Lesson 3，而不是把它当成 Checkpointer 的附带行为。

---

### 11. 现在形成完整模型

到这里，我们可以把 Phase 9 的核心概念串起来：

```text
                    Thread
                       │
                       ▼
                      Run
                       │
                       ▼
                     State
                       │
                       ▼
                  Checkpoint
                       │
                       ▼
                 Checkpointer
                       │
                       ▼
             Persistence Backend
```

然后：

```text
Application Stop
       ↓
Persistence remains
       ↓
Application Restart
       ↓
Same Thread
       ↓
Load Checkpoint
       ↓
Resume
       ↓
Continue Execution
```

---

### 12. 这和 Phase 10 的 HITL 有什么区别？

这个边界现在也必须明确。

Phase 9：

```text
Graph
 ↓
Checkpoint
 ↓
Stop
 ↓
Restart
 ↓
Resume
```

Phase 10：

```text
Graph
 ↓
interrupt()
 ↓
Human
 ├── Approve
 └── Reject
 ↓
Resume
```

虽然两者都涉及：

```text
暂停
恢复
```

但**原因完全不同**。

#### Phase 9

因为：

> Application execution 需要持久化和恢复。

#### Phase 10

因为：

> Workflow 主动等待 Human Decision。

所以 Phase 9 可以学习：

```text
stop / resume
```

但不能因此开始设计：

```text
Approval
Reject
Human Decision
```

否则就是提前进入 Phase 10。交接文档对此也有明确边界。

---

### 13. Lesson 1 到这里暂时不修改代码

这是有意的。

我们当前已经知道：

```text
当前：
builder
   ↓
compile()
   ↓
Graph
```

未来要变成：

```text
builder
   ↓
compile(
    checkpointer=...
)
   ↓
Persistent Graph
```

但是**现在不要急着直接改成这样**。

因为 Lesson 2 我们首先需要根据你当前实际 LangGraph 版本确定：

```text
具体 Checkpointer API
具体 config 结构
thread_id 的传递方式
checkpoint 查询方式
checkpoint identity
```

交接文档也明确规定：具体 LangGraph API 应以项目当前实际安装版本为准，而不是提前固定一个可能随版本变化的写法。

---

### Lesson 1 Acceptance

因此现在这一课的验收不是代码测试，而是概念验收。

你现在应该能够明确区分：

| 概念                    | 核心问题                                 |
|-------------------------|------------------------------------------|
| **Thread**              | 哪一个持续的 execution context？         |
| **Run**                 | 一次具体的 Graph execution 是什么？      |
| **State**               | 当前 Graph execution 的状态是什么？      |
| **Checkpoint**          | State 在执行过程中的持久化快照是什么？   |
| **Checkpointer**        | 谁负责 checkpoint 的保存/恢复？          |
| **Persistence Backend** | checkpoint 实际保存在哪里？              |
| **Memory**              | 跨 execution / Thread 的长期信息是什么？ |

以及最重要的两条：

```text
Checkpoint ≠ Long-term Memory
```

和：

```text
Thread A ≠ Thread B
```

---

### Lesson 1 Acceptance Criteria

按照我们既定交接标准：

```text
[✓] 能解释 Thread / Run / State / Checkpoint
[✓] 能解释 Checkpointer 职责
[✓] 能区分 Checkpoint 与 Memory
[✓] 能解释 Resume
[✓] 能解释 Thread Isolation

[✓] 不修改业务 Domain Model
[✓] 不实现 HITL
[✓] 不实现 Long-term Memory
```
---


## Lesson 2：把 Checkpointer 接入主 Application Graph

这一课开始真正修改代码。

目标非常明确：

> **让当前项目的主 Application Graph 具备 Checkpoint 能力，并证明不同 `thread_id` 之间能够隔离 State。**

本课**不做**：

* 不修改 `GraphState`
* 不增加 `thread_id` 字段
* 不实现 HITL
* 不实现 Long-term Memory
* 不实现 Error Recovery
* 不实现数据库持久化
* 不验证跨进程 Restart → Resume

原因是我们要严格控制 Phase 9 的演进顺序。LangGraph 的官方 Persistence 模型也是：在 `compile()` 时配置 Checkpointer，然后通过 `configurable.thread_id` 选择 Thread；最新 State 可以通过 `get_state()` 获取。([GitHub][1])

---

### 1. Lesson 2 的工程目标

Lesson 1 我们解决的是：

> **Checkpointer 到底是什么？Thread 到底是什么？**

Lesson 2 开始解决：

> **我们的 Agent Graph 到底怎样接入 Checkpointer？**

最终结构从：

```text
Input
  │
  ▼
Application Graph
  │
  ▼
State
  │
  ▼
Output
```

变成：

```text
                    ┌──────────────────────┐
                    │     Checkpointer     │
                    │   InMemorySaver      │
                    └──────────┬───────────┘
                               │
                               │ checkpoint
                               ▼
Input ──► Application Graph ──► State ──► Output
              │
              │
              └──── thread_id ────► Thread
```

这里最重要的是：

**`thread_id` 不属于 `GraphState`。**

它属于：

```python
config
```

也就是说：

```python
config = {
    "configurable": {
        "thread_id": "..."
    }
}
```

而不是：

```python
state = {
    "thread_id": "..."
}
```

这是非常重要的架构边界。

LangGraph 官方也是把 `thread_id` 定义为 Checkpointer 用来定位 Thread 的主键，而不是 Graph State 的业务字段。([GitHub][2])

---

### 2. 为什么 Lesson 2 使用 `InMemorySaver`

本项目当前使用：

```text
LangGraph 1.2.12
```

因此使用：

```python
from langgraph.checkpoint.memory import InMemorySaver
```

官方 API 中，`InMemorySaver` 就是内存型 Checkpointer；它可以用于测试和调试。([LangChain 参考文档][3])

但是必须非常明确：

```text
InMemorySaver
        │
        ├── 可以验证 Checkpointer API
        ├── 可以验证 Thread
        ├── 可以验证 State Snapshot
        ├── 可以验证 Thread Isolation
        │
        └── 不能跨进程持久化
```

也就是说：

```text
Process A
    │
    ├── Thread A
    ├── Checkpoint A
    │
    ▼
Process STOP
    │
    X
    │
Process B
    │
    └── InMemorySaver 中已经没有 A
```

官方文档也明确说明，`InMemorySaver` 存储在 RAM 中，进程重启后 checkpoint 会丢失。([GitHub][1])

所以：

> **Lesson 2 不是最终 Persistence。**

我们现在只是先把：

```text
Graph
  +
Checkpointer
  +
Thread
```

这条 Runtime 链路打通。

真正的：

```text
STOP
  ↓
RESTART
  ↓
same thread_id
  ↓
load checkpoint
  ↓
resume
```

要在后面的 Persistence Lesson 中完成。

---

### 3. 本项目的 Persistence Boundary

这是这一课另一个非常重要的架构决定。

目前项目里有很多 Graph：

```text
Main Application Graph
        │
        ├── Research Graph
        ├── Tool Graph
        ├── Tool Loop
        ├── Report Graph
        └── Agent Subgraphs
```

我们现在**不**做：

```python
every_subgraph.compile(
    checkpointer=...
)
```

而是首先确定：

```text
                 ┌─────────────────────┐
                 │ Main Application    │
                 │ Graph               │
                 │                     │
                 │  Checkpointer       │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
              Subgraph              Subgraph
```

也就是说：

> **Phase 9 第一阶段的 Persistence Boundary 是 Main Application Graph。**

这是有意的。

否则很容易出现：

```text
Main Graph
    ↓
Research Graph
    ↓
Tool Graph
    ↓
Report Graph
```

每一个 Graph 都拥有自己的 checkpoint 生命周期，最终 Thread / checkpoint namespace / resume 关系会变得非常复杂。

当前阶段我们先把：

```text
Application-level execution durability
```

建立起来。

---

### 4. Graph Topology 不发生变化

这一点也非常重要。

Lesson 2 **不会增加任何 Node**。

现在：

```text
START
  │
  ▼
initialize_state
  │
  ▼
company_research
  │
  ├──────────────► company_research_failure
  │
  ▼
llm_node
  │
  ├── retry ─────► retry_llm
  │                  │
  │                  └────► llm_node
  │
  ├──────────────► handle_llm_failure
  │
  ▼
create_research_plan
  │
  ▼
investment_decision_node
  │
  ├──────────────► handle_llm_failure
  │
  ▼
prepare_output
  │
  ▼
END
```

仍然完全不变。

变化只有：

```text
Before:

builder.compile()


After:

builder
   │
   ▼
compile(checkpointer=InMemorySaver())
   │
   ▼
graph
```

所以这不是业务逻辑变化。

它是：

> **Graph Runtime Infrastructure 的增强。**

---

### 5. 修改 `app/graph/graph.py`

当前文件最后是：

```python
graph = builder.compile()
```

我们只需要增加 Checkpointer。

#### 5.1 增加 import

在 `app/graph/graph.py` 的 import 区域加入：

```python
from langgraph.checkpoint.memory import InMemorySaver
```

例如原本：

```python
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState, InputState, OutputState
```

修改成：

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState, InputState, OutputState
```

---

#### 5.2 修改 Graph Compile

原来：

```python
graph = builder.compile()
```

改成：

```python
checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
)
```

也就是：

```python
builder
    │
    │ compile()
    ▼
graph
```

变成：

```python
builder
    │
    │ compile(checkpointer=checkpointer)
    ▼
graph
    │
    ▼
InMemorySaver
```

#### 最终这一部分应该是

```python
checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
)
```

---

### 6. 为什么 `checkpointer` 放在 Graph Compile 层

这是一个非常值得理解的设计。

错误思路是：

```python
def initialize_state(state):
    save_checkpoint(state)
```

然后：

```python
def llm_node(state):
    save_checkpoint(state)
```

再：

```python
def investment_decision_node(state):
    save_checkpoint(state)
```

这样做的问题是：

> Checkpoint 变成业务 Node 自己负责的事情。

这会导致：

```text
Business Logic
     +
Persistence Logic
```

强耦合。

而 LangGraph 的设计是：

```text
Node
 │
 └── only business/state transformation


Graph Runtime
 │
 └── checkpoint lifecycle


Checkpointer
 │
 └── persistence
```

因此：

```python
builder.compile(
    checkpointer=checkpointer
)
```

才是正确的边界。

官方文档的 Quickstart 也是在 `compile()` 时配置 Checkpointer。([GitHub][1])

---

### 7. `thread_id` 应该在哪里出现？

Graph 本身：

```python
graph
```

不需要知道：

```text
user123
```

或者：

```text
research-session-001
```

这些 Thread 信息。

真正执行时：

```python
config = {
    "configurable": {
        "thread_id": "research-thread-001",
    }
}
```

然后：

```python
graph.invoke(
    input_data,
    config,
)
```

因此架构变成：

```text
Application
     │
     │ input
     │
     ├─────────────────────┐
     │                     │
     ▼                     ▼
Graph                 Runtime Config
                           │
                           ▼
                      thread_id
                           │
                           ▼
                      Checkpointer
```

这意味着：

> **Thread 是 Runtime Context，而不是 Domain State。**

因此本课再次强调：

#### 不修改 `GraphState`

不要添加：

```python
thread_id: str
```

不要添加：

```python
checkpoint_id: str
```

不要添加：

```python
resume_state: ...
```

也不要添加：

```python
memory: ...
```

`state.py` 本课保持不变。

---

### 8. Lesson 2 的测试策略

这里需要特别认真。

如果我们直接：

```python
graph.invoke(...)
```

那么当前 Application Graph 会进入：

```text
Research
LLM
Tools
Valuation
Risk
Decision
```

这会把 Checkpointer 测试和整个业务执行链绑定起来。

这不是我们这一课想验证的东西。

我们现在需要验证三个层次：

#### Test A — Main Graph 已经接入 Checkpointer

验证：

```text
graph
  ↓
checkpointer
```

确实存在。

#### Test B — Checkpoint 能按照 Thread 保存

建立一个非常小的测试 Graph：

```text
START
  ↓
increment
  ↓
END
```

然后：

```text
thread-A
```

执行。

验证：

```python
graph.get_state(config)
```

能够拿到 checkpoint。

官方 API 提供的就是 `get_state(config)`，它返回当前 Thread 对应的 `StateSnapshot`。([GitHub][2])

#### Test C — Thread Isolation

执行：

```text
thread-A → value = 10
thread-B → value = 20
```

然后：

```text
get_state(thread-A)
get_state(thread-B)
```

必须得到：

```text
A → 10
B → 20
```

而不是：

```text
A → 20
```

这才真正证明：

> `thread_id` 是 Checkpoint 的隔离边界。

---

### 9. 新增测试文件

新建：

```text
tests/test_checkpoint.py
```

完整内容：

```python
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.graph import graph


class CounterState(TypedDict):
    value: int


def build_test_graph():
    builder = StateGraph(CounterState)

    def increment(state: CounterState):
        return {
            "value": state["value"] + 1,
        }

    builder.add_node("increment", increment)

    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)

    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
    )


def test_main_application_graph_has_checkpointer():
    assert graph.checkpointer is not None


def test_checkpointer_persists_state_for_a_thread():
    test_graph = build_test_graph()

    config = {
        "configurable": {
            "thread_id": "checkpoint-test-thread",
        }
    }

    result = test_graph.invoke(
        {"value": 0},
        config,
    )

    assert result["value"] == 1

    snapshot = test_graph.get_state(config)

    assert snapshot.values["value"] == 1
    assert snapshot.config["configurable"]["thread_id"] == (
        "checkpoint-test-thread"
    )


def test_threads_are_isolated():
    test_graph = build_test_graph()

    thread_a = {
        "configurable": {
            "thread_id": "thread-a",
        }
    }

    thread_b = {
        "configurable": {
            "thread_id": "thread-b",
        }
    }

    result_a = test_graph.invoke(
        {"value": 10},
        thread_a,
    )

    result_b = test_graph.invoke(
        {"value": 20},
        thread_b,
    )

    assert result_a["value"] == 11
    assert result_b["value"] == 21

    snapshot_a = test_graph.get_state(thread_a)
    snapshot_b = test_graph.get_state(thread_b)

    assert snapshot_a.values["value"] == 11
    assert snapshot_b.values["value"] == 21

    assert (
        snapshot_a.config["configurable"]["thread_id"]
        == "thread-a"
    )

    assert (
        snapshot_b.config["configurable"]["thread_id"]
        == "thread-b"
    )
```

---

### 10. 为什么测试 Graph 可以是假的？

这是一个非常重要的测试思想。

这里：

```python
CounterState
```

以及：

```python
increment()
```

不是项目业务逻辑。

它们只是：

> **Infrastructure Test Fixture**

我们测试的是：

```text
LangGraph
    +
Checkpointer
    +
thread_id
    +
State Snapshot
```

而不是：

```text
Investment Research
```

因此测试 Graph 越简单越好。

---

### 11. 第一个测试到底证明什么？

```python
def test_main_application_graph_has_checkpointer():
    assert graph.checkpointer is not None
```

它验证的是：

```text
app.graph.graph.graph
            │
            ▼
      Compiled Graph
            │
            ▼
       Checkpointer
```

已经存在。

这是一项非常基础但有价值的 Architecture Test。

它可以防止未来有人不小心把：

```python
graph = builder.compile(
    checkpointer=checkpointer,
)
```

改回：

```python
graph = builder.compile()
```

而业务测试可能仍然全部通过。

---

### 12. 第二个测试：Checkpoint 真正产生

核心代码：

```python
result = test_graph.invoke(
    {"value": 0},
    config,
)
```

然后：

```python
snapshot = test_graph.get_state(config)
```

最后：

```python
assert snapshot.values["value"] == 1
```

这里的链路是：

```text
invoke()
   │
   ▼
increment
   │
   ▼
value = 1
   │
   ▼
Checkpointer
   │
   ▼
Thread = checkpoint-test-thread
   │
   ▼
get_state()
   │
   ▼
StateSnapshot
```

所以我们已经证明：

```text
Graph State
     ↓
Checkpoint
     ↓
Thread
     ↓
StateSnapshot
```

整个链路是成立的。

---

### 13. 第三个测试：Thread Isolation

这是本课最重要的测试。

先：

```python
thread_a = {
    "configurable": {
        "thread_id": "thread-a",
    }
}
```

再：

```python
thread_b = {
    "configurable": {
        "thread_id": "thread-b",
    }
}
```

执行：

```python
test_graph.invoke(
    {"value": 10},
    thread_a,
)
```

得到：

```text
thread-a → 11
```

然后：

```python
test_graph.invoke(
    {"value": 20},
    thread_b,
)
```

得到：

```text
thread-b → 21
```

然后分别读取：

```python
snapshot_a = test_graph.get_state(thread_a)
snapshot_b = test_graph.get_state(thread_b)
```

要求：

```text
snapshot_a → 11
snapshot_b → 21
```

而不能出现：

```text
snapshot_a → 21
```

或者：

```text
snapshot_b → 11
```

这就是 Thread Isolation。

---

### 14. 一个非常容易犯的错误

不要写成：

```python
config = {
    "thread_id": "thread-a"
}
```

而应该：

```python
config = {
    "configurable": {
        "thread_id": "thread-a"
    }
}
```

因为 LangGraph Runtime Configuration 中，`thread_id` 位于：

```text
config
└── configurable
    └── thread_id
```

官方文档明确使用这一结构。([GitHub][1])

---

### 15. 本课暂时不测试什么？

这里必须画一条线。

我们现在**不会**测试：

```text
Process 1
   │
   ▼
invoke
   │
   ▼
STOP
   │
   X
   │
Process 2
   │
   ▼
same thread_id
   │
   ▼
resume
```

因为：

```python
InMemorySaver()
```

本身就在：

```text
Process Memory
```

里面。

Process 结束以后：

```text
InMemorySaver
      ↓
    消失
```

官方文档对此有明确说明。([GitHub][1])

所以：

> **如果这一课的测试能够证明跨进程恢复，反而说明测试设计有问题。**

真正的跨 Restart Persistence 会在后面的 Lesson 中使用持久化 Checkpointer。

---

### 16. Lesson 2 完成后的架构

现在项目变成：

```text
                       Application
                            │
                            ▼
                   ┌─────────────────┐
                   │ Main Graph      │
                   │                 │
                   │ initialize      │
                   │ research        │
                   │ LLM             │
                   │ planning        │
                   │ decision        │
                   │ output          │
                   └────────┬────────┘
                            │
                            │ State
                            ▼
                   ┌─────────────────┐
                   │  Checkpointer   │
                   │                 │
                   │ InMemorySaver   │
                   └────────┬────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
             Thread A              Thread B
                 │                     │
             Checkpoints           Checkpoints
```

而 Runtime Config：

```text
config
└── configurable
    └── thread_id
```

与：

```text
GraphState
```

保持完全分离。

---

### 17. Lesson 2 的验收标准

本课必须满足以下条件。

#### A. Checkpointer Integration

```text
[✓] app/graph/graph.py 引入 InMemorySaver
[✓] Main Application Graph 使用 checkpointer 编译
[✓] Graph Topology 没有改变
```

---

#### B. State Boundary

```text
[✓] GraphState 没有增加 thread_id
[✓] GraphState 没有增加 checkpoint_id
[✓] GraphState 没有增加 memory
[✓] Domain Model 没有因为 Persistence 改变
```

---

#### C. Thread Runtime

```text
[✓] thread_id 位于 config["configurable"]
[✓] graph.invoke() 可以携带 thread_id
[✓] graph.get_state() 可以读取 Thread Snapshot
```

---

#### D. Thread Isolation

```text
[✓] Thread A 可以保存自己的 State
[✓] Thread B 可以保存自己的 State
[✓] A 不会读取到 B 的 State
[✓] B 不会读取到 A 的 State
```

---

#### E. Testing

```text
[✓] Main Graph Checkpointer 存在性测试
[✓] Checkpoint State Snapshot 测试
[✓] Thread Isolation 测试
```

---

#### F. Phase Boundary

```text
[✓] 没有实现 HITL
[✓] 没有实现 Long-term Memory
[✓] 没有实现 Error Recovery
[✓] 没有实现 Observability
[✓] 没有实现 Evaluation
[✓] 没有实现 FastAPI
[✓] 没有实现跨进程 Persistence
```

---

### 18. 本课最重要的三个理解

#### 第一：Checkpointer 不是 Node

错误：

```text
Node → save_checkpoint()
```

正确：

```text
Graph Runtime
      │
      ▼
Checkpointer
```

---

#### 第二：Thread 不属于 State

错误：

```python
class GraphState:
    thread_id: str
```

正确：

```python
config = {
    "configurable": {
        "thread_id": "..."
    }
}
```

---

#### 第三：InMemorySaver ≠ 最终生产 Persistence

当前：

```text
Graph
  ↓
InMemorySaver
  ↓
Thread
  ↓
Checkpoint
```

只是把 Runtime Contract 建立起来。

最终工业级架构需要：

```text
Graph
  ↓
Checkpointer
  ↓
Persistent Backend
  ↓
Database / durable storage
  ↓
Application Restart
  ↓
same thread_id
  ↓
load checkpoint
  ↓
Resume
```

而且官方明确建议 `InMemorySaver` 仅用于调试/测试，生产环境应使用持久化 Checkpointer。([LangChain 参考文档][3])

---