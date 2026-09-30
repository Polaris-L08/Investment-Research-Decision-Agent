# Phase 6 — Valuation

## Lesson 1: Valuation Domain Model

### Goal

建立第一个真正独立的 **Valuation Domain Model**。

本课只解决：

> “一个估值结果在系统中应该长什么样？”

暂时不解决：

* 怎么计算
* 怎么调用 LLM
* 怎么调用金融 API
* 怎么产生 Target Price
* 怎么计算 Expected Upside
* 怎么进入 Supervisor
* 怎么进行 Risk Analysis
* 怎么做 Investment Decision

---

### 2. Why Now

Phase 5 已经建立了：

```text
Research
    ↓
ResearchState
```

Phase 6 要建立：

```text
Research
    ↓
Valuation
    ↓
ValuationResult
```

因此第一步不能直接写：

```python
target_price = earnings * multiple
```

而应该首先定义一个稳定的领域对象：

```text
Valuation Method
       +
Valuation Inputs
       +
Valuation Assumptions
       +
Valuation Result
       +
Metadata
```

这样后面的 Lesson 2、Lesson 3、Lesson 4 才有明确的数据边界。

---

### 3. Graph Topology

**Lesson 1 不新增 LangGraph Graph。**

这是有意的，而不是遗漏。

当前拓扑保持：

```text
Phase 5

Planner
   ↓
Supervisor
   ↓
Research Agents
   ↓
ResearchState
```

Lesson 1 新增的是 Domain Model：

```text
ResearchState
     │
     │  （后续 Lesson 3 才正式接入）
     ▼
Valuation Domain
     │
     ├── ValuationMethod
     ├── ValuationInputs
     ├── ValuationAssumptions
     ├── ValuationMetadata
     └── ValuationResult
```

所以本课不存在：

```text
START → Valuation Agent → END
```

因为目前还没有 Valuation Agent。

这符合我们的 Phase 6 分层：

```text
Lesson 1
Domain Model
    ↓
Lesson 2
Deterministic Valuation Calculation
    ↓
Lesson 3
LangGraph Valuation Agent Integration
    ↓
Lesson 4
Target Price + Expected Upside
```

---

### 4. Exact Files

新增：

```text
app/
└── valuation/
    ├── __init__.py
    └── models.py

tests/
└── test_valuation_models.py
```

Phase 5 的文件不修改。

---

### 5. Complete Code

#### `app/valuation/models.py`

```python
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ValuationMethod(str, Enum):
    """Supported valuation methodologies."""

    PE = "P/E"


class ValuationInputs(BaseModel):
    """Numerical inputs consumed by a valuation model."""

    model_config = ConfigDict(extra="forbid")

    earnings_per_share: float = Field(
        gt=0,
        description="Earnings per share used by the valuation model.",
    )


class ValuationAssumptions(BaseModel):
    """Explicit assumptions used to determine the valuation multiple."""

    model_config = ConfigDict(extra="forbid")

    multiple: float = Field(
        gt=0,
        description="Valuation multiple assumed by the analyst.",
    )
    rationale: str = Field(
        min_length=1,
        description="Reason for selecting the valuation multiple.",
    )


class ValuationMetadata(BaseModel):
    """Metadata describing how a valuation result was produced."""

    model_config = ConfigDict(extra="forbid")

    currency: str = Field(
        min_length=1,
        description="Currency of the per-share valuation result.",
    )
    model_version: str = Field(
        min_length=1,
        description="Version identifier of the valuation model.",
    )


class ValuationResult(BaseModel):
    """Structured output of a valuation model."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        description="Stock ticker symbol.",
    )
    method: ValuationMethod = Field(
        description="Valuation methodology used.",
    )
    inputs: ValuationInputs = Field(
        description="Numerical inputs used by the model.",
    )
    assumptions: ValuationAssumptions = Field(
        description="Explicit assumptions used by the model.",
    )
    implied_value_per_share: float = Field(
        gt=0,
        description="Implied per-share value produced by the model.",
    )
    metadata: ValuationMetadata = Field(
        description="Metadata describing the valuation result.",
    )
```

这里有一个刻意的设计：

```python
ValuationInputs
```

保存模型真正使用的数值输入：

```text
EPS
```

而：

```python
ValuationAssumptions
```

保存估值假设：

```text
P/E Multiple
Rationale
```

因此不是简单地把所有东西塞进一个 `dict[str, float]`。

---

#### `app/valuation/__init__.py`

```python
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)

__all__ = [
    "ValuationAssumptions",
    "ValuationInputs",
    "ValuationMetadata",
    "ValuationMethod",
    "ValuationResult",
]
```

这样后续可以直接：

```python
from app.valuation import ValuationResult
```

而不是让业务代码依赖具体模块路径。

---

### 6. Complete Tests

#### `tests/test_valuation_models.py`

