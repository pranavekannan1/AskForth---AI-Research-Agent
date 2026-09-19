"""MCP tools for testing AskForth report workflows safely.

Run with: python mcp_server.py
The server uses stdio and never requires provider credentials for local tests.
"""

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

from services.llm_service import (
    _local_revision,
    parse_revision_json,
)


mcp = FastMCP(
    "AskForth QA",
    instructions=(
        "Use these tools to test report revisions. Prefer offline scenario tests "
        "before live backend checks. Never request or expose secrets."
    ),
)


@mcp.tool()
def run_revision_scenarios(report: str) -> dict:
    """Run deterministic revision scenarios against a supplied report."""
    scenarios = {
        "shorter summary": "shorter summary",
        "humanized report": "I need a humanized report",
    }
    results = {}
    for name, request in scenarios.items():
        revision = _local_revision(report, [], request)
        results[name] = {
            "passed": bool(revision and revision["report"].strip() != report.strip()),
            "assistant_message": revision["assistant_message"] if revision else None,
            "report_changed": bool(revision and revision["report"].strip() != report.strip()),
        }
    return {
        "passed": all(item["passed"] for item in results.values()),
        "model_required_for_other_requests": True,
        "scenarios": results,
    }


@mcp.tool()
def validate_revision_response(response: str) -> dict:
    """Validate a model revision response without making a model request."""
    try:
        parsed = parse_revision_json(response)
    except RuntimeError as error:
        return {"valid": False, "error": str(error)}

    report = parsed.get("report")
    sources = parsed.get("sources", [])
    return {
        "valid": isinstance(report, str) and bool(report.strip()),
        "has_assistant_message": isinstance(parsed.get("assistant_message"), str),
        "has_report": isinstance(report, str) and bool(report.strip()),
        "sources_are_list": isinstance(sources, list),
    }


@mcp.tool()
def check_backend_health(base_url: str = "http://127.0.0.1:8000") -> dict:
    """Check the backend health endpoint without sending authentication data."""
    url = f"{base_url.rstrip('/')}/health"
    try:
        with urlopen(Request(url, method="GET"), timeout=10) as response:
            body = response.read().decode("utf-8")
            return {"reachable": True, "status_code": response.status, "body": body}
    except HTTPError as error:
        return {"reachable": True, "status_code": error.code, "error": error.reason}
    except URLError as error:
        return {"reachable": False, "error": str(error.reason)}
    except OSError as error:
        return {"reachable": False, "error": str(error)}


@mcp.tool()
def run_release_checks(report: str, base_url: str = "") -> dict:
    """Run offline revision checks and an optional backend health check."""
    scenarios = run_revision_scenarios(report)
    result = {
        "passed": scenarios["passed"],
        "revision_scenarios": scenarios,
    }
    if base_url.strip():
        result["backend_health"] = check_backend_health(base_url)
        result["passed"] = result["passed"] and result["backend_health"]["reachable"]
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
