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


## Lesson 2：Deterministic Report Assembly

本课开始真正建立：

```text
Phase 7 Results
      ↓
Deterministic Assembly
      ↓
InvestmentReport
```

核心原则只有一个：

> **Lesson 2 不产生新的投资事实，只负责把已经存在的事实组织成 `InvestmentReport`。**

---

### 1. 本课完成后的架构

Phase 7 已经产生：

```text
CompanyResearchResult
FinancialResearchResult
MarketResearchResult
IndustryMacroResearchResult
          │
          ├──────────────┐
          │              │
          ▼              ▼
   ValuationResult   RiskAnalysis
          │              │
          └──────┬───────┘
                 ▼
        InvestmentDecision
                 │
                 ▼
       build_investment_report()
                 │
                 ▼
        ┌─────────────────┐
        │ InvestmentReport│
        └─────────────────┘
```

这里的 `build_investment_report()` 是一个**纯确定性函数**：

* 不调用 LLM
* 不调用 Agent
* 不调用 Graph
* 不进行网络请求
* 不进行估值计算
* 不重新计算风险
* 不重新生成投资决策

---

### 2. 创建 `app/report/assembly.py`

新建：

```text
app/report/assembly.py
```

完整代码：

```python
from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.investment.models import InvestmentDecision
from app.report.models import InvestmentReport
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult


def _validate_ticker_consistency(
    ticker: str,
    company_research: CompanyResearchResult,
    financial_research: FinancialResearchResult,
    market_research: MarketResearchResult,
    industry_macro_research: IndustryMacroResearchResult,
    valuation: ValuationResult,
    risk_analysis: RiskAnalysis,
    investment_decision: InvestmentDecision,
) -> None:
    """Ensure every Phase 7 result belongs to the same investment."""

    sources = {
        "company_research": company_research.ticker,
        "financial_research": financial_research.ticker,
        "market_research": market_research.ticker,
        "industry_macro_research": industry_macro_research.ticker,
        "valuation": valuation.ticker,
        "risk_analysis": risk_analysis.ticker,
        "investment_decision": investment_decision.ticker,
    }

    mismatches = {
        name: source_ticker
        for name, source_ticker in sources.items()
        if source_ticker != ticker
    }

    if mismatches:
        details = ", ".join(
            f"{name}={source_ticker}"
            for name, source_ticker in mismatches.items()
        )
        raise ValueError(
            f"All report inputs must use ticker '{ticker}'. "
            f"Mismatched inputs: {details}"
        )


def _validate_cross_domain_contract(
    valuation: ValuationResult,
    risk_analysis: RiskAnalysis,
    investment_decision: InvestmentDecision,
) -> None:
    """Ensure the existing Phase 7 cross-domain contracts remain consistent."""

    if (
        valuation.current_price
        != investment_decision.current_price
    ):
        raise ValueError(
            "Valuation current_price must match "
            "InvestmentDecision current_price."
        )

    if valuation.target_price != investment_decision.target_price:
        raise ValueError(
            "Valuation target_price must match "
            "InvestmentDecision target_price."
        )

    if valuation.expected_upside != investment_decision.expected_upside:
        raise ValueError(
            "Valuation expected_upside must match "
            "InvestmentDecision expected_upside."
        )

    if risk_analysis.key_risks != investment_decision.key_risks:
        raise ValueError(
            "RiskAnalysis key_risks must match "
            "InvestmentDecision key_risks."
        )


def build_investment_report(
    company_research: CompanyResearchResult,
    financial_research: FinancialResearchResult,
    market_research: MarketResearchResult,
    industry_macro_research: IndustryMacroResearchResult,
    valuation: ValuationResult,
    risk_analysis: RiskAnalysis,
    investment_decision: InvestmentDecision,
) -> InvestmentReport:
    """
    Deterministically assemble Phase 7 results into an InvestmentReport.

    This function does not create new business facts. It only validates
    existing cross-domain contracts and maps existing results into the
    report domain.
    """

    ticker = investment_decision.ticker

    _validate_ticker_consistency(
        ticker=ticker,
        company_research=company_research,
        financial_research=financial_research,
        market_research=market_research,
        industry_macro_research=industry_macro_research,
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )

    _validate_cross_domain_contract(
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )

    return InvestmentReport(
        ticker=ticker,
        title=f"{ticker} Investment Research Report",
        executive_summary=investment_decision.investment_thesis,
        company_overview=company_research.summary,
        financial_summary=financial_research.summary,
        market_summary=market_research.summary,
        industry_macro_summary=industry_macro_research.summary,
        valuation_summary=(
            f"Valuation target price: "
            f"{valuation.target_price:.2f}; "
            f"current price: "
            f"{valuation.current_price:.2f}; "
            f"expected upside: "
            f"{valuation.expected_upside:.2%}."
        ),
        risk_summary=(
            f"Overall risk level: "
            f"{risk_analysis.overall_risk_level.value}. "
            f"Key risks: "
            f"{', '.join(risk_analysis.key_risks)}."
        ),
        investment_decision_summary=(
            f"Recommendation: "
            f"{investment_decision.recommendation.value}; "
            f"horizon: "
            f"{investment_decision.investment_horizon.value}; "
            f"conviction: "
            f"{investment_decision.conviction.value}."
        ),
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )
```