```python
import pytest
from pydantic import ValidationError

from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


def make_inputs() -> ValuationInputs:
    return ValuationInputs(
        earnings_per_share=10.0,
    )


def make_assumptions() -> ValuationAssumptions:
    return ValuationAssumptions(
        multiple=20.0,
        rationale="Selected as the assumed earnings multiple for the model.",
    )


def make_metadata() -> ValuationMetadata:
    return ValuationMetadata(
        currency="USD",
        model_version="pe-v1",
    )


def test_valuation_method_contains_supported_method():
    assert ValuationMethod.PE.value == "P/E"


def test_valuation_inputs_are_structured():
    inputs = make_inputs()

    assert inputs.earnings_per_share == 10.0


def test_valuation_assumptions_are_explicit():
    assumptions = make_assumptions()

    assert assumptions.multiple == 20.0
    assert assumptions.rationale


def test_valuation_result_contains_method_inputs_assumptions_result_and_metadata():
    result = ValuationResult(
        ticker="AAPL",
        method=ValuationMethod.PE,
        inputs=make_inputs(),
        assumptions=make_assumptions(),
        implied_value_per_share=200.0,
        metadata=make_metadata(),
    )

    assert result.ticker == "AAPL"
    assert result.method is ValuationMethod.PE
    assert result.inputs.earnings_per_share == 10.0
    assert result.assumptions.multiple == 20.0
    assert result.implied_value_per_share == 200.0
    assert result.metadata.currency == "USD"


@pytest.mark.parametrize(
    "field,value",
    [
        ("earnings_per_share", 0),
        ("earnings_per_share", -1),
    ],
)
def test_valuation_inputs_reject_non_positive_values(field, value):
    values = {
        "earnings_per_share": 10.0,
    }
    values[field] = value

    with pytest.raises(ValidationError):
        ValuationInputs(**values)


def test_valuation_assumptions_reject_non_positive_multiple():
    with pytest.raises(ValidationError):
        ValuationAssumptions(
            multiple=0,
            rationale="Invalid assumption.",
        )


def test_valuation_assumptions_reject_empty_rationale():
    with pytest.raises(ValidationError):
        ValuationAssumptions(
            multiple=20.0,
            rationale="",
        )


def test_valuation_result_rejects_non_positive_implied_value():
    with pytest.raises(ValidationError):
        ValuationResult(
            ticker="AAPL",
            method=ValuationMethod.PE,
            inputs=make_inputs(),
            assumptions=make_assumptions(),
            implied_value_per_share=0,
            metadata=make_metadata(),
        )


def test_valuation_result_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ValuationResult(
            ticker="AAPL",
            method=ValuationMethod.PE,
            inputs=make_inputs(),
            assumptions=make_assumptions(),
            implied_value_per_share=200.0,
            metadata=make_metadata(),
            unexpected_field="not allowed",
        )
```

---

### 7. Test Result

新增加的 Lesson 1 测试：

```bash
pytest -q tests/test_valuation_models.py
```

结果：

```text
10 passed
```

也就是说 Lesson 1 当前已经验证了：

* `ValuationMethod` 存在
* `ValuationInputs` 是结构化模型
* `ValuationAssumptions` 是结构化模型
* `ValuationResult` 能组合完整估值结果
* EPS 必须 > 0
* Multiple 必须 > 0
* Rationale 不能为空
* Implied Value 必须 > 0
* 未知字段会被拒绝

另外：

```bash
python -m compileall -q app tests
```

通过。

---

### 8. 为什么现在只支持 P/E？

这里需要特别强调。

不是最终系统只支持 P/E。

最终系统的 Valuation Layer 可以逐步支持：

```text
P/E
Forward P/E
EV/EBITDA
PEG
DCF
FCF Yield
Peer Comparison
Historical Valuation
...
```

但是 Phase 6 Lesson 1 不应该一次性建立所有模型。

当前结构：

```python
class ValuationMethod(str, Enum):
    PE = "P/E"
```

是**第一阶段的最小稳定领域边界**。

Lesson 2 再真正实现：

```text
EPS × P/E Multiple
       ↓
Implied Value
```

之后如果扩展 EV/EBITDA：

```python
class ValuationMethod(str, Enum):
    PE = "P/E"
    EV_EBITDA = "EV/EBITDA"
```

再增加对应输入模型或模型实现。

这比 Lesson 1 就建立一个庞大的：

```python
Dict[str, Any]
```

更容易演进，也更容易测试。

---

### 9. 一个重要的架构决定：为什么没有 `target_price`

现在：

```python
ValuationResult
    ├── method
    ├── inputs
    ├── assumptions
    ├── implied_value_per_share
    └── metadata
```

而没有：

```python
target_price
current_price
expected_upside
```

这是刻意的。

因为 roadmap 明确把：

```text
Target Price
Expected Upside
```

放在 **Lesson 4**。

因此现在：

```text
Lesson 1
        ↓
Valuation Result

Lesson 2
        ↓
Deterministic Calculation

Lesson 3
        ↓
ResearchState → Valuation Agent → ValuationResult

Lesson 4
        ↓
ValuationResult
        +
Current Price
        ↓
Target Price
        ↓
Expected Upside
```

这样每一个 Lesson 都有清晰的责任边界。

---

### 10. Current Phase 6 State

现在项目的架构状态可以准确描述为：

```text
                         Phase 5
                            │
                            ▼
                     ResearchState
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
         Company         Financial       Market
         Research        Research        Research
                            │
                            ▼
                    Industry / Macro
                            │
                            ▼
                    ─────────────────
                       Phase 6
                    ─────────────────
                            │
                            ▼
                  Valuation Domain Model
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         Valuation       Valuation     Valuation
          Method          Inputs      Assumptions
                            │
                            ▼
                    Valuation Result
                            │
                            ▼
                         下一课
                    Deterministic Model
```

目前 **还没有**：

```text
Valuation Agent
Target Price
Expected Upside
Risk
Investment Decision
Recommendation
Report
Checkpoint
HITL
Memory
FastAPI
```

这完全符合当前 Phase 6 的边界。

---

### 11. Acceptance Criteria

| Criteria                       | Status                    |
|--------------------------------|---------------------------|
| Valuation schema exists        | ✅                        |
| Valuation method structured    | ✅                        |
| Valuation inputs explicit      | ✅                        |
| Valuation assumptions explicit | ✅                        |
| Valuation result structured    | ✅                        |
| Metadata explicit              | ✅                        |
| Invalid values rejected        | ✅                        |
| Unknown fields rejected        | ✅                        |
| Calculation implemented        | ❌ intentionally deferred |
| LangGraph Agent integration    | ❌ Lesson 3               |
| Target Price                   | ❌ Lesson 4               |
| Expected Upside                | ❌ Lesson 4               |

因此 **Lesson 1 达成**。

---

### 12. 当前没有修改 Phase 5

这一点非常重要。

没有为了接入估值而修改：

```text
ResearchState
ResearchSupervisor
ResearchOrchestrator
ResearchFanout
ResearchParallel
ResearchPlanner
ResearchRouter
```

因为 Lesson 3 才是：

