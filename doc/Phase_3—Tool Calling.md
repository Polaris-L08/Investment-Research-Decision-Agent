# Phase 3: Tool Calling

## Lesson 1 — First Tool

这一课**只解决一个问题**：

> **什么是 Tool，以及如何在项目中定义、调用一个最简单的 Tool？**

暂时不让 LLM 自动选择 Tool，也不做 Tool Calling Loop。

本课先把下面这条链路跑通：

```text
Python Function
      ↓
     Tool
      ↓
 Tool Invocation
      ↓
  Tool Result
```

这正好对应交接文档规定的 Phase 3 第一课目标。:chatgpt-content-reference{index="0"}

---

### 1. 为什么现在学习 Tool？

Phase 2 我们已经拥有：

```text
User
 ↓
Prompt
 ↓
LLM
 ↓
Structured Output
 ↓
Graph State
```

但这里有一个非常明显的问题：

**LLM 本身不是实时金融数据源。**

例如用户问：

```text
What is Apple's current stock price?
```

我们不能简单地：

```text
LLM → "I think AAPL is $200"
```

因为这里缺少一个可以验证的数据来源。

Phase 3 开始引入：

```text
Agent
 ↓
Tool
 ↓
External Data
```

最终才会逐渐变成：

```text
Agent
 ↓
Tool
 ↓
Provider
 ↓
External API
 ↓
Real Financial Data
```

但是本课故意**不接真实 API**。

我们先使用：

```text
Mock Financial Tool
```

把 Tool 本身的机制学清楚。

这也是项目交接文档明确要求的顺序：**先 Mock，再接真实 Provider。**:chatgpt-content-reference{index="1"}

---

### 2. Tool 到底是什么？

先不要把 Tool 想得太复杂。

在当前项目里，可以先把 Tool 理解成：

> **一个 Agent 可以调用的、具有明确输入输出 Contract 的能力。**

例如：

```text
get_stock_price
```

它的职责非常明确：

```text
输入：
ticker

输出：
ticker
price
```

例如：

```text
Input

"AAPL"
```

得到：

```python
{
    "ticker": "AAPL",
    "price": 200.0,
}
```

---

### 3. Tool 和普通 Python Function 有什么关系？

这是本课最重要的第一个概念。

普通 Python：

```python
def get_stock_price(ticker: str):
    return {
        "ticker": ticker,
        "price": 200.0,
    }
```

它只是一个：

```text
Python Function
```

如果我们把它包装成 Tool：

```text
Python Function
      ↓
     Tool
      ↓
 Tool Schema
      ↓
Agent / LLM 可以识别
```

于是它就不再只是“程序内部的一个函数”。

它开始拥有：

- name
- description
- input schema
- callable behavior

这些信息以后会告诉 LLM：

> “我这里有一个叫 `get_stock_price` 的能力，你可以在需要的时候调用它。”

---

### 4. 为什么需要 Tool Schema？

假设我们告诉 LLM：

```text
这里有一个工具：
get_stock_price
```

这还不够。

LLM 还需要知道：

```text
这个工具干什么？

需要什么参数？

参数叫什么？

参数是什么类型？
```

所以我们最终希望形成类似：

```text
Tool Name:
get_stock_price

Description:
Get the current stock price for a ticker.

Input:
ticker: string
```

因此：

```text
Tool
 ↓
Schema
```

是后面 Tool Calling 的关键。

本项目交接文档也明确把第一课拆成：

```text
Tool Definition
      ↓
Tool Schema
      ↓
Tool Invocation
      ↓
Tool Result
```

:chatgpt-content-reference{index="2"}

---

### 5. 本课暂时不要碰 LLM

这一点非常重要。

虽然 Phase 3 叫：

> Tool Calling

但 **Lesson 1 还不是 LLM Tool Calling**。

本课先做：

```text
Python
 ↓
Tool
 ↓
invoke()
 ↓
Result
```

下一课再进一步研究：

```text
Tool Schema
```

之后才进入：

```text
LLM
 ↓
Tool Call
```

也就是说，我们现在是在**分层学习**。

不要一上来把：

```text
LLM + Tool + Graph + State + API
```

全部塞在一起。

---

### 6. 文件修改

这一课我们不需要大规模重构。

按照项目目前的目录演进原则，随着 Lesson 实际需要逐步增加目录，而不是提前创建大量空目录。:chatgpt-content-reference{index="3"}

如果当前项目还没有 `app/tools/`，现在创建：

```text
app/
├── graph/
├── tools/
└── ...
```

新增：

```text
app/tools/financial.py
```

以及测试：

```text
tests/
└── test_financial_tool.py
```

---

### 7. 完整代码：`app/tools/financial.py`

第一版我们故意保持非常简单。

```python
from langchain_core.tools import tool


@tool
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    mock_prices = {
        "AAPL": 200.0,
        "MSFT": 450.0,
        "GOOGL": 180.0,
    }

    return {
        "ticker": ticker,
        "price": mock_prices.get(ticker, 100.0),
    }
```

---

### 8. 逐行理解

#### 8.1 `@tool`

核心变化：

```python
@tool
def get_stock_price(...):
```

原来：

```text
Python Function
```

现在：

```text
LangChain Tool
```

也就是说，`@tool` 把这个 Python callable 转换成了 LangChain 可以识别的 Tool abstraction。

---

#### 8.2 Function Name

```python
def get_stock_price(...)
```

Tool 的名字就是：

```text
get_stock_price
```

这个名字以后非常重要。

因为 LLM 在 Tool Calling 时，本质上需要决定：

```text
我要调用哪个 Tool？
```

例如：

```text
get_stock_price
```

---

#### 8.3 Type Annotation

这里：

```python
ticker: str
```

非常重要。

它告诉 Tool：

```text
ticker
↓
string
```

这就是我们后面 Tool Schema 的基础。

现在先记住：

> **Type annotation 是 Tool 输入 Contract 的一部分。**

---

#### 8.4 Docstring

这里：

```python
"""Get the current stock price for a stock ticker."""
```

也不是随便写的。

Tool description 会成为 Tool 元数据的一部分。

未来 LLM 需要理解：

```text
这个工具什么时候应该使用？
```

那么 description 就非常重要。

因此不要写成：

```python
"""price"""
```

而应该尽可能明确：

```python
"""Get the current stock price for a stock ticker."""
```

---

### 9. 为什么这里叫 Mock Tool？

注意：

```python
mock_prices = {
    "AAPL": 200.0,
    "MSFT": 450.0,
    "GOOGL": 180.0,
}
```

这些数字不是实时市场数据。

它们只是为了测试 Tool：

```text
Input
 ↓
Tool
 ↓
Output
```

所以我们明确称为：

```text
Mock Financial Tool
```

而不是：

```text
Real Financial Data Tool
```

这符合项目当前阶段的架构原则：

```text
Phase 3
 ↓
先验证 Tool Calling
 ↓
再接 Provider
```

否则以后如果测试失败，我们很难区分：

```text
Tool 有问题？
LLM 有问题？
Provider 有问题？
Network 有问题？
Authentication 有问题？
```

交接文档已经明确强调要隔离这些问题。:chatgpt-content-reference{index="4"}

---

