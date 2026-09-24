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


## Lesson 5：Tool Failure

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
---


## Lesson 6: Tool Failure Routing / Retry

### 一、这一课解决什么问题？

Lesson 5 之后，我们已经能够得到：

#### Tool 成功

```text
ticker = AAPL
       ↓
get_stock_price
       ↓
current_price = 200
tool_error = None
```

#### Tool 失败

```text
ticker = INVALID
       ↓
get_stock_price
       ↓
tool_error = "Stock price not found..."
```

但现在存在一个问题：

> **Tool Failure 之后，Graph 应该做什么？**

我们不能让 Graph 简单地：

```text
Tool Failure
    ↓
END
```

因为某些错误是可以恢复的。

例如未来：

```text
API timeout
    ↓
Retry
```

而有些错误根本不应该 Retry：

```text
INVALID ticker
    ↓
Retry?
```

重复调用十次仍然是：

```text
INVALID ticker
```

所以这一课最重要的概念是：

> **不是所有 Tool Failure 都应该 Retry。**

---

### 二、先区分两类 Failure

为了保持这一课简单，我们先区分：

#### Retryable Failure

例如：

```text
Temporary timeout
Temporary provider error
Rate limit
Transient network error
```

这些错误：

```text
可能第一次失败
第二次成功
```

因此：

```text
Failure
  ↓
Retry
```

是合理的。

---

#### Non-Retryable Failure

例如：

```text
INVALID ticker
Missing required parameter
Invalid input
```

这种错误：

```text
重试不会改变输入
```

所以：

```text
Failure
  ↓
Retry
  ↓
Failure
  ↓
Retry
  ↓
...
```

是错误设计。

---

### 三、但是我们的 Mock Tool 目前只有一种 Failure

Lesson 5 中：

```python
id="..."
if ticker not in mock_prices:
    raise ValueError(...)
```

这属于：

```text
Invalid Input
```

所以严格来说：

> **当前 INVALID ticker 不应该 Retry。**

因此这一课我们需要增加一个**可以模拟 Retry 的 Tool Failure**。

为了避免现在引入真实网络，我们继续使用 Mock。

---

### 四、增加一个可重试的 Mock Failure

我们可以让特殊 ticker：

```text
RETRY
```

模拟一个临时错误。

但是这里有一个教学上的关键问题：

> 如果每次调用 `RETRY` 都失败，那么 Retry 没有任何意义。

所以我们需要让它：

```text
第一次调用 → Failure
第二次调用 → Success
```

这可以模拟真实 Provider 中的 transient failure。

---

### 五、为 Tool 增加一次性 Failure

修改：

```text
app/tools/financial.py
```

不过这里**不建议直接把全局计数器塞进 Tool**。

例如不要：

```python
call_count = 0
```

因为这种状态会污染测试，并且不符合最终生产架构。

更好的 Lesson 6 做法是：

> **把 retry simulation 放在 Tool Node 层，而不是污染 Tool 本身。**

这样 Tool 本身仍然是：

```text
Input
 ↓
Tool
 ↓
Result / Exception
```

而 Retry 属于：

```text
Graph orchestration
```

这是一个非常重要的架构边界。

---

### 六、Tool Node 增加 `retry_count`

我们之前已经有：

```text
tool_error
```

现在需要：

```text
retry_count
```

这与 Phase 2 的：

```text
retry_count
```

思想一致。

修改 `GraphState`：

```python
retry_count: int
```

并在：

```python
initialize_state()
```

中：

```python
"retry_count": 0,
```

---

### 七、为什么 `retry_count` 是 State？

因为 Retry 是：

> **Graph 当前执行过程中的状态。**

例如：

```text
第一次 Tool Call
retry_count = 0

失败
↓
retry_count = 1

第二次 Tool Call
↓
失败
↓
retry_count = 2
```

Graph 必须知道：

```text
我已经重试几次了？
```

否则无法安全限制：

```text
最大 Retry 次数
```

---

### 八、定义最大 Retry 次数

在 Tool Node 文件中：

```python
MAX_TOOL_RETRIES = 2
```

这里要特别注意语义：

```text
初始调用 = 1
retry = 2
```

所以最多：

```text
3 次 Tool Execution
```

这与 Phase 2 的：

```text
MAX_LLM_RETRIES = 2
```

保持一致。

---

### 九、但是 Lesson 6 先不要在 Node 内部 `while`

这里是一个非常重要的 LangGraph 设计原则。

不要写：

```python
while retry_count < 2:
    try:
        ...
    except:
        ...
```

因为这样：

```text
Retry
```

发生在：

```text
Python Function 内部
```

而不是：

```text
LangGraph topology
```

我们希望 Graph 本身能够表达：

```text
Tool
 ↓
Route
 ├── Success
 ├── Retry
 └── Failure
```

所以：

> **Retry 应该由 Graph Edge 控制，而不是 Node 内部 while loop。**

---

### 十、因此 Tool Node 只负责一次执行

我们把 Node 设计成：

```text
get_stock_price_node
```

每次只做：

```text
一次 Tool Call
```

然后更新：

```text
current_price
```

或者：

```text
tool_error
```

以及：

```text
retry_count
```

---

### 十一、修改 Tool Node

可以将当前 Node 调整为：

```python
from app.tools.financial import get_stock_price


def get_stock_price_node(state):
    ticker = state["ticker"]
    retry_count = state["retry_count"]

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
            "retry_count": retry_count + 1,
        }
```

但是这里马上出现一个问题：

#### INVALID ticker

第一次：

```text
retry_count = 0
```

失败后：

```text
retry_count = 1
```

然后如果我们无脑 Retry：

```text
retry_count = 2
```

最终：

```text
retry_count = 3
```

但实际上 INVALID ticker 根本不应该 Retry。

所以我们需要进一步增加：

```text
Failure Classification
```

---

### 十二、Lesson 6 不要把所有 `ValueError` 都当成 Retryable

这是本课真正的核心。

我们应该让 Node 输出：

```text
tool_error
tool_retryable
```

例如 State 增加：

```python
tool_retryable: bool
```

初始化：

```python
"tool_retryable": False,
```

成功：

```python
{
    "current_price": 200.0,
    "tool_error": None,
    "tool_retryable": False,
}
```

失败：

```python
{
    "tool_error": "...",
    "tool_retryable": True,
}
```

或者：

```python
{
    "tool_error": "...",
    "tool_retryable": False,
}
```

这样 Conditional Edge 才有依据。

---

### 十三、不过我们现在没有不同类型的 Tool Exception

所以我们可以在 Mock Tool 中明确增加两种异常：

```text
Invalid ticker
Transient failure
```

例如：

```python
class TransientToolError(Exception):
    pass
```

然后：

```python
if ticker == "TEMP_ERROR":
    raise TransientToolError(
        "Temporary stock price provider error."
    )
```

以及：

```python
if ticker not in mock_prices:
    raise ValueError(
        f"Stock price not found for ticker: {ticker}"
    )
```

这样：

```text
ValueError
    ↓
Non-retryable

TransientToolError
    ↓
Retryable
```

这就非常清楚。

---

### 十四、修改 `financial.py`

建议现在把完整文件调整为：

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class TransientToolError(Exception):
    """Temporary tool failure that may succeed when retried."""


class StockPriceInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    if ticker == "TEMP_ERROR":
        raise TransientToolError(
            "Temporary stock price provider error."
        )

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

现在我们拥有：

```text
AAPL
 ↓
Success

MSFT
 ↓
Success

INVALID
 ↓
ValueError
 ↓
Non-retryable

TEMP_ERROR
 ↓
TransientToolError
 ↓
Retryable
```

---

### 十五、修改 GraphState

增加：

```python
tool_retryable: bool
```

和：

```python
retry_count: int
```

因此相关 State 逻辑：

```python
current_price: float | None
tool_error: str | None
tool_retryable: bool
retry_count: int
```

初始化：

```python
"current_price": None,
"tool_error": None,
"tool_retryable": False,
"retry_count": 0,
```

---

### 十六、修改 Tool Node

