# Phase 7 — Risk + Investment Decision

## Lesson 1 — Risk Domain Model

本 Lesson **只建立 Risk Domain Model，不建立 Risk Agent，也不修改现有 Research / Valuation Graph**。

---

### 1. Goal

本 Lesson 的目标是建立一个能够表达投资风险的、经过 Pydantic 验证的 Domain Model。

完成后，我们应该能够表示：

```text
RiskItem
    ├── category
    ├── title
    ├── description
    ├── severity
    ├── likelihood
    ├── impact
    └── evidence

RiskAnalysis
    ├── ticker
    ├── risks[]
    ├── overall_risk_level
    ├── key_risks[]
    └── uncertainty_notes[]
```

注意：

> 本 Lesson 的重点不是“让 LLM 分析风险”，而是先定义**什么叫一个合法的 Risk Analysis 结果**。

这是后面的 Risk Agent 能否稳定工作的基础。

---

### 2. Why Now

Phase 6 结束以后，我们已经有：

```text
Research
    ↓
Valuation
    ↓
ValuationResult
```

例如：

```text
Current Price = 100
Target Price  = 130
Expected Upside = 30%
```

但这个结果本身不能回答：

> 这个 30% 的 upside 有哪些可能导致它无法实现的因素？

因此 Phase 7 的第一步不是立即让 LLM 输出：

```text
Buy
```

而是先建立：

```text
What can invalidate the thesis?
```

的结构化表达。

于是：

```text
Research
    ↓
Valuation
    ↓
Risk Domain
```

成为自然的下一层。

---

### 3. Core Concepts

本 Lesson 主要学习四个概念。

#### 3.1 Risk Category

风险首先需要分类。

第一版使用：

```text
Company
Operational
Financial
Market
Valuation
Industry
Macro
Regulatory
Data Uncertainty
```

对应：

```python
RiskCategory
```

使用 `Enum`，而不是任意字符串。

这样：

```text
"Financial"
```

和：

```text
"financial risk"
```

不会在系统中形成两个无法比较的类别。

---

#### 3.2 Risk Severity

Severity 表示：

> 如果该风险发生，对投资 Thesis 的影响有多严重？

第一版：

```text
Low
Medium
High
Critical
```

这是**结构化等级**，不是数学风险评分。

---

#### 3.3 Likelihood / Impact

Risk Analysis 中同时保留：

```text
likelihood
impact
```

第一版仍然采用离散枚举：

```text
Low
Medium
High
```

不要在这里建立：

```text
0.73 probability
×
$17.35 impact
```

之类的复杂风险模型。

原因很简单：

> Phase 7 的任务是建立 Risk Analysis capability，而不是建立 Quantitative Risk Management System。

---

#### 3.4 Evidence

每一个 RiskItem 应该能够说明：

```text
这个风险为什么存在？
```

因此至少保留：

```python
evidence: list[str]
```

例如：

```text
[
    "Revenue growth depends heavily on data-center demand.",
    "The valuation assumes continued earnings growth."
]
```

这里先不重新建立完整 Evidence Architecture。

Phase 8 / 后续 Evaluation 再系统化处理。

---

### 4. Graph Topology

本 Lesson：

> **没有 Graph。**

这是一个纯 Domain Model Lesson。

```text
┌──────────────────────────┐
│      Risk Domain         │
│                          │
│  RiskCategory            │
│  RiskSeverity            │
│  RiskLikelihood          │
│  RiskImpact              │
│  RiskItem                │
│  RiskAnalysis            │
└──────────────────────────┘
```

因此本 Lesson **不会修改**：

```text
app/agents/research_*.py
app/agents/valuation.py
app/graph/*
```

---

### 5. State Design

本 Lesson 同样：

> **不新增 LangGraph State。**

这是刻意设计的。

后面的 Lesson 2 才会考虑：

```text
RiskInputState
RiskGraphState
RiskOutputState
```

当前只定义：

```text
RiskAnalysis
```

这个 Domain Output。