### 10. 第一次直接调用 Tool

现在我们先不碰 Graph。

可以直接：

```python
result = get_stock_price.invoke(
    {"ticker": "AAPL"}
)
```

得到：

```python
{
    "ticker": "AAPL",
    "price": 200.0,
}
```

注意这里：

```python
.invoke(...)
```

而不是：

```python
get_stock_price("AAPL")
```

这是非常值得注意的变化。

我们现在已经不是简单地在调用普通 Python Function。

而是在调用：

```text
Tool
```

---

### 11. 完整测试

创建：

```text
tests/test_financial_tool.py
```

完整内容：

```python
from app.tools.financial import get_stock_price


def test_get_stock_price():
    result = get_stock_price.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["price"] == 200.0
```

---

### 12. 再增加一个测试

第一课至少验证另一个 ticker。

完整测试文件：

```python
from app.tools.financial import get_stock_price


def test_get_stock_price_aapl():
    result = get_stock_price.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["price"] == 200.0


def test_get_stock_price_msft():
    result = get_stock_price.invoke(
        {"ticker": "MSFT"}
    )

    assert result["ticker"] == "MSFT"
    assert result["price"] == 450.0
```

这里我们暂时**不测试错误输入**。

因为交接文档明确要求第一课不要一次把所有错误处理都塞进去，而是：

> 一次只增加一个核心能力。:chatgpt-content-reference{index="5"}

所以：

```text
Lesson 1
正常调用
        ↓
Lesson 2
Schema
        ↓
后续
invalid input
missing input
tool failure
```

这样学习曲线更加清晰。

---

### 13. 运行测试

在项目根目录运行：

```bash
pytest tests/test_financial_tool.py -v
```

预期：

```text
============================= test session starts =============================
...

tests/test_financial_tool.py::test_get_stock_price_aapl PASSED
tests/test_financial_tool.py::test_get_stock_price_msft PASSED

============================== 2 passed ==============================
```

如果你当前项目使用：

```bash
python -m pytest
```

也可以：

```bash
python -m pytest tests/test_financial_tool.py -v
```

---

### 14. 我们还应该直接观察 Tool

测试之外，我建议这一课做一次非常小的实验。

在 Python 中：

```python
from app.tools.financial import get_stock_price

print(get_stock_price)
print(get_stock_price.name)
print(get_stock_price.description)
print(get_stock_price.args)
```

你应该能够看到类似：

```text
name:
get_stock_price
```

以及：

```text
description:
Get the current stock price for a stock ticker.
```

而 `args` 会暴露 Tool 的输入参数信息。

这一步非常重要。

因为我们开始真正看到：

```text
Python Function
        ↓
      @tool
        ↓
      Tool
        ↓
      Metadata
        ↓
      Schema
```

而不是只把 `@tool` 当成一个“神奇装饰器”。

---

### 15. Lesson 1 的 Graph 变化

**这一课暂时不要修改现有 Graph。**

这是有意的。

当前 Phase 2 Graph：

```text
START
  ↓
initialize_state
  ↓
llm_node
  ↓
...
```

暂时保持不动。

我们先独立验证 Tool。

原因是：

```text
Tool
```

本身还没有进入：

```text
Graph
```

更没有进入：

```text
LLM Tool Calling
```

如果现在就把 Tool 强行塞进 Graph，我们会同时学习：

```text
Tool
+
Node
+
State
+
Graph
+
LLM
```

反而会模糊本课真正需要掌握的概念。

所以 Lesson 1 的边界非常明确：

```text
                Phase 3

Python Function
      ↓
   @tool
      ↓
     Tool
      ↓
   invoke()
      ↓
 Tool Result
```

---

### 16. 和 Phase 2 做一个对照

Phase 2：

```text
Graph State
     ↓
   Prompt
     ↓
    LLM
     ↓
Structured Output
     ↓
 Graph State
```

Phase 3 Lesson 1：

```text
Ticker
  ↓
 Tool
  ↓
Tool Result
```

下一步才会变成：

```text
User
 ↓
LLM
 ↓
Tool Call
 ↓
Tool
 ↓
Tool Result
 ↓
LLM
```

再往后：

```text
LLM
 ↓
Tool
 ↓
Tool Result
 ↓
Graph State
```

最终：

```text
Research Agent
      ↓
     Tool
      ↓
   Provider
      ↓
External Data
      ↓
   Evidence
```

这正是整个 Phase 3 要逐步建立起来的能力。:chatgpt-content-reference{index="6"}

---

### 17. Acceptance Criteria

Lesson 1 不需要达到后面的 Tool Calling Loop。

只检查以下内容。

#### ① Tool 存在

能够：

```python
from app.tools.financial import get_stock_price
```

---

#### ② Tool 有明确名称

应该是：

```text
get_stock_price
```

---

#### ③ Tool 有 description

应该能够看到：

```text
Get the current stock price for a stock ticker.
```

---

#### ④ Tool 可以接受 ticker

例如：

```python
get_stock_price.invoke(
    {"ticker": "AAPL"}
)
```

---

#### ⑤ Tool 返回结构化结果

例如：

```python
{
    "ticker": "AAPL",
    "price": 200.0,
}
```

---

#### ⑥ 测试通过

至少：

```text
AAPL → PASS
MSFT → PASS
```

---

#### ⑦ 没有接真实金融 API

本课仍然是：

```text
Mock
```

而不是：

```text
Yahoo Finance
Bloomberg
Alpha Vantage
```

---

### 18. 本课最重要的几个理解

#### 理解 1

**Tool 的底层仍然可以是 Python Function。**

不是出现了一个完全不同的东西。

而是：

```text
Python Function
      ↓
Tool Abstraction
```

---

#### 理解 2

Tool 不只是“一个函数”。

它还携带：

```text
name
description
input schema
```

这些元数据是以后 LLM Tool Calling 的基础。

---

#### 理解 3

本课还没有 LLM Tool Calling。

现在只是：

```text
Tool Invocation
```

即：

```python
get_stock_price.invoke(...)
```

真正的：

```text
LLM → Tool Call
```

属于后面的 Lesson。

---

#### 理解 4

为什么先 Mock？

因为我们当前要验证的是：

```text
Tool Mechanism
```

而不是：

```text
Financial Provider
```

这两个问题必须隔离。

---

#### 理解 5

这一课故意没有修改 Graph。

这是**控制复杂度**，不是遗漏。

我们正在按照：

```text
Tool
 ↓
Tool Schema
 ↓
LLM Tool Calling
 ↓
Tool Result
 ↓
Graph State
 ↓
Tool Failure
 ↓
Multiple Tools
 ↓
Tool Calling Loop
 ↓
Provider Abstraction
```

逐层建立能力。:chatgpt-content-reference{index="7"}

---





## Lesson 2 — Tool Schema

### 一、这一课要解决什么问题？

Lesson 1 我们已经有了一个 Tool：

```text
get_stock_price(ticker)
```

现在需要理解一个非常关键的问题：

> **LLM 怎么知道这个 Tool 需要什么参数？**

对于 Python 来说，我们看到：

```python
def get_stock_price(ticker: str) -> dict:
```

人类当然能理解：

