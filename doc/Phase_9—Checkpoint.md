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


## Lesson 3：从 InMemorySaver 到真正的持久化 Checkpoint

Lesson 2 已经证明：

```text
Graph
  ↓
Checkpointer
  ↓
thread_id
  ↓
StateSnapshot
```

这一课继续向前走一步：

> **把 Checkpoint 从进程内存搬到磁盘，使它能够跨 Application Restart 存活。**

这才是 Phase 9 真正意义上的 **Persistence**。

---

### 1. Lesson 3 的目标

本课完成后，我们要得到：

```text
Application Process A
        │
        ▼
Main Application Graph
        │
        ▼
SqliteSaver
        │
        ▼
checkpoints.sqlite
        │
        X
     Process STOP
        │
        ▼
Application Process B
        │
        ▼
重新创建 Graph
        │
        ▼
重新打开同一个 SQLite
        │
        ▼
same thread_id
        │
        ▼
读取之前的 Checkpoint
```

也就是说，本课第一次验证：

```text
STOP
  ↓
RESTART
  ↓
SAME THREAD
  ↓
STATE STILL EXISTS
```

这和 Lesson 2 的：

```text
InMemorySaver
```

是本质不同的。

LangGraph 官方当前将 `InMemorySaver` 定位为调试/测试用途，而 `SqliteSaver` 是本地文件持久化实现；更进一步的生产环境通常使用 PostgreSQL 等持久化后端。([GitHub][1])

---

### 2. 为什么这一课选择 SQLite

当前项目是：

```text
Python
+
LangGraph
+
本地 Agent Application
```

我们现在需要的是一个：

* 真正落盘
* 不需要启动额外数据库服务
* 能验证 Restart
* API 简单
* 测试方便

的 Persistence Backend。

SQLite 正好适合这个阶段。

架构：

```text
                Checkpointer
                     │
                     ▼
                SqliteSaver
                     │
                     ▼
             ┌────────────────┐
             │ SQLite File    │
             │                │
             │ checkpoints    │
             │ writes         │
             └────────────────┘
```

LangGraph 官方提供独立的：

```text
langgraph-checkpoint-sqlite
```

包来提供 `SqliteSaver`。它支持基于 SQLite 的 checkpoint 持久化；官方文档将其定位为本地开发、测试和轻量级部署场景。([GitHub][2])

---

### 3. 一个重要的架构认识

到 Lesson 2 为止：

```text
Application
    │
    ▼
Graph
    │
    ▼
InMemorySaver
    │
    ▼
RAM
```

现在：

```text
Application
    │
    ▼
Graph
    │
    ▼
SqliteSaver
    │
    ▼
SQLite
    │
    ▼
Disk
```

因此真正发生变化的是：

```text
Persistence Backend
```

而不是：

```text
GraphState
```

也不是：

```text
Node
```

更不是：

```text
Graph Topology
```

---

### 4. 本课依然不修改 Domain Model

再次强调：

`app/graph/state.py`

**不修改。**

不要加入：

```python
thread_id: str
```

不要加入：

```python
checkpoint_id: str
```

不要加入：

```python
checkpoint: ...
```

不要加入：

```python
memory: ...
```

Persistence 仍然属于：

```text
Runtime Infrastructure
```

而不是：

```text
Domain State
```

---

### 5. 依赖变化

Lesson 2 使用的：

```python
from langgraph.checkpoint.memory import InMemorySaver
```

属于 LangGraph Checkpoint 基础包。

SQLite 则是独立扩展包：

```text
langgraph-checkpoint-sqlite
```

官方安装方式是：

```bash
uv add langgraph-checkpoint-sqlite
```

([GitHub][2])

因此项目的依赖从：

```toml
dependencies = [
    "langgraph",
    "pydantic>=2.0",
]
```

增加：

```toml
"langgraph-checkpoint-sqlite",
```

最终：

