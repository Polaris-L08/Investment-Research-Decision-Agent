# Phase 8 —— Report


> InvestmentReport 是结构化的 Report Domain 对象，它承载 Research、Valuation、Risk 和 InvestmentDecision 的最终分析结果；
> LLM 在其上负责将这些已经确定的事实和结论组织成自然语言叙事，而 Renderer 再将完整的 Report 转换成 Markdown、HTML、PDF 等最终用户可读形式。

> InvestmentReport → LLM 生成 narrative → merge 回完整 Report → Renderer 生成最终用户可读文档。

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




好的。准备工作完成后，Lesson 3 重新开始，而且这次把刚才暴露出的架构问题彻底修正。

我检查了 Phase 7 的实际代码，确认项目已经有成熟的 LLM + Structured Output 模式：

```python
structured_llm = llm.with_structured_output(SomePydanticModel)
result = structured_llm.invoke(prompt)
```

Phase 7 的 `InvestmentDecision` 就是这样实现的。因此 **Lesson 3 不需要重新设计 LLM 基础设施**，应该复用现有 `app.llm.client.llm`。

同时，我确认了一个比上一版 `ReportNarrative` 更合理的方案：

> **LLM Output Schema 不应该复制 `InvestmentReport` 的字段。**

我们采用“报告章节列表”的形式作为 LLM 输出协议。

---


## Lesson 3： Report Agent

### Goal

建立真正的 **Report Agent 的 LLM Narrative Boundary**。

本 Lesson 最终要实现：

```text
Research
   │
Valuation
   │
Risk
   │
InvestmentDecision
   │
   ▼
InvestmentReport
   │
   ▼
LLM Narrative Generation
   │
   ▼
Narrative Output
   │
   ▼
Deterministic Merge
   │
   ▼
Final InvestmentReport
```

但今天第一步**只建立 LLM Narrative 的 Structured Output Contract**。

---

### Lesson 3 的完整拆分

为了避免架构一下子变得复杂，本课我们拆成：

```text
Lesson 3.1
    LLM Narrative Boundary
        ↓
    Structured Output Schema
        ↓
    Model Tests

Lesson 3.2
    Report Narrative Generation
        ↓
    LLM Prompt
        ↓
    Report Agent Node

Lesson 3.3
    Narrative Validation
        ↓
    Section Completeness
        ↓
    Source Consistency

Lesson 3.4
    Narrative → InvestmentReport
        ↓
    Deterministic Merge

Lesson 3.5
    LLM Mock / Failure Tests
        ↓
    Error Handling

Lesson 3 Acceptance
```

**现在只做 Lesson 3.1。**

---

### Lesson 3.1 — LLM Narrative Boundary

#### 1. 为什么现在需要一个 Boundary Schema？

我们已经有：

```text
InvestmentReport
```

它是 Report Domain Model。

但是我们不能直接让 LLM 输出：

```python
InvestmentReport
```

因为这意味着 LLM 可以直接生成：

```text
valuation
risk_analysis
investment_decision
```

这些 Domain Object。

这是错误的。

例如 LLM 如果直接生成：

```json
{
    "target_price": 230,
    "recommendation": "Strong Buy"
}
```

就可能改变原本：

```text
target_price = 220
recommendation = Buy
```

的 Domain Facts。

因此我们需要明确：

```text
InvestmentReport
        │
        │ read-only input
        ▼
       LLM
        │
        │ narrative only
        ▼
Narrative Output
```

---

#### 2. 为什么不创建第二个完整的 `ReportNarrative` Domain Model？

之前我们讨论过一个问题：

如果这样：

```python
class ReportNarrative(BaseModel):
    executive_summary: str
    company_overview: str
    financial_summary: str
    ...
```

那么它实际上又复制了一遍：

```python
InvestmentReport
```

这会造成两个模型之间长期同步的问题。

所以我们采用：

> **Section-based Structured Output Boundary**

也就是：

```text
ReportNarrativeOutput
        │
        └── sections[]
                │
                ├── section_id
                └── content
```

而不是复制整个 Report Schema。

---

#### 3. 新增文件

创建：

```text
app/report/generate.py
```

内容：

```python
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReportSectionId(str, Enum):
    """Identifiers for narrative sections in an investment report."""

    EXECUTIVE_SUMMARY = "executive_summary"
    COMPANY_OVERVIEW = "company_overview"
    FINANCIAL_SUMMARY = "financial_summary"
    MARKET_SUMMARY = "market_summary"
    INDUSTRY_MACRO_SUMMARY = "industry_macro_summary"
    VALUATION_SUMMARY = "valuation_summary"
    RISK_SUMMARY = "risk_summary"
    INVESTMENT_DECISION_SUMMARY = "investment_decision_summary"


class ReportSection(BaseModel):
    """A single LLM-generated narrative section."""

    model_config = ConfigDict(extra="forbid")

    section_id: ReportSectionId = Field(
        description="Identifier of the report section."
    )

    content: str = Field(
        min_length=1,
        description="Human-readable narrative content for the section.",
    )


class ReportNarrativeOutput(BaseModel):
    """Structured output boundary for LLM-generated report narrative."""

    model_config = ConfigDict(extra="forbid")

    sections: list[ReportSection] = Field(
        min_length=1,
        description="Narrative sections generated by the report LLM.",
    )
```

---

#### 4. 这里有一个非常重要的设计点

注意：

```python
ReportNarrativeOutput
```

**不是 Report Domain Model。**

它的性质是：

```text
LLM Structured Output Boundary
```

也可以理解成：

```text
LLM DTO
```

它存在的原因只是：

> 限制 LLM 能够输出什么。

所以它的生命周期是：

```text
LLM
 ↓
ReportNarrativeOutput
 ↓
Validation
 ↓
InvestmentReport
```

而不是：

```text
ReportNarrativeOutput
        ↓
永远存在的第二个 Report Domain
```

---

#### 5. 为什么使用 `section_id`？

因为我们希望 LLM 的输出和 `InvestmentReport` 建立**显式映射**：

```text
ReportSectionId.EXECUTIVE_SUMMARY
        ↓
InvestmentReport.executive_summary
```

```text
ReportSectionId.COMPANY_OVERVIEW
        ↓
InvestmentReport.company_overview
```

等等。

这样后面 Lesson 3.4 可以做：

```text
LLM Output
    ↓
deterministic mapping
    ↓
InvestmentReport
```

而不是依赖：

```text
sections[0]
sections[1]
sections[2]
```

这种脆弱的 positional mapping。

---

#### 6. 为什么 `section_id` 使用 Enum？

因为我们不希望 LLM 返回：

```text
"executive summary"
```

或者：

```text
"Executive Summary"
```

或者：

```text
"summary"
```

然后我们再猜它到底对应哪个字段。

我们直接定义有限集合：

```python
class ReportSectionId(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    ...
```

于是 Structured Output 层就可以约束：

```text
section_id
    ↓
必须是已知 Section
```

这也是目前项目一直采用的：

```text
Enum
+
Pydantic
+
Structured Output
```

模式的延续。

---

#### 7. 先不要加入这些东西

Lesson 3.1 **暂时不要**加入：

```text
❌ LLM Client
❌ Prompt
❌ LangGraph Node
❌ Graph
❌ InvestmentReport Merge
❌ Markdown
❌ HTML
❌ PDF
❌ retry
❌ fallback
```

原因很简单：

> 我们先把 LLM Boundary Contract 固定下来。

这是后续 Agent 实现的基础。

---

#### 8. Lesson 3.1 测试

新增：

```text
tests/test_report_narrative.py
```

完整内容：

```python
import pytest
from pydantic import ValidationError

from app.report.narrative import (
    ReportNarrativeOutput,
    ReportSection,
    ReportSectionId,
)


def test_report_section_can_be_constructed():
    section = ReportSection(
        section_id=ReportSectionId.EXECUTIVE_SUMMARY,
        content="Apple presents a positive medium-term investment profile.",
    )

    assert section.section_id == ReportSectionId.EXECUTIVE_SUMMARY
    assert section.content == (
        "Apple presents a positive medium-term investment profile."
    )


def test_report_narrative_output_can_be_constructed():
    output = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=ReportSectionId.EXECUTIVE_SUMMARY,
                content="Apple presents a positive investment profile.",
            ),
            ReportSection(
                section_id=ReportSectionId.VALUATION_SUMMARY,
                content="The valuation implies meaningful upside.",
            ),
        ]
    )

    assert len(output.sections) == 2
    assert output.sections[0].section_id == (
        ReportSectionId.EXECUTIVE_SUMMARY
    )
    assert output.sections[1].section_id == (
        ReportSectionId.VALUATION_SUMMARY
    )


def test_report_section_rejects_empty_content():
    with pytest.raises(ValidationError):
        ReportSection(
            section_id=ReportSectionId.EXECUTIVE_SUMMARY,
            content="",
        )


def test_report_section_rejects_extra_fields():
    with pytest.raises(ValidationError):
        ReportSection(
            section_id=ReportSectionId.EXECUTIVE_SUMMARY,
            content="Valid content.",
            unexpected_field="not allowed",
        )


def test_report_narrative_output_rejects_extra_fields():
    with pytest.raises(ValidationError):
        ReportNarrativeOutput(
            sections=[
                ReportSection(
                    section_id=ReportSectionId.EXECUTIVE_SUMMARY,
                    content="Valid content.",
                )
            ],
            unexpected_field="not allowed",
        )


def test_report_narrative_output_requires_at_least_one_section():
    with pytest.raises(ValidationError):
        ReportNarrativeOutput(sections=[])


def test_report_section_rejects_unknown_section_id():
    with pytest.raises(ValidationError):
        ReportSection(
            section_id="unknown_section",
            content="Some content.",
        )
```

---

#### 9. 这里暂时不测试“8 个 Section 必须全部存在”

你可能会发现：

```python
ReportNarrativeOutput(
    sections=[
        ...
    ]
)
```

现在允许只返回：

```text
EXECUTIVE_SUMMARY
VALUATION_SUMMARY
```

而不是强制：

```text
8 / 8 sections
```

这是**故意的**。

因为：

```text
Schema Validation
```

和：

```text
Business Completeness Validation
```

是两个不同的问题。

现在 Lesson 3.1 只负责：

> “这个东西是不是合法的 Narrative Output？”

后面的 Lesson 3.3 才负责：

> “一个完整的 InvestmentReport 是否要求这 8 个 section 全部存在？”

也就是说：

```text
Pydantic
   ↓
Structural Validation
```

而：

```text
Report Validator
   ↓
Semantic / Business Validation
```

两者不要混在一起。

---