现在 Node 可以精确区分：

```python
from app.tools.financial import (
    TransientToolError,
    get_stock_price,
)


def get_stock_price_node(state):
    ticker = state["ticker"]
    retry_count = state["retry_count"]

    try:
        result = get_stock_price.invoke(
            {"ticker": ticker}
        )

        return {
            "current_price": result["price"],
            "tool_error": None,
            "tool_retryable": False,
        }

    except TransientToolError as exc:
        return {
            "tool_error": str(exc),
            "tool_retryable": True,
            "retry_count": retry_count + 1,
        }

    except ValueError as exc:
        return {
            "tool_error": str(exc),
            "tool_retryable": False,
        }
```

这里有一个很重要的设计：

#### TransientToolError

```text
tool_retryable = True
retry_count += 1
```

#### ValueError

```text
tool_retryable = False
```

而不是：

```python
except Exception:
```

---

### 十七、现在建立 Conditional Router

新增：

```python
def route_after_tool(state):
    if state["tool_error"] is None:
        return "success"

    if (
        state["tool_retryable"]
        and state["retry_count"] <= MAX_TOOL_RETRIES
    ):
        return "retry"

    return "failure"
```

其中：

```python
MAX_TOOL_RETRIES = 2
```

---

### 十八、Router 的逻辑

可以画成：

```text
                 Tool Node
                    │
             ┌──────┴──────┐
             │             │
          Success        Failure
             │             │
             │       ┌─────┴─────┐
             │       │           │
             │   Retryable   Non-retryable
             │       │           │
             │       ▼           ▼
             │     Retry       Failure
             │
             ▼
          Continue
```

更准确一点：

```text
tool_error is None
       │
       └── success

tool_error != None
       │
       ├── retryable AND retry_count <= 2
       │        │
       │        └── retry
       │
       └── otherwise
                │
                └── failure
```

---

### 十九、为什么 Retry 是 Edge？

这是本课最重要的 LangGraph 概念。

我们希望 Graph Topology 本身表达：

```text
Tool
 ↓
Router
 ├── retry → Tool
 ├── failure → Failure Handler
 └── success → Continue
```

也就是说：

```text
Retry
```

不是：

```python
while ...
```

而是：

```text
Graph Edge
```

这样 LangGraph 才能：

- checkpoint
- interrupt
- observe
- recover
- visualize

这些能力。

这也是为什么最终生产系统应该让 **workflow control flow 显式存在于 Graph topology 中**。

---

### 二十、构建最小 Retry Graph

这一课暂时不要把它接回完整 Phase 2 Graph。

创建一个专门用于 Tool Retry 的最小 Graph。

例如：

```text
tests / 或 graph 测试辅助构建
```

我们可以先在：

```text
app/graph/tool_graph.py
```

创建：

```python
from langgraph.graph import StateGraph, START, END

from app.graph.nodes.tool_node import (
    get_stock_price_node,
    route_after_tool,
)


def build_tool_graph():
    builder = StateGraph(GraphState)

    builder.add_node(
        "get_stock_price",
        get_stock_price_node,
    )

    builder.add_node(
        "tool_failure",
        handle_tool_failure,
    )

    builder.add_edge(
        START,
        "get_stock_price",
    )

    builder.add_conditional_edges(
        "get_stock_price",
        route_after_tool,
        {
            "success": END,
            "retry": "get_stock_price",
            "failure": "tool_failure",
        },
    )

    builder.add_edge(
        "tool_failure",
        END,
    )

    return builder.compile()
```

但是这里涉及你当前项目具体的 `GraphState`、`handle_tool_failure` 所在文件位置。

**所以这一部分不要直接照抄创建。**

Lesson 6 的第一阶段，我们先把 **Router 单独测试好**，然后再把它正式加入 Graph。

这样仍然遵循我们一直采用的：

```text
先单点
 ↓
再集成
```

---

### 二十一、先测试 Router

增加：

```text
tests/test_tool_failure_routing.py
```

完整测试：

```python
from app.graph.nodes.tool_node import route_after_tool


def test_tool_success_routes_to_success():
    state = {
        "tool_error": None,
        "tool_retryable": False,
        "retry_count": 0,
    }

    assert route_after_tool(state) == "success"


def test_retryable_tool_failure_routes_to_retry():
    state = {
        "tool_error": "Temporary error",
        "tool_retryable": True,
        "retry_count": 1,
    }

    assert route_after_tool(state) == "retry"


def test_retryable_tool_failure_stops_after_max_retries():
    state = {
        "tool_error": "Temporary error",
        "tool_retryable": True,
        "retry_count": 3,
    }

    assert route_after_tool(state) == "failure"


def test_non_retryable_tool_failure_routes_to_failure():
    state = {
        "tool_error": "Invalid ticker",
        "tool_retryable": False,
        "retry_count": 0,
    }

    assert route_after_tool(state) == "failure"
```

---

### 二十二、再测试 Tool Node 的错误分类

在：

```text
tests/test_tool_result_to_state.py
```

增加：

```python
def test_retryable_tool_failure():
    state = {
        "ticker": "TEMP_ERROR",
        "retry_count": 0,
    }

    result = get_stock_price_node(state)

    assert result["tool_error"] is not None
    assert result["tool_retryable"] is True
    assert result["retry_count"] == 1
```

再增加：

```python
def test_invalid_ticker_is_not_retryable():
    state = {
        "ticker": "INVALID",
        "retry_count": 0,
    }

    result = get_stock_price_node(state)

    assert result["tool_error"] is not None
    assert result["tool_retryable"] is False
    assert "INVALID" in result["tool_error"]
```

这样我们就验证：

```text
TEMP_ERROR
   ↓
retryable

INVALID
   ↓
non-retryable
```

---

### 二十三、这里有一个细节需要特别注意

你会发现：

```text
retry_count
```

是在：

```python
TransientToolError
```

发生之后才：

```python
retry_count + 1
```

因此：

```text
第一次调用失败
retry_count = 1
```

Router 判断：

```text
1 <= 2
```

于是：

```text
retry
```

第二次：

```text
retry_count = 2
```

如果再次失败：

```text
retry
```

第三次：

```text
retry_count = 3
```

此时：

```text
3 <= 2
```

为 False：

```text
failure
```

所以总执行次数：

```text
Initial attempt
+
Retry #1
+
Retry #2
=
3 executions
```

这和我们之前 Phase 2 的 Retry 语义保持一致。

---

### 二十四、但是 `TEMP_ERROR` 现在永远失败

对。

所以目前我们验证的是：

```text
Retry Limit
```

还不是：

```text
Retry Recovery
```

这是故意的。

下一阶段我们会让 Mock Provider 能够模拟：

```text
第一次失败
第二次成功
```

从而验证：

```text
Tool
 ↓
Failure
 ↓
Retry
 ↓
Success
```

这会在后续 Tool Calling Loop / Provider abstraction 中更自然地实现。

当前 Lesson 6 的核心是：

> **Graph 能识别 Retryable Failure，并且不会无限 Retry。**

---

### 二十五、Lesson 6 的 Graph Topology

完成本课之后，我们希望明确得到：

```text
                 ┌─────────────────────┐
                 │                     │
                 ▼                     │
START → Tool Node → Router ── retry ───┘
                    │
                    ├── success → END
                    │
                    └── failure → Failure Handler → END
```

这比：

```text
Tool Node
   │
   └── while retry...
```

更加符合 LangGraph 的工作流思想。

---

### 二十六、这一课暂时不要做

不要现在：

- 接真实 Provider
- 接 Yahoo Finance
- 实现指数退避
- 实现 jitter
- 做 API rate-limit framework
- 做复杂异常层级
- 做 Provider fallback
- 修改完整 Investment Decision Graph
- 实现 Tool Calling Loop

这些都会在后面逐步加入。

---

### Lesson 6 Acceptance Criteria

这一课需要验证：

#### Tool Error Classification

```text
AAPL
 ↓
Success

INVALID
 ↓
Non-retryable Failure

TEMP_ERROR
 ↓
Retryable Failure
```

#### State

