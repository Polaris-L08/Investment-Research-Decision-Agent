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


## Lesson 2 — Risk Analysis

Lesson 1 已经建立了稳定的 Risk Domain Contract：

```text
RiskItem
    ↓
RiskAnalysis
```

现在进入 Lesson 2。这里第一次让 **LLM 真正参与 Risk Domain**，但仍然严格遵守：

```text
Research + Valuation
        ↓
    Risk Agent
        ↓
   RiskAnalysis
```

而不是让 Risk Agent 重新搜索外部世界。

---

### 1. Goal

本 Lesson 的目标是建立一个独立的 **Risk Analysis Agent Graph**。

完成后应该能够执行：

```text
CompanyResearchResult
FinancialResearchResult
MarketResearchResult
IndustryMacroResearchResult
ValuationResult
        │
        ▼
   Risk Agent
        │
        ▼
   RiskAnalysis
```

也就是说，我们第一次把：

```text
Phase 5 Research
+
Phase 6 Valuation
+
Phase 7 Risk Domain
```

连接到一个新的 Agent。

但这个连接仍然是**教学阶段的局部 Graph**，不是最终 Application Graph。

---

### 2. Why Now

Lesson 1 已经回答：

> Risk Analysis 长什么样？

现在需要回答：

> 谁负责生成 Risk Analysis？

答案是：

```text
Risk Agent
```

因此：

```text
Lesson 1
Domain Contract
       ↓
Lesson 2
Agent Implementation
```

这个顺序非常重要。

如果先写 Agent 再设计 Schema，很容易出现：

```text
LLM 输出什么
→ Schema 再去适应什么
```

我们现在采用相反方向：

```text
Domain Contract
→ Agent
→ Structured Output
```

---

### 3. Core Concepts

本 Lesson 有五个重点。

---

#### 3.1 Risk Agent 的职责

Risk Agent 负责：

```text
Analyze existing evidence
        ↓
Identify risks
        ↓
Classify risks
        ↓
Assess likelihood / impact / severity
        ↓
Return RiskAnalysis
```

它**不负责**：

```text
Search
Fetch API
Research
Valuation calculation
Investment recommendation
Report generation
```

---

### 4. Risk Agent 的输入

Risk Agent 接收：

```text
CompanyResearchResult
FinancialResearchResult
MarketResearchResult
IndustryMacroResearchResult
ValuationResult
```

这几个对象分别代表：

```text
Company
Financial
Market
Industry / Macro
Valuation
```

这是非常重要的设计。

Risk Agent 不应该接收一个已经拼接好的：

```text
mega_string
```

而应该保留 Domain Boundary：

```text
company_research
financial_research
market_research
industry_macro_research
valuation
```

这样后续 Evaluation 才能够知道：

```text
这个风险是根据哪一类信息产生的？
```

---

### 5. Risk Agent 的输出

输出严格限定为：

```text
RiskAnalysis
```

即：

```text
Risk Agent
     ↓
Structured Output
     ↓
RiskAnalysis
```

不会输出：

```text
str
dict
JSON string
Markdown
```

再由我们手工解析。

这和 Phase 2 / Phase 6 的 Structured Output 原则保持一致。

---

### 6. Graph Topology

本 Lesson 第一次建立 Risk Graph。

拓扑：

```text
              RiskInputState
                    │
                    ▼
              Risk Agent
                    │
                    ▼
             RiskOutputState
```

更具体：

```text
START
  │
  ▼
analyze_risk
  │
  ▼
 END
```

没有：

```text
Research Agent
Valuation Agent
Search Tool
Supervisor
Router
```

因为这些都不是 Risk Agent 的职责。

---

### 7. State Design

这里建议使用三个概念：

```text
RiskInputState
RiskGraphState
RiskOutputState
```

与 Phase 6 Valuation 的设计保持一致。

---

#### 7.1 RiskInputState

外部输入：

```python
class RiskInputState(TypedDict):
    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult
```

---

#### 7.2 RiskGraphState

内部 Graph State：

```python
class RiskGraphState(TypedDict, total=False):
    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult

    risk_analysis: RiskAnalysis | None
    risk_error: str | None
```

---

#### 7.3 RiskOutputState