- Tool 名字：`get_stock_price`
- 参数：`ticker`
- 类型：`str`

但 **LLM 并不会直接读取 Python 函数签名来决定如何调用 Tool**。

LangChain 会把 Tool 的定义转换成一个 **Tool Schema**，之后这个 Schema 才能被提供给 LLM。

所以这一课的核心链路是：

```text
Python Function
      ↓
@tool
      ↓
LangChain Tool
      ↓
Tool Schema
      ↓
LLM 可以理解的参数定义
```

---

#### 1. 什么是 Tool Schema？

可以把它暂时理解成 Tool 的“接口契约”。

例如我们的 Tool：

```text
get_stock_price
```

它需要：

```text
ticker: string
```

那么 Schema 大致表达的是：

```json
{
  "name": "get_stock_price",
  "description": "Get the current stock price for a stock ticker.",
  "parameters": {
    "ticker": {
      "type": "string"
    }
  }
}
```

这里有三个重要部分：

##### Tool Name

```text
get_stock_price
```

告诉 LLM：

> 我有哪些能力可以调用？

##### Description

```text
Get the current stock price for a stock ticker.
```

告诉 LLM：

> 这个 Tool 是干什么的？

##### Parameters

```text
ticker: string
```

告诉 LLM：

> 调用这个 Tool 时，需要提供什么参数？

---

#### 2. 为什么 Schema 在 Agent 中非常重要？

后面的完整链路会是：

```text
User
  │
  ▼
LLM
  │
  │ 根据 Tool Schema 判断
  ▼
Tool Call
  │
  ▼
get_stock_price(ticker="AAPL")
  │
  ▼
Tool Result
  │
  ▼
LLM
```

因此 Tool Schema 实际上是：

> **LLM 与外部工具之间的接口协议。**

这也是为什么在生产系统里，我们不能只关心：

```python
def get_stock_price(...)
```

还必须关心：

```text
Tool Name
Tool Description
Input Schema
Output
Error behavior
```

---

#### 3. 我们先观察当前 Tool 的 Schema

这一步非常重要。

**暂时不要修改代码。**

在 Python 中执行：

```python
from app.tools.financial import get_stock_price

print("name:")
print(get_stock_price.name)

print("\ndescription:")
print(get_stock_price.description)

print("\nargs:")
print(get_stock_price.args)
```

你应该看到类似：

```text
name:
get_stock_price

description:
Get the current stock price for a stock ticker.

args:
{
    'ticker': {
        'type': 'string',
        'title': 'Ticker'
    }
}
```

具体格式可能因为你当前安装的 LangChain 版本略有不同。

**不要要求输出必须逐字符一致。**

我们真正关心的是：

```text
name        → get_stock_price
description → 存在且正确
args        → 包含 ticker
ticker      → string
```

---

#### 4. 为什么 `ticker: str` 能产生 Schema？

看我们 Lesson 1 的代码：

```python
@tool
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""
```

这里其实同时提供了两类信息。

##### Python Type Hint

```python
ticker: str
```

告诉 LangChain：

> ticker 是字符串。

因此可以生成：

```json
{
  "ticker": {
    "type": "string"
  }
}
```

---

##### Docstring

```python
"""Get the current stock price for a stock ticker."""
```

告诉 LangChain：

> Tool 是干什么的。

因此：

```text
description
```

就可以被生成。

---

#### 5. 一个非常重要的认识

我们现在可以把：

```python
@tool
def get_stock_price(ticker: str) -> dict:
```

理解成：

> **Python Function + Type Hints + Description → Tool Contract**

这和普通 Python 函数相比已经发生了很重要的变化。

普通函数：

```python
def get_stock_price(ticker: str):
```

主要是给 Python 程序调用。

而 Tool：

```python
@tool
def get_stock_price(ticker: str):
```

则是给：

```text
Agent / LLM
```

调用的。

因此 Tool 的接口设计必须更加严格。

---

#### 6. 本课第一次小升级：显式 Schema

虽然 Lesson 1 已经能够自动生成 Schema，但为了真正理解 Schema，我们这一步**主动使用 Pydantic 定义输入模型**。

这也是后面生产项目非常重要的模式。

修改：

```text
app/tools/financial.py
```

为：

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class StockPriceInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    mock_prices = {
        "AAPL": 200.0,
        "MSFT": 450.0,
        "GOOGL": 180.0,
    }

    return {
        "ticker": ticker,
        "price": mock_prices.get(ticker, 100.0),
    }
```

---

#### 7. 这里发生了什么？

现在结构变成：

```text
StockPriceInput
        │
        ▼
   Tool Schema
        │
        ▼
get_stock_price
```

其中：

```python
class StockPriceInput(BaseModel):
```

定义的是：

> Tool 的输入协议。

而：

```python
ticker: str = Field(
    description="Stock ticker symbol, for example AAPL or MSFT."
)
```

同时定义了：

- 参数名称：`ticker`
- 类型：`str`
- 参数描述

---

#### 8. 为什么这里使用 Pydantic？

因为我们的最终系统不是只有一个 Tool。

未来会出现：

```text
get_stock_price
get_financial_statements
get_revenue
get_eps
get_market_cap
get_pe_ratio
get_industry_data
get_macro_data
...
```

如果所有 Tool 都依赖简单的：

```python
ticker: str
```

很快就会遇到复杂输入。

例如：

```text
ticker
period
start_date
end_date
currency
statement_type
```

这时候：

```python
Pydantic Model
```

会比单纯依靠函数签名更加清晰。

例如未来可能出现：

```python
class FinancialDataInput(BaseModel):
    ticker: str
    period: str
    statement_type: str
```

于是 Tool 的输入契约非常明确。

---

#### 9. 注意：现在不要做过度设计

这一课我们**只增加一个 Input Schema**。

不要现在就创建：

```text
schemas/
tool_schemas/
providers/
interfaces/
adapters/
factories/
```

这些内容后面需要时再逐步引入。

当前结构保持简单：

```text
app/
├── graph/
├── models/
├── tools/
│   └── financial.py
└── ...
```

这符合我们项目的渐进式设计原则。

---

#### 10. Lesson 2 测试

现在更新：

```text
tests/test_financial_tool.py
```

建议完整改成：

```python
from app.tools.financial import (
    StockPriceInput,
    get_stock_price,
)


def test_get_stock_price():
    result = get_stock_price.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["price"] == 200.0


def test_get_stock_price_aapl():
    result = get_stock_price.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["price"] == 200.0


def test_get_stock_price_msft():
    result = get_stock_price.invoke(
        {"ticker": "MSFT"}
    )

    assert result["ticker"] == "MSFT"
    assert result["price"] == 450.0


def test_tool_name():
    assert get_stock_price.name == "get_stock_price"


def test_tool_schema_contains_ticker():
    schema = get_stock_price.args

    assert "ticker" in schema
    assert schema["ticker"]["type"] == "string"


def test_stock_price_input_schema():
    schema = StockPriceInput.model_json_schema()

    assert "ticker" in schema["properties"]
    assert schema["properties"]["ticker"]["type"] == "string"