```text
ResearchState
      ↓
Valuation Agent
      ↓
ValuationResult
```

现在提前修改 `ResearchState`，反而会把 Lesson 1、Lesson 3 的边界混在一起。

---


## Lesson 2: Valuation Calculation

### 1. Goal

建立第一个**确定性的估值计算模型**：

```text
Earnings Per Share
        ×
Assumed P/E Multiple
        ↓
Implied Value Per Share
```

即：

$$
\text{Implied Value Per Share}
=
\text{EPS}
\times
\text{P/E Multiple}
$$

例如：

```text
EPS = 10
P/E = 20

10 × 20 = 200
```

这里的 `200` 是**估值模型产生的 implied value**，还不是 Lesson 4 的 `Target Price`。

---

### 2. 本课新增文件

```text
app/
└── valuation/
    ├── __init__.py
    ├── models.py
    └── calculations.py

tests/
├── test_valuation_models.py
└── test_valuation_calculations.py
```

其中：

```text
models.py
```

来自 Lesson 1，本课没有改变其领域模型设计。

新增：

```text
calculations.py
test_valuation_calculations.py
```

---

### 3. Graph Topology

本课**仍然不修改 LangGraph topology**。

当前：

```text
Research Planner
       ↓
Research Plan
       ↓
Supervisor
       ↓
Research Agents
       ↓
ResearchState
```

Valuation 当前仍然是独立的 domain/calculation layer：

```text
Research Results
       │
       │  Lesson 3 才正式接入 Graph
       ▼
ValuationInputs
       +
ValuationAssumptions
       │
       ▼
P/E Calculation
       │
       ▼
Implied Value Per Share
```

所以现在没有：

```text
START → Valuation Agent → END
```

也没有修改 Supervisor。

这正是 Lesson 2 应有的边界。

---

### 4. Complete Code

#### `app/valuation/calculations.py`

```python
from app.valuation.models import ValuationAssumptions, ValuationInputs


def calculate_pe_implied_value(
    inputs: ValuationInputs,
    assumptions: ValuationAssumptions,
) -> float:
    """Calculate implied value per share using the P/E valuation method.

    Formula:
        implied value per share = earnings per share × assumed P/E multiple

    The function is intentionally deterministic and has no LLM, provider,
    network, or LangGraph dependency.
    """

    return inputs.earnings_per_share * assumptions.multiple
```

这里最重要的是这个设计：

```python
def calculate_pe_implied_value(
    inputs: ValuationInputs,
    assumptions: ValuationAssumptions,
) -> float:
```

它不是：

```python
def calculate_pe_implied_value(data: dict) -> ...
```

也不是：

```python
def calculate_pe_implied_value(llm_output: str) -> ...
```

而是直接消费 Lesson 1 定义好的结构化领域对象。

---

### 5. Complete Calculation Tests

#### `tests/test_valuation_calculations.py`

```python
import pytest

from app.valuation.calculations import calculate_pe_implied_value
from app.valuation.models import ValuationAssumptions, ValuationInputs


def make_inputs(eps: float) -> ValuationInputs:
    return ValuationInputs(earnings_per_share=eps)


def make_assumptions(multiple: float) -> ValuationAssumptions:
    return ValuationAssumptions(
        multiple=multiple,
        rationale="Test valuation multiple.",
    )


def test_calculate_pe_implied_value_with_known_inputs():
    result = calculate_pe_implied_value(
        make_inputs(10.0),
        make_assumptions(20.0),
    )

    assert result == 200.0


def test_calculate_pe_implied_value_preserves_decimal_result():
    result = calculate_pe_implied_value(
        make_inputs(7.5),
        make_assumptions(18.0),
    )

    assert result == 135.0


@pytest.mark.parametrize(
    "eps,multiple,expected",
    [
        (1.0, 10.0, 10.0),
        (12.5, 8.0, 100.0),
        (25.25, 12.0, 303.0),
    ],
)
def test_calculate_pe_implied_value_matches_formula(eps, multiple, expected):
    result = calculate_pe_implied_value(
        make_inputs(eps),
        make_assumptions(multiple),
    )

    assert result == expected
```

---

### 6. `app/valuation/__init__.py`

现在导出计算函数：

```python
from app.valuation.calculations import calculate_pe_implied_value
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)

__all__ = [
    "ValuationAssumptions",
    "ValuationInputs",
    "ValuationMetadata",
    "ValuationMethod",
    "ValuationResult",
    "calculate_pe_implied_value",
]
```

因此后续业务代码可以直接：

```python
from app.valuation import calculate_pe_implied_value
```

---

### 7. 为什么计算函数不返回 `ValuationResult`

这是本课一个重要的架构决定。

目前我们把：

```text
Domain Model
```

和：

```text
Calculation
```

分开。

计算函数负责：

```text
EPS
+
Multiple
↓
Implied Value
```

而 `ValuationResult` 还包含：

```text
Ticker
Method
Inputs
Assumptions
Implied Value
Metadata
```

例如：

```text
ValuationResult
├── ticker
├── method
├── inputs
├── assumptions
├── implied_value_per_share
└── metadata
```

其中：

```text
ticker
currency
model_version
```

并不是数学计算本身需要的变量。

因此当前设计：

```text
                ┌─────────────────────┐
                │ ValuationInputs     │
                │ ValuationAssumptions│
                └──────────┬──────────┘
                           │
                           ▼
                  calculate_pe_...
                           │
                           ▼
                 implied_value_per_share
```

而未来 Lesson 3 再由 Agent / Node 负责把它组织成：

```text
ValuationResult
```

这使计算核心保持纯净、可测试、可复用。

---

### 8. LLM 不参与数学计算

这一点对最终工业级系统非常重要。

我们现在明确禁止这样的流程：

```text
Research
   ↓
LLM
   ↓
"根据我的判断，目标价值约为 $200"
```

而采用：

```text
Research
   ↓
Structured Inputs
   ↓
Deterministic Valuation Model
   ↓
Numerical Result
```

LLM 将来可以负责：