Graph 输出：

```python
class RiskOutputState(TypedDict):
    risk_analysis: RiskAnalysis | None
    risk_error: str | None
```

这里和 Phase 6 的思路保持一致：

```text
Input
 ↓
Graph State
 ↓
Output
```

---

### 8. 一个重要设计：为什么 ValuationResult 直接作为 Input？

我们不重新传：

```text
target_price
current_price
expected_upside
```

而是直接：

```python
valuation: ValuationResult
```

原因是：

```text
ValuationResult
```

本身就是 Phase 6 的 Domain Contract。

它已经包含：

```text
method
inputs
assumptions
implied_value_per_share
target_price
current_price
expected_upside
metadata
```

因此 Risk Agent 可以知道：

```text
这个投资 Thesis 建立在什么 valuation 基础上？
```

而不需要 Risk Layer 自己重新构造 valuation。

---

### 9. Exact Files

本 Lesson 新增：

```text
app/agents/risk.py
tests/test_risk_agent.py
```

可能需要读取现有：

```text
app/agents/models.py
app/valuation/models.py
app/risk/models.py
app/agents/llm.py
```

但**不修改这些已有文件**，除非你的当前实际源码与我们之前检查的 Phase 6 基线存在差异。

---

### 10. Implementation — `app/agents/risk.py`

新建完整文件：

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.agents.llm import get_llm
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult


class RiskInputState(TypedDict):
    """Input contract for the risk analysis graph."""

    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult


class RiskGraphState(TypedDict, total=False):
    """Internal state used by the risk analysis graph."""

    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult

    risk_analysis: RiskAnalysis | None
    risk_error: str | None


class RiskOutputState(TypedDict):
    """Output contract for the risk analysis graph."""

    risk_analysis: RiskAnalysis | None
    risk_error: str | None


def analyze_risk(state: RiskGraphState) -> dict:
    """Analyze investment risks from existing research and valuation."""

    llm = get_llm().with_structured_output(RiskAnalysis)

    prompt = f"""
You are an investment risk analysis agent.

Your task is to analyze the existing research and valuation evidence
and identify the major risks that could affect the investment thesis.

You must NOT perform new web searches.
You must NOT invent facts that are not supported by the supplied evidence.
You must NOT generate an investment recommendation.
You must only produce a structured risk analysis.

Ticker:
{state["ticker"]}

Company Research:
{state["company_research"].model_dump_json(indent=2)}

Financial Research:
{state["financial_research"].model_dump_json(indent=2)}

Market Research:
{state["market_research"].model_dump_json(indent=2)}

Industry / Macro Research:
{state["industry_macro_research"].model_dump_json(indent=2)}

Valuation:
{state["valuation"].model_dump_json(indent=2)}

Risk analysis requirements:

1. Identify material risks relevant to the investment thesis.
2. Classify each risk using the available risk categories.
3. Assess likelihood, impact, and severity using the defined enums.
4. Provide evidence supporting each identified risk.
5. Highlight the most important risks in key_risks.
6. Explicitly identify important uncertainties or limitations in
   uncertainty_notes.
7. Do not generate Buy, Sell, Hold, or any other investment recommendation.
8. Do not create a new target price or modify the supplied valuation.
"""

    try:
        risk_analysis = llm.invoke(prompt)

        return {
            "risk_analysis": risk_analysis,
            "risk_error": None,
        }

    except Exception as exc:
        return {
            "risk_analysis": None,
            "risk_error": str(exc),
        }


def build_risk_graph():
    """Build and compile the risk analysis graph."""

    graph = StateGraph(
        RiskGraphState,
        input_schema=RiskInputState,
        output_schema=RiskOutputState,
    )

    graph.add_node("analyze_risk", analyze_risk)

    graph.add_edge(START, "analyze_risk")
    graph.add_edge("analyze_risk", END)

    return graph.compile()
```

---

### 11. 为什么这里仍然使用 `try / except`？

这是一个值得特别说明的地方。

这里允许：

```python
try:
    ...
except Exception:
    ...
```

但这**不是 Phase 12 Error Recovery Framework**。

当前只是最基本的：

```text
Agent execution
        ↓
success
    OR