---

### 3. 为什么采用显式参数？

这里特意没有设计：

```python
class ReportInput(BaseModel):
    ...
```

然后：

```python
build_investment_report(report_input)
```

原因是当前 Phase 7 已经有明确的 Domain Models：

```text
CompanyResearchResult
FinancialResearchResult
MarketResearchResult
IndustryMacroResearchResult
ValuationResult
RiskAnalysis
InvestmentDecision
```

如果现在为了 assembler 再创造：

```python
ReportInput
```

实际上是在增加一个没有业务含义的中间 Domain。

目前没有必要。

所以我们让函数直接表达它真正需要什么：

```python
build_investment_report(
    company_research,
    financial_research,
    market_research,
    industry_macro_research,
    valuation,
    risk_analysis,
    investment_decision,
)
```

这也让依赖关系非常清晰。

---

### 4. 为什么需要 `_validate_ticker_consistency()`？

这是工业级 Agent 系统里非常重要的一层防护。

理论上所有结果都应该属于：

```text
NVDA
```

但如果未来某个 Agent 出现：

```text
CompanyResearchResult       → NVDA
FinancialResearchResult     → NVDA
MarketResearchResult        → NVDA
IndustryMacroResearchResult → NVDA
ValuationResult             → NVDA
RiskAnalysis                → NVDA
InvestmentDecision          → AAPL
```

我们绝对不能继续生成：

```text
NVDA Investment Research Report
```

因为那会产生跨股票污染。

因此 assembler 是一个很合适的**Domain Boundary Validation Point**。

---

### 5. 为什么还需要 `_validate_cross_domain_contract()`？

因为 Phase 7 已经建立了明确的跨 Domain Contract。

例如：

```text
Valuation
    │
    ├── current_price
    ├── target_price
    └── expected_upside
              │
              ▼
     InvestmentDecision
```

所以：

```python
valuation.current_price
```

和：

```python
investment_decision.current_price
```

必须一致。

同样：

```text
RiskAnalysis.key_risks
            │
            ▼
InvestmentDecision.key_risks
```

也必须一致。

这里**不是重新计算这些数据**。

我们只是检查：

> Phase 7 已经建立的 Contract 在进入 Report Domain 时仍然成立。

---

### 6. 一个非常重要的设计点：Executive Summary

这里我让：

```python
executive_summary=investment_decision.investment_thesis
```

而不是重新生成一段新的文本。

这是故意的。

因为目前还没有：

```text
Report LLM
```

也没有：

```text
Report Writer
```