```text
解释研究结果
解释假设
生成 rationale
选择/协调模型
```

但核心数学计算不依赖 LLM。

这也为 Phase 14 Evaluation 留出了非常清晰的 deterministic evaluation surface。

---

### 9. Test Result

本次运行：

```bash
pytest -q tests/test_valuation_models.py tests/test_valuation_calculations.py
```

结果：

```text
15 passed
```

其中：

```text
Lesson 1
10 tests
↓
10 passed

Lesson 2
5 tests
↓
5 passed
```

另外：

```bash
python -m compileall -q app tests
```

也通过。

---

### 10. Boundary Check

本课完成后，当前 `app/valuation` 中没有：

```text
target_price
expected_upside
LangGraph
LLM
Financial Provider
Risk
Investment Decision
Recommendation
```

也就是说没有发生 Phase 6 范围蔓延。

当前准确状态：

```text
Phase 6
│
├── Lesson 1 ✅
│   └── Valuation Domain Model
│
├── Lesson 2 ✅
│   └── Deterministic P/E Calculation
│
├── Lesson 3 ⏳
│   └── Valuation Agent Integration
│
└── Lesson 4 ⏳
    └── Target Price + Expected Upside
```

---

### 11. Lesson 2 Acceptance Criteria

| 要求                        | 状态        |
|-----------------------------|-------------|
| 第一个估值模型实现          | ✅          |
| 使用结构化输入              | ✅          |
| 计算确定性                  | ✅          |
| 已知输入得到已知结果        | ✅          |
| Unit Test                   | ✅          |
| Assumptions 显式存在        | ✅          |
| 不依赖 LLM 进行数学计算     | ✅          |
| 不依赖真实金融 API          | ✅          |
| LangGraph Agent Integration | ⏳ Lesson 3 |
| Target Price                | ⏳ Lesson 4 |
| Expected Upside             | ⏳ Lesson 4 |
| Risk Analysis               | ⏳ Phase 7  |

因此：

**Phase 6 — Lesson 2 达成。**

---

### 12. 下一步：Lesson 3

下一课才开始把目前独立存在的：

```text
ResearchState
      ↓
Valuation Domain Model
      ↓
P/E Calculation
```

真正接入 LangGraph。

目标拓扑将变成：

```text
Research Results
       ↓
Valuation Agent
       ↓
Valuation Inputs
       +
Valuation Assumptions
       ↓
Deterministic P/E Calculation
       ↓
ValuationResult
       ↓
State
```

这里会第一次回答 Phase 6 的核心集成问题：

> **Valuation 如何成为现有 Research/Supervisor 架构中的一个真正节点，而不是一个孤立的 Python demo？**

但 `Target Price` 和 `Expected Upside` 仍然留到 **Lesson 4**。


## Lesson 3：Valuation Agent Integration

Lesson 2 已确认通过，现在正式完成 **Lesson 3：将 Valuation 接入 LangGraph**。

本课的核心不是增加新的估值模型，而是把：

```text
ValuationInputs
        +
ValuationAssumptions
        ↓
P/E Calculation
        ↓
ValuationResult
```

真正放入 LangGraph State/Node 体系。

---

### 1. 本课目标

完成：

```text
ResearchState
      ↓
Valuation Agent
      ↓
Deterministic P/E Calculation
      ↓
ValuationResult
      ↓
ResearchState
```

因此 Lesson 3 结束后，Valuation 不再只是：

```python
calculate_pe_implied_value(...)
```

而是一个真正可以被 LangGraph 调用的 Agent/Node。

---

### 2. 一个重要的架构决定

检查当前 Phase 5 源码后发现：

```python
FinancialResearchResult
```

目前只有：

```text
revenue
net_income
profit_margin
```

并没有：

```text
earnings_per_share
shares_outstanding
```

而当前 Financial Tool 也没有提供 EPS。

因此本课**没有擅自修改 Phase 5 Financial Research Agent**，更没有：

```text
net_income / 某个虚构 shares outstanding
```

来制造 EPS。

这很重要。

否则虽然表面上可以让 Valuation 自动运行，但实际上是在**伪造估值输入**。

所以本课采用：

```text
ValuationInputs
ValuationAssumptions
```

作为明确的上游 State 输入。

也就是说：

> Lesson 3 负责“Valuation 如何进入 LangGraph”，而不是偷偷解决“EPS 数据从哪里来”这个尚未定义的数据供应问题。

后续如果需要建立正式的 valuation input assembly/provider，会在适当阶段设计，而不是在本课越界。

---

### 3. Graph Topology

本课第一次建立 Valuation Graph。

```text
             START
               │
               ▼
       ┌─────────────────┐
       │ Valuation Agent │
       └────────┬────────┘
                │
                ▼
       Valuation Calculation
                │
                ▼
        ValuationResult
                │
                ▼
               END
```

从 State 角度：

```text
ResearchState
     │
     ├── ticker
     ├── company_research
     ├── financial_research
     ├── market_research
     ├── industry_macro_research
     │
     ├── valuation_inputs
     ├── valuation_assumptions
     │
     ▼
Valuation Agent
     │
     ▼
valuation_analysis
```

这里有一个非常重要的特点：

**Research State 中原有的研究结果不会被 Valuation Agent 覆盖。**

Valuation 只是增加自己的：

```text
valuation_analysis
valuation_error
```

---

### 4. State Design

`ResearchState` 新增：

```python
valuation_inputs: ValuationInputs | None
valuation_assumptions: ValuationAssumptions | None
valuation_analysis: ValuationResult | None
valuation_error: str
```

完整 State 仍然是：

```text
ResearchState
├── ticker
├── research_plan
├── next_research_area
│
├── company_research
├── financial_research
├── market_research
├── industry_macro_research
│
├── research_errors
│
├── valuation_inputs
├── valuation_assumptions
├── valuation_analysis
└── valuation_error
```

注意：

```text
valuation_analysis
```

是 Valuation 的**结果字段**。

而：