```

这里我们新增了两类测试。

---

##### Test 1：Tool 本身的 Schema

```python
get_stock_price.args
```

测试：

```python
assert "ticker" in schema
```

以及：

```python
assert schema["ticker"]["type"] == "string"
```

验证：

> LangChain Tool 最终暴露出来的 Schema 正确。

---

##### Test 2：Pydantic Input Model

```python
StockPriceInput.model_json_schema()
```

验证：

> 我们定义的 Pydantic Schema 本身正确。

这两个测试虽然看起来相似，但测试对象不同。

```text
StockPriceInput
        │
        │ model_json_schema()
        ▼
Pydantic Schema
        │
        │ @tool(args_schema=...)
        ▼
LangChain Tool
        │
        ▼
Tool Schema
```

---

#### 11. 再做一个手工检查

执行：

```bash
python -c "from app.tools.financial import get_stock_price; print(get_stock_price.name); print(get_stock_price.description); print(get_stock_price.args)"
```

预期重点检查：

```text
get_stock_price
```

以及：

```text
ticker
```

和：

```text
string
```

---

#### 12. 运行测试

执行：

```bash
python -m pytest tests/test_financial_tool.py -v
```

---

### Lesson 2 Acceptance Criteria

本课通过需要满足：

#### Tool 层

- [ ] `get_stock_price` 可以正常导入
- [ ] Tool name 是 `get_stock_price`
- [ ] Tool description 存在
- [ ] Tool Schema 中存在 `ticker`
- [ ] `ticker` 类型是 `string`

#### Pydantic 层

- [ ] `StockPriceInput` 可以正常创建
- [ ] JSON Schema 中存在 `ticker`
- [ ] `ticker` 类型为 `string`

#### Functionality

- [ ] AAPL 测试通过
- [ ] MSFT 测试通过
- [ ] Tool `.invoke()` 仍然正常工作

#### Architecture

这一课**仍然不接 LLM**。

当前架构：

```text
                ┌──────────────────┐
                │ StockPriceInput  │
                │    Pydantic      │
                └────────┬─────────┘
                         │
                         ▼
┌──────────────┐    ┌──────────────┐
│ Python Func  │───▶│ LangChain    │
│              │    │ Tool         │
└──────────────┘    └──────┬───────┘
                           │
                           ▼
                     Tool Schema
```


## Lesson 3：LLM Tool Calling

Lesson 1 是：

```text
Tool Definition
```

Lesson 2 是：

```text
Tool Schema
```

这一课开始真正把：

```text
LLM
```

和：

```text
Tool
```

连接起来。

---

### 一、这一课的核心目标

到目前为止，架构是：

```text
Python
  │
  ▼
LangChain Tool
  │
  ▼
Tool Schema
```

但还没有 Agent。

我们希望变成：

```text
User
  │
  ▼
LLM
  │
  │ 判断需要调用 Tool
  ▼
Tool Call
  │
  ▼
get_stock_price
```

注意：

> **这一课先学习 LLM 如何“决定调用 Tool”，暂时不做完整的 Tool Calling Loop。**

完整 Loop 是下一阶段的概念。

---

### 二、最重要的概念：`bind_tools()`

LangChain 中非常关键的 API：

```python
llm.bind_tools(...)
```

它的作用不是：

> “马上执行 Tool”。

而是：

> **把 Tool 的定义告诉 LLM，使 LLM 获得调用这些 Tool 的能力。**

例如：

```python
llm_with_tools = llm.bind_tools(
    [get_stock_price]
)
```

此时：

```text
LLM
 │
 │ Tool Schema
 ▼
get_stock_price
```

LLM 就知道：

```text
我有一个叫 get_stock_price 的工具
它需要 ticker 参数
```

---

### 三、一个非常重要的区分

这里很容易产生第一个误解。

`bind_tools()`：

```python
llm_with_tools = llm.bind_tools(
    [get_stock_price]
)
```

**不会直接执行：**

```python
get_stock_price.invoke(...)
```

它只是告诉 LLM：

```text
你可以使用这个 Tool。
```

之后 LLM 返回的消息可能包含：

```text
tool_calls
```

例如逻辑上可能是：

```json
{
  "name": "get_stock_price",
  "args": {
    "ticker": "AAPL"
  }
}
```

然后才由 Agent / Graph 执行 Tool。

因此完整链路实际上是：

```text
                  Tool Schema
                       │
                       ▼
User ──────▶ LLM ──────┐
                       │
                       │ tool_calls
                       ▼
                  Tool Executor
                       │
                       ▼
                get_stock_price
```

---

### 四、为什么我们这一课继续使用 Mock？

因为现在我们要验证的是：

```text
LLM
 ↓
Tool Calling
```

而不是：

```text
LLM
 ↓
Tool Calling
 ↓
Yahoo Finance
 ↓
Network
 ↓
Authentication
```

如果直接接真实 Provider，一旦失败，我们无法判断到底是：

- LLM 配置问题
- Tool Schema 问题
- Tool Calling 问题
- 网络问题
- Provider API 问题

所以我们继续保持：

```text
Mock Tool
+
真实 LLM
```

这正是本 Phase 的第一原则。

---

### 五、先不修改 Graph

这是本课一个非常重要的教学设计。

**暂时不要修改 `app/graph/`。**

我们先单独验证：

```text
ChatOpenAI
      +
get_stock_price
      ↓
tool_calls
```

Graph 集成会在后面的 Lesson 逐步完成。

这样每一步都只有一个变量。

---

### 六、新增 Tool Calling 测试

建议新增：

```text
tests/test_tool_calling.py
```

完整内容：

```python
from unittest.mock import MagicMock, patch

from app.tools.financial import get_stock_price


def test_llm_can_call_stock_price_tool():
    mock_response = MagicMock()

    mock_response.tool_calls = [
        {
            "name": "get_stock_price",
            "args": {
                "ticker": "AAPL",
            },
            "id": "call_123",
            "type": "tool_call",
        }
    ]

    with patch(
        "langchain_openai.ChatOpenAI.invoke",
        return_value=mock_response,
    ):
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="test-model"
        )

        llm_with_tools = llm.bind_tools(
            [get_stock_price]
        )

        result = llm_with_tools.invoke(
            "What is the current stock price of AAPL?"
        )

        assert len(result.tool_calls) == 1

        tool_call = result.tool_calls[0]

        assert tool_call["name"] == "get_stock_price"
        assert tool_call["args"]["ticker"] == "AAPL"
```

但是这里有一个**重要问题**。

我们不能简单地这样测试：

```python
llm_with_tools.invoke(...)
```

然后期待：

```text
bind_tools()
```

一定会使用我们 patch 的 `ChatOpenAI.invoke`。

原因是：

```text
llm
 │
 ▼
bind_tools()
 │
 ▼
RunnableBinding
 │
 ▼
invoke()
```

所以我们需要理解 LangChain Runnable 的调用链。

为了让 Lesson 3 保持教学上的清晰，我们先采用更稳定的方式：

> **Mock LLM 返回一个包含 `tool_calls` 的 AIMessage，然后验证 Graph/Agent 层能够识别它。**

---

### 七、Lesson 3 第一阶段：理解 `AIMessage.tool_calls`

这一步非常关键。

在 LangChain 中，LLM 的 Tool Calling 输出通常不是普通字符串：

```python
"Please call get_stock_price"
```

而是结构化的：

```text
AIMessage
    │
    ├── content
    │
    └── tool_calls