#### 10. 当前 Report Domain 的关系

完成 Lesson 3.1 后，架构应该变成：

```text
                 InvestmentReport
                /       |        \
               /        |         \
        Valuation   RiskAnalysis   InvestmentDecision
              \         |          /
               \        |         /
                \       |        /
                 Report Domain
                       │
                       │ read-only
                       ▼
                     LLM
                       │
                       ▼
            ReportNarrativeOutput
                       │
                       ▼
              deterministic validation
                       │
                       ▼
              deterministic merge
                       │
                       ▼
                InvestmentReport
```

注意这里存在一个很重要的闭环：

```text
InvestmentReport
       ↓
    LLM reads
       ↓
NarrativeOutput
       ↓
 merge
       ↓
InvestmentReport
```

但**不是 LLM 自己修改 `InvestmentReport`**。

---

#### Lesson 3.1 Acceptance Criteria

这一小节完成的验收标准是：

##### A. Model

必须存在：

```text
app/report/narrative.py
```

并包含：

```text
ReportSectionId
ReportSection
ReportNarrativeOutput
```

---

##### B. Boundary

`ReportNarrativeOutput`：

```text
只能表达 narrative
```

不能直接表达：

```text
ValuationResult
RiskAnalysis
InvestmentDecision
```

---

##### C. Structural Validation

以下必须被拒绝：

```text
empty content
unknown section_id
extra fields
empty sections
```

---

##### D. Tests

执行：

```bash
pytest -q tests/test_report_narrative.py
```

预期：

```text
7 passed
```

---

##### E. Scope

本阶段**不应该出现**：

```text
LLM invocation
Graph
Report Agent Node
Markdown
HTML
PDF
```

---



### Lesson 3.2 — Report Narrative Generation

这一节完成三个目标：

1. 建立 **Report Generation Agent 的 State Contract**
2. 使用现有 `llm.with_structured_output(...)` 生成 `ReportNarrativeOutput`
3. 建立独立的 `report_generation_graph`

**本节仍然不做 Narrative → `InvestmentReport` Merge。**

---

#### 一、先确定 Lesson 3.2 的最终架构

我们现有项目的 Agent 模式是：

```text
Input State
    ↓
Agent Node
    ↓
Structured LLM
    ↓
Output State
```

因此 Report Agent 也完全采用相同模式：

```text
InvestmentReport
      │
      ▼
ReportGenerationInputState
      │
      ▼
generate_report_narrative
      │
      ▼
llm.with_structured_output(
    ReportNarrativeOutput
)
      │
      ▼
ReportGenerationOutputState
```

最终形成：

```text
report_generation_graph
```

它是一个**独立的 Report Domain Graph**。

暂时不要把它接到：

```text
app/graph/graph.py
```

主 Graph 中。

原因是 Lesson 3 还没有完成完整的：

```text
Generation
    ↓
Validation
    ↓
Merge
```

现在接入主 Graph 会过早。

---

#### 二、修改 `app/report/generation.py`

你现在已经把：

```text
app/report/narrative.py
```

改成了：

```text
app/report/generation.py
```

很好。

现在我们在这个文件基础上继续扩展。

完整文件建议如下：

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.llm.client import llm
from app.report.models import InvestmentReport


from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReportSectionId(str, Enum):
    """Identifiers for narrative sections in an investment report."""

    EXECUTIVE_SUMMARY = "executive_summary"
    COMPANY_OVERVIEW = "company_overview"
    FINANCIAL_SUMMARY = "financial_summary"
    MARKET_SUMMARY = "market_summary"
    INDUSTRY_MACRO_SUMMARY = "industry_macro_summary"
    VALUATION_SUMMARY = "valuation_summary"
    RISK_SUMMARY = "risk_summary"
    INVESTMENT_DECISION_SUMMARY = "investment_decision_summary"


class ReportSection(BaseModel):
    """A single LLM-generated narrative section."""

    model_config = ConfigDict(extra="forbid")

    section_id: ReportSectionId = Field(
        description="Identifier of the report section."
    )

    content: str = Field(
        min_length=1,
        description="Human-readable narrative content for the section.",
    )


class ReportNarrativeOutput(BaseModel):
    """Structured output boundary for LLM-generated report narrative."""

    model_config = ConfigDict(extra="forbid")

    sections: list[ReportSection] = Field(
        min_length=1,
        description="Narrative sections generated by the report LLM.",
    )


class ReportGenerationInputState(TypedDict):
    """Input contract for the report generation graph."""

    report: InvestmentReport


class ReportGenerationState(TypedDict, total=False):
    """Internal state used by the report generation graph."""

    report: InvestmentReport
    narrative: ReportNarrativeOutput | None
    generation_error: str | None


class ReportGenerationOutputState(TypedDict):
    """Output contract for the report generation graph."""

    narrative: ReportNarrativeOutput | None
    generation_error: str | None


def generate_report_narrative(
    state: ReportGenerationState,
) -> dict:
    """Generate human-readable report narrative from an InvestmentReport."""

    structured_report_llm = llm.with_structured_output(
        ReportNarrativeOutput
    )

    report = state["report"]

    prompt = f"""
You are an investment research report generation agent.

Your task is to transform the supplied structured investment analysis
into clear, professional, human-readable report narrative.

The supplied InvestmentReport and its nested domain objects are the
source of truth.

You must faithfully represent the supplied facts and conclusions.

You must NOT:
- perform new web searches;
- invent facts;
- invent financial data;
- perform a new valuation;
- change the current price;
- change the target price;
- change the expected upside;
- change the investment recommendation;
- change the investment horizon;
- change the conviction level;
- change the risk analysis;
- create new investment risks that are not supported by the input;
- create a new investment thesis;
- make a new investment decision.

You are responsible only for narrative generation.

The output must contain exactly one narrative section for each of
the following section identifiers:

1. executive_summary
2. company_overview
3. financial_summary
4. market_summary
5. industry_macro_summary
6. valuation_summary
7. risk_summary
8. investment_decision_summary

Each section must contain clear, concise, professional prose
appropriate for an investment research report.

InvestmentReport:

{report.model_dump_json(indent=2)}

Narrative generation requirements:

1. Preserve all important numerical facts from the supplied analysis.
2. Preserve the supplied valuation conclusion.
3. Preserve the supplied risk conclusions.
4. Preserve the supplied investment recommendation.
5. Preserve the supplied investment horizon and conviction.
6. Explain the analysis in natural language rather than merely
   repeating raw JSON.
7. Do not introduce unsupported claims.
8. Do not output Markdown headings.
9. Return only the structured narrative sections required by the schema.
"""

    try:
        narrative = structured_report_llm.invoke(prompt)

        return {
            "narrative": narrative,
            "generation_error": None,
        }

    except Exception as exc:
        return {
            "narrative": None,
            "generation_error": str(exc),
        }


def build_report_generation_graph():
    """Build and compile the report generation graph."""

    graph = StateGraph(
        ReportGenerationState,
        input_schema=ReportGenerationInputState,
        output_schema=ReportGenerationOutputState,
    )

    graph.add_node(
        "generate_report_narrative",
        generate_report_narrative,
    )

    graph.add_edge(
        START,
        "generate_report_narrative",
    )

    graph.add_edge(
        "generate_report_narrative",
        END,
    )

    return graph.compile()


report_generation_graph = build_report_generation_graph()
```

---

#### 三、这里有一个代码风格调整

上面的代码为了展示完整文件，把 import 分成了两段。

实际项目中请整理成：

```python
from enum import Enum
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.llm.client import llm
from app.report.models import InvestmentReport
```

也就是最终文件顶部应该是：

```python
from enum import Enum
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.llm.client import llm
from app.report.models import InvestmentReport
```

---

#### 四、为什么 `InvestmentReport` 是唯一 Input？

这一点非常重要。

我们没有设计：

```python
class ReportGenerationInputState(TypedDict):
    ticker: str
    valuation: ValuationResult
    risk_analysis: RiskAnalysis
    investment_decision: InvestmentDecision
```

而是：

```python
class ReportGenerationInputState(TypedDict):
    report: InvestmentReport
```

原因是：

> **Report Agent 的输入边界就是 Report Domain Boundary。**

上游发生什么，不应该继续暴露给 Report Agent。

因此：

```text
Research
Valuation
Risk
Decision
        ↓
InvestmentReport
        ↓
Report Agent
```

而不是：

```text
Research ──────┐
Valuation ─────┤
Risk ──────────┤
Decision ──────┤
                ↓
            Report Agent
```

这就是前面为什么要先建立 `InvestmentReport`。

---

#### 五、为什么 LLM 直接看到整个 `InvestmentReport`？

这是当前阶段合理的。

因为：

```python
report.model_dump_json(indent=2)
```

会提供：

```text
ticker
title
executive_summary
company_overview
...
valuation
risk_analysis
investment_decision
```

LLM 可以看到：

##### Valuation

例如：

```json
{
  "current_price": 180,
  "target_price": 220,
  "expected_upside": 0.222
}
```

##### Risk

例如：

```json
{
  "overall_risk_level": "...",
  "key_risks": [...]
}
```

##### Decision

例如：

```json
{
  "recommendation": "Buy",
  "investment_horizon": "Medium Term",
  "conviction": "Medium"
}
```

因此它有足够的信息进行**叙事转换**。

---

#### 六、为什么 Prompt 里反复强调不能改变事实？

这是故意的。

例如：

```text
Valuation:
target_price = 220
```

LLM 可能自然地产生：

> “The valuation suggests a target price of approximately $225...”

从语言模型角度，这并不奇怪。

但对我们的系统来说，这是**数据一致性错误**。

所以我们明确告诉它：

```text
The supplied InvestmentReport and its nested domain objects
are the source of truth.
```

以及：

```text
You must NOT:
...
change the target price;
change the expected upside;
change the investment recommendation;
...
```

---

#### 七、为什么还要求“不输出 Markdown headings”？

因为：

```text
Generation
```

和：

```text
Rendering
```

必须分离。

LLM 负责：

```text
"Apple continues to demonstrate..."
```

而不是：

```markdown
## Company Overview

Apple continues to demonstrate...
```

后面 Renderer 再决定：

```text
Markdown
HTML
PDF
```

具体应该怎样排版。

所以：

```text
LLM
 ↓
Narrative
```

而：

```text
Renderer
 ↓
Presentation
```

这两个职责不能混。

---

#### 八、Graph Topology

Lesson 3.2 完成后：

```text
┌──────────────────────────┐
│ InvestmentReport         │
└────────────┬─────────────┘
             │
             ▼
        START
             │
             ▼