error captured in state
```

目的是让 Graph 能够返回：

```text
risk_analysis
risk_error
```

而不是因为 LLM provider 或 structured output 异常直接导致 Graph 崩溃。

Phase 12 才会正式建立：

```text
Retry
Fallback
Partial Result
Recovery
Escalation
```

---

### 12. 为什么 Prompt 中明确禁止 Recommendation？

这是 Phase 7 一个非常重要的 Domain Boundary。

Risk Agent：

```text
Risk
```

Decision Agent：

```text
Investment Decision
```

所以 Risk Agent 不能输出：

```text
BUY
```

即使它认为：

```text
风险较低
```

也只能表达：

```text
overall_risk_level = Low
```

而不是：

```text
recommendation = Buy
```

最终：

```text
RiskAnalysis
        ↓
InvestmentDecision Agent
```

由 Decision Agent 完成综合判断。

---

### 13. 为什么 Prompt 中禁止修改 Valuation？

同样：

```text
Valuation Agent
```

负责：

```text
Target Price
Expected Upside
```

Risk Agent 负责：

```text
Valuation Risk
```

例如：

```text
The investment thesis depends on a relatively high P/E multiple.
```

而不是：

```text
Target price should actually be 85.
```

否则会破坏：

```text
Research
   ↓
Valuation
   ↓
Risk
```

的数据契约。

---

### 14. Tests — `tests/test_risk_agent.py`

这里采用项目已有的测试风格：

```text
Real LLM
+
Deterministic Mock Inputs
```

但我们需要避免测试依赖真实金融 API。

因此创建 deterministic fixtures。

完整测试文件：

```python
from unittest.mock import MagicMock, patch

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.agents.risk import (
    RiskInputState,
    build_risk_graph,
)
from app.risk.models import (
    RiskAnalysis,
    RiskCategory,
    RiskImpact,
    RiskItem,
    RiskLikelihood,
    RiskSeverity,
)
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMethod,
    ValuationMetadata,
    ValuationResult,
)


def make_company_research() -> CompanyResearchResult:
    return CompanyResearchResult(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        current_price=180.0,
        business_summary=(
            "NVIDIA designs GPUs and accelerated computing platforms "
            "serving data center and other computing markets."
        ),
        key_products=[
            "Data center GPUs",
            "Accelerated computing platforms",
        ],
        competitive_advantages=[
            "Strong software ecosystem",
            "Broad accelerated computing platform",
        ],
        risks=[
            "Competitive pressure",
            "Dependence on data center demand",
        ],
    )


def make_financial_research() -> FinancialResearchResult:
    return FinancialResearchResult(
        ticker="NVDA",
        revenue=100.0,
        net_income=30.0,
        profit_margin=0.30,
        revenue_growth=0.25,
        earnings_growth=0.30,
        financial_strength="Strong",
        key_financial_trends=[
            "Strong revenue growth",
            "Expanding profitability",
        ],
    )


def make_market_research() -> MarketResearchResult:
    return MarketResearchResult(
        ticker="NVDA",
        current_price=180.0,
        price_change_1d=0.02,
        price_change_1w=0.04,
        price_change_1m=0.08,
        market_sentiment="Positive",
        key_market_factors=[
            "Strong AI infrastructure demand",
            "Elevated technology sector expectations",
        ],
    )


def make_industry_macro_research() -> IndustryMacroResearchResult:
    return IndustryMacroResearchResult(
        ticker="NVDA",
        industry="Semiconductors",
        industry_growth_outlook="Strong",
        competitive_dynamics="Highly competitive",
        macro_factors=[
            "AI infrastructure investment",
            "Interest rate sensitivity",
        ],
        regulatory_factors=[
            "Export restrictions",
        ],
    )


def make_valuation() -> ValuationResult:
    return ValuationResult(
        ticker="NVDA",
        method=ValuationMethod.PE,
        inputs=ValuationInputs(
            eps=6.0,
        ),
        assumptions=ValuationAssumptions(
            assumed_pe=30.0,
        ),
        implied_value_per_share=180.0,
        target_price=180.0,
        current_price=180.0,
        expected_upside=0.0,
        metadata=ValuationMetadata(
            model_version="phase6-v1",
        ),
    )