```

例如：

```python
[
    {
        "name": "get_stock_price",
        "args": {
            "ticker": "AAPL"
        },
        "id": "call_123",
        "type": "tool_call"
    }
]
```

这意味着：

> **LLM 并不是自己执行 Python 函数。**

它只是产生一个：

```text
Tool Call Request
```

真正执行：

```python
get_stock_price.invoke(...)
```

的是后面的 Tool execution layer。

这对理解 Agent Architecture 非常重要。

---

### 八、我们现在创建一个最小 Tool Calling 示例

新建：

```text
app/agents/
```

不过这里我建议**不要现在创建 `agents/` 目录**。

因为目前还没有真正的 Agent。

我们只增加测试：

```text
tests/test_tool_calling.py
```

然后使用一个 Mock LLM。

完整测试：

```python
from langchain_core.messages import AIMessage

from app.tools.financial import get_stock_price


def test_llm_tool_call_structure():
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_stock_price",
                "args": {
                    "ticker": "AAPL",
                },
                "id": "call_123",
                "type": "tool_call",
            }
        ],
    )

    assert len(response.tool_calls) == 1

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "get_stock_price"
    assert tool_call["args"]["ticker"] == "AAPL"
```

---

### 九、这个测试看起来是不是“没有 LLM”？

是的。

这是**故意的**。

我们现在测试的是：

```text
Tool Call Message Contract
```

而不是：

```text
LLM Provider
```

这就是我们之前 Phase 2 学到的：

> **先 Mock，再 Real Provider。**

Phase 2 我们已经验证过：

```text
LLM
 ↓
Structured Output
```

所以这一课不应该同时引入：

```text
真实 OpenAI API
```

来验证基础数据结构。

---

### 十、但我们最终必须验证真实 LLM

没错。

因此 Lesson 3 会分成两个层次：

#### Level 1 — Mock

验证：

```text
AIMessage
 ↓
tool_calls
 ↓
Tool Call Schema
```

#### Level 2 — Real LLM

验证：

```text
ChatOpenAI
 ↓
bind_tools()
 ↓
真实 LLM
 ↓
AIMessage.tool_calls
```

这两个测试解决的是不同问题。

---

### 十一、现在增加 Mock 测试

创建：

```text
tests/test_tool_calling.py
```

完整代码：

```python
from langchain_core.messages import AIMessage

from app.tools.financial import get_stock_price


def test_llm_tool_call_structure():
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_stock_price",
                "args": {
                    "ticker": "AAPL",
                },
                "id": "call_123",
                "type": "tool_call",
            }
        ],
    )

    assert len(response.tool_calls) == 1

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "get_stock_price"
    assert tool_call["args"]["ticker"] == "AAPL"


def test_tool_call_matches_registered_tool():
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_stock_price",
                "args": {
                    "ticker": "MSFT",
                },
                "id": "call_456",
                "type": "tool_call",
            }
        ],
    )

    available_tools = {
        get_stock_price.name: get_stock_price
    }

    tool_call = response.tool_calls[0]

    assert tool_call["name"] in available_tools

    tool = available_tools[tool_call["name"]]

    result = tool.invoke(tool_call["args"])

    assert result["ticker"] == "MSFT"
    assert result["price"] == 450.0
```

现在这个测试已经开始形成真正的 Agent 思维：

```text
AIMessage
   │
   ▼
tool_calls
   │
   ▼
tool name
   │
   ▼
find registered Tool
   │
   ▼
tool.invoke(args)
   │
   ▼
Tool Result
```

这实际上已经是一个极简 Tool Executor 的雏形。

---

### 十二、运行测试

先运行：

```bash
python -m pytest tests/test_tool_calling.py -v
```

然后运行整个 Phase 3 当前测试：

```bash
python -m pytest tests -v
```

目前理论上应该：

```text
Lesson 1
3 tests

+

Lesson 2
6 tests

+

Lesson 3
2 tests
```

总共：

```text
11 passed
```

如果你的项目中已有其他测试，则总数可能更多。

---

### 十三、现在再理解 `bind_tools()`

完成 Mock 测试之后，我们才正式看真实 LLM：

```python
from langchain_openai import ChatOpenAI

from app.tools.financial import get_stock_price


llm = ChatOpenAI(
    model="你的模型"
)

llm_with_tools = llm.bind_tools(
    [get_stock_price]
)
```

此时：

```text
llm
```

和：

```text
llm_with_tools
```

最大的区别是：

```text
llm
    ↓
只能生成普通 LLM Response

llm_with_tools
    ↓
可以生成 Tool Call
```

---

### 十四、真实 LLM 测试暂时不要加入自动测试套件

这一点尤其重要。

因为真实 LLM 测试具有：

- API 成本
- 网络依赖
- Provider 可用性
- 模型行为非确定性
- Tool Calling 行为可能随模型版本变化

因此我们不要把它放进：

```text
pytest tests/
```

的默认测试流程。

后面可以建立：

```text
integration tests
```

或者使用明确的：

```text
pytest -m integration
```

但现在还没有必要。

---

### 十五、手工进行一次真实 Tool Calling

如果你的 `.env` 已经配置好 Phase 2 使用的：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
LLM_MODEL
```

可以建立一个临时脚本，例如：

```text
scripts/test_tool_calling.py
```

内容：

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.tools.financial import get_stock_price


load_dotenv()


llm = ChatOpenAI()

llm_with_tools = llm.bind_tools(
    [get_stock_price]
)


response = llm_with_tools.invoke(
    "What is the current stock price of AAPL?"
)


print("content:")
print(response.content)

print("\ntool_calls:")
print(response.tool_calls)
```

运行：

```bash
python scripts/test_tool_calling.py
```

如果模型决定调用 Tool，你应该看到类似：

```text
tool_calls:
[
    {
        "name": "get_stock_price",
        "args": {
            "ticker": "AAPL"
        },
        ...
    }
]
```

**注意：**

这里即使看到：

```text
tool_calls
```

也不代表：

```python
get_stock_price()
```

已经执行。

这恰恰是本课最重要的知识点之一。

---

### 十六、现在整个架构变成什么？

到 Lesson 2：

```text
Tool
  │
  ▼
Tool Schema
```

Lesson 3：

```text
                 Tool Schema
                      │
                      ▼
User ───────────────▶ LLM
                      │
                      │
                      ▼
                  tool_calls
                      │
                      ▼
                Tool Executor
                      │
                      ▼
               get_stock_price
```

但是我们现在还没有把：

```text
Tool Result
```

送回 LLM。

所以当前还不是完整 Agent Loop。

---

### Lesson 3 当前验收标准

#### Mock 层

- [ ] `AIMessage.tool_calls` 能正确解析
- [ ] Tool name 能匹配注册 Tool
- [ ] Tool args 能正确传入
- [ ] Tool 能被 `.invoke()` 执行
- [ ] Tool Result 正确返回

#### Real LLM 层

手工验证：

- [ ] `ChatOpenAI` 正常初始化
- [ ] `llm.bind_tools([get_stock_price])` 正常
- [ ] LLM 能产生 `tool_calls`
- [ ] `tool_calls.name == "get_stock_price"`
- [ ] `tool_calls.args["ticker"]` 正确

---


## Lesson 4：Tool Result → Graph State

这一课开始把前面两部分真正连接起来：

```text
Phase 2
LLM + Graph State
```

+

```text
Phase 3
Tool Calling
```

最终形成：

```text
LLM
 ↓