```text
valuation_inputs
valuation_assumptions
```

是 Valuation 的**输入字段**。

这与 Lesson 1 的 Domain Model 保持一致。

---

### 5. 新增文件

新增：

```text
app/agents/valuation.py
tests/test_valuation_agent.py
```

修改：

```text
app/agents/research_state.py
```

没有修改：

```text
Research Planner
Research Router
Research Supervisor
Research Orchestrator
Research Fan-out
Company Research
Financial Research
Market Research
Industry/Macro Research
```

---

### 6. Complete Code

#### `app/agents/valuation.py`

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.research_state import ResearchState
from app.valuation.calculations import calculate_pe_implied_value
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


class ValuationInputState(ResearchState, total=False):
    """Input boundary for the valuation graph."""

    valuation_inputs: ValuationInputs
    valuation_assumptions: ValuationAssumptions


class ValuationOutputState(ResearchState, total=False):
    """Output boundary for the valuation graph."""

    valuation_analysis: ValuationResult | None
    valuation_error: str


def valuation_agent(
    state: ResearchState,
) -> ResearchState:
    """Run the deterministic valuation model from shared research state."""

    ticker = state.get("ticker")
    inputs = state.get("valuation_inputs")
    assumptions = state.get("valuation_assumptions")

    if not ticker:
        return {
            "valuation_analysis": None,
            "valuation_error": "Ticker is required for valuation.",
        }

    if inputs is None:
        return {
            "valuation_analysis": None,
            "valuation_error": "Valuation inputs are required.",
        }

    if assumptions is None:
        return {
            "valuation_analysis": None,
            "valuation_error": "Valuation assumptions are required.",
        }

    try:
        implied_value = calculate_pe_implied_value(
            inputs,
            assumptions,
        )

        result = ValuationResult(
            ticker=ticker,
            method=ValuationMethod.PE,
            inputs=inputs,
            assumptions=assumptions,
            implied_value_per_share=implied_value,
            metadata=ValuationMetadata(
                currency="USD",
                model_version="pe-v1",
            ),
        )

    except Exception as exc:
        return {
            "valuation_analysis": None,
            "valuation_error": str(exc),
        }

    return {
        "valuation_analysis": result,
        "valuation_error": "",
    }


def build_valuation_graph():
    """Build the Phase 6 valuation graph."""

    builder = StateGraph(
        ResearchState,
        input_schema=ValuationInputState,
        output_schema=ValuationOutputState,
    )

    builder.add_node(
        "valuation_agent",
        valuation_agent,
    )

    builder.add_edge(
        START,
        "valuation_agent",
    )

    builder.add_edge(
        "valuation_agent",
        END,
    )

    return builder.compile()


valuation_graph = build_valuation_graph()
```

---

### 7. `ResearchState`

完整修改后的：

#### `app/agents/research_state.py`

```python
from typing import TypedDict, Annotated

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
    ResearchArea,
    ResearchPlan,
)
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationResult,
)


def merge_research_errors(
    existing: dict[str, str] | None,
    new: dict[str, str] | None,
) -> dict[str, str]:
    """Merge research errors from parallel research agents."""
    merged = dict(existing or {})
    merged.update(new or {})
    return merged


class ResearchState(TypedDict, total=False):
    """Shared state boundary for multi-agent research orchestration."""

    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: Annotated[dict[str, str], merge_research_errors]

    # Phase 6 valuation state
    valuation_inputs: ValuationInputs | None
    valuation_assumptions: ValuationAssumptions | None
    valuation_analysis: ValuationResult | None
    valuation_error: str
```

这里的：

```python
# Phase 6 valuation state
```

是对 Phase 5 Shared State 的**扩展**，不是重构。

---

### 8. Complete Tests

#### `tests/test_valuation_agent.py`

```python
from app.agents.valuation import (
    build_valuation_graph,
    valuation_agent,
    valuation_graph,
)
from app.agents.research_state import ResearchState
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMethod,
)


def make_state() -> ResearchState:
    return {
        "ticker": "AAPL",
        "valuation_inputs": ValuationInputs(
            earnings_per_share=10.0,
        ),
        "valuation_assumptions": ValuationAssumptions(
            multiple=20.0,
            rationale="Use a 20x P/E multiple for this test valuation.",
        ),
        "company_research": None,
        "financial_research": None,
        "market_research": None,
        "industry_macro_research": None,
        "research_errors": {},
    }


def test_valuation_graph_is_compiled():
    assert valuation_graph is not None
    assert build_valuation_graph() is not None


def test_valuation_agent_returns_structured_valuation_result():
    result = valuation_agent(make_state())

    valuation = result["valuation_analysis"]

    assert valuation is not None
    assert valuation.ticker == "AAPL"
    assert valuation.method is ValuationMethod.PE
    assert valuation.inputs.earnings_per_share == 10.0
    assert valuation.assumptions.multiple == 20.0
    assert valuation.implied_value_per_share == 200.0
    assert result["valuation_error"] == ""


def test_valuation_agent_requires_inputs():
    state = make_state()
    state.pop("valuation_inputs")

    result = valuation_agent(state)

    assert result["valuation_analysis"] is None
    assert result["valuation_error"] == "Valuation inputs are required."


def test_valuation_agent_requires_assumptions():
    state = make_state()
    state.pop("valuation_assumptions")

    result = valuation_agent(state)

    assert result["valuation_analysis"] is None
    assert result["valuation_error"] == "Valuation assumptions are required."


def test_valuation_graph_preserves_research_state():
    state = make_state()
    state["research_errors"] = {"company": "test error"}

    result = valuation_graph.invoke(state)

    assert result["ticker"] == "AAPL"
    assert result["research_errors"] == {"company": "test error"}
    assert result["valuation_analysis"].implied_value_per_share == 200.0
    assert result["valuation_error"] == ""
