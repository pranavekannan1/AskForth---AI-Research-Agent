from mcp_server import run_revision_scenarios, validate_revision_response


def test_mcp_revision_scenarios_pass():
    report = (
        "# Topic\n\n"
        "## Executive Summary\n\n"
        "It is important to note that this matters. It affects users. It needs review.\n\n"
        "## Sources\n\n1. https://example.com"
    )

    result = run_revision_scenarios(report)

    assert result["passed"] is True
    assert result["scenarios"]["shorter summary"]["report_changed"] is True
    assert result["scenarios"]["humanized report"]["report_changed"] is True


def test_mcp_validates_revision_json():
    result = validate_revision_response(
        '{"assistant_message":"Updated","report":"# Revised","sources":[]}'
    )

    assert result == {
        "valid": True,
        "has_assistant_message": True,
        "has_report": True,
        "sources_are_list": True,
    }