因此 Lesson 2 阶段不应该假装自己具备高级报告写作能力。

当前：

```text
InvestmentDecision.investment_thesis
                 ↓
          executive_summary
```

只是一个**确定性映射**。

未来 Lesson 3/后续 Report Generation 阶段，如果需要 LLM 进行真正的报告写作，我们再明确引入：

```text
Structured facts
      ↓
Report generation
      ↓
Narrative
```

而不是现在提前把两层混在一起。

---

### 7. 三个 Summary 的来源

当前采用：

#### Company

```python
company_overview = company_research.summary
```

#### Financial

```python
financial_summary = financial_research.summary
```

#### Market

```python
market_summary = market_research.summary
```

#### Industry / Macro

```python
industry_macro_summary = industry_macro_research.summary
```

这四个完全是 Phase 7 已经存在的研究结果。

---

#### Valuation Summary

这里采用确定性模板：

```text
Valuation target price: 216.00;
current price: 180.00;
expected upside: 20.00%.
```

这些数字全部来自：

```python
ValuationResult
```

没有重新计算。

---

#### Risk Summary

同样：

```text
Overall risk level: High.
Key risks: Valuation Multiple Compression, Competitive Pressure.
```

来源：

```python
RiskAnalysis
```

---

#### Investment Decision Summary

来源：

```python
InvestmentDecision
```

例如：

```text
Recommendation: Buy;
horizon: Medium Term;
conviction: Medium.
```

---

### 8. 创建 Lesson 2 测试

新建：

```text
tests/test_report_assembly.py
```

建议完整使用下面的测试：