```toml
dependencies = [
    "langgraph",
    "langgraph-checkpoint-sqlite",
    "pydantic>=2.0",
]
```

如果你的项目使用的是 `uv`，推荐直接：

```powershell
uv add langgraph-checkpoint-sqlite
```

而不是手工编辑 lock file。

---

### 6. Persistence Backend 的位置

这里我们需要做一个小但重要的架构调整。

Lesson 2 是：

```python
checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
)
```

这在验证概念时没有问题。

但是现在我们有了真正的外部资源：

```text
SQLite connection
```

继续把所有东西塞进：

```text
app/graph/graph.py
```

会逐渐让 Graph Definition 和 Persistence Infrastructure 耦合。

因此这一课新增：

```text
app/graph/checkpointer.py
```

注意：

> 这不是为了“增加目录层次感”，而是因为 Persistence Backend 已经成为一个独立的 runtime infrastructure concern。

我们没有新建：

```text
app/infrastructure/persistence/
app/core/database/
app/services/checkpoint/
```

这一大堆目录。

当前项目规模下：

```text
app/graph/checkpointer.py
```

已经足够。

---

### 7. 新增 `app/graph/checkpointer.py`

完整内容：

```python
from pathlib import Path
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CHECKPOINT_DB_PATH = DATA_DIR / "checkpoints.sqlite"


def create_checkpointer() -> SqliteSaver:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        CHECKPOINT_DB_PATH,
        check_same_thread=False,
    )

    return SqliteSaver(connection)
```

这里有几个关键点。

---

### 8. 为什么使用 `Path`

不要写：

```python
sqlite3.connect(
    "D:\\PycharmProject\\xxx\\checkpoints.sqlite"
)
```

因为这会把开发机器路径写死。

我们使用：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
```

因此：

```text
app/
  graph/
    checkpointer.py
```

向上：

```text
parents[0] → graph
parents[1] → app
parents[2] → project root
```

然后：

```python
DATA_DIR = PROJECT_ROOT / "data"
```

得到：

```text
project/
├── app/
├── tests/
├── pyproject.toml
└── data/
    └── checkpoints.sqlite
```

---

### 9. 为什么 `data/` 不应该提交到 Git

SQLite 文件是：

```text
Runtime Data
```

不是：

```text
Source Code
```

因此应该加入 `.gitignore`：

```gitignore
data/
```

如果项目当前已经存在 `.gitignore`，加入：

```gitignore
data/
```

如果没有，则新建：

```text
.gitignore
```

完整内容至少包含：

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc

data/
```

如果你原来的 `.gitignore` 已经包含前面的内容，则**只增加**：

```gitignore
data/
```

不要覆盖已有规则。

---

### 10. 为什么 `check_same_thread=False`

我们使用：

```python
sqlite3.connect(
    CHECKPOINT_DB_PATH,
    check_same_thread=False,
)
```

这里不是因为我们现在已经实现了多线程 Agent。

而是因为 `SqliteSaver` 的实现本身对 SQLite connection 有线程安全处理；官方示例也使用 `check_same_thread=False`。([GitHub][3])

不过必须注意：

> SQLite 本身不是我们最终的生产级高并发 Persistence Backend。

官方当前的说明也明确指出 `SqliteSaver` 更适合 lightweight synchronous use cases，并不适合扩展到多线程/高并发生产场景。([GitHub][3])

所以：

```text
SQLite
```

在本项目中的定位是：

```text
Phase 9
Development / Local Persistence
```

而不是最终：

```text
Production Distributed Persistence
```

后续真正进入生产化阶段时，再切换 PostgreSQL 等后端。

---

### 11. 修改 `app/graph/graph.py`

原来 Lesson 2：

```python
from langgraph.checkpoint.memory import InMemorySaver
```

删除。

增加：

```python
from app.graph.checkpointer import create_checkpointer
```

然后原来的：

```python
checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
)
```

修改为：

```python
checkpointer = create_checkpointer()

graph = builder.compile(
    checkpointer=checkpointer,
)
```