- [ ] `tool_retryable` 存在
- [ ] `retry_count` 存在
- [ ] 初始化正确
- [ ] Retryable failure 会增加 `retry_count`

#### Router

- [ ] Success → `success`
- [ ] Retryable + retry_count 未超限 → `retry`
- [ ] Retryable + retry_count 超限 → `failure`
- [ ] Non-retryable → `failure`

---


## Lesson 7：Multiple Tools

Lesson 6 我们解决的是：

> **一个 Tool 出错以后，Graph 如何判断 Success / Retry / Failure。**

现在进入一个更重要的能力：

> **一个 LLM 可以同时拥有多个 Tools，并根据用户需求决定调用哪个 Tool。**

---

### 一、Lesson 7 的目标

目前我们的 Agent 只有一个 Tool：

```text
LLM
 │
 └── get_stock_price
```

本节增加第二个 Tool：

```text
LLM
 │
 ├── get_stock_price
 │
 └── get_company_info
```

最终希望理解完整的关系：

```text
                    ┌── get_stock_price
                    │
LLM ── Tool Call ───┤
                    │
                    └── get_company_info
```

这里最重要的不是“多写一个 Python 函数”。

而是理解：

> **LLM 如何从多个 Tool 中选择合适的 Tool。**

---

### 二、为什么需要 Multiple Tools？

真实的 Investment Research Agent 不可能只有：

```text
get_stock_price()
```

例如后续可能存在：

```text
get_stock_price()
get_company_info()
get_financial_statements()
get_market_data()
get_news()
get_industry_data()
```

LLM 的职责不是执行这些函数。

它负责：

```text
理解用户需求
    ↓
判断需要什么信息
    ↓
选择 Tool
    ↓
生成 Tool Call
```

而 Graph / Tool Runtime 负责：

```text
接收 Tool Call
    ↓
找到对应 Tool
    ↓
执行 Tool
    ↓
返回 Tool Result
```

因此架构开始变成：

```text
User
 ↓
LLM
 ↓
选择 Tool
 ↓
Tool Call
 ↓
Tool Runtime
 ↓
具体 Tool
 ↓
Tool Result
```

---

### 三、Lesson 7 不做什么

这一节我们**故意不做**：

- Tool Calling Loop
- 多 Tool 连续调用
- Tool Result 回传 LLM
- Real API
- Yahoo Finance
- Financial Statements
- Provider abstraction
- Agent 自动循环

这些属于后面的 Lesson。

Lesson 7 只解决一个问题：

> **LLM 面对多个 Tools 时，能否正确选择并生成对应的 Tool Call？**

---

### 四、第二个 Tool：`get_company_info`

我们继续保持目前的 Mock 策略。

新增：

```python
get_company_info(ticker)
```

例如：

```text
AAPL
↓
{
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology"
}
```

暂时不连接任何真实数据源。

---

### 五、修改 `app/tools/financial.py`

在现有文件中增加第二个 Tool。

你现在的文件应该已经包含：

```python
StockPriceInput
TransientToolError
get_stock_price
```

在这个基础上增加：

```python
class CompanyInfoInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


@tool(args_schema=CompanyInfoInput)
def get_company_info(ticker: str) -> dict:
    """Get basic company information for a stock ticker."""

    mock_companies = {
        "AAPL": {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "sector": "Technology",
        },
        "MSFT": {
            "ticker": "MSFT",
            "company_name": "Microsoft Corporation",
            "sector": "Technology",
        },
        "GOOGL": {
            "ticker": "GOOGL",
            "company_name": "Alphabet Inc.",
            "sector": "Communication Services",
        },
    }

    if ticker not in mock_companies:
        raise ValueError(
            f"Company information not found for ticker: {ticker}"
        )

    return mock_companies[ticker]
```

注意：

#### `get_stock_price`

负责：

```text
价格
```

#### `get_company_info`

负责：

```text
公司基本信息
```

不要让一个 Tool 同时返回：

```text
price
company_name
sector
...
```

这是非常重要的 Tool Design 原则：

> **一个 Tool 应该有清晰、单一的业务职责。**

---

### 六、先测试第二个 Tool 本身

新建：

```text
tests/test_multiple_tools.py
```

第一部分先不要测试 LLM。

测试 Tool 本身：

```python
from app.tools.financial import get_company_info


def test_get_company_info_returns_company_data():
    result = get_company_info.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["sector"] == "Technology"


def test_get_company_info_requires_ticker():
    schema = get_company_info.args_schema

    assert "ticker" in schema.model_fields


def test_get_company_info_invalid_ticker():
    import pytest

    with pytest.raises(
        ValueError,
        match="Company information not found",
    ):
        get_company_info.invoke(
            {"ticker": "INVALID"}
        )
```

先运行：

```bash
python -m pytest tests/test_multiple_tools.py -v
```

这里我们首先验证：

```text
Tool Definition
      ↓
Tool Schema
      ↓
Tool Invocation
      ↓
Tool Result
      ↓
Tool Failure
```

也就是说，我们没有因为进入 Multiple Tools 就跳过前面学过的 Tool 基础。

---

### 七、然后让 LLM 同时看到两个 Tools

现在是本节真正的重点。

你之前 Lesson 3 使用的是：

```python
llm_with_tools = llm.bind_tools(
    [get_stock_price]
)
```

现在改成：

```python
llm_with_tools = llm.bind_tools(
    [
        get_stock_price,
        get_company_info,
    ]
)
```

这意味着：

> LLM 的 Tool registry 现在包含两个 Tool。

---

### 八、一个非常重要的概念

注意：

```python
llm.bind_tools(
    [
        get_stock_price,
        get_company_info,
    ]
)
```

**并不是执行两个 Tool。**

它只是把 Tool 的：

```text
name
description
input schema
```

提供给 LLM。

例如 LLM 看到类似：

```text
get_stock_price
    ticker: string

get_company_info
    ticker: string
```

然后由 LLM 根据 Prompt 决定：

```text
用户：
告诉我 AAPL 的股价

LLM：
→ get_stock_price
```

或者：

```text
用户：
告诉我 AAPL 是什么公司，属于什么行业

LLM：
→ get_company_info
```

这就是：

> **Tool Selection**

---

### 九、增加两个 Tool Selection 测试

继续在：

```text
tests/test_multiple_tools.py
```

中增加：

```python
from langchain_core.messages import HumanMessage

from app.llm import get_llm
from app.tools.financial import (
    get_company_info,
    get_stock_price,
)


def test_llm_selects_stock_price_tool():
    llm = get_llm()

    llm_with_tools = llm.bind_tools(
        [
            get_stock_price,
            get_company_info,
        ]
    )

    response = llm_with_tools.invoke(
        [
            HumanMessage(
                content="What is the current stock price of AAPL?"
            )
        ]
    )

    assert response.tool_calls

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "get_stock_price"
    assert tool_call["args"]["ticker"] == "AAPL"
```

第二个：

```python
def test_llm_selects_company_info_tool():
    llm = get_llm()

    llm_with_tools = llm.bind_tools(
        [
            get_stock_price,
            get_company_info,
        ]
    )

    response = llm_with_tools.invoke(
        [
            HumanMessage(
                content=(
                    "What company is AAPL and "
                    "what sector does it belong to?"
                )
            )
        ]
    )

    assert response.tool_calls

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "get_company_info"
    assert tool_call["args"]["ticker"] == "AAPL"
```

---

### 十、这里有一个测试设计上的重要变化

Lesson 3 我们验证的是：

```text
LLM
 ↓
get_stock_price
```

现在 Lesson 7 验证：

```text
LLM
 ├── get_stock_price
 └── get_company_info
```

因此测试的重点变成：

```text
Tool Registry
      ↓
Tool Selection
      ↓
Tool Call Name
      ↓
Tool Call Arguments
```

尤其是：

```python
assert tool_call["name"] == ...
```

非常重要。

因为：

```python
response.tool_calls
```

只说明：

> LLM 决定调用 Tool。

但是：

```python
tool_call["name"]
```

才能说明：

> LLM 选择了哪个 Tool。

---