Tool Call
 ↓
Tool Execution
 ↓
Tool Result
 ↓
Graph State
```

这一步非常重要，因为从这里开始，Tool 不再只是一个独立 Python Function，而会成为 **LangGraph 工作流中的一个节点能力**。

---

### 一、先回顾目前我们有什么

到目前为止，我们已经建立：

#### Tool

```python
get_stock_price(ticker)
```

返回：

```python
{
    "ticker": "AAPL",
    "price": 200.0
}
```

#### Tool Schema

```text
ticker: string
```

#### LLM Tool Calling

LLM 可以产生：

```python
{
    "name": "get_stock_price",
    "args": {
        "ticker": "AAPL"
    }
}
```

但是现在还有一个断点：

```text
LLM
 ↓
tool_calls
 ↓
???
 ↓
GraphState
```

这个 `???` 就是本课要解决的问题。

---

### 二、核心概念：Tool Call 和 Tool Result 是两回事

这是这一课最需要建立的概念。

LLM 返回：

```python
response.tool_calls
```

例如：

```python
[
    {
        "name": "get_stock_price",
        "args": {
            "ticker": "AAPL"
        }
    }
]
```

这只是：

> **LLM 要求系统调用什么 Tool。**

然后我们的程序执行：

```python
get_stock_price.invoke(
    {"ticker": "AAPL"}
)
```

得到：

```python
{
    "ticker": "AAPL",
    "price": 200.0
}
```

这才叫：

> **Tool Result**

所以：

```text
Tool Call
    ↓
Tool Execution
    ↓
Tool Result
```

是三个不同阶段。

---

### 三、为什么最终必须进入 Graph State？

因为我们的 Agent 最终不是单纯的：

```text
LLM → Tool → 返回结果
```

而是：

```text
Research Agent
      │
      ▼
Graph State
```

例如未来：

```text
ticker = AAPL
current_price = 200
revenue = ...
eps = ...
market_cap = ...
risk_factors = ...
```

这些数据都必须进入 State。

否则下一节点：

```text
Financial Research
```

根本不知道前一个 Tool 查到了什么。

因此我们现在需要新增：

```text
stock_price
```

或者更明确：

```text
current_price
```

到 Graph State。

---

### 四、这一课先做最小改动

我们不要现在把整个 Phase 2 Graph 重构掉。

只增加：

```text
Tool
 ↓
Tool Execution Node
 ↓
GraphState.current_price
```

这样可以保持每课只增加一个核心能力。

---

### 五、先检查当前 GraphState

根据 Phase 2 的设计，我们当前已经有：

```text
GraphState
```

并且：

```text
initialize_state
```

负责初始化 State。

现在新增一个字段：

```python
current_price: float | None
```

如果你的项目当前使用：

```python
TypedDict
```

那么应该加入：

```python
current_price: float | None
```

同时必须检查：

```python
initialize_state()
```

这一点我们之前专门强调过：

> `TypedDict` 不会自动创建运行时默认值。

所以不能只修改类型定义而忘记初始化。

---

### 六、增加 Tool Result State

假设当前 `GraphState` 位于：

```text
app/graph/state.py
```

那么在原有字段基础上增加：

```python
current_price: float | None
```

例如逻辑上：

```python
class GraphState(TypedDict):
    ...
    current_price: float | None
```

然后在：

```python
initialize_state()
```

中确保：

```python
"current_price": None,
```

---

### 七、为什么这里不直接把 Tool Result 整个塞进去？

我们现在 Tool 返回：

```python
{
    "ticker": "AAPL",
    "price": 200.0
}
```

但 GraphState 不应该简单变成：

```python
tool_result = {
    "ticker": "AAPL",
    "price": 200.0
}
```

至少在当前阶段不建议这样设计。

因为：

```text
Tool Result
```

是 Tool 层的数据结构。

而：

```text
GraphState
```

是业务工作流的数据结构。

两者应该有一个转换：

```text
Tool Result
     ↓
Node
     ↓
Business State
```

这也是以后 Provider Abstraction 很重要的基础。

---

### 八、创建 Tool Execution Node

现在我们增加一个非常小的 Node。

例如：

```text
app/graph/nodes/tool_node.py
```

完整代码：

```python
from app.tools.financial import get_stock_price


def get_stock_price_node(state):
    ticker = state["ticker"]

    result = get_stock_price.invoke(
        {"ticker": ticker}
    )

    return {
        "current_price": result["price"]
    }
```

这里非常值得注意：

```python
ticker = state["ticker"]
```

Node 从：

```text
GraphState
```

读取业务输入。

然后：

```python
get_stock_price.invoke(...)
```

调用 Tool。

最后：

```python
return {
    "current_price": result["price"]
}
```

只更新：

```text
current_price
```

---

### 九、这就是我们一直强调的 Node Ownership

Node：

```text
get_stock_price_node
```

负责：

```text
current_price
```

所以它只写：

```python
{
    "current_price": ...
}
```

而不是：

```python
{
    "ticker": ...,
    "recommendation": ...,
    "investment_thesis": ...,
    "current_price": ...
}
```

这是 LangGraph State 设计中的重要原则：

> **Node 只更新自己负责的 State 字段。**

---

### 十、先不要把 LLM 接进 Graph

这里又是一个刻意的教学选择。

现在先验证：

```text
GraphState
 ↓
Tool Node
 ↓
Tool
 ↓
GraphState
```

也就是说：

```text
ticker
 ↓
get_stock_price_node
 ↓
get_stock_price
 ↓
current_price
```

而不是马上：

```text
LLM
 ↓
Tool Call
 ↓
Tool Node
```

为什么？

因为这样我们可以先独立证明：

> **Tool Result 能正确进入 Graph State。**

下一步再把 LLM Tool Call 接进去。

---

### 十一、增加一个最小测试

新增：

```text
tests/test_tool_result_to_state.py
```

完整代码：

```python
from app.graph.nodes.tool_node import get_stock_price_node


def test_get_stock_price_result_updates_graph_state():
    state = {
        "ticker": "AAPL",
    }

    result = get_stock_price_node(state)

    assert result["current_price"] == 200.0
```

这里测试的是：

```text
Graph State Input
        ↓
      Node
        ↓
      Tool
        ↓
State Update
```

而不是测试 Tool 本身。

Tool 本身已经在 Lesson 1 / Lesson 2 测试过了。

---

### 十二、这里其实出现了三层测试

现在我们的测试边界已经开始清晰了。

#### Layer 1 — Tool

```text
test_financial_tool.py
```

验证：

```text
Tool → Result
```

---

#### Layer 2 — Tool Calling

```text
test_tool_calling.py
```

验证：

```text
LLM → Tool Call
```

以及：

```text
Tool Call → Tool
```

---

#### Layer 3 — Graph Integration

```text
test_tool_result_to_state.py
```

验证：

```text
Tool → Graph State
```

最终三个部分组合：

```text
          LLM
           │
           ▼
       Tool Call
           │
           ▼
       Tool Node
           │
           ▼
          Tool
           │
           ▼
      Tool Result
           │
           ▼
       Graph State
