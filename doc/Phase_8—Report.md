# Phase 8 —— Report

## Lesson 1：InvestmentReport Domain Model

### 一、本课目标

本课完成三个目标：

1. 创建 `app/report` Domain
2. 定义 `InvestmentReport`
3. 为 `InvestmentReport` 建立独立的 Model Tests

最终结构：

```text
app/
├── investment/
│   └── models.py
│
├── valuation/
│   └── models.py
│
├── risk/
│   └── models.py
│
├── agents/
│   └── models.py
│
└── report/
    ├── __init__.py
    └── models.py
```

核心依赖关系：

```text
                    ┌──────────────────────┐
                    │ CompanyResearchResult│
                    ├──────────────────────┤
                    │ FinancialResearchResult
                    ├──────────────────────┤
                    │ MarketResearchResult │
                    ├──────────────────────┤
                    │ IndustryMacroResearch│
                    └──────────┬───────────┘
                               │
                               │ Phase 8 后续 Lesson
                               ▼
                    ┌──────────────────────┐
                    │  InvestmentReport    │
                    │                      │
                    │ narrative summaries  │
                    │ +                   │
                    │ existing domain      │
                    │ results              │
                    └──────┬───────┬───────┘
                           │       │
              ┌────────────┘       └─────────────┐
              ▼                                  ▼
      ┌───────────────┐                  ┌──────────────────┐
      │ ValuationResult│                  │  RiskAnalysis    │
      └───────────────┘                  └──────────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ InvestmentDecision │
                  └────────────────────┘
```

注意：

**Report 不重新计算这些数据。**

例如：

```python
report.valuation.expected_upside
```

才是报告中的预期上涨空间来源。

而不是：

```python
report.expected_upside
```

再保存一份。

同理：

```python
report.investment_decision.recommendation
```

是 Recommendation 的唯一来源。

---

### 二、第一步：创建 `app/report/__init__.py`

新建：

```text
app/report/__init__.py
```

内容保持非常简单：

```python
from .models import InvestmentReport

__all__ = ["InvestmentReport"]
```

这里没有任何业务逻辑。

它只是让：

```python
from app.report import InvestmentReport
```

成为稳定的公开导入接口。

---

### 三、第二步：创建 `app/report/models.py`

这是本课的核心。

新建：

```text
app/report/models.py
```

完整内容：

```python
from pydantic import BaseModel, ConfigDict, Field

from app.investment.models import InvestmentDecision
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult


class InvestmentReport(BaseModel):
    """
    Domain model representing a complete investment research report.

    The report composes existing domain results instead of duplicating
    business facts owned by other domains.
    """

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        description="Stock ticker symbol.",
    )

    title: str = Field(
        min_length=1,
        description="Report title.",
    )

    executive_summary: str = Field(
        min_length=1,
        description="Executive summary of the investment research.",
    )

    company_overview: str = Field(
        min_length=1,
        description="Narrative overview of the company.",
    )

    financial_summary: str = Field(
        min_length=1,
        description="Narrative summary of the company's financials.",
    )

    market_summary: str = Field(
        min_length=1,
        description="Narrative summary of the market environment.",
    )

    industry_macro_summary: str = Field(
        min_length=1,
        description="Narrative summary of industry and macro conditions.",
    )

    valuation_summary: str = Field(
        min_length=1,
        description="Narrative summary of the valuation analysis.",
    )

    risk_summary: str = Field(
        min_length=1,
        description="Narrative summary of the risk analysis.",
    )

    investment_decision_summary: str = Field(
        min_length=1,
        description="Narrative summary of the investment decision.",
    )

    valuation: ValuationResult = Field(
        description="Valuation result used as the source of truth for valuation facts.",
    )

    risk_analysis: RiskAnalysis = Field(
        description="Risk analysis used as the source of truth for risk facts.",
    )

    investment_decision: InvestmentDecision = Field(
        description="Investment decision used as the source of truth for decision facts.",
    )
```

---

### 四、为什么这样设计？

这里是 Phase 8 最重要的架构原则。

#### 1. 不重复 `InvestmentDecision`

Phase 7 已经建立：

```python
InvestmentDecision
```

它已经拥有：

```text
recommendation
investment_horizon
current_price
target_price
expected_upside
conviction
investment_thesis
key_catalysts
key_risks
invalidation_conditions
supporting_evidence
```

因此我们**不再**在 `InvestmentReport` 中定义：

```python
recommendation
current_price
target_price
expected_upside
...
```

否则会产生两个来源：

