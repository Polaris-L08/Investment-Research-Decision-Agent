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