```

这正是我们希望逐步建立的架构。

---

### 十三、把 Node 加入 Graph

现在还差一步：

> 这个 Node 必须真的成为 LangGraph Node。

找到当前 Graph 创建代码。

原来的结构大致是：

```text
START
 ↓
initialize_state
 ↓
llm_node
 ↓
...
```

我们暂时不要改变原有 Phase 2 主流程。

先在 Graph 中注册：

```python
builder.add_node(
    "get_stock_price",
    get_stock_price_node,
)
```

但是**不要急着把它插入主流程**。

第一阶段只验证：

```text
Graph 可以注册 Tool Node
```

然后再决定它应该放在哪条边上。

这是为了避免 Lesson 4 一开始就同时修改：

- State
- Node
- Edge
- LLM
- Tool Calling
- Retry

导致问题难以定位。

---

### 十四、这一课最终要形成的 Graph Topology

Lesson 4 完成后，我们最终希望得到一个最小 Graph：

```text
START
  │
  ▼
initialize_state
  │
  ▼
get_stock_price
  │
  ▼
prepare_output
  │
  ▼
END
```

其中：

```text
initialize_state
        │
        │ ticker
        ▼
get_stock_price_node
        │
        │ Tool.invoke()
        ▼
get_stock_price
        │
        │ {"ticker": "AAPL", "price": 200}
        ▼
current_price
```

注意：

**这一课还不需要把 LLM 放进这条最小测试 Graph。**

下一课再把：

```text
LLM
 ↓
Tool Call
```

接到这里。

---

### 十五、Lesson 4 第一阶段任务

这一次我们只做以下修改：

#### ① GraphState

增加：

```python
current_price: float | None
```

#### ② initialize_state

增加：

```python
"current_price": None
```

#### ③ Tool Node

新增：

```text
app/graph/nodes/tool_node.py
```

实现：

```python
def get_stock_price_node(state):
    ticker = state["ticker"]

    result = get_stock_price.invoke(
        {"ticker": ticker}
    )

    return {
        "current_price": result["price"]
    }
```

#### ④ Test

新增：

```text
tests/test_tool_result_to_state.py
```

测试：

```text
AAPL → 200.0
MSFT → 450.0
```

我建议直接写两个测试：

```python
from app.graph.nodes.tool_node import get_stock_price_node


def test_get_stock_price_result_updates_graph_state_aapl():
    state = {
        "ticker": "AAPL",
    }

    result = get_stock_price_node(state)

    assert result["current_price"] == 200.0


def test_get_stock_price_result_updates_graph_state_msft():
    state = {
        "ticker": "MSFT",
    }

    result = get_stock_price_node(state)

    assert result["current_price"] == 450.0
```

---

### Lesson 4 当前 Acceptance Criteria

#### State

- [ ] `GraphState` 包含 `current_price`
- [ ] `initialize_state()` 正确初始化 `current_price`

#### Tool Node

- [ ] Node 可以从 State 获取 ticker
- [ ] Node 调用 `get_stock_price`
- [ ] Node 将 Tool Result 转换成 `current_price`
- [ ] Node 只更新自己负责的字段

#### Tests

- [ ] AAPL → `200.0`
- [ ] MSFT → `450.0`
- [ ] 原有 Phase 1 / Phase 2 / Phase 3 测试全部保持通过

#### Architecture

当前我们建立：

```text
GraphState
    │
    ▼
Tool Node
    │
    ▼
Tool
    │
    ▼
Tool Result
    │
    ▼
GraphState.current_price
```


## Phase 3 — Lesson 5：Tool Failure

这一课开始进入 **Error Handling**。

前面我们已经建立：

```text
LLM
 ↓
Tool Call
 ↓
Tool
 ↓
Tool Result
 ↓
Graph State
```

但真实系统里，Tool 不可能永远成功。

例如：

```text
Ticker 不存在
Provider 返回错误
网络超时
API 限流
数据缺失
Provider 暂时不可用
```

如果我们直接：

```python
result = get_stock_price.invoke(...)
```

一旦抛异常，整个 Graph 可能直接失败。

所以这一课要建立一个非常重要的原则：

> **Tool Failure 必须成为 Graph 中可处理的状态，而不能只是 Python Exception。**

这也对应项目交接文档中已经确定的错误分类：Tool Failure、LLM Failure、Timeout、Invalid Structured Output、Missing Data、Partial Research Failure 等需要分别处理，而不是用 `except Exception: pass` 静默吞掉错误。:chatgpt-content-reference{index="0"}

---

### 一、这一课的目标

我们最终希望：

```text
Tool Success
    │
    ▼
current_price
```

以及：

```text
Tool Failure
    │
    ▼
tool_error
    │
    ▼
Failure Path
```

也就是说：

```text
                  ┌── Success ──→ current_price
                  │
Tool Execution ───┤
                  │
                  └── Failure ──→ tool_error
```

而不是：

```text
Tool Execution
      │
      X
   Exception
      │
   Graph Crash
```

---

### 二、第一步：让 Mock Tool 能够失败

目前我们的 Tool：

```python
@tool
def get_stock_price(ticker: str) -> dict:
```

对于未知 ticker：

```python
mock_prices.get(ticker, 100.0)
```

仍然返回：

```python
{
    "ticker": "UNKNOWN",
    "price": 100.0
}
```

这对于 Lesson 5 不够好。

因为：

> **未知 ticker 应该是 Tool Failure，而不是一个假价格。**

所以我们需要改变 Mock Tool 的行为。

---

### 三、修改 `get_stock_price`

修改：

```text
app/tools/financial.py
```

完整版本：

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class StockPriceInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    mock_prices = {
        "AAPL": 200.0,
        "MSFT": 450.0,
        "GOOGL": 180.0,
    }

    if ticker not in mock_prices:
        raise ValueError(
            f"Stock price not found for ticker: {ticker}"
        )

    return {
        "ticker": ticker,
        "price": mock_prices[ticker],
    }
```

这里的核心变化是：

```python
if ticker not in mock_prices:
    raise ValueError(...)
```

---

### 四、为什么这里可以抛 Exception？

这是一个很重要的设计问题。

可能会产生一个疑问：

> 刚才不是说 Tool Failure 不应该让 Graph Crash 吗？

这里需要区分两个层次。

#### Tool 层

Tool 本身负责：

> **准确表达“我无法完成这个 Tool 请求”。**

所以：

```python
raise ValueError(...)
```

是合理的。

Tool 不应该偷偷返回：

```python
{
    "price": 0
}
```

或者：

```python
{
    "price": 100
}
```

来伪装成功。

---

#### Graph Node 层

真正负责：

> **把 Tool Exception 转换成 Graph 可处理的 State。**

也就是说：

```text
Tool
 │
 ├── Success → result
 │
 └── Failure → Exception
                    │
                    ▼
              Tool Node
                    │
                    ▼
                tool_error
```

这是我们这一课真正要实现的地方。

