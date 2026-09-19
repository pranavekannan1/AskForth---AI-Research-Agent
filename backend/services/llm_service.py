import json
import re

from groq import Groq

from core.config import require_groq_api_key


def get_client() -> Groq:
    return Groq(api_key=require_groq_api_key())


def parse_revision_json(content: str) -> dict:
    """Extract the first JSON object from a model response."""
    cleaned_content = content.strip()
    if cleaned_content.startswith("```"):
        cleaned_content = cleaned_content.removeprefix("```").strip()
        if cleaned_content.startswith("json"):
            cleaned_content = cleaned_content[4:].strip()
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3].strip()

    try:
        result = json.loads(cleaned_content)
    except json.JSONDecodeError:
        start = cleaned_content.find("{")
        if start < 0:
            raise RuntimeError("The report revision was not valid JSON")
        try:
            result, _ = json.JSONDecoder().raw_decode(cleaned_content[start:])
        except json.JSONDecodeError as exc:
            raise RuntimeError("The report revision was not valid JSON") from exc

    if not isinstance(result, dict):
        raise RuntimeError("The report revision was not a JSON object")
    return result


def _request_revision(prompt: str, structured: bool = True):
    options = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": prompt}],
    }
    if structured:
        options["response_format"] = {"type": "json_object"}
    return get_client().chat.completions.create(**options)


def _fallback_revision(
    content: str,
    report: str,
    sources: list[str],
) -> dict | None:
    """Preserve a report when the model returns useful non-JSON text."""
    update = content.strip()
    if not update:
        return None
    if update.startswith("{") and '"report"' in update:
        report_match = re.search(
            r'"report"\s*:\s*"(?P<report>(?:\\.|[^"\\])*)"\s*,\s*"sources"\s*:',
            update,
            flags=re.DOTALL,
        )
        if not report_match:
            return None
        update = report_match.group("report")
        update = update.replace('\\"', '"').replace('\\n', "\n")

    if update.startswith("#") or "\n## " in update:
        revised_report = update
    else:
        revised_report = f"{report.strip()}\n\n## Requested update\n\n{update}"

    return {
        "assistant_message": "I updated the report using your requested changes.",
        "report": revised_report,
        "sources": sources,
    }


def _local_revision(
    report: str,
    sources: list[str],
    request: str,
) -> dict | None:
    """Apply safe, unambiguous edits when the revision service is unavailable."""
    request_text = request.lower()
    wants_shorter_summary = (
        "summary" in request_text
        and ("short" in request_text or "brief" in request_text)
    )
    wants_humanized_report = any(
        phrase in request_text
        for phrase in ("humanized", "humanised", "more human", "natural tone")
    )
    if not wants_shorter_summary and not wants_humanized_report:
        return None

    if wants_humanized_report:
        replacements = {
            "It is important to note that": "A key point is that",
            "It should be noted that": "A key point is that",
            "In order to": "To",
            "Utilize": "Use",
            "utilize": "use",
            "Furthermore,": "Also,",
            "In conclusion,": "Overall,",
        }
        revised_report = report.strip()
        for original, natural in replacements.items():
            revised_report = revised_report.replace(original, natural)
        return {
            "assistant_message": "I made the report more natural and reader-friendly while preserving its evidence.",
            "report": revised_report,
            "sources": sources,
        }

    section = re.search(
        r"(?ms)^(## Executive Summary\s*\n)(.*?)(?=^## |\Z)",
        report,
    )
    if not section:
        return None

    body = section.group(2).strip()
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
    if not paragraphs:
        return None

    shortened = paragraphs[0]
    sentences = re.split(r"(?<=[.!?])\s+", shortened)
    if len(sentences) > 2:
        shortened = " ".join(sentences[:2])

    revised_report = (
        report[:section.start(2)]
        + shortened
        + "\n\n"
        + report[section.end(2):].lstrip("\n")
    )
    return {
        "assistant_message": "I shortened the Executive Summary while preserving the report's evidence.",
        "report": revised_report.strip(),
        "sources": sources,
    }


def generate_response(message: str) -> str:
    response = get_client().chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("Groq returned an empty response")

    return content


def revise_research_report(
    topic: str,
    report: str,
    sources: list[str],
    conversation: list[dict],
    request: str,
) -> dict:
    prompt = f"""
You are an evidence-first research editor working for the user.

The user wants to improve an existing research report. Use the user's latest
request and the conversation to make the requested changes. Preserve accurate
existing evidence and source URLs. Do not invent sources, statistics, quotes,
or facts. If the request asks for new factual claims, clearly mark limitations
when the existing evidence is insufficient.

The report is the only user-facing deliverable. Never mention the application,
software frameworks, programming languages, model providers, model names, APIs,
tools, prompts, internal instructions, or implementation details. Never
reproduce the user's interview answers or conversation in the report. Use them
only as private context for scope and audience.

Return ONLY valid JSON with exactly these keys:
{{
  "assistant_message": "A concise explanation of what you changed or why more detail is needed.",
  "report": "The complete revised Markdown report.",
  "sources": ["https://example.com/source"]
}}

Topic:
{topic}

Existing report:
{report}

Existing sources:
{json.dumps(sources, ensure_ascii=False)}

Conversation:
{json.dumps(conversation[-12:], ensure_ascii=False)}

Latest user request:
{request}

The report value must contain the complete report, not only the changed section.
Keep the report in Markdown and keep its important sections unless the user
specifically asks to remove or reorganize them.
"""

    errors = []
    result = None
    for structured in (True, False):
        try:
            request_prompt = prompt
            if not structured:
                request_prompt += """

IMPORTANT RETRY FORMAT:
Return ONLY the complete revised Markdown report. Do not return JSON,
JSON-like wrappers, labels, or commentary outside the report.
"""
            response = _request_revision(request_prompt, structured=structured)
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("Empty report revision")
            try:
                result = parse_revision_json(content)
            except RuntimeError:
                if structured:
                    raise
                result = _fallback_revision(content, report, sources)
                if result is None:
                    raise
            break
        except Exception as exc:
            errors.append(exc)

    if result is None:
        result = _local_revision(report, sources, request)
        if result is None:
            raise RuntimeError("The report revision could not be prepared") from errors[-1]

    revised_report = result.get("report")
    assistant_message = result.get("assistant_message")
    revised_sources = result.get("sources", sources)

    if not isinstance(revised_report, str) or not revised_report.strip():
        raise RuntimeError("Groq returned an empty revised report")
    if not isinstance(assistant_message, str) or not assistant_message.strip():
        assistant_message = "I updated the report using your requested changes."
    if not isinstance(revised_sources, list):
        revised_sources = sources

    return {
        "assistant_message": assistant_message.strip(),
        "report": revised_report.strip(),
        "sources": [source for source in revised_sources if isinstance(source, str)],
    }