┌──────────────────────────┐
│ generate_report_narrative│
│                          │
│ structured LLM           │
│        ↓                 │
│ ReportNarrativeOutput    │
└────────────┬─────────────┘
             │
             ▼
            END
```

这是一个标准的：

```text
START → Agent → END
```

Graph。

和当前：

```text
Risk
InvestmentDecision
IndustryMacroResearch
```

等 Agent 的结构一致。

---

#### 九、但是现在还没有 Merge

这是本 Lesson 最容易产生误解的地方。

当前：

```text
InvestmentReport
       │
       ▼
      LLM
       │
       ▼
ReportNarrativeOutput
```

到这里就停止。

**不要做：**

```python
report.executive_summary = narrative...
```

也不要：

```python
return InvestmentReport(...)
```

因为那属于 **Lesson 3.4：Deterministic Merge**。

当前 Lesson 的职责只是：

> **证明 Report Agent 能够从 Report Domain Boundary 生成受约束的 Narrative Boundary。**

---

#### 十、测试：不调用真实 LLM

这一点非常重要。

我们现在不能让测试：

```text
pytest
   ↓
OpenAI API
   ↓
LLM
```

否则：

* 测试不稳定
* 需要 API Key
* 测试成本不可控
* LLM 输出具有非确定性

因此 Lesson 3.2 必须使用 Mock。

---

#### 十一、创建测试文件

如果你已经有：

```text
tests/test_report_narrative.py
```

可以把它扩展成：

```text
tests/test_report_generation.py
```

建议**单独建立**：

```text
tests/test_report_generation.py
```

这样：

```text
test_report_narrative.py
```

负责：

> Boundary Model

而：

```text
test_report_generation.py
```

负责：

> Agent / Graph

---

#### 十二、测试数据

我们需要一个最小合法 `InvestmentReport`。

可以在测试文件中建立 fixture：

```python
import pytest

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
```

但是注意：

**当前 `InvestmentReport` 本身并不直接保存这些 Research Result。**

所以我们实际上不需要为了 Generation Test 再构造 Research Objects。

直接构造：

```python
ValuationResult
RiskAnalysis
InvestmentDecision
```

即可。

---

#### 十三、推荐测试代码

创建：

```text
tests/test_report_generation.py
```

内容：

```python
from types import SimpleNamespace

from app.investment.models import (
    InvestmentConviction,
    InvestmentDecision,
    InvestmentHorizon,
    InvestmentRecommendation,
)
from app.report.generation import (
    ReportNarrativeOutput,
    ReportSection,
    ReportSectionId,
    build_report_generation_graph,
    generate_report_narrative,
)
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


def build_test_report() -> InvestmentReport:
    valuation = ValuationResult(
        ticker="TEST",
        method=ValuationMethod.PE,
        inputs=ValuationInputs(
            earnings_per_share=10.0,
        ),
        assumptions=ValuationAssumptions(
            multiple=20.0,
            rationale="Representative multiple.",
        ),
        implied_value_per_share=200.0,
        target_price=200.0,
        current_price=160.0,
        expected_upside=0.25,
        metadata=ValuationMetadata(
            currency="USD",
            model_version="test-v1",
        ),
    )

    risk_item = RiskItem(
        category=RiskCategory.MARKET,
        title="Market volatility",
        description="The stock remains exposed to broad market volatility.",
        severity=RiskSeverity.MEDIUM,
        likelihood=RiskLikelihood.MEDIUM,
        impact=RiskImpact.MEDIUM,
        evidence=["Historical market volatility"],
    )

    risk_analysis = RiskAnalysis(
        ticker="TEST",
        risks=[risk_item],
        overall_risk_level=RiskSeverity.MEDIUM,
        key_risks=["Market volatility"],
        uncertainty_notes=["Future market conditions remain uncertain."],
    )

    investment_decision = InvestmentDecision(
        ticker="TEST",
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=160.0,
        target_price=200.0,
        expected_upside=0.25,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis=(
            "The current valuation provides meaningful upside."
        ),
        key_catalysts=["Earnings growth"],
        key_risks=["Market volatility"],
        invalidation_conditions=[
            "Material deterioration in earnings expectations."
        ],
        supporting_evidence=[
            "Current valuation implies a 25% expected upside."
        ],
    )

    return InvestmentReport(
        ticker="TEST",
        title="Test Investment Research Report",
        executive_summary="Existing executive summary.",
        company_overview="Existing company overview.",
        financial_summary="Existing financial summary.",
        market_summary="Existing market summary.",
        industry_macro_summary="Existing industry and macro summary.",
        valuation_summary="Existing valuation summary.",
        risk_summary="Existing risk summary.",
        investment_decision_summary="Existing investment decision summary.",
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )


def build_mock_narrative() -> ReportNarrativeOutput:
    return ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=ReportSectionId.EXECUTIVE_SUMMARY,
                content="The company presents a positive investment profile.",
            ),
            ReportSection(
                section_id=ReportSectionId.COMPANY_OVERVIEW,
                content="The company operates in its relevant business market.",
            ),
            ReportSection(
                section_id=ReportSectionId.FINANCIAL_SUMMARY,
                content="Financial performance supports the current thesis.",
            ),
            ReportSection(
                section_id=ReportSectionId.MARKET_SUMMARY,
                content="Market conditions provide a relevant backdrop.",
            ),
            ReportSection(
                section_id=ReportSectionId.INDUSTRY_MACRO_SUMMARY,
                content="Industry and macro conditions remain relevant.",
            ),
            ReportSection(
                section_id=ReportSectionId.VALUATION_SUMMARY,
                content="The valuation implies meaningful upside.",
            ),
            ReportSection(
                section_id=ReportSectionId.RISK_SUMMARY,
                content="Market volatility is the primary identified risk.",
            ),
            ReportSection(
                section_id=ReportSectionId.INVESTMENT_DECISION_SUMMARY,
                content="The resulting recommendation is Buy with medium conviction.",
            ),
        ]
    )


class FakeStructuredLLM:
    def __init__(self, result: ReportNarrativeOutput):
        self.result = result
        self.received_prompt = None

    def invoke(self, prompt):
        self.received_prompt = prompt
        return self.result


class FakeLLM:
    def __init__(self, result: ReportNarrativeOutput):
        self.structured_llm = FakeStructuredLLM(result)

    def with_structured_output(self, schema):
        assert schema is ReportNarrativeOutput
        return self.structured_llm


def test_generate_report_narrative_uses_structured_output(
    monkeypatch,
):
    report = build_test_report()
    expected = build_mock_narrative()
    fake_llm = FakeLLM(expected)

    monkeypatch.setattr(
        "app.report.generation.llm",
        fake_llm,
    )

    result = generate_report_narrative(
        {
            "report": report,
        }
    )

    assert result["narrative"] is expected
    assert result["generation_error"] is None


def test_generate_report_narrative_prompt_contains_report_facts(
    monkeypatch,
):
    report = build_test_report()
    expected = build_mock_narrative()
    fake_llm = FakeLLM(expected)

    monkeypatch.setattr(
        "app.report.generation.llm",
        fake_llm,
    )

    generate_report_narrative(
        {
            "report": report,
        }
    )

    prompt = fake_llm.structured_llm.received_prompt

    assert "TEST" in prompt
    assert "target_price" in prompt
    assert "200.0" in prompt
    assert "recommendation" in prompt
    assert "Buy" in prompt


def test_generate_report_narrative_returns_error_on_llm_failure(
    monkeypatch,
):
    class FailingStructuredLLM:
        def invoke(self, prompt):
            raise RuntimeError("LLM unavailable")

    class FailingLLM:
        def with_structured_output(self, schema):
            assert schema is ReportNarrativeOutput
            return FailingStructuredLLM()

    monkeypatch.setattr(
        "app.report.generation.llm",
        FailingLLM(),
    )

    result = generate_report_narrative(
        {
            "report": build_test_report(),
        }
    )

    assert result["narrative"] is None
    assert result["generation_error"] == "LLM unavailable"


def test_report_generation_graph_returns_narrative(
    monkeypatch,
):
    report = build_test_report()
    expected = build_mock_narrative()

    monkeypatch.setattr(
        "app.report.generation.llm",
        FakeLLM(expected),
    )

    graph = build_report_generation_graph()

    result = graph.invoke(
        {
            "report": report,
        }
    )

    assert result["narrative"] is expected
    assert result["generation_error"] is None
```

---

#### 十四、这里有一个测试设计上的重点

我们没有测试：

```python
assert narrative.content == ...
```

因为：

> LLM 的自然语言不是 deterministic business logic。

我们测试的是：

```text
LLM 被要求输出什么 Schema
LLM 收到了什么事实
LLM 输出是否进入正确的 State
LLM 失败时是否正确返回 error
Graph 是否正确连接
```

这才是 Agent 单元测试应该关注的东西。

---

#### 十五、Lesson 3.2 的 Graph Contract

现在应该明确成：

##### Input

```python
{
    "report": InvestmentReport(...)
}
```

##### Internal State

```python
{
    "report": InvestmentReport(...),
    "narrative": ReportNarrativeOutput | None,
    "generation_error": str | None,
}
```

##### Output

```python
{
    "narrative": ReportNarrativeOutput | None,
    "generation_error": str | None,
}
```

这里有一个重要设计：

**Output State 不再返回 `report`。**

因为 Report Generation 本身还没有 Merge。

---

#### 十六、为什么 Error 是 State，而不是直接 `raise`

这与当前项目的 Agent 模式一致。

例如现有：

```python
return {
    "investment_decision": None,
    "decision_error": str(exc),
}
```

Risk：

```python
return {
    "risk_analysis": None,
    "risk_error": str(exc),
}
```

所以 Report：

```python
return {
    "narrative": None,
    "generation_error": str(exc),
}
```

保持一致。

后面的：

```text
Error Recovery
Retry
Checkpoint
Observability
```

阶段再进一步完善。

现在不要提前加入 retry/fallback。

---

#### 十七、一个暂时保留的问题

当前 `InvestmentReport` 中：

```python
executive_summary
company_overview
financial_summary
...
```

这些字段实际上已经由 Lesson 2 的 Assembly 填充了。

因此现在会出现：

```text
Assembly
   ↓
已有 narrative-like text
   ↓
LLM
   ↓
新的 narrative
```

这在当前 Phase 8 的教学推进中是**暂时可以接受的**，因为 Lesson 2 的 Assembly 是 deterministic 的结构组装，而 Lesson 3 正在把这些内容升级为真正的 LLM narrative。

但是我们**现在不要修改 `InvestmentReport`**。

否则会把 Lesson 1/2 的边界一起重新设计。

等 Lesson 3.4 做 Merge 时，我们再处理：

```text
existing deterministic placeholder
                ↓
