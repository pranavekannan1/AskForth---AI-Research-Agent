from mcp_server import classify_revision_request, report_review, validate_report


def test_validate_report_is_local_and_structural():
    result = validate_report(
        "# Topic\n\n## Executive Summary\n\nSummary.\n\n"
        "## Sources\n\n1. https://example.com"
    )

    assert result["valid"] is True
    assert result["source_count"] == 1
    assert result["has_sources_section"] is True


def test_classify_revision_request_handles_humanized_tone():
    result = classify_revision_request("Please make the report more humanized")

    assert result["categories"] == ["humanized_tone"]
    assert result["ambiguous"] is False


def test_report_review_does_not_require_credentials():
    result = report_review("# Topic\n\n## Conclusion\n\nThe evidence is uncertain.")

    assert result["paragraph_count"] == 3
    assert result["has_uncertainty_language"] is True