所以 `graph.py` 的 Persistence 部分最终是：

```python
from app.graph.checkpointer import create_checkpointer
```

以及：

```python
checkpointer = create_checkpointer()

graph = builder.compile(
    checkpointer=checkpointer,
)
```

---

### 12. 当前 Main Graph 的架构

现在：

```text
app/graph/graph.py
        │
        │ create_checkpointer()
        ▼
app/graph/checkpointer.py
        │
        ▼
SqliteSaver
        │
        ▼
data/checkpoints.sqlite
```

Graph Definition 本身仍然只负责：

```text
Node
Edge
Conditional Edge
Compile
```

Persistence Backend 负责：

```text
Checkpoint Storage
```

这是一个比 Lesson 2 更清晰的边界。

---

### 13. Graph Topology 仍然完全不变

依旧是：

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

唯一变化：

```text
InMemorySaver
      ↓
SqliteSaver
```

所以这仍然不是业务逻辑改造。

---

### 14. 一个重要问题：SQLite 什么时候创建？

我们的代码：

```python
connection = sqlite3.connect(
    CHECKPOINT_DB_PATH,
    check_same_thread=False,
)
```

会创建：

```text
data/checkpoints.sqlite
```

但 checkpoint 表并不是简单依赖 SQLite 文件本身。

`SqliteSaver` 会在第一次需要时建立自己的数据库结构。官方实现中包含 `checkpoints` 和 `writes` 表，并且 `setup()` 会负责创建它们。([GitHub][3])

因此我们不需要自己写：

```sql
CREATE TABLE checkpoints ...
```

更不能自己设计一套表结构替代 LangGraph 的 Checkpointer。

否则就会变成：

```text
Our custom persistence layer
          +
LangGraph checkpoint model
```

两套模型，很容易失控。

---

### 15. Lesson 3 的关键验证：Restart

这一课真正重要的测试不是：

```python
graph.get_state(config)
```

因为 Lesson 2 已经证明这个能力。

这一课必须证明：

```text
Graph Instance A
       │
       ▼
SQLite
       │
       X
   destroy A
       │
       ▼
Graph Instance B
       │
       ▼
same SQLite
       │
       ▼
same thread_id
       │
       ▼
old State
```

也就是说：

> **我们不复用同一个 Graph Instance。**

这是关键。

---

### 16. 测试 Graph Builder

在：

```text
tests/test_checkpoint.py
```

中，我们需要一个可以反复创建的 Graph。

可以把之前的：

```python
build_test_graph()
```

保留，但增加 SQLite 版本。

完整的测试文件建议改成：

```python
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from typing import TypedDict

from app.graph.graph import graph


class CounterState(TypedDict):
    value: int


def build_test_graph(checkpointer):
    builder = StateGraph(CounterState)

    def increment(state: CounterState):
        return {
            "value": state["value"] + 1,
        }

    builder.add_node("increment", increment)

    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)

    return builder.compile(
        checkpointer=checkpointer,
    )


def test_main_application_graph_has_checkpointer():
    assert graph.checkpointer is not None


def test_sqlite_checkpointer_persists_state(tmp_path):
    database_path = tmp_path / "checkpoints.sqlite"

    connection = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    checkpointer = SqliteSaver(connection)

    test_graph = build_test_graph(checkpointer)

    config = {
        "configurable": {
            "thread_id": "sqlite-test-thread",
        }
    }

    result = test_graph.invoke(
        {"value": 0},
        config,
    )

    assert result["value"] == 1

    snapshot = test_graph.get_state(config)

    assert snapshot.values["value"] == 1


def test_sqlite_checkpoint_survives_graph_recreation(tmp_path):
    database_path = tmp_path / "restart-test.sqlite"

    config = {
        "configurable": {
            "thread_id": "restart-test-thread",
        }
    }

    connection_1 = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    checkpointer_1 = SqliteSaver(connection_1)

    graph_1 = build_test_graph(checkpointer_1)

    result_1 = graph_1.invoke(
        {"value": 10},
        config,
    )

    assert result_1["value"] == 11

    connection_1.close()

    connection_2 = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    checkpointer_2 = SqliteSaver(connection_2)

    graph_2 = build_test_graph(checkpointer_2)

    snapshot = graph_2.get_state(config)

    assert snapshot.values["value"] == 11

    connection_2.close()


def test_sqlite_threads_are_isolated(tmp_path):
    database_path = tmp_path / "thread-isolation.sqlite"

    connection = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    checkpointer = SqliteSaver(connection)

    test_graph = build_test_graph(checkpointer)

    thread_a = {
        "configurable": {
            "thread_id": "sqlite-thread-a",
        }
    }

    thread_b = {
        "configurable": {
            "thread_id": "sqlite-thread-b",
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

    connection.close()
```

