import json
from typing import Any

from groq import Groq

from core.config import require_groq_api_key


def get_client() -> Groq:
    return Groq(
        api_key=require_groq_api_key(),
        default_headers={
            "Groq-Model-Version": "latest"
        },
    )


def _collect_urls(value: Any, found: list[str]) -> None:
    """
    Recursively search any Groq tool output for URLs.
    """

    if isinstance(value, dict):
        for key, item in value.items():

            if key.lower() in {
                "url",
                "link",
                "source_url",
                "href",
            }:
                if isinstance(item, str):
                    if item.startswith("http://") or item.startswith("https://"):
                        found.append(item)

            _collect_urls(item, found)

    elif isinstance(value, list):

        for item in value:
            _collect_urls(item, found)

    elif isinstance(value, str):

        words = value.split()

        for word in words:

            cleaned = word.strip(
                " \n\t\r\"'`()[]{}<>.,;:"
            )

            if cleaned.startswith("http://") or cleaned.startswith("https://"):
                found.append(cleaned)


def _unique_urls(urls: list[str]) -> list[str]:
    """
    Remove duplicate URLs while preserving order.
    """

    result = []
    seen = set()

    for url in urls:

        if url not in seen:
            seen.add(url)
            result.append(url)

    return result


def _extract_message_content(response: Any) -> str:
    """
    Safely extract the final textual response from Groq.
    """

    try:
        message = response.choices[0].message
    except Exception:
        return ""

    content = getattr(message, "content", None)

    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    return str(content).strip()


def _extract_executed_tools(response: Any) -> Any:
    """
    Extract Groq Compound executed tools.
    """

    try:
        return getattr(
            response.choices[0].message,
            "executed_tools",
            None,
        )
    except Exception:
        return None


def _run_research(prompt: str):
    """
    Run one Compound research request.
    """

    response = get_client().chat.completions.create(
        model="groq/compound",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        compound_custom={
            "tools": {
                "enabled_tools": [
                    "web_search",
                    "visit_website",
                ]
            }
        },
    )

    return response


def generate_research_report(
    topic: str,
    profile: dict,
    plan: dict,
):
    """
    Perform web research and generate the final ResearchOS report.
    """

    profile_text = json.dumps(
        profile or {},
        ensure_ascii=False,
        indent=2,
    )

    plan_text = json.dumps(
        plan or {},
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are an evidence-first research analyst.

Your task is to conduct real web research and produce a professional,
evidence-based research report.

RESEARCH TOPIC:
{topic}

RESEARCH PROFILE:
{profile_text}

RESEARCH PLAN:
{plan_text}

IMPORTANT RESEARCH REQUIREMENTS:

1. Actually research the topic using the available web search tools.

2. Search multiple relevant sources.

3. Prefer:
   - official sources
   - government sources
   - academic / peer-reviewed research
   - reputable organizations
   - high-quality industry reports
   - reputable journalism

4. Do not invent sources, statistics, quotations, URLs, or findings.

5. Distinguish:
   - established findings
   - evidence-supported findings
   - uncertain findings
   - conflicting evidence

6. Look specifically for contradictions or disagreements between sources.

7. Identify important limitations and research gaps.

8. Use current information where appropriate.

9. Consider the geographic scope and audience from the research profile.

10. The final response MUST contain the complete report.
Do not return only search results.
Do not return only research notes.
Do not return only a summary.

11. Use Markdown.

12. Keep tables compact.
Avoid huge tables.
Use tables only when they make comparison easier.

13. IMPORTANT:
The report must begin immediately with:

# {topic}

Then use these sections:

## Executive Summary

## Research Scope & Method

## Key Findings

## Evidence & Analysis

## Contradictions & Limitations

## Research Gaps

## Recommendations

## Conclusion

## Sources

14. Under Sources, provide a clean numbered list of the important sources
with source title and URL when available.

15. The final answer must be useful as a professional research report
that can be rendered into a PDF.

16. The report must contain only the requested research deliverable. Do not
include interview answers, user messages, private profile values, assistant
messages, internal reasoning, tool execution, application names, software
frameworks, programming languages, model providers, model names, APIs,
prompts, or other implementation details.

17. Do not say that you are unable to browse.

18. If some evidence is unavailable, explicitly state that limitation
inside the report rather than inventing information.

Now conduct the research and write the complete report.
"""

    # ---------------------------------------------------------
    # First research attempt
    # ---------------------------------------------------------

    response = _run_research(prompt)

    report = _extract_message_content(response)
    executed_tools = _extract_executed_tools(response)

    urls: list[str] = []

    _collect_urls(
        executed_tools,
        urls,
    )

    # ---------------------------------------------------------
    # Debug information
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("RESEARCH ENGINE DEBUG")
    print("=" * 70)

    print("Topic:")
    print(topic)

    print()

    print("Report characters:")
    print(len(report))

    print()

    print("Executed tools:")
    print(executed_tools)

    print()

    print("Extracted URLs:")
    print(_unique_urls(urls))

    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # Retry if Compound returned no final report
    # ---------------------------------------------------------

    if not report:

        retry_prompt = f"""
The previous research attempt gathered information but did not return
the final report.

You MUST now produce the final research report.

Topic:
{topic}

Research profile:
{profile_text}

Research plan:
{plan_text}

Use the web-search and website tools again if necessary.

Return ONLY the completed Markdown research report.

The report MUST contain:

# {topic}

## Executive Summary

## Research Scope & Method

## Key Findings

## Evidence & Analysis

## Contradictions & Limitations

## Research Gaps

## Recommendations

## Conclusion

## Sources

Do not return an empty response.
Do not return tool notes.
Do not return internal reasoning.
Do not return only search results.

Write the complete professional report now.
"""

        retry_response = _run_research(
            retry_prompt
        )

        retry_report = _extract_message_content(
            retry_response
        )

        retry_tools = _extract_executed_tools(
            retry_response
        )

        _collect_urls(
            retry_tools,
            urls,
        )

        if retry_report:
            report = retry_report

        print()
        print("=" * 70)
        print("RESEARCH RETRY")
        print("=" * 70)
        print("Retry report characters:")
        print(len(retry_report))
        print("=" * 70)
        print()

    # ---------------------------------------------------------
    # Final validation
    # ---------------------------------------------------------

    if not report:

        raise RuntimeError(
            "Research engine returned an empty report after retry. "
            "Check the AskForth backend terminal for Compound response details."
        )

    urls = _unique_urls(urls)

    return report, urls


def generate_research_followup(
    topic: str,
    profile: dict,
    plan: dict,
    report: str,
    conversation: list[dict[str, Any]],
):
    """Answer a follow-up question using the completed report as context."""

    conversation_text = json.dumps(
        conversation,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are AskForth, an evidence-first AI research assistant.

Answer the user's latest follow-up question using the research report below.
Use web research when the question asks for current information or requires
evidence beyond the report. Do not invent facts or sources. Use Markdown and
cite source URLs when available.

RESEARCH TOPIC:
{topic}

RESEARCH PROFILE:
{json.dumps(profile or {}, ensure_ascii=False, indent=2)}

RESEARCH PLAN:
{json.dumps(plan or {}, ensure_ascii=False, indent=2)}

COMPLETED REPORT:
{report}

CONVERSATION:
{conversation_text}

Return only the answer to the latest user message.
"""

    response = _run_research(prompt)
    answer = _extract_message_content(response)
    urls: list[str] = []

    _collect_urls(_extract_executed_tools(response), urls)
    _collect_urls(answer, urls)

    if not answer:
        raise RuntimeError("Research follow-up returned an empty response.")

    return answer, _unique_urls(urls)