```python
import pytest

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.investment.models import (
    InvestmentConviction,
    InvestmentDecision,
    InvestmentHorizon,
    InvestmentRecommendation,
)
from app.report.assembly import build_investment_report
from app.report.models import InvestmentReport
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
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


def make_company_research(
    ticker: str = "NVDA",
) -> CompanyResearchResult:
    return CompanyResearchResult(
        ticker=ticker,
        company_name="NVIDIA Corporation",
        sector="Semiconductors",
        current_price=180.0,
        summary=(
            "NVIDIA designs GPUs and accelerated computing platforms."
        ),
    )


def make_financial_research(
    ticker: str = "NVDA",
) -> FinancialResearchResult:
    return FinancialResearchResult(
        ticker=ticker,
        revenue=100.0,
        net_income=30.0,
        profit_margin=0.30,
        summary="The company has strong financial performance.",
    )


def make_market_research(
    ticker: str = "NVDA",
) -> MarketResearchResult:
    return MarketResearchResult(
        ticker=ticker,
        market_index="NASDAQ",
        market_return=0.08,
        summary="The broader technology market remains positive.",
    )


def make_industry_macro_research(
    ticker: str = "NVDA",
) -> IndustryMacroResearchResult:
    return IndustryMacroResearchResult(
        ticker=ticker,
        industry="Semiconductors",
        industry_growth=0.15,
        macro_environment="Growth-oriented technology environment",
        macro_growth=0.03,
        summary="AI infrastructure supports semiconductor demand.",
    )


def make_valuation(
    ticker: str = "NVDA",
) -> ValuationResult:
    return ValuationResult(
        ticker=ticker,
        method=ValuationMethod.PE,
        inputs=ValuationInputs(
            earnings_per_share=6.0,
        ),
        assumptions=ValuationAssumptions(
            multiple=36.0,
            rationale="Illustrative P/E multiple assumption.",
        ),
        implied_value_per_share=216.0,
        target_price=216.0,
        current_price=180.0,
        expected_upside=0.20,
        metadata=ValuationMetadata(
            currency="USD",
            model_version="phase7-v1",
        ),
    )


def make_risk_analysis(
    ticker: str = "NVDA",
) -> RiskAnalysis:
    return RiskAnalysis(
        ticker=ticker,
        risks=[
            RiskItem(
                category=RiskCategory.VALUATION,
                title="Valuation Multiple Compression",
                description=(
                    "A contraction in the valuation multiple "
                    "could reduce expected returns."
                ),
                severity=RiskSeverity.HIGH,
                likelihood=RiskLikelihood.MEDIUM,
                impact=RiskImpact.HIGH,
                evidence=[
                    "The valuation relies on an assumed P/E multiple."
                ],
            )
        ],
        overall_risk_level=RiskSeverity.HIGH,
        key_risks=[
            "Valuation Multiple Compression",
        ],
        uncertainty_notes=[
            "Long-term demand remains uncertain.",
        ],
    )


def make_investment_decision(
    ticker: str = "NVDA",
    key_risks: list[str] | None = None,
) -> InvestmentDecision:
    if key_risks is None:
        key_risks = [
            "Valuation Multiple Compression",
        ]

    return InvestmentDecision(
        ticker=ticker,
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=180.0,
        target_price=216.0,
        expected_upside=0.20,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis=(
            "Strong financial performance and industry conditions "
            "support the investment thesis."
        ),
        key_catalysts=[
            "Continued AI infrastructure investment",
        ],
        key_risks=key_risks,
        invalidation_conditions=[
            "Material deterioration in growth expectations",
        ],
        supporting_evidence=[
            "Strong financial performance",
            "Valuation target above current price",
        ],
    )


def build_inputs():
    return {
        "company_research": make_company_research(),
        "financial_research": make_financial_research(),
        "market_research": make_market_research(),
        "industry_macro_research": make_industry_macro_research(),
        "valuation": make_valuation(),
        "risk_analysis": make_risk_analysis(),
        "investment_decision": make_investment_decision(),
    }


def test_build_investment_report_returns_report():
    report = build_investment_report(**build_inputs())

    assert isinstance(report, InvestmentReport)
    assert report.ticker == "NVDA"


def test_build_investment_report_maps_research_summaries():
    report = build_investment_report(**build_inputs())

    assert report.company_overview == (
        "NVIDIA designs GPUs and accelerated computing platforms."
    )
    assert report.financial_summary == (
        "The company has strong financial performance."
    )
    assert report.market_summary == (
        "The broader technology market remains positive."
    )
    assert report.industry_macro_summary == (
        "AI infrastructure supports semiconductor demand."
    )


def test_build_investment_report_preserves_domain_objects():
    inputs = build_inputs()

    report = build_investment_report(**inputs)

    assert report.valuation is inputs["valuation"]
    assert report.risk_analysis is inputs["risk_analysis"]
    assert report.investment_decision is inputs["investment_decision"]


def test_build_investment_report_preserves_phase7_facts():
    report = build_investment_report(**build_inputs())

    assert report.valuation.current_price == 180.0
    assert report.valuation.target_price == 216.0
    assert report.valuation.expected_upside == 0.20

    assert (
        report.investment_decision.recommendation
        == InvestmentRecommendation.BUY
    )
    assert (
        report.investment_decision.investment_horizon
        == InvestmentHorizon.MEDIUM_TERM
    )
    assert (
        report.investment_decision.conviction
        == InvestmentConviction.MEDIUM
    )

    assert report.risk_analysis.key_risks == [
        "Valuation Multiple Compression",
    ]


def test_build_investment_report_rejects_ticker_mismatch():
    inputs = build_inputs()
    inputs["valuation"] = make_valuation(ticker="AAPL")

    with pytest.raises(ValueError, match="ticker"):
        build_investment_report(**inputs)


def test_build_investment_report_rejects_valuation_decision_mismatch():
    inputs = build_inputs()

    inputs["investment_decision"] = InvestmentDecision(
        ticker="NVDA",
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=180.0,
        target_price=225.0,
        expected_upside=0.25,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis="Test thesis.",
        key_catalysts=["Test catalyst."],
        key_risks=["Valuation Multiple Compression"],
        invalidation_conditions=["Test invalidation."],
        supporting_evidence=["Test evidence."],
    )

    with pytest.raises(
        ValueError,
        match="target_price",
    ):
        build_investment_report(**inputs)


def test_build_investment_report_rejects_risk_decision_mismatch():
    inputs = build_inputs()

    inputs["investment_decision"] = make_investment_decision(
        key_risks=["Different risk"],
    )

    with pytest.raises(
        ValueError,
        match="key_risks",
    ):
        build_investment_report(**inputs)
```