---

### 五、GraphState 增加 Tool Error

之前我们增加了：

```python
current_price: float | None
```

现在增加：

```python
tool_error: str | None
```

因此逻辑上：

```python
class GraphState(TypedDict):
    ...
    current_price: float | None
    tool_error: str | None
```

同时在：

```python
initialize_state()
```

中增加：

```python
"tool_error": None,
```

这一点不能漏。

因为我们之前已经明确：

> 新增 GraphState 字段之后，必须检查 `initialize_state()`。

---

### 六、修改 Tool Node

之前我们的 Node 类似：

```python
def get_stock_price_node(state):
    ticker = state["ticker"]

    result = get_stock_price.invoke(
        {"ticker": ticker}
    )

    return {
        "current_price": result["price"]
    }
```

现在我们需要增加明确的 Error Path。

完整修改为：

```python
from app.tools.financial import get_stock_price


def get_stock_price_node(state):
    ticker = state["ticker"]

    try:
        result = get_stock_price.invoke(
            {"ticker": ticker}
        )

        return {
            "current_price": result["price"],
            "tool_error": None,
        }

    except ValueError as exc:
        return {
            "tool_error": str(exc),
        }
```

---

### 七、为什么这里捕获 `ValueError`，而不是 `Exception`？

这是一个非常重要的工程习惯。

我们现在明确知道 Tool 对未知 ticker 使用：

```python
ValueError
```

所以 Node 捕获：

```python
except ValueError
```

而不是：

```python
except Exception
```

原因是：

```text
精确捕获已知错误
        ↓
明确处理
        ↓
未知错误继续暴露
```

相比：

```python
except Exception:
    ...
```

更容易发现真正的程序 Bug。

项目架构中已经明确要求不要使用：

```python
except Exception:
    pass
```

静默吞错。:chatgpt-content-reference{index="1"}

---

### 八、但是这里还有一个问题

现在：

```python
except ValueError:
    return {
        "tool_error": str(exc)
    }
```

没有返回：

```python
"current_price"
```

这其实是有意的。

因为失败情况下：

```text
current_price
```

应该保持原状态，而不是被伪造。

例如：

```text
current_price = None
tool_error = "Stock price not found..."
```

这比：

```text
current_price = 0
```

安全得多。

对于投资研究系统，这是非常重要的。

---

### 九、成功和失败状态

现在 Node 的输出有两种可能。

#### Success

```python
{
    "current_price": 200.0,
    "tool_error": None,
}
```

#### Failure

```python
{
    "tool_error": "Stock price not found for ticker: INVALID"
}
```

因此 Graph State 可以表达：

```text
Success
├── current_price = 200.0
└── tool_error = None
```

或者：

```text
Failure
├── current_price = None
└── tool_error = "..."
```

这就是显式 Failure State。

---

### 十、增加测试

现在修改：

```text
tests/test_tool_result_to_state.py
```

建议完整版本：

```python
from app.graph.nodes.tool_node import get_stock_price_node


def test_get_stock_price_result_updates_graph_state_aapl():
    state = {
        "ticker": "AAPL",
    }

    result = get_stock_price_node(state)

    assert result["current_price"] == 200.0
    assert result["tool_error"] is None


def test_get_stock_price_result_updates_graph_state_msft():
    state = {
        "ticker": "MSFT",
    }

    result = get_stock_price_node(state)

    assert result["current_price"] == 450.0
    assert result["tool_error"] is None


def test_get_stock_price_tool_failure():
    state = {
        "ticker": "INVALID",
    }

    result = get_stock_price_node(state)

    assert "tool_error" in result
    assert result["tool_error"] is not None
    assert "INVALID" in result["tool_error"]
```

现在我们有：

```text
AAPL
 ↓
Success

MSFT
 ↓
Success

INVALID
 ↓
Failure
```

---

### 十一、还需要直接测试 Tool Failure

Node 测试已经验证了 Failure Path，但 Tool 本身也应该有一个测试。

修改：

```text
tests/test_financial_tool.py
```

增加：

```python
import pytest

from app.tools.financial import get_stock_price
```

然后：

```python
def test_get_stock_price_invalid_ticker():
    with pytest.raises(ValueError, match="INVALID"):
        get_stock_price.invoke(
            {"ticker": "INVALID"}
        )
```

这里测试的是：

```text
Tool 层
```

而前面的：

```python
test_get_stock_price_tool_failure()
```

测试的是：

```text
Graph Node 层
```

这两个测试不要混为一谈。

---

### 十二、现在我们的错误边界变得清楚了

整个架构现在是：

```text
                 ┌───────────────┐
                 │ Graph State   │
                 │ ticker        │
                 └───────┬───────┘
                         │
                         ▼
               ┌─────────────────┐
               │ Tool Node       │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ get_stock_price │
               └────────┬────────┘
                        │
             ┌──────────┴──────────┐
             │                     │
          Success               Failure
             │                     │
             ▼                     ▼
      current_price           tool_error
```

这已经开始接近真正的 Agent Error Handling。

---

### 十三、为什么 `tool_error` 放进 State？

因为下一节点需要知道：

```text
Tool 成功了吗？
```

例如后面我们会有：

```text
Tool Node
   │
   ▼
route_after_tool
   │
   ├── success → continue
   │
   └── failure → retry / fallback / failure
```

如果 Error 只是 Python Exception：

```text
Exception
```

Graph 的后续节点无法自然读取。

而现在：

```python
state["tool_error"]
```

可以直接进行条件路由。

这与 Phase 2 的：

```text
llm_error
failure_reason
retry_count
```

是同一种架构思想。

---

### 十四、下一阶段会出现 Tool Failure Routing

本课我们暂时只完成：

```text
Tool Failure
 ↓
tool_error
```

下一课我们会进一步变成：

```text
                    ┌── success ──→ continue
                    │
Tool Node ──────────┤
                    │
                    └── failure ──→ recovery
```

也就是说：

### Lesson 6 — Tool Failure Routing / Retry

我们会开始讨论：

```text
Tool Failure
   ↓
Should Retry?
   ├── Yes → Tool Again
   └── No  → Failure Path
```

这时才会真正把：

```text
Error
+
Conditional Edge
+
Retry
```

结合起来。

---

### 十五、这一课暂时不要做的事情

现在不要：

- 接 Yahoo Finance
- 接真实金融 API
- 加网络 Retry
- 加 Exponential Backoff
- 加 Provider abstraction
- 加复杂 Error hierarchy
- 修改 LLM Node
- 把所有异常统一成一个 `Exception`
- 创建复杂的 error framework

这些都会在后续需要时逐步加入。

当前只学习：

> **Tool Failure → Explicit Graph State**

---

### Lesson 5 Acceptance Criteria

完成后应该满足：

#### Tool 层

- [ ] AAPL 正常
- [ ] MSFT 正常
- [ ] GOOGL 正常
- [ ] INVALID ticker 抛出 `ValueError`

#### State 层

- [ ] `GraphState` 有 `tool_error`
- [ ] `initialize_state()` 初始化 `tool_error = None`

#### Node 层

成功：

```text
current_price = 200
tool_error = None
```

失败：

```text
tool_error = "...INVALID..."
```