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