---

### 9. 为什么测试 `is` 而不是只测试 `==`？

这里：

```python
assert report.valuation is inputs["valuation"]
```

而不是：

```python
assert report.valuation == inputs["valuation"]
```

这是有意的。

我们希望明确证明：

> Assembly 没有重新构造一个新的 `ValuationResult`。

而是：

```text
Phase 7 ValuationResult
          │
          │ same object
          ▼
InvestmentReport.valuation
```

同理：

```python
report.risk_analysis is inputs["risk_analysis"]
report.investment_decision is inputs["investment_decision"]
```

这进一步强化了 Source of Truth 的设计。

---

### 10. 一个值得注意的地方：没有加入 `current_price` 参数

你可能会注意到：

```python
build_investment_report(...)
```

没有：

```python
current_price
target_price
expected_upside
recommendation
```

这是正确的。

因为这些东西已经包含在：

```text
ValuationResult
InvestmentDecision
```

中。

如果 assembler 接受：

```python
current_price=180
```

就会产生：

```text
ValuationResult.current_price = 180
        │
        ├── assembler.current_price = 180
        │
        └── InvestmentDecision.current_price = 180
```

这会增加冗余输入和不一致的可能。

---

### 11. Lesson 2 的职责边界

现在我们已经形成一个非常清晰的分层：

#### Phase 7

负责：

```text
Research
Valuation
Risk
Investment Decision
```

---

#### Phase 8 Lesson 1

负责：

```text
InvestmentReport Domain Model
```

---

#### Phase 8 Lesson 2

负责：

```text
Phase 7 Results
       ↓
validate contracts
       ↓
assemble
       ↓
InvestmentReport
```

---

#### 后续 Report Generation

才负责：

```text
InvestmentReport
       ↓
Report generation
       ↓
Markdown / HTML / PDF / ...
```

这条边界非常重要。

---

### 12. 本课验收条件

Lesson 2 完成后必须满足：

#### Assembly

* [ ] 存在 `app/report/assembly.py`
* [ ] 存在 `build_investment_report()`
* [ ] 函数是确定性的
* [ ] 不调用 LLM
* [ ] 不调用 Agent
* [ ] 不调用 Graph
* [ ] 不进行外部 I/O

#### Data Integrity

* [ ] 所有输入 ticker 必须一致
* [ ] `ValuationResult.current_price` 与 `InvestmentDecision.current_price` 一致
* [ ] `target_price` 一致
* [ ] `expected_upside` 一致
* [ ] `RiskAnalysis.key_risks` 与 `InvestmentDecision.key_risks` 一致

#### Source of Truth

* [ ] Report 使用原有 `ValuationResult`
* [ ] Report 使用原有 `RiskAnalysis`
* [ ] Report 使用原有 `InvestmentDecision`
* [ ] 不复制这些 Domain Model 的业务字段
* [ ] 不重新计算 `expected_upside`

#### Research Mapping

* [ ] Company summary → `company_overview`
* [ ] Financial summary → `financial_summary`
* [ ] Market summary → `market_summary`
* [ ] Industry/Macro summary → `industry_macro_summary`

#### Tests

至少通过：

```text
✓ report assembly
✓ research summary mapping
✓ domain object preservation
✓ Phase 7 fact preservation
✓ ticker mismatch rejection
✓ valuation/decision mismatch rejection
✓ risk/decision mismatch rejection
```

---