```text
InvestmentDecision
        │
        ├── recommendation = BUY
        │
        └── expected_upside = 0.25

InvestmentReport
        │
        ├── recommendation = HOLD
        │
        └── expected_upside = 0.18
```

这对于工业级系统是非常危险的。

所以：

```python
report.investment_decision.recommendation
```

是唯一事实来源。

---

#### 2. Valuation 同样不复制

Phase 7 的：

```python
ValuationResult
```

已经拥有：

```python
current_price
target_price
expected_upside
```

因此：

```python
report.valuation.current_price
report.valuation.target_price
report.valuation.expected_upside
```

就是 Report 中这些数值的来源。

Report 本身不重新计算：

```python
(target_price - current_price) / current_price
```

---

#### 3. Risk 同样不复制

Phase 7：

```python
RiskAnalysis
```

已经拥有：

```python
key_risks
overall_risk_level
uncertainty_notes
risks
```

所以：

```python
report.risk_analysis.key_risks
```

就是风险事实的来源。

---

### 五、为什么 Report 仍然需要 Summary 字段？

这里要区分：

#### Domain Facts

例如：

```python
report.valuation.target_price
report.investment_decision.recommendation
report.risk_analysis.key_risks
```

这些是**结构化业务事实**。

---

#### Report Narrative

例如：

```python
report.valuation_summary
report.risk_summary
report.executive_summary
```

这些是**面向最终报告读者的叙事内容**。

二者不是同一种东西。

最终可能出现：

```text
ValuationResult
        │
        │ structured facts
        ▼
valuation_summary
        │
        │ human-readable narrative
        ▼
Markdown / HTML / PDF
```

这也是为什么 Report Domain 有存在的必要，而不是简单把几个 Phase 7 Model 拼起来。

---

### 六、第三步：创建测试

新建：

```text
tests/test_report_models.py
```

内容：

```python
import pytest
from pydantic import ValidationError

from app.investment.models import (
    InvestmentConviction,
    InvestmentDecision,
    InvestmentHorizon,
    InvestmentRecommendation,
)
from app.report.models import InvestmentReport
from app.risk.models import RiskAnalysis
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


def build_valuation() -> ValuationResult:
    return ValuationResult(
        ticker="TEST",
        method=ValuationMethod.PE,
        inputs=ValuationInputs(
            earnings_per_share=10.0,
        ),
        assumptions=ValuationAssumptions(
            multiple=20.0,
            rationale="Stable earnings growth supports the selected multiple.",
        ),
        implied_value_per_share=200.0,
        target_price=200.0,
        current_price=160.0,
        expected_upside=0.25,
        metadata=ValuationMetadata(
            currency="USD",
            model_version="phase7-v1",
        ),
    )


def build_risk_analysis() -> RiskAnalysis:
    return RiskAnalysis(
        ticker="TEST",
        risks=[],
        overall_risk_level="Medium",
        key_risks=[
            "Revenue growth may slow.",
        ],
        uncertainty_notes=[
            "Macro conditions remain uncertain.",
        ],
    )


def build_investment_decision() -> InvestmentDecision:
    return InvestmentDecision(
        ticker="TEST",
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=160.0,
        target_price=200.0,
        expected_upside=0.25,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis="Valuation provides sufficient upside relative to identified risks.",
        key_catalysts=[
            "Earnings growth.",
        ],
        key_risks=[
            "Revenue growth may slow.",
        ],
        invalidation_conditions=[
            "Material deterioration in earnings.",
        ],
        supporting_evidence=[
            "Current valuation implies meaningful upside.",
        ],
    )


def build_report() -> InvestmentReport:
    return InvestmentReport(
        ticker="TEST",
        title="TEST Investment Research Report",
        executive_summary="The company presents a moderate-upside investment opportunity.",
        company_overview="TEST operates in its core industry.",
        financial_summary="Financial performance remains stable.",
        market_summary="The broader market environment is mixed.",
        industry_macro_summary="Industry growth remains positive but uncertain.",
        valuation_summary="The valuation indicates meaningful upside.",
        risk_summary="The primary risks relate to growth and macro uncertainty.",
        investment_decision_summary="The current evidence supports a medium-term investment thesis.",
        valuation=build_valuation(),
        risk_analysis=build_risk_analysis(),
        investment_decision=build_investment_decision(),
    )


def test_investment_report_can_be_constructed():
    report = build_report()

    assert report.ticker == "TEST"
    assert report.title == "TEST Investment Research Report"


def test_investment_report_composes_existing_domain_models():
    report = build_report()

    assert isinstance(report.valuation, ValuationResult)
    assert isinstance(report.risk_analysis, RiskAnalysis)
    assert isinstance(report.investment_decision, InvestmentDecision)


def test_investment_report_preserves_phase7_source_of_truth():
    report = build_report()

    assert report.valuation.current_price == 160.0
    assert report.valuation.target_price == 200.0
    assert report.valuation.expected_upside == 0.25

    assert report.investment_decision.recommendation == InvestmentRecommendation.BUY
    assert report.investment_decision.investment_horizon == InvestmentHorizon.MEDIUM_TERM
    assert report.investment_decision.conviction == InvestmentConviction.MEDIUM

    assert report.risk_analysis.key_risks == [
        "Revenue growth may slow.",
    ]


def test_investment_report_rejects_empty_required_strings():
    with pytest.raises(ValidationError):
        build_report.model_copy(
            update={
                "title": "",
            },
        )


def test_investment_report_rejects_extra_fields():
    with pytest.raises(ValidationError):
        InvestmentReport(
            **build_report().model_dump(),
            unexpected_field="not allowed",
        )


def test_investment_report_does_not_duplicate_decision_fields():
    report_fields = set(InvestmentReport.model_fields)

    duplicated_fields = {
        "recommendation",
        "investment_horizon",
        "current_price",
        "target_price",
        "expected_upside",
        "conviction",
        "investment_thesis",
        "key_catalysts",
        "key_risks",
        "invalidation_conditions",
        "supporting_evidence",
    }

    assert report_fields.isdisjoint(duplicated_fields)
```