```

---

### 9. 测试设计

本课实际验证四层。

#### ① Graph 编译

```text
valuation_graph
```

能够正常建立。

#### ② Agent 执行

验证：

```text
ValuationInputs
+
ValuationAssumptions
↓
Valuation Agent
↓
ValuationResult
```

#### ③ 输入缺失

没有：

```text
valuation_inputs
```

必须失败，而不是偷偷使用默认值。

同样：

```text
valuation_assumptions
```

缺失也必须失败。

这对最终工业级 Agent 很重要。

我们不希望系统出现：

```text
missing valuation assumption
        ↓
偷偷默认 20x
```

这种不可追踪行为。

#### ④ State 保留

验证：

```text
research_errors
ticker
```

等原有 State 内容仍然存在。

因此 Valuation Node 是：

```text
State augmentation
```

而不是：

```text
State replacement
```

---

### 10. 为什么没有把 Valuation 接到 Research Supervisor

这是本课另一个重要边界。

当前 Phase 5 Supervisor 的职责是：

```text
研究协调
```

即：

```text
Planner
   ↓
Research Supervisor
   ↓
Research Agent
```

而 Phase 6 的 Valuation 是研究完成之后的下一阶段：

```text
Research
   ↓
Valuation
```

因此现在不应该把：

```text
Valuation
```

塞进：

```text
ResearchArea
```

或者：

```text
ResearchPlan.research_areas
```

否则会造成概念污染：

```text
ResearchArea.COMPANY
ResearchArea.FINANCIAL
ResearchArea.MARKET
ResearchArea.INDUSTRY_MACRO
ResearchArea.VALUATION
```

然后让 Research Supervisor 同时负责：

```text
Research + Valuation
```

这会违反当前 Phase 5 的领域边界。

现在保持：

```text
Research Supervisor
        │
        ▼
Research Results
        │
        ▼
Valuation Graph
        │
        ▼
Valuation Result
```

更干净。

后续 Phase 5 的 Supervisor 在最终工业架构中当然还会演化成更强的跨阶段协调器，但那属于路线图后面的工作，而不是现在偷偷塞回 Phase 5。

---

### 11. 为什么 Valuation Agent 没有 LLM

这也是有意的。

当前：

```text
Valuation Agent
      ↓
calculate_pe_implied_value()
```

而不是：

```text
Valuation Agent
      ↓
LLM
      ↓
"我认为价值是 $200"
```

因为 Lesson 2 已经建立：

```text
Deterministic Calculation
```

Lesson 3 的职责只是把它接入 LangGraph。

因此：

```text
LangGraph
    = orchestration

Valuation Agent
    = domain execution boundary

Calculation
    = deterministic mathematics
```

三个层次被保留下来。

这对于后续：

```text
Phase 9 Persistence
Phase 10 HITL
Phase 12 Error Recovery
Phase 13 Observability
Phase 14 Evaluation
```

都会更有价值。

---

### 12. 本课与最终工业版本的关系

现在是第一版：

```text
ResearchState
   ↓
Valuation Agent
   ↓
P/E
   ↓
ValuationResult
```

最终会逐步演化成：

```text
Research Results
        ↓
Valuation Input Assembly
        ↓
Valuation Model Selection
        ↓
┌─────────────────────────┐
│ P/E                     │
│ Forward P/E             │
│ EV/EBITDA               │
│ DCF                     │
│ FCF Yield               │
│ Peer Comparison         │
│ Historical Valuation    │
└────────────┬────────────┘
             ↓
       Valuation Analysis
             ↓
       Target Price
             ↓
      Expected Upside
```

但这些不应该在 Lesson 3 一次性实现。

---

### 13. 当前 Lesson 3 状态

```text
Phase 6
│
├── Lesson 1
│   └── Valuation Domain Model        ✅
│
├── Lesson 2
│   └── Deterministic Calculation     ✅
│
├── Lesson 3
│   └── LangGraph Integration         ✅
│
└── Lesson 4
    └── Target Price + Upside         ⏳
```

Lesson 3 的最终数据流：

```text
ResearchState
     │
     │ valuation_inputs
     │ valuation_assumptions
     │
     ▼
┌──────────────────┐
│ Valuation Agent  │
└────────┬─────────┘
         │
         ▼
calculate_pe_implied_value()
         │
         ▼
┌──────────────────┐
│ ValuationResult  │
└────────┬─────────┘
         │
         ▼
ResearchState
```

---

### 14. Acceptance Criteria

| 要求                            | 状态        |
|---------------------------------|-------------|
| Valuation Agent 存在            | ✅          |
| LangGraph Graph 建立            | ✅          |
| ResearchState → Valuation Agent | ✅          |
| Valuation Agent 调用确定性模型  | ✅          |
| ValuationResult 写入 State      | ✅          |
| 原有 Research State 保留        | ✅          |
| 缺少 valuation inputs 时失败    | ✅          |
| 缺少 assumptions 时失败         | ✅          |
| LLM 不参与数学计算              | ✅          |
| Target Price                    | ⏳ Lesson 4 |
| Expected Upside                 | ⏳ Lesson 4 |
| Risk                            | ⏳ Phase 7  |
| Investment Decision             | ⏳ Phase 7  |

---

### 15. 关于测试

当前执行环境没有安装 `langgraph` / `langchain_core`，所以我无法在这个环境中实际执行新增的 LangGraph 测试；这是环境依赖问题，不应被误报为代码测试失败。

我已经完成：

```bash
python -m compileall -q app tests
```

语法检查通过。

你本地环境已经能够运行前两课测试，因此请在你的 `.venv` 中运行：

```bash
pytest -q
```

这一次尤其需要确认**全量测试**，因为我们第一次修改了共享的：

```text
app/agents/research_state.py
```

如果全量测试通过，则 Phase 5 + Phase 6 Lesson 1–3 的回归链条完整保持。

---

### 16. 下一课

测试通过后，进入最后一个 Phase 6 Lesson：

**Lesson 4 — Target Price + Expected Upside**

届时才加入：

```text
ValuationResult
       ↓
Target Price
       ↓
Current Price
       ↓