关系是：

```text
Lesson 1

Risk Domain Model
        │
        ▼
RiskAnalysis
        │
        │
Lesson 2
        ▼
Risk Agent
        │
        ▼
RiskAnalysis
```

也就是说：

> Domain Model 先于 Agent。

---

### 6. Exact Files

本 Lesson 建议新增：

```text
app/risk/__init__.py
app/risk/models.py
tests/test_risk_models.py
```

不会修改已有 Phase 5 / Phase 6 文件。

最终结构：

```text
app/
├── agents/
│   ├── ...
│   └── valuation.py
│
├── risk/
│   ├── __init__.py
│   └── models.py
│
└── valuation/
    ├── __init__.py
    └── models.py
```

---

### 7. Implementation

#### 7.1 `app/risk/__init__.py`

新建：

```python
"""Risk domain models and risk analysis functionality."""
```

---

#### 7.2 `app/risk/models.py`

完整文件：

```python
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskCategory(str, Enum):
    """Categories used to classify investment risks."""

    COMPANY = "Company"
    OPERATIONAL = "Operational"
    FINANCIAL = "Financial"
    MARKET = "Market"
    VALUATION = "Valuation"
    INDUSTRY = "Industry"
    MACRO = "Macro"
    REGULATORY = "Regulatory"
    DATA_UNCERTAINTY = "Data Uncertainty"


class RiskSeverity(str, Enum):
    """Severity of the potential effect on the investment thesis."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskLikelihood(str, Enum):
    """Estimated likelihood that a risk materializes."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskImpact(str, Enum):
    """Potential impact of a risk on the investment thesis."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskItem(BaseModel):
    """A single structured investment risk."""

    model_config = ConfigDict(extra="forbid")

    category: RiskCategory = Field(
        description="Category of the investment risk.",
    )

    title: str = Field(
        min_length=1,
        description="Short title describing the risk.",
    )

    description: str = Field(
        min_length=1,
        description="Explanation of how the risk could affect the investment thesis.",
    )

    severity: RiskSeverity = Field(
        description="Overall severity of the risk.",
    )

    likelihood: RiskLikelihood = Field(
        description="Estimated likelihood of the risk materializing.",
    )

    impact: RiskImpact = Field(
        description="Potential impact on the investment thesis if the risk materializes.",
    )

    evidence: list[str] = Field(
        min_length=1,
        description="Evidence supporting the identification of this risk.",
    )


class RiskAnalysis(BaseModel):
    """Structured risk analysis for an investment thesis."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        description="Stock ticker symbol.",
    )

    risks: list[RiskItem] = Field(
        description="Structured list of identified investment risks.",
    )

    overall_risk_level: RiskSeverity = Field(
        description="Overall risk level assigned to the investment case.",
    )

    key_risks: list[str] = Field(
        description="Titles of the most important risks for the investment case.",
    )

    uncertainty_notes: list[str] = Field(
        description="Important uncertainties or limitations in the available evidence.",
    )
```

---

### 8. 为什么 `RiskItem` 同时有 `severity`、`likelihood`、`impact`？

这里有一个容易混淆的问题。

它们不是重复字段。

#### `likelihood`

回答：

> 这个风险发生的可能性有多高？

例如：

```text
High
```

#### `impact`

回答：

> 如果发生，对 Thesis 的影响有多大？

例如：

```text
High
```

#### `severity`

回答：

> 综合来看，这个风险在投资判断中的严重程度是什么？

例如：

```text
Critical
```

因此：

```text
Risk

Likelihood → High
Impact     → High
Severity   → Critical
```

是完全合理的。

---

### 9. 为什么 `key_risks` 暂时是 `list[str]`？

这里刻意没有设计成：

```python
key_risks: list[RiskItem]
```

而使用：

```python
key_risks: list[str]
```

原因是 `risks` 已经保存完整结构化风险：

```text
risks
 ├── RiskItem
 ├── RiskItem
 └── RiskItem
```

而：

```text
key_risks
```