LLM narrative
                ↓
final report
```

这属于当前 Lesson 3 的后续步骤。

---

#### 十八、Lesson 3.2 Acceptance Criteria

完成后必须满足：

##### 结构

```text
app/report/generation.py
```

包含：

```text
ReportSectionId
ReportSection
ReportNarrativeOutput

ReportGenerationInputState
ReportGenerationState
ReportGenerationOutputState

generate_report_narrative()
build_report_generation_graph()

report_generation_graph
```

---

##### LLM

必须使用：

```python
llm.with_structured_output(
    ReportNarrativeOutput
)
```

而不是重新创建：

```python
ChatOpenAI(...)
```

---

##### LLM Input

必须包含：

```text
InvestmentReport
```

及其关键结构化事实。

---

##### LLM Output

只能是：

```text
ReportNarrativeOutput
```

不能直接输出：

```text
InvestmentDecision
ValuationResult
RiskAnalysis
InvestmentReport
```

---

##### Graph

Topology 必须是：

```text
START
  ↓
generate_report_narrative
  ↓
END
```

---

##### Error

LLM 异常必须得到：

```python
{
    "narrative": None,
    "generation_error": "...",
}
```

---

##### Test

执行：

```bash
pytest -q tests/test_report_generation.py
```

应该通过：

```text
4 passed
```

同时之前的：

```bash
pytest -q tests/test_report_narrative.py
```

也必须继续通过。

---

#### 当前 Lesson 3 的进度

完成这一节之后，我们实际上已经有：

```text
Lesson 3.1
    ✅ Narrative Structured Output Boundary

Lesson 3.2
    ⬅️ 当前
    Report Generation Agent
    Report Generation Graph

Lesson 3.3
    → Narrative Validation

Lesson 3.4
    → Deterministic Merge

Lesson 3.5
    → Failure / Mock / Contract Tests

Lesson 3 Acceptance
```
---

### Lesson 3.3 — Narrative Completeness & Semantic Validation

#### 3.3.1 本课的架构位置

目前流程是：

```text
InvestmentReport
      │
      ▼
Report Generation Graph
      │
      │ LLM + Structured Output
      ▼
ReportNarrativeOutput
      │
      ▼
？？？
```

Lesson 3.3 要补上：

```text
InvestmentReport
      │
      ▼
Report Generation Graph
      │
      │ LLM + Structured Output
      ▼
ReportNarrativeOutput
      │
      ▼
validate_report_narrative()
      │
      ├── section 完整性
      ├── section 唯一性
      ├── section 顺序
      └── 内容有效性
      │
      ▼
Validated ReportNarrativeOutput
```

注意这里有一个非常重要的架构原则：

> **不要让 LLM 自己判断“我是不是已经生成完整报告”。**

LLM 负责生成。

程序负责验证。

也就是：

```text
LLM = probabilistic generation
Python validation = deterministic contract enforcement
```

这也是工业级 Agent 和简单 Demo 的一个重要区别。

---

#### 3.3.2 先定义“完整 Narrative”的业务契约

当前 `ReportSectionId` 已经定义了 8 个 section：

```python
class ReportSectionId(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    COMPANY_OVERVIEW = "company_overview"
    FINANCIAL_SUMMARY = "financial_summary"
    MARKET_SUMMARY = "market_summary"
    INDUSTRY_MACRO_SUMMARY = "industry_macro_summary"
    VALUATION_SUMMARY = "valuation_summary"
    RISK_SUMMARY = "risk_summary"
    INVESTMENT_DECISION_SUMMARY = "investment_decision_summary"
```

因此 Lesson 3.3 的完整性契约应该明确为：

```text
必须有 8 个 section
每个 section_id 恰好出现一次
不能缺失
不能重复
不能出现未知 section
section 顺序固定
content 必须是有效的非空文本
```

这里尤其要区分：

##### Structural validation

Lesson 3.1 已经负责：

```text
section_id 是合法 Enum
content 非空
extra field 禁止
sections 至少一个
```

##### Semantic/business validation

Lesson 3.3 负责：

```text
是不是恰好 8 个 section？
是不是每个 section 都出现？
是不是没有重复？
是不是按照规定顺序？
```

这是两个不同层次。

---

#### 3.3.3 不修改 `ReportNarrativeOutput`

这一点非常重要。

目前：

```python
class ReportNarrativeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[ReportSection] = Field(
        min_length=1,
        description="Narrative sections generated by the report LLM.",
    )
```

**先不要把完整性逻辑塞进 Pydantic model validator。**

原因是：

`ReportNarrativeOutput` 是：

> LLM Structured Output Boundary DTO

而不是 Report Domain Model。

因此保持：

```text
ReportNarrativeOutput
        ↓
validate_report_narrative()
```

而不是：

```text
ReportNarrativeOutput
    └── 自己承担全部业务规则
```

这样职责更清晰。

---

#### 3.3.4 修改 `app/report/generation.py`

在现有代码基础上，增加一个固定 section 顺序：

```python
EXPECTED_REPORT_SECTION_IDS = (
    ReportSectionId.EXECUTIVE_SUMMARY,
    ReportSectionId.COMPANY_OVERVIEW,
    ReportSectionId.FINANCIAL_SUMMARY,
    ReportSectionId.MARKET_SUMMARY,
    ReportSectionId.INDUSTRY_MACRO_SUMMARY,
    ReportSectionId.VALUATION_SUMMARY,
    ReportSectionId.RISK_SUMMARY,
    ReportSectionId.INVESTMENT_DECISION_SUMMARY,
)
```

这里使用 tuple，而不是 list。

原因很简单：

这是一个**固定的不可变业务契约**。

---

然后增加：

```python
def validate_report_narrative(
    narrative: ReportNarrativeOutput,
) -> ReportNarrativeOutput:
    actual_section_ids = [section.section_id for section in narrative.sections]

    if len(actual_section_ids) != len(EXPECTED_REPORT_SECTION_IDS):
        raise ValueError(
            "Report narrative must contain exactly "
            f"{len(EXPECTED_REPORT_SECTION_IDS)} sections, "
            f"but received {len(actual_section_ids)}."
        )

    if len(set(actual_section_ids)) != len(actual_section_ids):
        raise ValueError(
            "Report narrative contains duplicate section IDs."
        )

    expected_section_ids = set(EXPECTED_REPORT_SECTION_IDS)
    actual_section_ids_set = set(actual_section_ids)

    missing_section_ids = expected_section_ids - actual_section_ids_set
    if missing_section_ids:
        raise ValueError(
            "Report narrative is missing required sections: "
            f"{sorted(section_id.value for section_id in missing_section_ids)}."
        )

    unexpected_section_ids = actual_section_ids_set - expected_section_ids
    if unexpected_section_ids:
        raise ValueError(
            "Report narrative contains unexpected sections: "
            f"{sorted(section_id.value for section_id in unexpected_section_ids)}."
        )

    if tuple(actual_section_ids) != EXPECTED_REPORT_SECTION_IDS:
        raise ValueError(
            "Report narrative sections are in an invalid order."
        )

    return narrative
```

---

##### 为什么返回 `narrative`？

不要设计成：

```python
def validate_report_narrative(...) -> None:
```

虽然技术上也可以。

但：

```python
def validate_report_narrative(
    narrative: ReportNarrativeOutput,
) -> ReportNarrativeOutput:
```

更适合当前 pipeline：

```python
narrative = structured_report_llm.invoke(prompt)

narrative = validate_report_narrative(narrative)

return {
    "narrative": narrative,
    "generation_error": None,
}
```

这样后续可以非常自然地形成：

```text
LLM output
    ↓
validate
    ↓
validated output
    ↓
merge
```

而且不会创建新的对象。

---

#### 3.3.5 最关键的一步：把 validator 接入 Agent

Lesson 3.2 当前应该类似：

```python
narrative = structured_report_llm.invoke(prompt)

return {
    "narrative": narrative,
    "generation_error": None,
}
```

现在修改成：

```python
narrative = structured_report_llm.invoke(prompt)

narrative = validate_report_narrative(narrative)

return {
    "narrative": narrative,
    "generation_error": None,
}
```

也就是说：

```text
LLM
 ↓
Pydantic structural validation
 ↓
business semantic validation
 ↓
state
```

如果 validator 抛异常，那么现有的：

```python
try:
    ...
except Exception as exc:
    return {
        "narrative": None,
        "generation_error": str(exc),
    }
```

就会捕获它。

因此不会破坏 Lesson 3.2 已经建立的错误处理模式。

---

#### 3.3.6 为什么现在不做“自动修复”？

这一课非常容易产生一个诱人的想法：

> 如果 LLM 少了一个 section，那我就在 Python 里自动补一个。

**现在不要这么做。**

例如：

```python
if missing:
    narrative.sections.append(...)
```

这是错误方向。

因为程序并不知道缺失 section 应该写什么。

更不能：

```text
LLM → 缺 valuation_summary
       ↓
程序自己编一个 valuation_summary
```

这会破坏：

```text
Source of Truth
```

当前阶段正确策略是：

```text
LLM output invalid
        ↓
deterministic validation failed
        ↓
generation_error
        ↓
future retry/recovery layer
```

未来 Phase 的：

* retry
* fallback
* error recovery
* observability

才负责解决“失败之后怎么办”。

Lesson 3.3 只负责回答：

> **这个输出是否合格？**

---

#### 3.3.7 测试

新增或扩展：

```text
tests/test_report_generation.py
```

建议增加以下测试。

##### Test 1：完整 narrative 可以通过

```python
def test_validate_report_narrative_accepts_complete_narrative():
    narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=section_id,
                content=f"{section_id.value} content",
            )
            for section_id in EXPECTED_REPORT_SECTION_IDS
        ]
    )

    validated = validate_report_narrative(narrative)

    assert validated is narrative
```

这里故意检查：

```python
validated is narrative
```

因为 validator 不应该无意义地复制 DTO。

---

##### Test 2：缺少 section

```python
def test_validate_report_narrative_rejects_missing_section():
    sections = [
        ReportSection(
            section_id=section_id,
            content=f"{section_id.value} content",
        )
        for section_id in EXPECTED_REPORT_SECTION_IDS
        if section_id != ReportSectionId.VALUATION_SUMMARY
    ]

    narrative = ReportNarrativeOutput(sections=sections)

    with pytest.raises(ValueError, match="exactly"):
        validate_report_narrative(narrative)