Expected Upside
```

核心公式严格确定为：

$$
Expected\ Upside
=
\frac{Target\ Price-Current\ Price}
{Current\ Price}
$$

不会让 LLM 自己计算。

Lesson 4 完成并通过计算测试后，Phase 6 才正式关闭，然后进入 **Phase 7 — Risk + Investment Decision**。

---


## Lesson 4：Target Price + Expected Upside

Lesson 3 的 Valuation Agent 已经接入 LangGraph。本课完成 Phase 6 最后一个功能点：

```text
Valuation Result
      ↓
Target Price
      ↓
Current Price
      ↓
Expected Upside / Downside
```

完成后，Phase 6 的四个核心目标全部具备：

```text
Valuation Model
      ↓
Deterministic Calculation
      ↓
LangGraph Valuation Agent
      ↓
Target Price + Expected Upside
```

---

### 1. Lesson 4 Goal

本课实现两个确定性结果：

#### Target Price

当前 P/E 模型产生：

```text
EPS × P/E Multiple
        ↓
Implied Value Per Share
```

在当前 Phase 6 的单模型架构下：

```text
Target Price = Implied Value Per Share
```

例如：

```text
EPS = 10
P/E = 20

Implied Value = 200
Target Price  = 200
```

#### Expected Upside

严格使用：

$$
Expected\ Upside =
\frac{Target\ Price-Current\ Price}{Current\ Price}
$$

例如：

```text
Target Price  = 200
Current Price = 160

Expected Upside
= (200 - 160) / 160
= 0.25
= 25%
```

如果 Target Price 低于 Current Price：

```text
Target = 160
Current = 200

Expected Upside
= -0.20
= -20%
```

因此这个字段同时表达：

```text
positive → upside
negative → downside
zero     → no expected price change
```

---

### 2. Graph Topology

本课**不再新增 Graph Node**。

这是有意的。

Lesson 3 已经建立：

```text
START
  ↓
Valuation Agent
  ↓
END
```

本课只是扩展 Valuation Agent 内部的确定性计算链：

```text
                         ┌────────────────────┐
                         │   Valuation Agent  │
                         └─────────┬──────────┘
                                   │
                                   ▼
                        P/E Implied Value
                                   │
                                   ▼
                             Target Price
                                   │
                                   ▼
                        Expected Upside
                                   │
                                   ▼
                         ValuationResult
```

因此没有为了“看起来有变化”而人为添加：

```text
Valuation
   ↓
Target Price Node
   ↓
Upside Node
```

当前阶段它们都属于同一个 Valuation Domain Operation。

未来如果系统需要更复杂的多模型估值、模型选择、敏感性分析，再拆分节点才有意义。

---

### 3. Domain Model 修改

`ValuationResult` 现在完整包含：

```text
ValuationResult
├── ticker
├── method
├── inputs
├── assumptions
├── implied_value_per_share
├── target_price
├── current_price
├── expected_upside
└── metadata
```

即：

```python
target_price: float
current_price: float
expected_upside: float
```

其中：

* `target_price > 0`
* `current_price > 0`
* `expected_upside` 可以为负数，因此不能设置 `gt=0`

---

### 4. Complete Calculation Code

#### `app/valuation/calculations.py`

当前完整内容：

```python
from app.valuation.models import ValuationAssumptions, ValuationInputs


def calculate_pe_implied_value(
    inputs: ValuationInputs,
    assumptions: ValuationAssumptions,
) -> float:
    """Calculate implied value per share using the P/E valuation method.

    Formula:
        implied value per share = earnings per share × assumed P/E multiple

    The function is intentionally deterministic and has no LLM, provider,
    network, or LangGraph dependency.
    """

    return inputs.earnings_per_share * assumptions.multiple


def calculate_target_price(implied_value_per_share: float) -> float:
    """Convert the valuation model's implied value into the target price."""

    if implied_value_per_share <= 0:
        raise ValueError("Implied value per share must be positive.")

    return implied_value_per_share


def calculate_expected_upside(
    target_price: float,
    current_price: float,
) -> float:
    """Calculate expected upside/downside from target and current prices.

    Formula:
        (target price - current price) / current price
    """

    if target_price <= 0:
        raise ValueError("Target price must be positive.")

    if current_price <= 0:
        raise ValueError("Current price must be positive.")

    return (target_price - current_price) / current_price
```

这里最重要的是：

```python
return (target_price - current_price) / current_price
```

这是 Python 确定性计算。

**没有 LLM 参与。**

---

### 5. Current Price 从哪里来？

这一点本课也进行了明确处理。

当前已有：

```python
CompanyResearchResult.current_price
```

而 Company Research Agent 的工具链已经存在股票价格工具。

因此 Valuation Agent 使用：

```text
CompanyResearchResult
        ↓
current_price
        ↓
Valuation
```

而不是重新制造一个价格。

所以：

```text
Company Research
       ↓
Current Price
       │
       ├──────────────┐
       │              │
       ▼              ▼
 Research State    Valuation
                      │
                      ▼
                  Target Price
                      │
                      ▼
                Expected Upside
```

这也避免了 State 中重复维护同一个 `current_price` 数据源。

---

### 6. Valuation Agent 的完整核心流程

现在 Agent 的逻辑变成：

```text
ticker
   │
   ├── valuation_inputs
   │
   ├── valuation_assumptions
   │
   └── company_research.current_price
             │
             ▼
      calculate_pe_implied_value()
             │
             ▼
        implied_value
             │
             ▼
       calculate_target_price()
             │
             ▼
        target_price
             │
             ▼
   calculate_expected_upside()
             │
             ▼
       expected_upside
             │
             ▼
      ValuationResult
```

对应核心代码：

```python
implied_value = calculate_pe_implied_value(
    inputs,
    assumptions,
)

target_price = calculate_target_price(implied_value)

expected_upside = calculate_expected_upside(
    target_price,
    current_price,
)
```

这是整个 Phase 6 最重要的计算链。

---

### 7. 为什么 `target_price` 没有让 LLM 生成？

这是非常重要的工业架构原则。

错误方式：

```text
Research
   ↓