---

### 17. 这里为什么使用 `tmp_path`

测试绝对不要直接写：

```text
data/checkpoints.sqlite
```

否则测试运行以后：

```text
tests
  ↓
修改真实运行数据
```

会产生污染。

pytest 提供：

```python
tmp_path
```

因此：

```python
database_path = tmp_path / "restart-test.sqlite"
```

会得到一个测试专用临时数据库。

测试结束后由 pytest 管理临时目录。

因此：

```text
Production Runtime
        ↓
data/checkpoints.sqlite


Tests
        ↓
temporary sqlite file
```

完全隔离。

---

### 18. Restart Test 为什么特别重要

看这个测试：

```python
connection_1 = sqlite3.connect(
    database_path,
    check_same_thread=False,
)
```

然后：

```python
graph_1 = build_test_graph(checkpointer_1)
```

执行：

```python
result_1 = graph_1.invoke(
    {"value": 10},
    config,
)
```

得到：

```text
11
```

Checkpoint 写入：

```text
restart-test.sqlite
```

然后：

```python
connection_1.close()
```

这一步非常重要。

它模拟：

```text
Application STOP
```

然后重新：

```python
connection_2 = sqlite3.connect(
    database_path,
    check_same_thread=False,
)
```

重新：

```python
checkpointer_2 = SqliteSaver(connection_2)
```

重新：

```python
graph_2 = build_test_graph(checkpointer_2)
```

此时：

```text
graph_1
```

已经不存在。

我们使用的是：

```text
graph_2
```

但是：

```python
config = {
    "configurable": {
        "thread_id": "restart-test-thread",
    }
}
```

保持完全相同。

于是：

```python
snapshot = graph_2.get_state(config)
```

应该仍然得到：

```text
value = 11
```

这就是本项目第一次真正意义上的：

```text
Persistence
```

---

### 19. 注意：这里还不是 Resume

这里要特别避免一个概念混淆。

我们现在证明：

```text
Restart
  ↓
same thread_id
  ↓
load old checkpoint
```

但是我们还没有实现：

```text
Resume execution from checkpoint
```

因此：

```text
Persistence
```

和：

```text
Resume
```

仍然是两个概念。

本课首先证明：

> **Checkpoint 在 Application Restart 后仍然存在。**

后续再专门处理：

> **如何从特定 checkpoint 恢复 Graph execution。**

这也是为什么 Phase 9 不能被简单理解成“加一个数据库”。

---

### 20. 一个非常重要的 SQLite 测试边界

测试里：

```python
connection_1.close()
```

然后重新：

```python
connection_2
```

非常关键。

如果我们只是：

```python
graph_1.invoke(...)
graph_1.get_state(...)
```

那么仍然可能只是：

```text
同一个 Process
同一个 Connection
同一个 Graph
```

无法证明真正的持久化。

所以 Lesson 3 的验收测试必须包含：

```text
Connection 1
    ↓
write
    ↓
close
    ↓
Connection 2
    ↓
read
```

这才是真正的 Disk Persistence Test。