```

---

##### Test 3：重复 section

```python
def test_validate_report_narrative_rejects_duplicate_section():
    sections = [
        ReportSection(
            section_id=section_id,
            content=f"{section_id.value} content",
        )
        for section_id in EXPECTED_REPORT_SECTION_IDS
    ]

    sections[-1] = ReportSection(
        section_id=ReportSectionId.RISK_SUMMARY,
        content="duplicate risk summary",
    )

    narrative = ReportNarrativeOutput(sections=sections)

    with pytest.raises(ValueError, match="duplicate"):
        validate_report_narrative(narrative)
```

这里虽然 section 数量仍然是 8，但：

```text
risk_summary × 2
investment_decision_summary × 0
```

因此必须失败。

---

##### Test 4：顺序错误

```python
def test_validate_report_narrative_rejects_invalid_order():
    section_ids = list(EXPECTED_REPORT_SECTION_IDS)
    section_ids[0], section_ids[1] = section_ids[1], section_ids[0]

    narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=section_id,
                content=f"{section_id.value} content",
            )
            for section_id in section_ids
        ]
    )

    with pytest.raises(ValueError, match="order"):
        validate_report_narrative(narrative)
```

---

##### Test 5：generation agent 会执行 semantic validation

这个测试非常重要。

不能只测试：

```text
validator 本身工作
```

还必须测试：

```text
generate_report_narrative()
        ↓
真的调用 validator
```

可以让 Fake LLM 返回一个缺 section 的 narrative。

例如：

```python
class FakeStructuredLLM:
    def __init__(self, response):
        self.response = response

    def invoke(self, prompt):
        return self.response
```

然后：

```python
def test_generate_report_narrative_rejects_incomplete_llm_output(monkeypatch):
    incomplete_narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=section_id,
                content=f"{section_id.value} content",
            )
            for section_id in EXPECTED_REPORT_SECTION_IDS[:-1]
        ]
    )

    fake_llm = FakeLLM()
    fake_llm.structured_response = incomplete_narrative

    monkeypatch.setattr(
        generation.llm,
        "with_structured_output",
        lambda _: fake_llm,
    )

    result = generate_report_narrative(
        {"report": build_test_report()}
    )

    assert result["narrative"] is None
    assert result["generation_error"]
```

不过这里有一个实现细节需要注意：

**不要机械照抄这个 monkeypatch 结构。**

因为你当前 Lesson 3.2 的测试已经有自己的 `FakeStructuredLLM` / `FakeLLM` 设计。最好的做法是**沿用你已经通过的 Lesson 3.2 测试基础设施**，只增加“不完整 narrative”这个场景。

这样测试会更稳定，也不会为了 Lesson 3.3 重复设计 mock infrastructure。

---

#### 3.3.8 当前 `generation.py` 的职责边界

完成 Lesson 3.3 后，这个文件承担的是：

```text
app/report/generation.py

├── ReportSectionId
│
├── ReportSection
│
├── ReportNarrativeOutput
│
├── ReportGenerationInputState
│
├── ReportGenerationState
│
├── ReportGenerationOutputState
│
├── generate_report_narrative()
│   ├── prepare prompt
│   ├── call structured LLM
│   ├── validate narrative
│   └── return state
│
├── validate_report_narrative()
│   ├── count
│   ├── duplicate
│   ├── missing
│   ├── unexpected
│   └── order
│
└── build_report_generation_graph()
```

这仍然属于：

> **Report Narrative Generation Boundary**

而不是 Renderer。

---

#### 3.3.9 Lesson 3.3 完成后的完整链路

此时我们已经建立：

```text
Research Results
       │
       ▼
ValuationResult
RiskAnalysis
InvestmentDecision
       │
       ▼
InvestmentReport
       │
       │
       ▼
Report Generation Graph
       │
       ▼
LLM
       │
       ▼
ReportNarrativeOutput
       │
       ▼
Structural Validation
       │
       ▼
Semantic Validation
       │
       ▼
Validated ReportNarrativeOutput
```

还**没有**：

```text
       ↓
merge
       ↓
final InvestmentReport
       ↓
Markdown Renderer
       ↓
HTML Renderer
       ↓
PDF Renderer
```

这些留给后续 Lesson。

---

#### Lesson 3.3 验收条件

本课不要以“代码写完”为结束，而要严格按以下条件验收。

##### A. Model 层

* [ ] `ReportNarrativeOutput` 保持不变
* [ ] `ReportSectionId` 定义完整的 8 个 section
* [ ] 定义固定的 `EXPECTED_REPORT_SECTION_IDS`

##### B. Validator

* [ ] 完整 8 sections → 通过
* [ ] 少一个 section → 失败
* [ ] 重复 section → 失败
* [ ] 缺失 section → 失败
* [ ] unexpected section → 失败
* [ ] section 顺序错误 → 失败
* [ ] validator 不创建新的 narrative 对象

##### C. Generation Agent

必须验证：

```text
LLM
 ↓
ReportNarrativeOutput
 ↓
validate_report_narrative()
 ↓
state
```

而不是：

```text
LLM
 ↓
state
```

##### D. Error Handling

非法 narrative 必须进入：

```python
{
    "narrative": None,
    "generation_error": "...",
}
```

而不是：

```python
{
    "narrative": invalid_narrative,
    "generation_error": None,
}
```

##### E. Scope

本课**明确不做**：

* ❌ Narrative → InvestmentReport merge
* ❌ Markdown Renderer
* ❌ HTML Renderer
* ❌ PDF Renderer
* ❌ Main Graph integration
* ❌ Retry
* ❌ Fallback
* ❌ HITL
* ❌ Persistence
* ❌ Error Recovery

这些都不要提前实现。

---

#### 这一课最重要的工程思想

Phase 8 到这里实际上已经形成了一个很重要的边界：

```text
             Probabilistic
                 │
                 ▼
              LLM
                 │
                 ▼
        Structured Output
                 │
                 ▼
       Deterministic Validation
                 │
                 ▼
        Trusted Narrative DTO
```

也就是说：

> **不要因为用了 Structured Output，就认为 LLM 输出已经可信。**

Structured Output 解决的是：

> “它是不是符合预定义的数据结构？”

Lesson 3.3 进一步解决：

> “它是不是符合我们的业务完整性契约？”

这两个层次都通过之后，才有资格进入下一步 **Narrative → InvestmentReport 的 deterministic merge**。

### Lesson 3.4：Narrative → InvestmentReport Deterministic Merge**。

这一课是目前 Phase 8 最重要的边界之一。我们现在已经完成：

```text
Lesson 3.1
ReportNarrativeOutput
        ↓
Lesson 3.2
LLM Narrative Generation
        ↓
Lesson 3.3
Structural + Semantic Validation
        ↓
Lesson 3.4   ← 当前
Deterministic Merge
        ↓
Completed InvestmentReport
```

核心原则只有一句：

> **LLM 负责生成 Narrative；Python 负责把已经验证过的 Narrative 确定性地合并回 `InvestmentReport`。**

---

#### 一、Lesson 3.4 要解决什么问题

当前 `InvestmentReport` 已经有 8 个 narrative 字段：

```python
class InvestmentReport(BaseModel):
    ...
    executive_summary: str
    company_overview: str
    financial_summary: str
    market_summary: str
    industry_macro_summary: str
    valuation_summary: str
    risk_summary: str
    investment_decision_summary: str

    valuation: ValuationResult
    risk_analysis: RiskAnalysis
    investment_decision: InvestmentDecision
```

而 LLM 输出的是：

```text
ReportNarrativeOutput
    └── sections
          ├── executive_summary
          ├── company_overview
          ├── financial_summary
          ├── market_summary
          ├── industry_macro_summary
          ├── valuation_summary
          ├── risk_summary
          └── investment_decision_summary
```

因此现在需要一个**纯确定性函数**：

```text
ReportNarrativeOutput
          +
InvestmentReport
          ↓
merge_report_narrative()
          ↓
InvestmentReport
```

---

#### 二、为什么一定要 Deterministic Merge

这里千万不要继续让 LLM 做一次：

```text
LLM → 重新生成整个 InvestmentReport
```

这是错误的架构。

因为这样会产生一个非常危险的问题：

```text
ValuationResult
    ↓
InvestmentReport
    ↓
LLM
    ↓
新的 InvestmentReport
```

LLM 有机会重新生成：

* `target_price`
* `current_price`
* `expected_upside`
* `recommendation`
* `conviction`
* `key_risks`

这等于重新打开了 Phase 6 / Phase 7 已经关闭的业务决策边界。

我们真正需要的是：

```text
InvestmentReport
       │
       ├── structured facts ──────────────┐
       │                                  │
       ▼                                  │
ReportNarrativeOutput                     │
       │                                  │
       ▼                                  │
deterministic merge                       │
       │                                  │
       └──────────────────────────────────┘
                       │
                       ▼
             Completed InvestmentReport
```

因此：

> **Merge 只允许修改 8 个 narrative 字段。**

其他字段必须保持不变。

---

#### 三、先定义明确的映射关系

不要使用：

```python
setattr(report, section.section_id.value, section.content)
```

虽然代码很短，但对于工业级系统来说不够明确。

因为这会让：

```text
LLM output
    ↓
任意字符串
    ↓
动态修改对象属性
```

边界过于松散。

我们应该显式定义：

```python
REPORT_NARRATIVE_FIELD_MAP = {
    ReportSectionId.EXECUTIVE_SUMMARY: "executive_summary",
    ReportSectionId.COMPANY_OVERVIEW: "company_overview",
    ReportSectionId.FINANCIAL_SUMMARY: "financial_summary",
    ReportSectionId.MARKET_SUMMARY: "market_summary",
    ReportSectionId.INDUSTRY_MACRO_SUMMARY: "industry_macro_summary",
    ReportSectionId.VALUATION_SUMMARY: "valuation_summary",
    ReportSectionId.RISK_SUMMARY: "risk_summary",
    ReportSectionId.INVESTMENT_DECISION_SUMMARY: "investment_decision_summary",
}
```

这里实际上建立了一个非常重要的 **Domain Mapping Contract**：

```text
LLM section_id
      ↓
唯一允许写入的 InvestmentReport field
```

---

#### 四、增加 Merge 函数

建议在：

```text
app/report/generation.py
```

中继续实现。

原因是当前文件负责整个：

> Report Narrative Generation Boundary

后续如果项目规模进一步扩大，也可以再拆成 `merge.py`，但**现在不要为了拆分而拆分**。

增加：

```python
def merge_report_narrative(
    report: InvestmentReport,
    narrative: ReportNarrativeOutput,
) -> InvestmentReport:
    narrative_data = {
        field_name: section.content
        for section, field_name in (
            (
                section,
                REPORT_NARRATIVE_FIELD_MAP[section.section_id],
            )
            for section in narrative.sections
        )
    }

    return report.model_copy(update=narrative_data)