LLM
   ↓
"Based on the research,
 target price is probably $200."
```

正确方式：

```text
Structured Research
       ↓
Explicit Assumptions
       ↓
Deterministic Valuation Model
       ↓
Implied Value
       ↓
Target Price
       ↓
Expected Upside
```

这样 Target Price 才具备：

* 可复现性
* 可测试性
* 可解释性
* 可审计性
* 可回归验证

这也是为什么 Phase 6 专门设计成一个独立的 Valuation Layer。

---

### 8. Complete Test Coverage

本课增加了：

#### Target Price

```python
def test_calculate_target_price_uses_implied_value():
    assert calculate_target_price(200.0) == 200.0
```

以及非法值：

```python
def test_calculate_target_price_rejects_non_positive_value():
    ...
```

#### Expected Upside

测试三个关键情况：

```text
Target > Current
    → positive

Target == Current
    → 0

Target < Current
    → negative
```

即：

```python
(200, 160) → 0.25
(200, 200) → 0.00
(160, 200) → -0.20
```

同时测试：

```text
Current Price <= 0
Target Price <= 0
```

都会拒绝。

---

### 9. Agent Integration Test

Agent 测试现在验证完整链路：

```text
EPS = 10
P/E = 20
Current Price = 160
```

得到：

```text
Implied Value = 200
Target Price = 200
Expected Upside = 0.25
```

即：

```python
assert valuation.implied_value_per_share == 200.0
assert valuation.target_price == 200.0
assert valuation.current_price == 160.0
assert valuation.expected_upside == 0.25
```

同时测试：

```text
没有 valuation_inputs
没有 valuation_assumptions
没有 company_research/current_price
```

都会明确失败。

---

### 10. 为什么没有加入 Investment Recommendation

现在即使已经有：

```text
Target Price
Current Price
Expected Upside
```

也**不能**在 Phase 6 增加：

```text
Strong Buy
Buy
Hold
Reduce
Sell
```

也不能增加：

```text
Investment Horizon
Investment Thesis
Key Catalysts
Key Risks
Invalidation Conditions
```

这些全部属于：

### 11. Phase 6 当前完整架构

现在 Phase 6 已经形成完整闭环：

```text
                    Research State
                          │
                          ▼
                  Valuation Inputs
                          │
                          ▼
                 Valuation Assumptions
                          │
                          ▼
                  ┌───────────────┐
                  │ Valuation     │
                  │ Agent         │
                  └───────┬───────┘
                          │
                          ▼
                  P/E Calculation
                          │
                          ▼
                 Implied Value/Share
                          │
                          ▼
                    Target Price
                          │
                          ▼
                  Expected Upside
                          │
                          ▼
                  ValuationResult
```

这已经可以作为 Phase 7 的输入边界。

---

### 12. Phase 6 Acceptance Criteria

根据项目交接文档规定的 Phase 6 验收标准：

| 要求                    | 状态       |
|-------------------------|------------|
| Valuation executes      | ✅         |
| Assumptions explicit    | ✅         |
| Target price generated  | ✅         |
| Calculation test passes | ✅         |
| Deterministic valuation | ✅         |
| LangGraph integration   | ✅         |
| Expected upside         | ✅         |
| Risk Analysis           | ⏳ Phase 7 |
| Investment Decision     | ⏳ Phase 7 |
| Recommendation          | ⏳ Phase 7 |
| Investment Horizon      | ⏳ Phase 7 |
| Investment Thesis       | ⏳ Phase 7 |
| Report                  | ⏳ Phase 8 |

所以从**代码设计和 Lesson 4 实现**角度，Phase 6 已经完成。

---

### 13. 测试状态

这里需要特别说明实际情况：

我在当前执行环境中运行测试时，环境缺少：

```text
langgraph
```

因此涉及 `app.agents.valuation` 的 pytest 在 collection 阶段报：

```text
ModuleNotFoundError: No module named 'langgraph'
```

这不是本课代码产生的测试失败。

同时：

```bash
python -m compileall -q app tests
```

已经通过。

我还直接验证了 Pydantic `ValuationResult` 能正确构造：

```text
EPS = 10
P/E = 20
Target Price = 200
Current Price = 160
Expected Upside = 0.25
```

所以请你在自己的项目 `.venv` 中运行：

```bash
pytest -q
```

这次建议**直接跑完整测试套件，而不是只跑 Phase 6 测试**。

因为 Phase 6 已经修改了：

```text
app/agents/research_state.py
app/valuation/models.py
app/agents/valuation.py
```

必须确认 Phase 1–5 没有回归。

---

### 14. Phase 6 的最终边界

现在可以明确冻结：

```text
Phase 6
│
├── Valuation Domain Model        ✅
├── Valuation Calculation         ✅
├── Valuation Agent Integration   ✅
├── Target Price                  ✅
└── Expected Upside               ✅
```

不继续增加：

```text
❌ DCF
❌ EV/EBITDA
❌ PEG
❌ Peer Valuation
❌ Valuation Model Selector
❌ Risk Analysis
❌ Recommendation
❌ Investment Horizon
❌ Investment Thesis
❌ Report
❌ Checkpoint
❌ HITL
❌ Memory
❌ Error Recovery Framework
❌ Observability
❌ Evaluation
❌ FastAPI
```

尤其不要因为现在已经有一个 P/E 模型，就继续扩展成一个“半成品多模型估值平台”。

**Phase 6 到这里应该停。**

---

### 16. Phase 6 完成状态

因此现在：

```text
Phase 0  Architecture                  ✅
Phase 1  Minimal LangGraph Core       ✅
Phase 2  LLM + Structured Output      ✅
Phase 3  Tool Calling                 ✅
Phase 4  Research Agents              ✅
Phase 5  Multi-Agent Orchestration    ✅
Phase 6  Valuation                    ✅
Phase 7  Risk + Investment Decision   ⏳
```

**Phase 6 到此完成。**