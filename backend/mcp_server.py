"""Credential-free MCP tools for AskForth users and support workflows.

Run separately from the application with:
    python mcp_server.py

This server performs local report inspection only. It does not access the
AskForth database, Firebase, provider APIs, browser storage, or user tokens.
"""

import re
from collections.abc import Mapping

from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    "AskForth User Tools",
    instructions=(
        "Use these local tools to inspect a report or clarify an edit request. "
        "They never access credentials, accounts, databases, or provider APIs."
    ),
)

_REPORT_SECTIONS = (
    "Executive Summary",
    "Research Scope & Method",
    "Key Findings",
    "Evidence & Analysis",
    "Contradictions & Limitations",
    "Recommendations",
    "Conclusion",
    "Sources",
)


@mcp.tool()
def validate_report(report: str) -> dict[str, object]:
    """Check report structure and source formatting without sending the report anywhere."""
    text = report.strip()
    headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    source_urls = re.findall(r"https?://[^\s)]+", text)
    missing_sections = [section for section in _REPORT_SECTIONS if section not in headings]
    return {
        "valid": bool(text) and text.startswith("# "),
        "character_count": len(text),
        "headings": headings,
        "missing_recommended_sections": missing_sections,
        "source_count": len(set(source_urls)),
        "has_sources_section": "Sources" in headings,
    }


@mcp.tool()
def classify_revision_request(request: str) -> dict[str, object]:
    """Classify a user's report-edit request without calling an AI provider."""
    text = request.strip().lower()
    categories: list[str] = []
    patterns: Mapping[str, tuple[str, ...]] = {
        "shorter_summary": ("shorter summary", "brief summary", "shorten the summary"),
        "stronger_evidence": ("stronger evidence", "more evidence", "add sources", "citations"),
        "humanized_tone": ("humanized", "humanised", "more human", "natural tone"),
        "different_audience": ("different audience", "for students", "for executives", "for beginners"),
        "new_section": ("new section", "add a section", "include a section"),
    }
    for category, phrases in patterns.items():
        if any(phrase in text for phrase in phrases):
            categories.append(category)
    return {
        "request": request.strip(),
        "categories": categories,
        "ambiguous": bool(text) and not categories,
        "empty": not bool(text),
        "suggestion": (
            "Describe the section, audience, tone, or evidence you want changed."
            if text and not categories
            else None
        ),
    }


@mcp.tool()
def report_review(report: str) -> dict[str, object]:
    """Return a concise local quality review for a report before it is shared."""
    validation = validate_report(report)
    paragraphs = [part for part in re.split(r"\n\s*\n", report.strip()) if part.strip()]
    return {
        "validation": validation,
        "paragraph_count": len(paragraphs),
        "has_markdown_tables": "|" in report and "---" in report,
        "has_uncertainty_language": bool(
            re.search(r"\b(limitation|uncertain|uncertainty|conflicting)\b", report, re.I)
        ),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