只是一个高层摘要：

```text
[
    "AI demand slowdown",
    "Margin compression",
    "Valuation multiple contraction",
]
```

后续 Decision Agent 可以非常容易地消费：

```text
RiskAnalysis
    ├── risks
    └── key_risks
```

同时避免 Phase 7 Lesson 1 就引入复杂的对象引用关系。

---

### 10. 为什么 `uncertainty_notes` 单独存在？

Risk 和 uncertainty 不是完全相同的概念。

例如：

```text
Risk:
Valuation multiple may contract.
```

这是一个具体风险。

而：

```text
Uncertainty:
The available financial data does not provide enough information
to independently verify the long-term margin assumption.
```

更接近：

```text
Evidence Uncertainty
```

这也是为什么我们在 `RiskCategory` 中保留：

```text
DATA_UNCERTAINTY
```

同时 `RiskAnalysis` 还有：

```python
uncertainty_notes
```

这为后续：

```text
Risk
→ Decision
→ Report
```

提供了基础。

---

### 11. Tests

新建：

```text
tests/test_risk_models.py
```

完整内容：

```python
import pytest
from pydantic import ValidationError

from app.risk.models import (
    RiskAnalysis,
    RiskCategory,
    RiskImpact,
    RiskItem,
    RiskLikelihood,
    RiskSeverity,
)


def make_risk_item() -> RiskItem:
    return RiskItem(
        category=RiskCategory.VALUATION,
        title="Valuation Multiple Compression",
        description=(
            "A contraction in the valuation multiple could reduce "
            "the expected return even if operating performance remains strong."
        ),
        severity=RiskSeverity.HIGH,
        likelihood=RiskLikelihood.MEDIUM,
        impact=RiskImpact.HIGH,
        evidence=[
            "The valuation depends on the assumed earnings multiple.",
        ],
    )


def make_risk_analysis() -> RiskAnalysis:
    return RiskAnalysis(
        ticker="NVDA",
        risks=[make_risk_item()],
        overall_risk_level=RiskSeverity.HIGH,
        key_risks=["Valuation Multiple Compression"],
        uncertainty_notes=[
            "The assumed valuation multiple is sensitive to market sentiment."
        ],
    )


def test_risk_category_contains_expected_categories():
    assert RiskCategory.COMPANY.value == "Company"
    assert RiskCategory.OPERATIONAL.value == "Operational"
    assert RiskCategory.FINANCIAL.value == "Financial"
    assert RiskCategory.MARKET.value == "Market"
    assert RiskCategory.VALUATION.value == "Valuation"
    assert RiskCategory.INDUSTRY.value == "Industry"
    assert RiskCategory.MACRO.value == "Macro"
    assert RiskCategory.REGULATORY.value == "Regulatory"
    assert RiskCategory.DATA_UNCERTAINTY.value == "Data Uncertainty"


def test_risk_severity_is_structured():
    assert RiskSeverity.LOW.value == "Low"
    assert RiskSeverity.MEDIUM.value == "Medium"
    assert RiskSeverity.HIGH.value == "High"
    assert RiskSeverity.CRITICAL.value == "Critical"


def test_risk_item_is_structured():
    risk = make_risk_item()

    assert risk.category == RiskCategory.VALUATION
    assert risk.title == "Valuation Multiple Compression"
    assert risk.severity == RiskSeverity.HIGH
    assert risk.likelihood == RiskLikelihood.MEDIUM
    assert risk.impact == RiskImpact.HIGH
    assert risk.evidence


def test_risk_analysis_is_structured():
    analysis = make_risk_analysis()

    assert analysis.ticker == "NVDA"
    assert len(analysis.risks) == 1
    assert analysis.overall_risk_level == RiskSeverity.HIGH
    assert analysis.key_risks == ["Valuation Multiple Compression"]
    assert analysis.uncertainty_notes


def test_risk_item_rejects_empty_title():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_empty_description():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_empty_evidence():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=[],
        )


def test_risk_item_rejects_invalid_category():
    with pytest.raises(ValidationError):
        RiskItem(
            category="Invalid Category",
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity="Extreme",
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_invalid_likelihood():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood="Almost Certain",
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_invalid_impact():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact="Extreme",
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
            unexpected_field="not allowed",
        )


def test_risk_analysis_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RiskAnalysis(
            ticker="NVDA",
            risks=[make_risk_item()],
            overall_risk_level=RiskSeverity.HIGH,
            key_risks=["Valuation Multiple Compression"],
            uncertainty_notes=[],
            unexpected_field="not allowed",
        )


def test_risk_analysis_requires_ticker():
    with pytest.raises(ValidationError):
        RiskAnalysis(
            ticker="",
            risks=[make_risk_item()],
            overall_risk_level=RiskSeverity.HIGH,
            key_risks=["Valuation Multiple Compression"],
            uncertainty_notes=[],
        )
```

