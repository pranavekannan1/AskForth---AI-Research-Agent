import json

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

    try:
        response = get_client().chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
    except Exception as structured_error:
        try:
            response = get_client().chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception:
            raise structured_error

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty report revision")

    result = parse_revision_json(content)

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