def make_risk_analysis() -> RiskAnalysis:
    return RiskAnalysis(
        ticker="NVDA",
        risks=[
            RiskItem(
                category=RiskCategory.VALUATION,
                title="Valuation Multiple Compression",
                description=(
                    "A contraction in the valuation multiple could reduce "
                    "the expected investment return."
                ),
                severity=RiskSeverity.HIGH,
                likelihood=RiskLikelihood.MEDIUM,
                impact=RiskImpact.HIGH,
                evidence=[
                    "The valuation relies on an assumed P/E multiple.",
                ],
            ),
            RiskItem(
                category=RiskCategory.INDUSTRY,
                title="Competitive Pressure",
                description=(
                    "Intensifying competition could reduce market share "
                    "or pricing power."
                ),
                severity=RiskSeverity.MEDIUM,
                likelihood=RiskLikelihood.MEDIUM,
                impact=RiskImpact.MEDIUM,
                evidence=[
                    "The semiconductor industry has strong competitive dynamics."
                ],
            ),
        ],
        overall_risk_level=RiskSeverity.HIGH,
        key_risks=[
            "Valuation Multiple Compression",
            "Competitive Pressure",
        ],
        uncertainty_notes=[
            "Long-term demand growth remains uncertain.",
        ],
    )


def make_input_state() -> RiskInputState:
    return {
        "ticker": "NVDA",
        "company_research": make_company_research(),
        "financial_research": make_financial_research(),
        "market_research": make_market_research(),
        "industry_macro_research": make_industry_macro_research(),
        "valuation": make_valuation(),
    }


def test_risk_agent_graph_returns_structured_risk_analysis():
    expected_analysis = make_risk_analysis()

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = expected_analysis

    with patch("app.agents.risk.get_llm", return_value=mock_llm):
        graph = build_risk_graph()

        result = graph.invoke(make_input_state())

    assert result["risk_error"] is None
    assert isinstance(result["risk_analysis"], RiskAnalysis)
    assert result["risk_analysis"].ticker == "NVDA"
    assert len(result["risk_analysis"].risks) == 2
    assert result["risk_analysis"].overall_risk_level == RiskSeverity.HIGH


def test_risk_agent_graph_preserves_structured_risk_items():
    expected_analysis = make_risk_analysis()

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = expected_analysis

    with patch("app.agents.risk.get_llm", return_value=mock_llm):
        graph = build_risk_graph()

        result = graph.invoke(make_input_state())

    risks = result["risk_analysis"].risks

    assert risks[0].category == RiskCategory.VALUATION
    assert risks[0].severity == RiskSeverity.HIGH
    assert risks[0].likelihood == RiskLikelihood.MEDIUM
    assert risks[0].impact == RiskImpact.HIGH
    assert risks[0].evidence


def test_risk_agent_graph_preserves_uncertainty_notes():
    expected_analysis = make_risk_analysis()

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = expected_analysis

    with patch("app.agents.risk.get_llm", return_value=mock_llm):
        graph = build_risk_graph()

        result = graph.invoke(make_input_state())

    assert result["risk_analysis"].uncertainty_notes == [
        "Long-term demand growth remains uncertain.",
    ]


def test_risk_agent_graph_captures_llm_error():
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("LLM failure")

    with patch("app.agents.risk.get_llm", return_value=mock_llm):
        graph = build_risk_graph()

        result = graph.invoke(make_input_state())

    assert result["risk_analysis"] is None
    assert result["risk_error"] == "LLM failure"
```

---

### 15. 这里有一个测试设计上的重要点

测试中：

```python
mock_llm.invoke.return_value = expected_analysis
```

而不是：

```python
mock_llm.invoke.return_value = {
    ...
}
```

这是为了验证：

```text
Risk Agent
    ↓