```

但是这里我建议进一步提高可读性，不使用这种嵌套 comprehension。

对于这个项目，我们更重视**业务边界可读性**。

建议直接写：

```python
def merge_report_narrative(
    report: InvestmentReport,
    narrative: ReportNarrativeOutput,
) -> InvestmentReport:
    narrative_updates: dict[str, str] = {}

    for section in narrative.sections:
        field_name = REPORT_NARRATIVE_FIELD_MAP[section.section_id]
        narrative_updates[field_name] = section.content

    return report.model_copy(update=narrative_updates)
```

这样以后维护者一眼就能看出：

```text
section
   ↓
mapping
   ↓
field
   ↓
update
```

---

#### 五、但这里有一个非常重要的问题

你可能注意到了：

```python
report.model_copy(update=narrative_updates)
```

Pydantic 的 `model_copy(update=...)` **不会重新进行完整 validation**。

这在我们 Lesson 1 时已经遇到过。

因此不能简单认为：

```text
model_copy()
=
重新构造并验证 InvestmentReport
```

它不是。

所以工业级实现更推荐：

```python
updated_data = report.model_dump()
updated_data.update(narrative_updates)

return InvestmentReport.model_validate(updated_data)
```

最终：

```python
def merge_report_narrative(
    report: InvestmentReport,
    narrative: ReportNarrativeOutput,
) -> InvestmentReport:
    narrative_updates: dict[str, str] = {}

    for section in narrative.sections:
        field_name = REPORT_NARRATIVE_FIELD_MAP[section.section_id]
        narrative_updates[field_name] = section.content

    updated_data = report.model_dump()
    updated_data.update(narrative_updates)

    return InvestmentReport.model_validate(updated_data)
```

我推荐这一版。

因为这里我们明确要求：

```text
merge
 ↓
重新构造 InvestmentReport
 ↓
重新执行 Domain Model validation
```

---

#### 六、Merge 前是否还要验证 Narrative？

Lesson 3.3 已经有：

```python
validate_report_narrative()
```

因此正常 pipeline 应该是：

```text
LLM
 ↓
ReportNarrativeOutput
 ↓
validate_report_narrative()
 ↓
merge_report_narrative()
```

而不是：

```text
LLM
 ↓
merge_report_narrative()
```

但是 `merge_report_narrative()` 自身应该具备合理的防御性。

因此这里建议：

```python
def merge_report_narrative(
    report: InvestmentReport,
    narrative: ReportNarrativeOutput,
) -> InvestmentReport:
    validate_report_narrative(narrative)

    ...
```

完整：

```python
def merge_report_narrative(
    report: InvestmentReport,
    narrative: ReportNarrativeOutput,
) -> InvestmentReport:
    validate_report_narrative(narrative)

    narrative_updates: dict[str, str] = {}

    for section in narrative.sections:
        field_name = REPORT_NARRATIVE_FIELD_MAP[section.section_id]
        narrative_updates[field_name] = section.content

    updated_data = report.model_dump()
    updated_data.update(narrative_updates)

    return InvestmentReport.model_validate(updated_data)
```

这样即使未来某个调用者绕过 `generate_report_narrative()`，直接调用 merge，也不会把一个非法 Narrative 写进 Report。

这属于典型的：

> **Defense in Depth**

---

#### 七、最重要的测试：Source of Truth 不得改变

Lesson 3.4 的测试重点不是“字符串有没有成功复制”。

真正重要的是：

> **Merge 之后，Valuation / Risk / Decision 必须完全保持不变。**

建议新增：

```text
tests/test_report_generation.py
```

或者如果你目前已经开始把 merge 测试独立出来，可以创建：

```text
tests/test_report_merge.py
```

我更推荐后者，因为从这一课开始，Merge 已经是一个独立职责。

---

##### Test 1：成功 Merge

```python
def test_merge_report_narrative_updates_all_narrative_fields():
    report = build_test_report()

    narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=section_id,
                content=f"generated {section_id.value}",
            )
            for section_id in EXPECTED_REPORT_SECTION_IDS
        ]
    )

    merged_report = merge_report_narrative(
        report,
        narrative,
    )

    assert merged_report.executive_summary == "generated executive_summary"
    assert merged_report.company_overview == "generated company_overview"
    assert merged_report.financial_summary == "generated financial_summary"
    assert merged_report.market_summary == "generated market_summary"
    assert (
        merged_report.industry_macro_summary
        == "generated industry_macro_summary"
    )
    assert merged_report.valuation_summary == "generated valuation_summary"
    assert merged_report.risk_summary == "generated risk_summary"
    assert (
        merged_report.investment_decision_summary
        == "generated investment_decision_summary"
    )
```

---

#### 八、Test 2：Domain Facts 必须保持

这个测试比上一个更重要。

```python
def test_merge_report_narrative_preserves_source_of_truth():
    report = build_test_report()

    original_valuation = report.valuation
    original_risk_analysis = report.risk_analysis
    original_investment_decision = report.investment_decision

    narrative = build_complete_test_narrative()

    merged_report = merge_report_narrative(
        report,
        narrative,
    )

    assert merged_report.valuation == original_valuation
    assert merged_report.risk_analysis == original_risk_analysis
    assert merged_report.investment_decision == original_investment_decision
```

还可以进一步检查：

```python
assert merged_report.valuation is original_valuation
assert merged_report.risk_analysis is original_risk_analysis
assert merged_report.investment_decision is original_investment_decision
```

由于 `model_dump()` / `model_validate()` 会产生新的 Pydantic 对象，这里**不要强制要求 identity**。

所以这里建议只检查：

```python
==
```

而不是：

```python
is
```

这一点与 Lesson 2 的 `build_investment_report()` 不同。

Lesson 2 是：

> 组装已有 Domain Objects，因此保留 identity 是有意义的。

Lesson 3.4 是：

> 重建一个新的 `InvestmentReport`，因此 equality preservation 才是正确契约。

这是两个不同场景。

---

#### 九、Test 3：原始 Report 不应该被修改

这是另一个关键契约。

Merge 应该是：

```text
old report
    │
    ├──────────────→ remains unchanged
    │
    ▼
new report
```

而不是：

```text
old report
    ↓
in-place mutation
```

因此：

```python
def test_merge_report_narrative_does_not_mutate_original_report():
    report = build_test_report()

    original_executive_summary = report.executive_summary
    original_company_overview = report.company_overview

    narrative = build_complete_test_narrative()

    merged_report = merge_report_narrative(
        report,
        narrative,
    )

    assert report.executive_summary == original_executive_summary
    assert report.company_overview == original_company_overview

    assert (
        merged_report.executive_summary
        != original_executive_summary
    )
```

这建立：

> **Functional Transformation**

而不是 mutable state mutation。

对于未来：

* Graph
* persistence
* checkpoint
* retry
* concurrent execution

这会更加安全。

---

#### 十、Test 4：非法 Narrative 必须被拒绝

不要只测试 validator 本身。

还要验证：

```text
merge()
 ↓
validate_report_narrative()
```

确实存在。

例如：

```python
def test_merge_report_narrative_rejects_incomplete_narrative():
    report = build_test_report()

    narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=section_id,
                content=f"{section_id.value} content",
            )
            for section_id in EXPECTED_REPORT_SECTION_IDS[:-1]
        ]
    )

    with pytest.raises(ValueError):
        merge_report_narrative(report, narrative)
```

---

#### 十一、Test 5：禁止修改非-narrative fields

这是本课非常值得增加的一个测试。

假设未来有人错误地修改：

```python
REPORT_NARRATIVE_FIELD_MAP
```

或者增加了：

```python
ReportSectionId.CURRENT_PRICE
```

然后试图把：

```text
current_price
```

作为 narrative 写入。

这种设计应该被结构性地禁止。

当前我们的 Enum 本身就只有：

```text
8 narrative section IDs
```

因此已经形成了一层保护。

可以再增加一个测试，验证 merge 后：

```python
assert merged_report.ticker == report.ticker
assert merged_report.valuation.current_price == report.valuation.current_price
assert (
    merged_report.investment_decision.recommendation
    == report.investment_decision.recommendation
)
assert (
    merged_report.investment_decision.target_price
    == report.investment_decision.target_price
)
```

尤其是：

```text
current_price
target_price
expected_upside
recommendation
conviction
key_risks
```

都不能被 Narrative 改变。

---

#### 十二、把 Lesson 3.4 接入 Generation Pipeline

这里要特别注意：

**不要在 Lesson 3.4 一上来就把它接到主 Graph。**

我们只扩展当前的 Report Generation Graph。

现在：

```text
generate_report_narrative
```

实际上只有：

```text
START
  ↓
generate_report_narrative
  ↓
END
```

Lesson 3.4 后应该变成：

```text
START
  ↓
generate_report_narrative
  ↓
merge_report_narrative
  ↓
END
```

但是这里又有一个状态设计问题。

---

#### 十三、调整 Report Generation State

当前大概是：

```python
class ReportGenerationState(TypedDict, total=False):
    report: InvestmentReport
    narrative: ReportNarrativeOutput | None
    generation_error: str | None
```

现在增加：

```python
merge_error: str | None
```

成为：

```python
class ReportGenerationState(TypedDict, total=False):
    report: InvestmentReport
    narrative: ReportNarrativeOutput | None
    generation_error: str | None
    merge_error: str | None
```

但是这里我建议再进一步：

最终我们真正需要的是：

```text
report
```

因此 Graph 内部可以保持：

```text
report = original report
```

直到 merge 节点。

Merge 节点再产生：

```text
completed report
```

---

#### 十四、定义 Merge Node

建议：

```python
def merge_report_narrative_node(
    state: ReportGenerationState,
) -> ReportGenerationState:
    report = state.get("report")
    narrative = state.get("narrative")

    if report is None:
        return {
            "merge_error": "Report is required for narrative merge.",
        }

    if narrative is None:
        return {
            "merge_error": "Narrative is required for report merge.",
        }

    try:
        merged_report = merge_report_narrative(
            report,
            narrative,
        )

        return {
            "report": merged_report,
            "merge_error": None,
        }

    except Exception as exc:
        return {
            "merge_error": str(exc),
        }