---

### 12. 一个值得注意的设计决定

这里没有加入类似：

```python
risk_score: float
```

也没有：

```python
likelihood_score: float
impact_score: float
```

原因不是未来永远不需要，而是：

```text
Phase 7 Lesson 1
```

目前只需要：

```text
Structured Risk Domain
```

而不是：

```text
Quantitative Risk Engine
```

如果未来需要：

```text
Probability
Expected Loss
Risk-adjusted Valuation
Portfolio Risk
```

应该在明确的后续 Domain Enhancement 中设计，而不是把复杂度提前塞进 Phase 7。

---

### 13. Acceptance Criteria

Lesson 1 只有满足以下条件才算完成：

```text
Risk Domain

[ ] app/risk/models.py exists
[ ] RiskCategory exists
[ ] RiskSeverity exists
[ ] RiskLikelihood exists
[ ] RiskImpact exists
[ ] RiskItem exists
[ ] RiskAnalysis exists

Validation

[ ] Invalid category rejected
[ ] Invalid severity rejected
[ ] Invalid likelihood rejected
[ ] Invalid impact rejected
[ ] Empty title rejected
[ ] Empty description rejected
[ ] Empty evidence rejected
[ ] Extra fields rejected

Tests

[ ] Lesson 1 tests pass
[ ] Existing regression tests pass
```

---

### 14. Out of Scope

本 Lesson **明确不做**：

```text
❌ Risk Agent
❌ LLM
❌ Risk Graph
❌ Research → Risk connection
❌ Valuation → Risk connection
❌ Risk scoring engine
❌ Probability model
❌ Monte Carlo
❌ Risk-adjusted valuation
❌ Decision Agent
❌ Recommendation
❌ Investment Horizon
❌ Report
❌ Evidence Architecture redesign
❌ Persistence
❌ HITL
```

特别注意：

> **不要在本 Lesson 创建 `risk.py` Agent 文件。**

`app/risk/models.py` 是 Domain Model。

真正的：

```text
app/agents/risk.py
```

属于 **Lesson 2**。

---

### 15. Key Understanding

完成这个 Lesson 后，你应该形成一个非常重要的架构认识：

```text
LLM Agent
    ↓
需要一个稳定的 Output Contract
    ↓
RiskAnalysis
    ↓
由 Domain Model 定义
```

因此后面 Lesson 2 的 Risk Agent 并不是“让 LLM 随便写一段风险分析”。

而是：

```text
Research
+
Valuation
      ↓
   Risk Agent
      ↓
 structured output
      ↓
 RiskAnalysis
```

这和 Phase 6 的设计是一致的：

```text
Valuation Agent
      ↓
ValuationResult
```

以及未来：

```text
Decision Agent
      ↓
InvestmentDecision
```

整个项目正在逐步形成：

```text
Research
   ↓
ResearchResult

Valuation
   ↓
ValuationResult

Risk
   ↓
RiskAnalysis

Decision
   ↓
InvestmentDecision
```

这正是我们后面能够进行可靠 Integration 和 Evaluation 的基础。

---