---

### 21. 安全问题：Checkpoint 是可反序列化数据

这里开始进入一个之前 InMemorySaver 不明显、但生产化必须关注的问题。

Checkpoint 存储的不只是简单：

```text
{"value": 1}
```

LangGraph 的 Checkpoint Serialization 涉及对象序列化。

当前官方文档特别提醒，Checkpoint 反序列化需要考虑不可信数据库内容，并提供：

```text
LANGGRAPH_STRICT_MSGPACK=true
```

以及显式允许的 module list 等安全控制。([GitHub][2])

因此本项目后续进入 Production Persistence 时，还需要专门处理：

```text
Serialization Security
```

但是：

> **本课暂时不把它扩展成一个新的安全子系统。**

现在先建立正确 Persistence Boundary。

---

### 22. 为什么现在不直接上 PostgreSQL？

这是一个非常容易产生的疑问。

既然我们的最终目标是：

```text
Industrial-grade Agent
```

为什么不直接：

```text
PostgreSQL
```

答案是：

#### 因为这一课的目标不是验证生产数据库。

我们要先验证：

```text
Graph
  ↓
Checkpointer
  ↓
Persistent Backend
  ↓
Restart
  ↓
same Thread
  ↓
old State
```

SQLite 足够完成这个验证。

如果直接引入 PostgreSQL：

```text
Agent
  ↓
LangGraph
  ↓
Postgres
  ↓
Docker
  ↓
Connection Pool
  ↓
Migration
  ↓
Environment Config
```

会把本课真正要学习的：

```text
Checkpoint Persistence Semantics
```

淹没在基础设施配置中。

而且官方当前也把 SQLite 定位为 local/lightweight 场景，把 PostgreSQL 定位为生产 workload。([LangChain 参考文档][4])

所以路线应该是：

```text
Lesson 2
InMemorySaver
     ↓
Lesson 3
SqliteSaver
     ↓
后续生产化阶段
Postgres / durable production backend
```

而不是：

```text
Lesson 2
InMemorySaver
     ↓
直接跳到复杂生产部署
```

---

### 23. 本课完成后的完整架构

现在我们拥有：

```text
                     Application
                          │
                          ▼
                 Main Application Graph
                          │
                          │
                          ▼
                    Checkpointer
                          │
                          ▼
                    SqliteSaver
                          │
                          ▼
                ┌────────────────────┐
                │ checkpoints.sqlite │
                └─────────┬──────────┘
                          │
               ┌──────────┴──────────┐
               │                     │
               ▼                     ▼
          Thread A               Thread B
               │                     │
          Checkpoints           Checkpoints
```

而 Application Restart：

```text
             PROCESS A
                 │
                 ▼
          SqliteSaver #1
                 │
                 ▼
          checkpoints.sqlite
                 │
                 X
             PROCESS STOP
                 │
                 ▼
             PROCESS B
                 │
                 ▼
          SqliteSaver #2
                 │
                 ▼
          checkpoints.sqlite
                 │
                 ▼
          same thread_id
                 │
                 ▼
          previous checkpoint
```

这条链路已经成立。

---

### 25. 本课运行顺序

首先安装依赖：

```powershell
uv add langgraph-checkpoint-sqlite
```

然后运行：

```powershell
pytest tests/test_checkpoint.py -v
```

预期至少：

```text
4 passed
```

然后：

```powershell
pytest -v
```

---

### 26. 手工验证真正的 SQLite Persistence

为了让你真正看到：

```text
Process A
```

和：

```text
Process B
```

之间的区别，建议额外做一次手工实验。

可以建立一个临时测试脚本：

```text
tests/manual_checkpoint_write.py
```

内容：