```

这里有一个重要的状态语义：

```text
generation_error
```

表示：

> LLM Narrative Generation 失败。

而：

```text
merge_error
```

表示：

> Narrative 已经存在，但无法合并进 InvestmentReport。

两个错误必须区分。

---

#### 十五、Output State 怎么办？

这是本课需要认真处理的地方。

Lesson 3.2 的 Output State 是：

```python
class ReportGenerationOutputState(TypedDict):
    narrative: ReportNarrativeOutput | None
    generation_error: str | None
```

如果现在 Graph 已经完成 merge，那么下游真正需要的输出应该包括：

```python
report: InvestmentReport | None
```

因此修改为：

```python
class ReportGenerationOutputState(TypedDict):
    report: InvestmentReport | None
    narrative: ReportNarrativeOutput | None
    generation_error: str | None
    merge_error: str | None
```

这样 Graph 的完整结果是：

```text
report
    ↓
完成后的 InvestmentReport

narrative
    ↓
LLM 原始 Narrative DTO

generation_error
    ↓
生成阶段错误

merge_error
    ↓
合并阶段错误
```

这里保留 `narrative` 是有价值的，因为未来：

* observability
* debugging
* evaluation

都可能需要看到 LLM 实际输出。

---

#### 十六、Graph topology

最终 Lesson 3.4 的局部 Graph：

```text
                   ┌───────────────────────┐
                   │                       │
                   ▼                       │
START → generate_report_narrative → merge_report_narrative → END
                   │                       │
                   │                       │
             generation_error          merge_error
```

正常路径：

```text
START
  ↓
LLM
  ↓
ReportNarrativeOutput
  ↓
semantic validation
  ↓
merge
  ↓
InvestmentReport
  ↓
END
```

失败路径目前仍然只是：

```text
generation_error
```

或者：

```text
merge_error
```

**不要在这里加入 retry。**

---

#### 十七、但是有一个重要的 Graph 控制问题

如果 `generate_report_narrative()` 失败：

```python
{
    "narrative": None,
    "generation_error": "...",
}
```

那么下一节点：

```text
merge_report_narrative
```

仍然会被执行。

它会发现：

```python
narrative is None
```

然后产生：

```text
merge_error = "Narrative is required..."
```

这样就出现：

```text
真正错误：
generation_error

附带错误：
merge_error
```

这并不好。

因此我们需要一个简单的 conditional edge：

```text
generate
   │
   ├── generation_error → END
   │
   └── success → merge
```

所以 Graph topology 应该是：

```text
                       ┌──────────────→ END
                       │ generation_error
                       │
START → generate ───────┤
                       │
                       └── success → merge → END
```

这才是正确的错误传播。

---

#### 十八、Conditional Routing

可以增加：

```python
def route_after_generation(
    state: ReportGenerationState,
) -> str:
    if state.get("generation_error"):
        return "end"

    return "merge"
```

然后：

```python
graph.add_conditional_edges(
    "generate_report_narrative",
    route_after_generation,
    {
        "merge": "merge_report_narrative",
        "end": END,
    },
)
```

最终：

```python
graph.add_edge(START, "generate_report_narrative")
graph.add_node(
    "merge_report_narrative",
    merge_report_narrative_node,
)
graph.add_edge(
    "merge_report_narrative",
    END,
)
```

这样错误不会继续向 Merge 传播。

---

#### 十九、最终的 `build_report_generation_graph()`

整体结构应接近：

```python
def build_report_generation_graph():
    graph = StateGraph(
        ReportGenerationState,
        input_schema=ReportGenerationInputState,
        output_schema=ReportGenerationOutputState,
    )

    graph.add_node(
        "generate_report_narrative",
        generate_report_narrative,
    )

    graph.add_node(
        "merge_report_narrative",
        merge_report_narrative_node,
    )

    graph.add_edge(
        START,
        "generate_report_narrative",
    )

    graph.add_conditional_edges(
        "generate_report_narrative",
        route_after_generation,
        {
            "merge": "merge_report_narrative",
            "end": END,
        },
    )

    graph.add_edge(
        "merge_report_narrative",
        END,
    )

    return graph.compile()
```

然后：

```python
report_generation_graph = build_report_generation_graph()
```

---

#### 二十、Lesson 3.4 测试矩阵

完成后至少需要验证：

| 场景                    | 预期                              |
|-------------------------|-----------------------------------|
| 完整 Narrative + Report | Merge 成功                        |
| Narrative 8 sections    | 全部写入                          |
| Valuation               | 完全不变                          |
| Risk                    | 完全不变                          |
| InvestmentDecision      | 完全不变                          |
| 原 Report               | 不被修改                          |
| 缺 section              | Merge 失败                        |
| 重复 section            | Merge 失败                        |
| LLM generation failure  | 不进入 merge                      |
| generation success      | 正常进入 merge                    |
| merge failure           | `merge_error`                     |
| Graph success           | 返回 completed `InvestmentReport` |

特别重要的是测试这条：

```text
LLM generation failure
        ↓
END
```

而不是：

```text
LLM generation failure
        ↓
merge
        ↓
第二个错误
```

---

#### 二十一、Lesson 3.4 完成后的架构

完成这一课之后，Phase 8 的 Report Domain 会变成：

```text
                         Structured Domain Facts
                                  │
                                  ▼
                         InvestmentReport
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ Report Generation Graph │
                    │                         │
                    │  LLM                    │
                    │   ↓                     │
                    │  Structured Output      │
                    │   ↓                     │
                    │  Validation             │
                    │   ↓                     │
                    │  Narrative DTO          │
                    │   ↓                     │
                    │  Deterministic Merge    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                       Completed InvestmentReport
                                 │
                                 ▼
                         【下一阶段】
                            Renderer
```

注意最终得到的依然是：

```text
InvestmentReport
```

而不是：

```text
ReportNarrativeOutput
```

这点非常重要。

`ReportNarrativeOutput` 是临时的：

```text
LLM Boundary DTO
```

而 `InvestmentReport` 是稳定的：

```text
Report Domain Model
```

---

#### Lesson 3.4 验收条件

本课结束前，必须全部满足：

##### Merge Contract

* [ ] Narrative 的 8 个 section 可以确定性映射到 8 个 Report 字段
* [ ] 不使用任意 `setattr()` 动态修改 Report
* [ ] Merge 前执行 Narrative validation
* [ ] Merge 后重新执行 `InvestmentReport` Pydantic validation
* [ ] 原 `InvestmentReport` 不被 mutation
* [ ] Valuation 保持不变
* [ ] Risk Analysis 保持不变
* [ ] Investment Decision 保持不变
* [ ] ticker 保持不变
* [ ] 所有结构化投资事实保持不变

##### Graph Contract

```text
START
  ↓
generate
  ↓
validation
  ↓
merge
  ↓
END
```

Generation failure：

```text
generate
  ↓
generation_error
  ↓
END
```

不能进入 merge。

##### Scope Boundary

本课**不做**：

* ❌ Markdown
* ❌ HTML
* ❌ PDF
* ❌ Renderer
* ❌ Main Investment Graph Integration
* ❌ Retry
* ❌ Fallback
* ❌ Persistence
* ❌ Checkpoint
* ❌ HITL
* ❌ Observability

---

#### 最终要记住的设计原则

Lesson 3.4 真正建立的是：

```text
LLM
  ↓
Narrative
  ↓
Validation
  ↓
Deterministic Merge
  ↓
Domain Object
```

而不是：

```text
LLM
  ↓
Domain Object
```

这是本项目后面走向工业级实现时非常关键的一条边界：

> **LLM 可以参与解释和叙事，但不能通过“重新生成 Domain Model”的方式获得对业务事实的修改权。**


## Lesson 4：Markdown Renderer

正式开始。

这一课我们只解决一个问题：

> **如何把已经完成的 `InvestmentReport`，确定性地渲染成一份结构清晰、可直接阅读的 Markdown 投资研究报告。**

不会在这一课提前加入 HTML、PDF、主 Graph 集成、Persistence、HITL 等内容。

---

### 1. Lesson 4 在整个 Phase 8 中的位置

我们现在已经完成：

```text
Research Results
      ↓
ValuationResult
RiskAnalysis
InvestmentDecision
      ↓
build_investment_report()
      ↓
InvestmentReport
      ↓
LLM Narrative Generation
      ↓
ReportNarrativeOutput
      ↓
Narrative Validation
      ↓
Deterministic Merge
      ↓
Completed InvestmentReport
```

Lesson 4 从这里继续：

```text
Completed InvestmentReport
            ↓
     Markdown Renderer
            ↓
       Markdown str
```

因此完整链路变成：

```text
                    Research
                       │
                       ▼
              Analysis Domains
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Valuation       Risk       Decision
          │            │            │
          └────────────┼────────────┘
                       ▼
               InvestmentReport
                       │
                       ▼
             Narrative Generation
                       │
                       ▼
              Narrative Validation
                       │
                       ▼
             Deterministic Merge
                       │
                       ▼
          Completed InvestmentReport
                       │
                       ▼
              Markdown Renderer
                       │
                       ▼
               Markdown Document
```

---

### 2. 为什么现在需要 Renderer？

前面的 `InvestmentReport` 不是最终用户看到的 Markdown。

它是一个**结构化 Report Domain Boundary**。

例如：

```python
InvestmentReport(
    ticker="AAPL",
    title="Investment Research Report - AAPL",
    executive_summary="...",
    company_overview="...",
    ...
)
```

这个对象适合：

* 程序内部传递
* API response
* 后续 HTML Renderer
* 后续 PDF Renderer
* 测试
* Persistence
* Evaluation

但是用户最终需要看到的是：

```markdown
# Investment Research Report - AAPL

## Executive Summary

...

## Company Overview

...

## Financial Summary

...
```

所以 Renderer 的职责就是：

> **把已经确定的结构化 Report 转换为具体 Presentation Format。**

---

### 3. Renderer 最重要的架构原则

这里必须把三个概念严格区分：

```text
Generation
Rendering
Decision
```

#### Generation

负责：

> 用 LLM 生成自然语言 narrative。

```text
InvestmentReport
      ↓
      LLM
      ↓
Narrative
```

#### Rendering

负责：

> 把已经完成的 Report 转换成指定格式。

```text
InvestmentReport
      ↓
Deterministic Renderer
      ↓
Markdown
```

#### Decision

负责：

> 形成投资判断。

```text
Research
  +
Valuation
  +
Risk
  ↓
InvestmentDecision
```

因此 Renderer **绝对不能变成第二个 Decision Agent**。

---

### 4. Renderer 为什么应该是 Deterministic？

这是这一课最重要的工程概念之一。

假设同一个：

```python
InvestmentReport
```

第一次渲染：

```text
Recommendation: Buy
```

第二次却因为 LLM：

```text
Recommendation: Hold
```

这会产生非常严重的问题。

因此：

```text
同一个 InvestmentReport
        +