---

### 七、这里有一个测试细节需要特别注意

测试：

```python
build_report.model_copy(
    update={"title": ""}
)
```

不会触发 Pydantic validation。

所以这段测试实际上不正确。

工业级项目里，我们不应该留下一个“看起来在测试、实际上没有测试到”的测试。

应该改成：

```python
def test_investment_report_rejects_empty_required_strings():
    data = build_report().model_dump()
    data["title"] = ""

    with pytest.raises(ValidationError):
        InvestmentReport.model_validate(data)
```

因此最终测试函数应当使用这个版本。

---

### 八、完整测试文件中最终保留的版本

也就是说，`test_investment_report_rejects_empty_required_strings()` 使用：

```python
def test_investment_report_rejects_empty_required_strings():
    data = build_report().model_dump()
    data["title"] = ""

    with pytest.raises(ValidationError):
        InvestmentReport.model_validate(data)
```

而不是前面的 `model_copy()` 版本。

---

### 九、本课明确不做什么

Lesson 1 到这里就应该停止。

**不要现在做：**

```text
❌ Report Agent
❌ LLM
❌ Prompt
❌ Markdown
❌ HTML
❌ PDF
❌ Graph Node
❌ Graph State
❌ LangGraph Edge
❌ Persistence
❌ Checkpoint
❌ HITL
❌ API
❌ Memory
❌ Observability
```

尤其不要现在做：

```python
class ReportAgent(...)
```

因为这会把 **Domain Model** 和 **Report Generation Process** 混在一起。

我们下一阶段才会把：

```text
Phase 7 outputs
      ↓
deterministic report assembly
      ↓
InvestmentReport
```

建立起来。

---

### 十、本课验收条件

Lesson 1 完成后必须满足：

#### Domain

* [ ] 存在 `app/report/__init__.py`
* [ ] 存在 `app/report/models.py`
* [ ] 可以：

```python
from app.report import InvestmentReport
```

#### InvestmentReport

* [ ] `extra="forbid"`
* [ ] `ticker` 非空
* [ ] `title` 非空
* [ ] 所有 narrative summary 非空
* [ ] `valuation: ValuationResult`
* [ ] `risk_analysis: RiskAnalysis`
* [ ] `investment_decision: InvestmentDecision`

#### Architecture

* [ ] 不重复 `InvestmentDecision` 的业务字段
* [ ] 不重复 `ValuationResult` 的业务字段
* [ ] 不重复 `RiskAnalysis` 的业务字段
* [ ] 不重新计算 `expected_upside`
* [ ] 不创建 `ReportRecommendation`
* [ ] 不修改 Phase 7 Model

#### Scope

* [ ] 无 LLM
* [ ] 无 Agent
* [ ] 无 Graph
* [ ] 无 Markdown
* [ ] 无 Persistence
* [ ] 无 API

#### Tests

至少验证：

```text
✓ 可以构造 InvestmentReport
✓ 正确组合三个 Phase 7 Domain Models
✓ Phase 7 数据保持 source of truth
✓ 空字符串被拒绝
✓ extra fields 被拒绝
✓ Report 没有重复 Decision business fields
```

---