```python
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from typing import TypedDict


class State(TypedDict):
    value: int


def increment(state: State):
    return {
        "value": state["value"] + 1,
    }


builder = StateGraph(State)

builder.add_node("increment", increment)

builder.add_edge(START, "increment")
builder.add_edge("increment", END)


connection = sqlite3.connect(
    "restart-demo.sqlite",
    check_same_thread=False,
)

checkpointer = SqliteSaver(connection)

graph = builder.compile(
    checkpointer=checkpointer,
)

config = {
    "configurable": {
        "thread_id": "demo-thread",
    }
}

result = graph.invoke(
    {"value": 100},
    config,
)

print(result)

connection.close()
```

执行：

```powershell
python tests/manual_checkpoint_write.py
```

应该得到：

```text
{'value': 101}
```

然后这个 Python Process 结束。

现在再建立：

```text
tests/manual_checkpoint_read.py
```

内容：

```python
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from typing import TypedDict


class State(TypedDict):
    value: int


def increment(state: State):
    return {
        "value": state["value"] + 1,
    }


builder = StateGraph(State)

builder.add_node("increment", increment)

builder.add_edge(START, "increment")
builder.add_edge("increment", END)

connection = sqlite3.connect(
    "restart-demo.sqlite",
    check_same_thread=False,
)

checkpointer = SqliteSaver(connection)

graph = builder.compile(
    checkpointer=checkpointer,
)

config = {
    "configurable": {
        "thread_id": "demo-thread",
    }
}

snapshot = graph.get_state(config)

print(snapshot.values)

connection.close()
```

运行：

```powershell
python tests/manual_checkpoint_read.py
```

应该看到：

```text
{'value': 101}
```

注意这里：

```text
write process
      ↓
STOP
      ↓
read process
```

已经是真正的两个 Python Process。

所以：

```text
InMemorySaver
```

无法完成这个实验。

而：

```text
SqliteSaver
```

可以。

---

### 27. 这一课的验收标准

Lesson 3 只有在下面条件全部成立时才算完成。

#### Persistence Backend

```text
[✓] 引入 langgraph-checkpoint-sqlite
[✓] 使用 SqliteSaver
[✓] SQLite 数据库落盘
[✓] 不再使用 InMemorySaver 作为 Main Graph 的 Checkpointer
```

#### Architecture

```text
[✓] 新增 app/graph/checkpointer.py
[✓] Graph Definition 与 Persistence Backend 分离
[✓] Graph Topology 不改变
[✓] GraphState 不改变
[✓] thread_id 不进入 GraphState
```

#### Persistence

```text
[✓] Checkpoint 写入 SQLite
[✓] 可以通过 get_state() 读取
[✓] 关闭原 SQLite connection
[✓] 创建新的 SQLite connection
[✓] 创建新的 Graph Instance
[✓] 使用同一个 thread_id
[✓] 能读取之前的 State
```

#### Thread Isolation

```text
[✓] Thread A 与 Thread B 使用同一个 SQLite
[✓] 两者 Checkpoint 相互隔离
```

#### Scope

```text
[✓] 没有 HITL
[✓] 没有 Long-term Memory
[✓] 没有 Error Recovery
[✓] 没有 Observability
[✓] 没有 FastAPI
```

---

### 28. Lesson 3 最核心的理解

现在请把 Phase 9 的前三步连起来：

```text
Lesson 1
────────────────────────────
理解：

Thread
Run
State
Checkpoint
Checkpointer
Persistence
Resume
Isolation
```

↓

```text
Lesson 2
────────────────────────────
InMemorySaver

Graph
  ↓
Checkpointer
  ↓
Thread
  ↓
Checkpoint
```

↓

```text
Lesson 3
────────────────────────────
SqliteSaver

Graph
  ↓
Checkpointer
  ↓
SQLite
  ↓
Disk
```

于是第一次得到：

```text
Process A
    │
    ▼
Checkpoint
    │
    ▼
SQLite
    │
    X
Process STOP
    │
    ▼
Process B
    │
    ▼
same thread_id
    │
    ▼
Checkpoint
```

这一步是整个 Phase 9 非常关键的里程碑。

---