同一个 Renderer
        ↓
应该得到确定性的 Markdown
```

也就是说：

```text
Renderer(report)
```

本质上应该是：

```text
f(report) -> markdown
```

而不是：

```text
f(report, LLM) -> markdown
```

这也是为什么本课 **不调用 LLM**。

---

### 5. Renderer 应该读取什么？

这里继续遵守前面已经建立的 `InvestmentReport` Boundary。

Renderer 的输入只有：

```python
InvestmentReport
```

而不是：

```python
ValuationResult
RiskAnalysis
InvestmentDecision
CompanyResearchResult
FinancialResearchResult
...
```

也就是说：

```text
Renderer
   ↑
InvestmentReport
```

而不是：

```text
Renderer
   ↑
多个 Domain Object
```

这样以后我们可以非常自然地增加：

```text
InvestmentReport
      │
      ├── MarkdownRenderer
      ├── HTMLRenderer
      └── PDFRenderer
```

而上游完全不用改变。

---

### 6. Markdown 文档结构

本课我们采用固定、确定性的章节结构：

```markdown
# {title}

## Executive Summary

{executive_summary}

## Company Overview

{company_overview}

## Financial Summary

{financial_summary}

## Market Summary

{market_summary}

## Industry & Macro Summary

{industry_macro_summary}

## Valuation Summary

{valuation_summary}

## Risk Summary

{risk_summary}

## Investment Decision

{investment_decision_summary}
```

注意这里有一个非常重要的设计：

**Renderer 不重新生成这些内容。**

例如：

```python
report.valuation_summary
```

已经是 Lesson 3 中生成并 Merge 后的 narrative。

Renderer 只负责：

```text
取出来
↓
放到正确位置
↓
组成 Markdown
```

---

### 7. 投资决策的结构化事实怎么办？

这里存在一个很容易犯的错误。

例如有人可能写：

```markdown
## Investment Decision

Buy

Medium Term

Medium Conviction

Target Price: $210
```

然后 Renderer 自己读取：

```python
report.investment_decision.recommendation
```

再拼接一套新的内容。

这会让 Renderer 开始承担 Report Generation 的职责。

当前 Lesson 4 **不这么做**。

我们的原则是：

```text
InvestmentDecision
       ↓
Investment Report Assembly
       ↓
LLM Narrative
       ↓
InvestmentReport.investment_decision_summary
       ↓
Renderer
```

因此 Renderer 的正文主要使用：

```python
report.investment_decision_summary
```

而不是重新组织投资决策。

后续如果我们需要在最终报告中增加结构化“Key Metrics / Recommendation Box”，可以单独设计 **deterministic metadata presentation layer**，但不在本课扩大范围。

---

### 8. 文件设计

本课新增：

```text
app/report/rendering.py
```

职责非常单一：

```text
InvestmentReport
       ↓
render_markdown()
       ↓
str
```

暂时不需要：

```text
app/report/renderers/
```

也不需要创建：

```text
markdown.py
html.py
pdf.py
```

因为当前只有一个 Renderer。

遵循项目一直以来的原则：

> **不要为了“看起来像 Production”提前创建 abstraction。**

等 HTML/PDF 真正出现时，再根据实际需求自然拆分。

---

### 9. Renderer API

我们先定义一个非常简单的 Contract：

```python
def render_markdown(report: InvestmentReport) -> str:
    ...
```

输入：

```text
InvestmentReport
```

输出：

```text
str
```

并且：

```text
No LLM
No Tool
No Graph
No I/O
No Mutation
```

这使它成为一个非常容易测试的 deterministic pure function。

---

### 10. 实现

新建：

`app/report/rendering.py`

内容：

```python
from app.report.models import InvestmentReport


def render_markdown(report: InvestmentReport) -> str:
    """Render a completed InvestmentReport as Markdown."""

    return "\n".join(
        [
            f"# {report.title}",
            "",
            "## Executive Summary",
            "",
            report.executive_summary,
            "",
            "## Company Overview",
            "",
            report.company_overview,
            "",
            "## Financial Summary",
            "",
            report.financial_summary,
            "",
            "## Market Summary",
            "",
            report.market_summary,
            "",
            "## Industry & Macro Summary",
            "",
            report.industry_macro_summary,
            "",
            "## Valuation Summary",
            "",
            report.valuation_summary,
            "",
            "## Risk Summary",
            "",
            report.risk_summary,
            "",
            "## Investment Decision",
            "",
            report.investment_decision_summary,
        ]
    )
```

这里故意没有使用：

```python
f"""
...
"""
```

而使用：

```python
"\n".join([...])
```

原因不是性能，而是**结构显式**。

每一个 Markdown 元素都非常清楚：

```text
Title
Section Heading
Section Content
```

以后测试也非常直接。

---

### 11. 为什么不让 Renderer 自动处理任意字段？

例如不要写：

```python
for field_name, value in report.model_dump().items():
    ...
```

这种设计看起来很灵活，但实际上会产生几个问题：

#### 问题 1：Presentation Order 不明确

Markdown 报告需要固定的业务顺序。

#### 问题 2：Domain Model 改字段可能直接改变文档

例如以后 `InvestmentReport` 增加：

```python
internal_debug_info
```

通用 Renderer 可能直接把它输出。

#### 问题 3：Presentation Structure 被 Domain Schema 绑架

Domain Model：

```text
描述系统内部数据结构
```

Renderer：

```text
描述用户看到的文档结构
```

两者不是同一个概念。

因此我们继续使用：

> **Explicit Presentation Mapping**

---

### 12. 测试设计

本课测试至少需要覆盖以下几个概念。

#### Test 1：返回 Markdown

```text
render_markdown(report)
        ↓
str
```

#### Test 2：包含 Title

验证：

```markdown
# Investment Research Report - AAPL
```

#### Test 3：包含全部 8 个章节

验证：

```text
Executive Summary
Company Overview
Financial Summary
Market Summary
Industry & Macro Summary
Valuation Summary
Risk Summary
Investment Decision
```

#### Test 4：内容来自 InvestmentReport

例如：

```python
assert "Generated executive summary." in markdown
```

而不是测试某个硬编码的内容。

#### Test 5：章节顺序正确

必须保证：

```text
Executive Summary
        ↓
Company Overview
        ↓
Financial Summary
        ↓
Market Summary
        ↓
Industry & Macro Summary
        ↓
Valuation Summary
        ↓
Risk Summary
        ↓
Investment Decision
```

#### Test 6：Renderer 不修改 Report

```python
original_report = report.model_copy(deep=True)

render_markdown(report)

assert report == original_report
```

#### Test 7：Renderer 不依赖 LLM

由于 `render_markdown()` 本身没有 LLM dependency，这实际上由 architecture 保证；测试重点是它可以在没有任何 LLM mock 的情况下直接运行。

---

### 13. 完整测试

新增：

`tests/test_report_rendering.py`

建议使用：

```python
from app.report.rendering import render_markdown
```

然后复用与 `test_report_generation.py` 相同的 `InvestmentReport` fixture 思路。

完整测试：

```python
def test_render_markdown_returns_string():
    report = build_test_report()

    markdown = render_markdown(report)

    assert isinstance(markdown, str)


def test_render_markdown_contains_title():
    report = build_test_report()

    markdown = render_markdown(report)

    assert "# Investment Research Report - AAPL" in markdown


def test_render_markdown_contains_all_sections():
    report = build_test_report()

    markdown = render_markdown(report)

    expected_headings = [
        "## Executive Summary",
        "## Company Overview",
        "## Financial Summary",
        "## Market Summary",
        "## Industry & Macro Summary",
        "## Valuation Summary",
        "## Risk Summary",
        "## Investment Decision",
    ]

    for heading in expected_headings:
        assert heading in markdown


def test_render_markdown_contains_report_narrative():
    report = build_test_report()

    markdown = render_markdown(report)

    assert "Original executive summary." in markdown
    assert "Original company overview." in markdown
    assert "Original financial summary." in markdown
    assert "Original market summary." in markdown
    assert "Original industry and macro summary." in markdown
    assert "Original valuation summary." in markdown
    assert "Original risk summary." in markdown
    assert "Original investment decision summary." in markdown


def test_render_markdown_preserves_section_order():
    report = build_test_report()

    markdown = render_markdown(report)

    positions = [
        markdown.index("## Executive Summary"),
        markdown.index("## Company Overview"),
        markdown.index("## Financial Summary"),
        markdown.index("## Market Summary"),
        markdown.index("## Industry & Macro Summary"),
        markdown.index("## Valuation Summary"),
        markdown.index("## Risk Summary"),
        markdown.index("## Investment Decision"),
    ]

    assert positions == sorted(positions)


def test_render_markdown_does_not_mutate_report():
    report = build_test_report()
    original_report = report.model_copy(deep=True)

    render_markdown(report)

    assert report == original_report
```

这里的 `build_test_report()` 可以直接沿用上一课测试中的 fixture 构造方式。

---

### 14. Lesson 4 的 Acceptance Criteria

完成这一课后，需要全部满足：

#### A. Renderer Contract

* [ ] `render_markdown(report)` 接收 `InvestmentReport`
* [ ] 返回 `str`
* [ ] 不调用 LLM
* [ ] 不调用 Tool
* [ ] 不依赖 Graph
* [ ] 不进行 I/O

#### B. Markdown Structure

* [ ] Title 正确
* [ ] 8 个 Report sections 全部存在
* [ ] Section 顺序固定
* [ ] Narrative 内容完整进入 Markdown

#### C. Domain Safety

* [ ] 不修改 `InvestmentReport`
* [ ] 不修改 `valuation`
* [ ] 不修改 `risk_analysis`
* [ ] 不修改 `investment_decision`
* [ ] 不重新计算 valuation
* [ ] 不重新生成 recommendation
* [ ] 不进行新的 investment reasoning

#### D. Testing

* [ ] Renderer 单元测试全部通过
* [ ] Phase 8 已有测试不能出现 regression

#### E. Scope Control

本课**不实现**：

```text
HTML
PDF
Main Graph Integration
FastAPI
Persistence
HITL
Retry
Observability
```

---

### 这一课真正建立的能力

到这里，Phase 8 会第一次形成完整的：

```text
Content
   ↓
Generation
   ↓
Validation
   ↓
Merge
   ↓
Rendering
```

也就是：

```text
InvestmentReport
      │
      ├── contains structured source-of-truth
      │
      ├── contains generated narrative
      │
      ▼
Completed Report Domain Object
      │
      ▼
Presentation Layer
      │
      ▼
Markdown
```
---