RiskAnalysis
```

这个 Domain Contract。

我们不是在测试：

```text
LLM 能不能生成 JSON
```

而是在测试：

```text
Graph 能否消费并输出 RiskAnalysis
```

真正的 LLM Structured Output 行为已经在 Phase 2 建立过基础。

---

### 16. Graph 的输入输出契约

完成后：

```text
RiskInputState
```

输入：

```text
ticker
company_research
financial_research
market_research
industry_macro_research
valuation
```

经过：

```text
analyze_risk
```

输出：

```text
RiskOutputState
```

包含：

```text
risk_analysis
risk_error
```

因此：

```text
                ┌──────────────────────┐
                │   RiskInputState     │
                ├──────────────────────┤
                │ ticker               │
                │ company_research     │
                │ financial_research   │
                │ market_research      │
                │ industry_macro       │
                │ valuation            │
                └──────────┬───────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Risk Agent  │
                    └──────┬──────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  RiskOutputState     │
                ├──────────────────────┤
                │ risk_analysis        │
                │ risk_error           │
                └──────────────────────┘
```

---

### 17. 为什么现在不使用 Supervisor？

Phase 5 已经教过：

```text
Supervisor
Router
Fan-out
Reducer
```

但是本 Lesson 不需要。

现在的任务是：

```text
Existing Evidence
      ↓
One Domain Agent
```

如果此时引入：

```text
Risk Supervisor
Risk Router
Risk Researcher
Risk Reducer
```

只是增加 Graph Complexity，并没有增加业务能力。

这是一个很重要的工程判断：

> **不要因为 LangGraph 提供了某个机制，就强行把它放进每一个 Graph。**

---

### 18. 为什么 Risk Agent 不直接接 `ResearchState`？

这里尤其重要。

我们不写：

```python
def analyze_risk(state: ResearchState):
```

因为：

```text
ResearchState
```

是 Phase 5 的 Research Domain / Teaching State。

而 Risk Agent 的正式业务输入应该是：

```text
Research Results
+
Valuation Result
```

也就是：

```text
Domain Output
→
Domain Input
```

而不是：

```text
Graph A Internal State
→
Graph B Internal State
```

这正是后期建立 Subgraph Contract 时非常重要的原则。

---

### 19. Lesson 2 Acceptance Criteria

本 Lesson 完成条件：

```text
Risk Agent

[ ] app/agents/risk.py exists
[ ] RiskInputState exists
[ ] RiskGraphState exists
[ ] RiskOutputState exists
[ ] Risk Agent consumes all four research domains
[ ] Risk Agent consumes ValuationResult
[ ] Risk Agent uses structured output
[ ] Risk Agent produces RiskAnalysis
[ ] Risk Agent does not generate recommendation
[ ] Risk Agent does not modify valuation
[ ] LLM error is represented in risk_error


Graph

[ ] START → analyze_risk → END
[ ] Graph compiles
[ ] Graph invocation works


Tests

[ ] Risk Agent test passes
[ ] Existing Lesson 1 tests pass
[ ] Phase 5 regression passes
[ ] Phase 6 regression passes
```

---

### 20. Out of Scope

Lesson 2 明确不做：

```text
❌ Investment Decision
❌ Recommendation
❌ Investment Horizon
❌ Target Price calculation
❌ Expected Upside calculation
❌ New valuation model
❌ Web Search
❌ Financial API
❌ Market API
❌ Risk Supervisor
❌ Risk Router
❌ Dynamic Fan-out
❌ Risk Recovery Framework
❌ Persistence
❌ HITL
❌ Memory
❌ Report
❌ Final Top-Level Graph
```

特别是：

```text
Risk Agent
    ↓
Buy / Hold / Sell
```

**禁止。**

正确的是：

```text
Risk Agent
    ↓
RiskAnalysis
```

然后 Lesson 4 才会：

```text
Research
+
Valuation
+
Risk
    ↓
Investment Decision Agent
```

---

### 21. Key Understanding

完成 Lesson 2 后，目前的 Domain Pipeline 会变成：

```text
Research
    │
    ├── CompanyResearchResult
    ├── FinancialResearchResult
    ├── MarketResearchResult
    └── IndustryMacroResearchResult
    │
    ▼
Valuation
    │
    ▼
ValuationResult
    │
    ▼
Risk Agent
    │
    ▼
RiskAnalysis
```

注意这里还没有：

```text
Recommendation
```

因此目前系统回答的是：

```text
What did we learn?
        ↓
What is it worth?
        ↓
What can go wrong?
```

下一阶段 Lesson 3 才建立：

```text
What structured investment conclusion
should represent all of this?
```

也就是：

```text
InvestmentDecision
```

---