### 十一、不要直接测试 Tool Result

本节暂时不要写：

```python
get_stock_price.invoke(...)
```

然后把结果喂回 LLM。

也不要写：

```text
LLM
 ↓
Tool
 ↓
LLM
```

因为这已经进入下一阶段：

**Lesson 8 — Tool Calling Loop**

Lesson 7 只观察：

```text
Prompt
 ↓
LLM
 ↓
Tool Call
```

Lesson 8 才会变成：

```text
Prompt
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

这个区别非常重要。

---

### 十二、Lesson 7 的 Graph 暂时也不需要大改

这一节我们甚至**不要求修改主 Graph topology**。

因为我们现在学习的是：

```text
LLM Tool Registry
        +
Tool Selection
```

而不是 Workflow Loop。

所以目前：

```text
Graph
```

仍然可以保持现状。

我们通过测试独立验证：

```text
LLM
 │
 ├── Tool A
 │
 └── Tool B
```

这样可以继续贯彻我们一直使用的：

> **先隔离一个能力，再把它集成进 Graph。**

---

### 十三、Lesson 7 当前任务

你现在按下面顺序完成即可。

#### Step 1

修改：

```text
app/tools/financial.py
```

增加：

```text
CompanyInfoInput
get_company_info
```

---

#### Step 2

创建：

```text
tests/test_multiple_tools.py
```

加入：

- Tool invocation
- Schema
- Invalid ticker
- LLM selects `get_stock_price`
- LLM selects `get_company_info`

---

#### Step 3

运行：

```bash
python -m pytest tests/test_multiple_tools.py -v
```

---

#### Step 4

如果通过，再运行完整测试：

```bash
python -m pytest tests -v
```

---

### Lesson 7 Acceptance Criteria

全部满足才算 Lesson 7 完成：

- [ ] `get_company_info` Tool 存在
- [ ] `CompanyInfoInput` 使用 Pydantic
- [ ] Tool 有明确 description
- [ ] Tool 可以正常 `.invoke()`
- [ ] Invalid ticker 会产生明确错误
- [ ] LLM 同时注册两个 Tools
- [ ] 查询股价时选择 `get_stock_price`
- [ ] 查询公司信息时选择 `get_company_info`
- [ ] Tool Call 参数正确
- [ ] 现有全部测试继续通过
- [ ] 本节没有提前实现 Tool Calling Loop

---


## Lesson 8：Tool Calling Loop

前面 7 个 Lesson，我们已经把 Tool Calling 的各个零件拆开学习：

```text
Lesson 1
Tool Definition
        ↓
Lesson 2
Tool Schema
        ↓
Lesson 3
LLM → Tool Call
        ↓
Lesson 4
Tool Result → Graph State
        ↓
Lesson 5
Tool Failure
        ↓
Lesson 6
Tool Failure → Retry / Failure
        ↓
Lesson 7
Multiple Tools
```

现在终于要把其中最关键的一条链真正串起来：

```text
                    ┌──────────────┐
                    │              │
                    ▼              │
User → LLM → Tool Call → Tool → Tool Result
                    ▲              │
                    └──── LLM ◄───┘
```

也就是：

> **LLM 不只是调用一次 Tool，而是能够根据 Tool Result 决定下一步是否还需要 Tool。**

---

### 一、Lesson 8 的核心目标

我们最终要建立这样的流程：

```text
START
  ↓
LLM
  ↓
是否需要 Tool？
  ├── No ───────────────→ END
  │
  └── Yes
       ↓
    Tool Call
       ↓
    Tool Execution
       ↓
    Tool Result
       ↓
      LLM
       │
       └───────────────┐
                       │
                       ▼
                 是否还需要 Tool？
```

这里第一次出现真正的：

> **循环（Loop）**

这也是 LangGraph 非常重要的能力之一。

---

### 二、先明确：为什么需要 Loop？

假设用户问：

> “AAPL 当前股价是多少？然后告诉我它属于哪个行业。”

LLM 第一次看到问题：

```text
User
 ↓
LLM
```

它可能决定：

```text
→ get_stock_price(AAPL)
```

Tool 返回：

```python
{
    "ticker": "AAPL",
    "price": 200.0
}
```

但是：

> LLM 还没有得到行业信息。

因此不能结束。

它需要继续：

```text
Tool Result
    ↓
LLM
    ↓
get_company_info(AAPL)
```

得到：

```python
{
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology"
}
```

然后 LLM 才能生成最终答案。

所以完整过程是：

```text
User
 ↓
LLM
 ↓
get_stock_price
 ↓
Tool Result
 ↓
LLM
 ↓
get_company_info
 ↓
Tool Result
 ↓
LLM
 ↓
Final Answer
```

这就是 Tool Calling Loop。

---

### 三、一个非常重要的架构变化

Lesson 7 我们测试的是：

```text
LLM
 ↓
Tool Call
```

Lesson 8 开始，我们真正构建：

```text
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

因此这一次需要真正进入 Graph。

---

### 四、我们先不要修改现有主 Graph

这里继续遵守我们的教学策略：

> **先建立独立的最小 Loop，再考虑把它合并到现有 Investment Agent。**

因此我们新增一个专门用于 Lesson 8 的 Graph。

建议创建：

```text
app/graph/tool_loop.py
```

它只负责：

```text
LLM ↔ Tools
```

而不是：

```text
Investment Research
```

这样不会污染当前 Phase 2 的主 Graph。

---

### 五、Tool Calling Loop 的 State

创建：

```python id="8ayc5m"
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ToolLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

这里出现一个我们之前还没有正式使用过的东西：

```python
Annotated[list[BaseMessage], add_messages]
```

这是本节非常重要的知识点。

---

### 六、为什么不能直接用普通的 `messages`

如果写：

```python
messages: list[BaseMessage]
```

那么 Node 返回：

```python
{
    "messages": [new_message]
}
```

它的语义更接近：

> 用新的 list 更新这个字段。

但是 Tool Calling Loop 需要：

```text
HumanMessage
    ↓
AIMessage(tool_call)
    ↓
ToolMessage
    ↓
AIMessage
    ↓
ToolMessage
    ↓
AIMessage
```

我们需要的是：

> **不断追加消息，而不是覆盖消息。**

所以使用：

```python
Annotated[
    list[BaseMessage],
    add_messages
]
```

告诉 LangGraph：

> `messages` 字段使用 `add_messages` 作为 reducer。

---

### 七、LLM Node

新建：

```text id="9d1f4c"
app/graph/nodes/tool_loop_node.py
```

内容：

```python
from langchain_core.messages import BaseMessage

from app.llm import get_llm
from app.tools.financial import (
    get_company_info,
    get_stock_price,
)


llm_with_tools = get_llm().bind_tools(
    [
        get_stock_price,
        get_company_info,
    ]
)


def tool_loop_llm_node(
    state: dict,
) -> dict:
    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }
```

这里第一次出现一个非常重要的结构：

```text
state["messages"]
       ↓
      LLM
       ↓
AIMessage
       ↓
state["messages"]
```

由于 `messages` 使用 `add_messages` reducer，所以不会覆盖之前的消息。

---

### 八、Tool Node

现在我们需要真正执行 LLM 产生的 Tool Call。

这里先使用 LangChain/LangGraph 已经提供的 ToolNode。

修改：

```text id="q5r9t4"
app/graph/tool_loop.py
```

加入：

```python
from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.tools.financial import (
    get_company_info,
    get_stock_price,
)
```

然后：

```python
tools = [
    get_stock_price,
    get_company_info,
]

tool_node = ToolNode(tools)
```

这里要特别理解：

> `ToolNode` 是 LangGraph 对 Tool Execution 的封装。

我们之前 Lesson 4 手工写过：

```python
result = get_stock_price.invoke(...)
```

现在不再手工解析：

```text
AIMessage.tool_calls
```

而是让：

```text
ToolNode
```

负责执行这些 Tool Calls。

---

### 九、Conditional Routing

接下来是整个 Lesson 8 最重要的 Graph Routing。

我们需要判断：

```text
LLM 返回的 AIMessage
        ↓
