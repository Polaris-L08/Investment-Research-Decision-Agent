from app.report.rendering import render_markdown
from tests.test_report_generation import build_test_report


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