有没有 tool_calls？
```

如果：

```text
有
 ↓
ToolNode
```

如果：

```text
没有
 ↓
END
```

创建：

```python id="p5q4hy"
def route_after_llm(state: ToolLoopState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"
```

这个函数非常简单，但它代表了一个非常重要的 Agent 模式：

```text
LLM
 ↓
Decision
 ├── Tool
 └── Final Answer
```

---

### 十、构建 Loop Graph

完整：

```python id="6u3jz8"
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.llm import get_llm
from app.tools.financial import (
    get_company_info,
    get_stock_price,
)


class ToolLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


tools = [
    get_stock_price,
    get_company_info,
]

llm_with_tools = get_llm().bind_tools(tools)

tool_node = ToolNode(tools)


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


def build_tool_loop_graph():
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

---

### 十一、现在观察这个 Graph Topology

这是 Lesson 8 最重要的 Graph：

```text
              ┌──────────────────────┐
              │                      │
              ▼                      │
           ┌──────┐                 │
START ───→ │ LLM  │                 │
           └───┬──┘                 │
               │                    │
        ┌──────┴──────┐             │
        │             │             │
   tool_calls       no tool_calls   │
        │             │             │
        ▼             ▼             │
   ┌────────┐        END            │
   │ Tools  │                       │
   └────┬───┘                       │
        │                            │
        └────────────────────────────┘
```

这就是一个真正的 Agent Loop。

注意：

```text
Tools → LLM
```

而不是：

```text
Tools → END
```

这是 Lesson 8 与 Lesson 4 的本质区别。

---

### 十二、第一次运行：单 Tool

先测试最简单的：

> “What is the current stock price of AAPL?”

流程应该是：

```text
HumanMessage
     ↓
LLM
     ↓
get_stock_price(AAPL)
     ↓
ToolMessage
     ↓
LLM
     ↓
Final AIMessage
```

---

### 十三、测试文件

创建：

```text id="0hrf3f"
tests/test_tool_calling_loop.py
```

第一组测试：

```python id="5k1h2m"
from langchain_core.messages import HumanMessage

from app.graph.tool_loop import build_tool_loop_graph


def test_tool_calling_loop_returns_final_answer():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What is the current stock price "
                        "of AAPL?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    assert len(messages) >= 4

    assert messages[0].type == "human"
    assert messages[1].type == "ai"
    assert messages[1].tool_calls

    assert messages[2].type == "tool"
    assert messages[3].type == "ai"

    assert not messages[3].tool_calls
```

这里我们不是简单测试：

```python
assert result
```

而是在验证整个消息链：

```text
Human
 ↓
AI Tool Call
 ↓
Tool Result
 ↓
AI Final Answer
```

---

### 十四、第二个测试：Multiple Tools Loop

然后测试 Lesson 7 的多个 Tool 能否真正进入 Loop。

```python id="3g2x7n"
def test_tool_calling_loop_can_use_company_info():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What company is AAPL and "
                        "what sector does it belong to?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    tool_calls = [
        message.tool_calls
        for message in messages
        if message.type == "ai"
        and message.tool_calls
    ]

    assert tool_calls

    first_tool_call = tool_calls[0][0]

    assert first_tool_call["name"] == "get_company_info"
    assert first_tool_call["args"]["ticker"] == "AAPL"

    assert messages[-1].type == "ai"
    assert not messages[-1].tool_calls
```

---

### 十五、第三个测试：真正验证 Loop

这一测试非常重要。

我们让 LLM 面对一个需要**两个不同信息源**的问题：

> “What is the current stock price of AAPL, and what sector does the company belong to?”

理论流程：

```text
              ┌─ get_stock_price
              │
LLM ──────────┤
              │
              └─ get_company_info
```

但这里有一个现实问题：

> **LLM 不一定严格按照我们期待的顺序调用两个 Tool。**

它可能：

```text
get_stock_price
 ↓
get_company_info
 ↓
final
```

也可能：

```text
get_company_info
 ↓
get_stock_price
 ↓
final
```

甚至某些模型支持一次 AIMessage 中产生多个 Tool Calls。

因此本测试**不要测试调用顺序**。

应该测试：

```python id="u3g5s2"
def test_tool_calling_loop_can_use_multiple_tools():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What is the current stock price of AAPL, "
                        "and what sector does the company belong to?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    tool_names = []

    for message in messages:
        if message.type == "ai":
            for tool_call in message.tool_calls:
                tool_names.append(tool_call["name"])

    assert "get_stock_price" in tool_names
    assert "get_company_info" in tool_names

    assert messages[-1].type == "ai"
    assert not messages[-1].tool_calls
```

这个测试真正验证：

```text
LLM
 ↓
Tool A
 ↓
LLM
 ↓
Tool B
 ↓
LLM
 ↓
Final Answer
```

或者：

```text
LLM
 ↓
Tool A + Tool B
 ↓
LLM
 ↓
Final Answer
```

两者都可以。

---

### 十六、这里必须理解一个 LangGraph 核心概念

现在我们有：

```python
builder.add_edge(
    "tools",
    "llm",
)
```

这条 Edge：

```text
Tools → LLM
```

就是 Loop 的来源。

LangGraph 并不是：

```text
while True:
    ...
```

而是：

```text
Graph Topology
       ↓
Conditional Edge
       ↓
循环回到之前的 Node
```

这和 Lesson 6 的 Retry 思路完全一致。

---

### 十七、Retry Loop 和 Tool Calling Loop 的区别

现在我们已经可以把两个概念区分开：

#### Lesson 6

```text
Tool
 ↓
Failure
 ↓
Router
 ↓
Retry
 ↓
Tool
```

这是：

> **Error Recovery Loop**

---

#### Lesson 8

```text
LLM
 ↓
Tool
 ↓
Result
 ↓
LLM
```

这是：

> **Agent Reasoning / Tool Calling Loop**

两个 Loop 的目的完全不同。

```text
Retry Loop
    → 解决失败

Tool Calling Loop
    → 继续完成任务
```

这是后面设计 Agent 时非常重要的区别。

---

### 十八、本节暂时不要处理 Tool Error

虽然我们已经有：

```text
tool_error
tool_retry_count
handle_tool_failure
```

但是**不要现在把 Lesson 6 的错误处理直接复制进这个独立 Loop**。

原因是我们正在学习两个不同抽象：

```text
Lesson 6
Tool execution failure handling

Lesson 8
LLM ↔ Tool execution loop
```

下一阶段再把：

```text
Tool Loop
+
Tool Failure
+
Retry
```

统一起来会更清楚。

---

### 十九、Lesson 8 的测试顺序

先运行新测试：

```bash
python -m pytest tests/test_tool_calling_loop.py -v
```

如果通过，再运行：

```bash
python -m pytest tests -v
```

---

### 二十、Acceptance Criteria

Lesson 8 需要满足：

- [ ] `ToolLoopState` 使用 `messages`
- [ ] `messages` 使用 `add_messages` reducer
- [ ] LLM Node 可以读取完整 message history
- [ ] LLM 可以产生 Tool Call
- [ ] `ToolNode` 可以执行 Tool
- [ ] Tool Result 会进入 message history
- [ ] Tool Result 会再次发送给 LLM
- [ ] LLM 没有 Tool Call 时进入 `END`
- [ ] LLM 有 Tool Call 时进入 `ToolNode`
- [ ] `ToolNode → LLM` 形成 Graph Loop
- [ ] 单 Tool Calling Loop 成功
- [ ] Multiple Tools Calling Loop 成功
- [ ] 最终能够得到没有 `tool_calls` 的 AIMessage
- [ ] 所有旧测试继续通过

### 本节最重要的一句话

> **Tool Calling Agent 的核心不是“调用 Tool”，而是让 `LLM → Tool → Result → LLM` 成为一个由 Graph 控制的闭环。**
---


## Lesson 9：Tool Abstraction / Provider Separation

这一节非常重要，因为它开始从：

> “怎么使用 Tool？”

进入：

> **“怎么设计一个不会被具体数据供应商绑死的 Tool？”**

---

### 一、我们现在实际上有一个隐藏的问题

目前：

```text
get_stock_price
```

里面直接写了：

```python
mock_prices = {
    "AAPL": 200.0,
    "MSFT": 450.0,
    "GOOGL": 180.0,
}
```

这对于教学非常好。

但如果以后换成：

```text
Yahoo Finance
Alpha Vantage
Polygon
Finnhub
Bloomberg
公司内部数据服务
```

难道我们要修改：

```text
get_stock_price()
```

本身吗？

如果这样做：

```text
LLM
 ↓
Tool
 ↓
Yahoo Finance
```

然后以后：

```text
LLM
 ↓
Tool
 ↓
Alpha Vantage
```

那么 Tool 本身就会和 Provider 紧密耦合。

这是我们现在要解决的问题。

---

### 二、最终希望形成的结构

我们希望从：

```text
LLM
 ↓
Tool
 ↓
Mock Data
```

演变成：

```text
                    ┌── Mock Provider
                    │
LLM → Tool → Provider├── Yahoo Finance
                    │
                    ├── Alpha Vantage
                    │
                    └── Other Provider
```

也就是说：

> **Tool 决定“Agent 能做什么”，Provider 决定“数据从哪里来”。**

这是本节最重要的一句话。

---

### 三、Tool 和 Provider 的职责

我们先把职责彻底分开。

#### Tool

例如：

```text
get_stock_price(ticker)
```

它属于 Agent 能力层。

它应该关心：

```text
ticker
 ↓
获取股票价格
 ↓
返回标准结果
```

但它**不应该关心**：

```text
Yahoo Finance API 怎么调用
API Key 放在哪里
HTTP 请求怎么发送
第三方响应 JSON 长什么样
```

---

#### Provider

Provider 负责：

```text
数据获取
```

例如：

```text
StockPriceProvider
```

它可能有：

```text
MockStockPriceProvider
YahooFinanceStockPriceProvider
```

于是：

```text
Tool
 ↓
Provider
 ↓
Data Source
```

---

### 四、Lesson 9 第一目标

这一次我们**不接真实金融 API**。

仍然使用 Mock。

但是把 Mock 数据从 Tool 中移出去。

原来：

```text
get_stock_price
    ↓
mock_prices
```

改成：

```text
get_stock_price
    ↓
StockPriceProvider
    ↓
MockStockPriceProvider
    ↓
mock_prices
```

这一步看起来只是多了一层，但它实际上是在建立未来 Provider 替换的边界。

---

### 五、创建 Provider

新建：

```text
app/providers/financial.py
```

先定义：

```python
from abc import ABC, abstractmethod


class StockPriceProvider(ABC):

    @abstractmethod
    def get_stock_price(self, ticker: str) -> dict:
        """Get stock price data for a ticker."""
        raise NotImplementedError
```

这里使用抽象基类，是为了表达一个明确的 Contract：

```text
StockPriceProvider
        ↓
必须提供
get_stock_price(ticker)
```

---

### 六、Mock Provider

继续在：

```text
app/providers/financial.py
```

增加：

```python
class MockStockPriceProvider(StockPriceProvider):

    def __init__(self):
        self.mock_prices = {
            "AAPL": 200.0,
            "MSFT": 450.0,
            "GOOGL": 180.0,
        }

    def get_stock_price(self, ticker: str) -> dict:
        if ticker == "TEMP_ERROR":
            raise TransientToolError(
                "Temporary stock price provider error."
            )

        if ticker not in self.mock_prices:
            raise ValueError(
                f"Stock price not found for ticker: {ticker}"
            )

        return {
            "ticker": ticker,
            "price": self.mock_prices[ticker],
        }
```

这里有一个需要马上注意的地方：

`TransientToolError` 目前属于：

```text
app.tools.financial
```

而现在 Provider 不应该依赖 Tool。

所以我们需要把这个异常移动到一个更合适的位置。

---

### 七、异常也应该进行分层

我们现在已经开始出现一个架构问题：

```text
Provider
 ↓
TransientToolError
```

但这个异常却定义在：

```text
tools/financial.py
```

这反过来了。

所以 Lesson 9 正好把它调整。

创建：

```text
app/providers/exceptions.py
```

内容：

```python
class TransientProviderError(Exception):
    """Temporary provider failure that may succeed when retried."""
```

然后：

```text
Tool
 ↓
Provider
```

两层都不应该依赖对方的实现。

Provider 使用：

```python
TransientProviderError
```

Tool 再决定：

```text
Provider Error
 ↓
Tool Error
```

怎么映射。

---

### 八、修改 Mock Provider

因此最终：

```python
from abc import ABC, abstractmethod

from app.providers.exceptions import TransientProviderError


class StockPriceProvider(ABC):

    @abstractmethod
    def get_stock_price(self, ticker: str) -> dict:
        raise NotImplementedError


class MockStockPriceProvider(StockPriceProvider):

    def __init__(self):
        self.mock_prices = {
            "AAPL": 200.0,
            "MSFT": 450.0,
            "GOOGL": 180.0,
        }

    def get_stock_price(self, ticker: str) -> dict:
        if ticker == "TEMP_ERROR":
            raise TransientProviderError(
                "Temporary stock price provider error."
            )

        if ticker not in self.mock_prices:
            raise ValueError(
                f"Stock price not found for ticker: {ticker}"
            )

        return {
            "ticker": ticker,
            "price": self.mock_prices[ticker],
        }
```

---

### 九、修改 Tool

现在：

```text
app/tools/financial.py
```

不再拥有：

```python
mock_prices = {...}
```

而是：

```python
from app.providers.financial import MockStockPriceProvider
from app.providers.exceptions import TransientProviderError
```

然后：

```python
stock_price_provider = MockStockPriceProvider()
```

Tool：

```python
@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    try:
        return stock_price_provider.get_stock_price(ticker)

    except TransientProviderError as exc:
        raise TransientToolError(
            str(exc)
        ) from exc
```

这里的 `TransientToolError` 应该重新定义在 Tool 层。

所以：

```python
class TransientToolError(Exception):
    """Temporary tool failure that may succeed when retried."""
```

仍然可以留在：

```text
app/tools/financial.py
```

这样分层就变成：

```text
Provider
    ↓
TransientProviderError
    ↓
Tool
    ↓
TransientToolError
    ↓
Graph
    ↓
tool_retryable
```

---

### 十、这就是这一节真正要理解的 Error Boundary

现在我们已经有三层：

```text
Provider Layer
        │
        │ Provider Error
        ▼
Tool Layer
        │
        │ Tool Error
        ▼
Graph Layer
        │
        │ Graph State
        ▼
Agent Workflow
```

例如真实世界：

```text
Yahoo Finance
    ↓
HTTP timeout
    ↓
YahooFinanceProvider
    ↓
TransientProviderError
    ↓
get_stock_price
    ↓
TransientToolError
    ↓
get_stock_price_node
    ↓
tool_retryable = True
    ↓
Graph Retry
```

这个链条以后会非常重要。

---

### 十一、`get_company_info` 也做同样的 Provider Separation

Lesson 7 增加的：

```text
get_company_info
```

目前也直接持有：

```python
mock_companies
```

这一次也抽出来。

在：

```text
app/providers/financial.py
```

增加：

```python
class CompanyInfoProvider(ABC):

    @abstractmethod
    def get_company_info(self, ticker: str) -> dict:
        raise NotImplementedError


class MockCompanyInfoProvider(CompanyInfoProvider):

    def __init__(self):
        self.mock_companies = {
            "AAPL": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology",
            },
            "MSFT": {
                "ticker": "MSFT",
                "company_name": "Microsoft Corporation",
                "sector": "Technology",
            },
            "GOOGL": {
                "ticker": "GOOGL",
                "company_name": "Alphabet Inc.",
                "sector": "Communication Services",
            },
        }

    def get_company_info(self, ticker: str) -> dict:
        if ticker not in self.mock_companies:
            raise ValueError(
                f"Company information not found for ticker: {ticker}"
            )

        return self.mock_companies[ticker]
```

于是：

```text
get_company_info Tool
        ↓
CompanyInfoProvider
        ↓
MockCompanyInfoProvider
```

---

### 十二、Provider 和 Tool 的关系现在变成

```text
             Agent
               │
        ┌──────┴──────┐
        ▼             ▼
 get_stock_price  get_company_info
        │             │
        ▼             ▼
StockPriceProvider  CompanyInfoProvider
        │             │
        ▼             ▼
Mock Provider      Mock Provider
```

未来替换 Provider 时：

```text
MockStockPriceProvider
        ↓
YahooFinanceStockPriceProvider
```

Tool 的接口可以保持：

```text
get_stock_price(ticker)
```

不变。

这意味着：

> LLM 根本不需要知道数据来自哪里。

这正是我们希望实现的解耦。

---

### 十三、Lesson 9 的测试

这一节测试重点发生变化。

之前：

```text
Tool
 ↓
Mock Data
```

现在需要验证：

```text
Provider
 ↓
Tool
 ↓
LLM
```

但我们仍然不接真实 Provider。

---

#### Test 1：Provider

创建：

```text
tests/test_providers.py
```

测试：

```python
from app.providers.financial import (
    MockCompanyInfoProvider,
    MockStockPriceProvider,
)


def test_mock_stock_price_provider():
    provider = MockStockPriceProvider()

    result = provider.get_stock_price("AAPL")

    assert result == {
        "ticker": "AAPL",
        "price": 200.0,
    }


def test_mock_company_info_provider():
    provider = MockCompanyInfoProvider()

    result = provider.get_company_info("AAPL")

    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["sector"] == "Technology"
```

---

### 十四、Test 2：Provider Failure

继续测试：

```python
import pytest

from app.providers.exceptions import TransientProviderError
from app.providers.financial import MockStockPriceProvider


def test_mock_stock_price_provider_transient_failure():
    provider = MockStockPriceProvider()

    with pytest.raises(TransientProviderError):
        provider.get_stock_price("TEMP_ERROR")


def test_mock_stock_price_provider_invalid_ticker():
    provider = MockStockPriceProvider()

    with pytest.raises(
        ValueError,
        match="Stock price not found",
    ):
        provider.get_stock_price("INVALID")
```

这样我们明确验证：

```text
Provider Failure
```

而不是：

```text
Tool Failure
```

---

### 十五、Test 3：Tool 仍然正常工作

原来的：

```text
tests/test_financial_tool.py
```

应该继续全部通过。

这非常重要。

因为我们的重构目标是：

```text
内部实现改变
        ↓
外部 Tool Contract 不改变
```

例如：

```python
get_stock_price.invoke(
    {"ticker": "AAPL"}
)
```

仍然应该得到：

```python
{
    "ticker": "AAPL",
    "price": 200.0
}
```

---

### 十六、Test 4：Tool Failure Mapping

Lesson 6 已经验证了：

```text
TEMP_ERROR
 ↓
TransientToolError
 ↓
tool_retryable = True
```

现在我们需要确认 Provider Error 被 Tool 正确转换。

原来的：

```text
tests/test_tool_result_to_state.py
```

继续验证：

```python
def test_retryable_tool_failure():
    state = {
        "ticker": "TEMP_ERROR",
        "tool_retry_count": 0,
    }

    result = get_stock_price_node(state)

    assert result["tool_error"] is not None
    assert result["tool_retryable"] is True
    assert result["tool_retry_count"] == 1
```

如果这里仍然通过，说明：

```text
Provider
 ↓
Provider Error
 ↓
Tool
 ↓
Tool Error
 ↓
Graph State
```

整个错误链没有被这次抽象破坏。

---

### 十七、Lesson 9 最重要的 Acceptance Criteria

这一次不是看“有没有多一个类”。

而是看**边界是否建立成功**：

#### Provider

- [ ] `StockPriceProvider` 定义 Contract
- [ ] `CompanyInfoProvider` 定义 Contract
- [ ] `MockStockPriceProvider` 实现 Contract
- [ ] `MockCompanyInfoProvider` 实现 Contract
- [ ] Mock 数据从 Tool 中移出

#### Tool

- [ ] `get_stock_price` 通过 Provider 获取数据
- [ ] `get_company_info` 通过 Provider 获取数据
- [ ] Tool 对外接口没有改变
- [ ] Tool 不再直接持有 Mock 数据

#### Error Boundary

- [ ] Provider 使用 `TransientProviderError`
- [ ] Tool 使用 `TransientToolError`
- [ ] Provider Error 可以转换为 Tool Error
- [ ] Graph 仍然能够识别 retryable Tool Failure

#### Regression

- [ ] Lesson 1～8 测试全部通过
- [ ] Tool Calling Loop 不受影响
- [ ] Multiple Tools 不受影响

---

### 十八、一个暂时不要做的事情

这节**不要创建**：

```text
YahooFinanceProvider
AlphaVantageProvider
PolygonProvider
```

也不要安装金融数据 SDK。

我们现在只是建立：

```text
Tool
 ↓
Provider Interface
 ↓
Mock Provider
```

下一步如果真的接 Provider，才会进入：

```text
Real Provider
 ↓
Network
 ↓
Authentication
 ↓
Timeout
 ↓
Rate Limit
 ↓
Provider-specific Error
```

那是另外一个问题。

---

### 十九、Lesson 9 完成后的架构

完成后，我们的 Phase 3 架构会第一次变成：

```text
                         ┌─────────────────────┐
                         │        LLM          │
                         └──────────┬──────────┘
                                    │
                              Tool Call
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            get_stock_price                 get_company_info
                    │                               │
                    ▼                               ▼
          StockPriceProvider                CompanyInfoProvider
                    │                               │
                    ▼                               ▼
         MockStockPriceProvider            MockCompanyInfoProvider
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                              Tool Result
                                    │
                                    ▼
                                   LLM
```

这时候我们才真正开始拥有一个合理的 Agent Tool Architecture。

---


## Lesson 10：End-to-End Tool Integration

### 一、这一节解决什么问题？

到 Lesson 9，我们已经分别验证了：

```text
LLM
 ↓
Tool Calling
```

```text
Tool
 ↓
Provider
```

```text
Provider
 ↓
Tool Result
 ↓
Graph State
```

```text
LLM
 ↓
Tool
 ↓
Tool Result
 ↓
LLM
```

但这些能力目前还是分散验证的。

Lesson 10 要把它们组合成：

```text
                    ┌──────────────────────┐
                    │         LLM          │
                    └──────────┬───────────┘
                               │
                         Tool Call
                               │
                    ┌──────────┴───────────┐
                    │                      │
                    ▼                      ▼
            get_stock_price        get_company_info
                    │                      │
                    ▼                      ▼
             Stock Provider         Company Provider
                    │                      │
                    ▼                      ▼
               Mock Data              Mock Data
                    │                      │
                    └──────────┬───────────┘
                               │
                          Tool Result
                               │
                               ▼
                              LLM
                               │
                               ▼
                         Final Answer
```

也就是说：

> **Lesson 10 是 Phase 3 的集成验证课，而不是继续增加一个新机制。**

---

### 二、为什么现在做 End-to-End Integration？

这是非常重要的工程习惯。

我们前面大量使用的是：

```text
Unit Test
```

例如：

```text
test_financial_tool.py
test_providers.py
test_tool_result_to_state.py
test_tool_failure_routing.py
```

这些测试分别证明局部正确。

但局部正确并不意味着系统正确。

例如：

```text
Provider 正确
Tool 正确
LLM Tool Calling 正确
Graph Loop 正确
```

理论上都通过了，但是如果：

```text
Tool → Provider
```

连接错了，整个系统仍然失败。

因此 Lesson 10 开始验证：

```text
Integration
```

---

### 三、Lesson 10 的第一个目标：建立正式的 Tool Runtime

目前 Lesson 8 已经有：

```text
app/graph/tool_loop.py
```

它里面有：

```python
tools = [
    get_stock_price,
    get_company_info,
]
```

以及：

```python
tool_node = ToolNode(tools)
```

这已经是一个基本的 Tool Runtime。

本节我们不再创建第二套 Tool Runtime。

而是把这个概念明确下来：

```text
Tool Registry
        ↓
ToolNode
        ↓
Tool Execution
```

---

### 四、创建 Tool Registry

建议新增：

```text
app/tools/registry.py
```

内容：

```python
from app.tools.financial import (
    get_company_info,
    get_stock_price,
)


TOOLS = [
    get_stock_price,
    get_company_info,
]
```

然后修改：

```text
app/graph/tool_loop.py
```

不再自己定义：

```python
tools = [
    get_stock_price,
    get_company_info,
]
```

而是：

```python
from app.tools.registry import TOOLS
```

然后：

```python
llm_with_tools = get_llm().bind_tools(TOOLS)

tool_node = ToolNode(TOOLS)
```

这样我们第一次建立：

```text
                    ┌── get_stock_price
TOOLS ──────────────┤
                    └── get_company_info
```

---

### 五、为什么需要 Registry？

现在只有两个 Tool，看起来：

```python
TOOLS = [...]
```

似乎没有必要。

但最终项目会有：

```text
get_stock_price
get_company_info
get_financial_statements
get_market_data
get_news
get_industry_data
...
```

如果每个 Graph 都自己写：

```python
[
    get_stock_price,
    get_company_info,
    ...
]
```

很快就会出现：

```text
Graph A
    ↓
Tool List A

Graph B
    ↓
Tool List B

Agent C
    ↓
Tool List C
```

然后不同 Agent 使用的 Tool 集合可能悄悄发生偏差。

Registry 的作用就是提供一个明确的：

> **Tool Registration Boundary**

---

### 六、注意：Registry 不是 Provider Registry

这一点非常重要。

现在有两个不同概念：

#### Tool Registry

```text
Agent 能调用什么？
```

例如：

```text
get_stock_price
get_company_info
```

#### Provider

```text
Tool 从哪里获取数据？
```

例如：

```text
MockStockPriceProvider
YahooFinanceStockPriceProvider
```

不要混淆：

```text
Tool Registry ≠ Provider Registry
```

这是两个不同层次。

---

### 七、第二个目标：验证完整 Tool Loop

现在我们重新验证：

```text
Human
 ↓
LLM
 ↓
Tool Call
 ↓
ToolNode
 ↓
Tool
 ↓
Provider
 ↓
Tool Result
 ↓
LLM
 ↓
Final Answer
```

这一次，真正的区别在于：

```text
Tool
 ↓
Provider
```

已经不再是：

```text
Tool
 ↓
Mock Dictionary
```

而是：

```text
Tool
 ↓
Provider Interface
 ↓
Mock Provider
 ↓
Mock Data
```

所以这是第一次完整验证：

> **Agent 层完全不关心数据 Provider 的实现。**

---

### 八、增加 Integration Test

创建：

```text
tests/test_tool_integration.py
```

第一项：

```python
from langchain_core.messages import HumanMessage

from app.graph.tool_loop import build_tool_loop_graph


def test_stock_price_end_to_end():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What is the current stock price "
                        "of AAPL?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    assert messages[0].type == "human"

    tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

    assert tool_messages

    tool_message = tool_messages[0]

    assert "AAPL" in tool_message.content
    assert "200.0" in tool_message.content

    final_message = messages[-1]

    assert final_message.type == "ai"
    assert not final_message.tool_calls
```

这里第一次验证：

```text
LLM
 ↓
Tool Call
 ↓
ToolNode
 ↓
Tool
 ↓
Provider
 ↓
ToolMessage
 ↓
LLM
```

---

### 九、第二个 Integration Test

验证公司信息：

```python
def test_company_info_end_to_end():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What company is AAPL and "
                        "what sector does it belong to?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

    assert tool_messages

    tool_message = tool_messages[0]

    assert "Apple Inc." in tool_message.content
    assert "Technology" in tool_message.content

    final_message = messages[-1]

    assert final_message.type == "ai"
    assert not final_message.tool_calls
```

---

### 十、第三个 Integration Test：两个 Tool

这是本节最有价值的测试。

```python
def test_multiple_tools_end_to_end():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What is the current stock price of AAPL, "
                        "and what sector does the company belong to?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    tool_names = []

    for message in messages:
        if message.type != "ai":
            continue

        for tool_call in message.tool_calls:
            tool_names.append(tool_call["name"])

    assert "get_stock_price" in tool_names
    assert "get_company_info" in tool_names

    tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

    assert tool_messages

    final_message = messages[-1]

    assert final_message.type == "ai"
    assert not final_message.tool_calls
```

这里不要检查：

```text
get_stock_price 一定先执行
```

也不要检查：

```text
get_company_info 一定第二个执行
```

因为 Tool Call 顺序是模型行为的一部分，不应该在这个测试里人为绑定。

我们只要求：

```text
两个必要 Tool 都被使用
        ↓
Tool Result 都进入消息历史
        ↓
最终 LLM 结束 Loop
```

---

### 十一、一个很重要的测试边界

你可能会注意到：

```python
assert "200.0" in tool_message.content
```

这里我们测试的是 `ToolMessage` 的内容，而不是：

```python
assert final_message.content == "..."
```

这是故意的。

最终 LLM 的自然语言可能是：

```text
AAPL is currently trading at $200.
```

也可能：

```text
The current price of Apple is $200.0.
```

甚至：

```text
According to the latest available data, AAPL is priced at 200 dollars.
```

如果我们把自然语言答案写死：

```python
assert final_message.content == "..."
```

测试就会变得非常脆弱。

所以当前阶段：

```text
Tool Result
    ↓
确定性验证

Final Answer
    ↓
只验证结构和是否结束
```

这是比较合理的。

---

### 十二、Lesson 10 暂时不把它接入主 Investment Graph

这点继续保持。

现在我们有：

```text
app/graph/graph.py
```

主 Investment Graph。

以及：

```text
app/graph/tool_loop.py
```

Tool Calling Loop。

本节**不要把 Tool Loop 整个塞进主 Graph**。

因为 Phase 3 的目标是：

```text
理解 Tool Calling
```

而不是：

```text
把所有代码提前整合成最终 Agent
```

真正把 Tool Loop 接入 Research Agent，是 Phase 4/5 的事情。

---

### 十三、Lesson 10 的架构意义

完成之后，我们会得到三个清晰边界：

```text
┌─────────────────────────────────┐
│             Agent               │
│                                 │
│       LLM + Tool Calling        │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│              Tool               │
│                                 │
│ get_stock_price                 │
│ get_company_info                │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│            Provider             │
│                                 │
│ StockPriceProvider               │
│ CompanyInfoProvider              │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│          Data Source            │
│                                 │
│       Mock Provider              │
└─────────────────────────────────┘
```

未来真正接 API 时，只替换最下面：

```text
MockStockPriceProvider
        ↓
YahooFinanceStockPriceProvider
```

而：

```text
LLM
Tool
Graph
Tool Calling Loop
```

理论上都不需要改变。

这就是本 Phase 3 最终希望建立的核心架构思想。

---

### 十四、Lesson 10 测试顺序

先：

```bash
python -m pytest tests/test_tool_integration.py -v
```

然后：

```bash
python -m pytest tests -v
```

如果全部通过，Lesson 10 完成。

---

### Lesson 10 Acceptance Criteria

- [ ] 建立 `app/tools/registry.py`
- [ ] Tool Registry 包含当前两个 Tool
- [ ] Tool Loop 使用统一 Registry
- [ ] LLM 使用 Registry 注册 Tools
- [ ] `ToolNode` 使用 Registry 执行 Tools
- [ ] Tool → Provider → Mock Provider 链路正常
- [ ] Stock Price End-to-End 测试通过
- [ ] Company Info End-to-End 测试通过
- [ ] Multiple Tools End-to-End 测试通过
- [ ] 最终 AI Message 没有 `tool_calls`
- [ ] 所有 Phase 3 之前测试继续通过
- [ ] 不修改主 Investment Graph 的架构

---