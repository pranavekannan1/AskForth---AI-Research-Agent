import json

from services.llm_service import generate_response


VALID_PRIORITIES = {"high", "medium", "low"}


def clean_llm_json(response: str) -> str:
    """
    Remove common Markdown formatting around JSON.
    """

    response = response.strip()

    if response.startswith("```json"):
        response = response[7:]

    elif response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    return response.strip()


def validate_research_plan(plan: dict, topic: str):
    """
    Validate and normalize the structure returned by the LLM.
    """

    if not isinstance(plan, dict):
        return None

    research_goal = plan.get("research_goal")

    if not isinstance(research_goal, str) or not research_goal.strip():
        research_goal = topic

    tasks = plan.get("tasks")

    if not isinstance(tasks, list):
        return None

    # We expect between 3 and 8 tasks.
    if not 3 <= len(tasks) <= 8:
        return None

    validated_tasks = []

    for index, task in enumerate(tasks, start=1):

        if not isinstance(task, dict):
            return None

        task_id = task.get("task_id")
        title = task.get("title")
        description = task.get("description")
        priority = task.get("priority")
        source_types = task.get("source_types")

        # Required string fields
        if not isinstance(title, str) or not title.strip():
            return None

        if not isinstance(description, str) or not description.strip():
            return None

        # Normalize task ID if missing/invalid
        if not isinstance(task_id, str) or not task_id.strip():
            task_id = f"task_{index}"

        # Normalize priority
        if not isinstance(priority, str):
            priority = "medium"
        else:
            priority = priority.lower().strip()

        if priority not in VALID_PRIORITIES:
            priority = "medium"

        # Validate source types
        if not isinstance(source_types, list):
            return None

        source_types = [
            source.strip()
            for source in source_types
            if isinstance(source, str) and source.strip()
        ]

        if not source_types:
            return None

        validated_tasks.append(
            {
                "task_id": task_id.strip(),
                "title": title.strip(),
                "description": description.strip(),
                "priority": priority,
                "source_types": source_types,
            }
        )

    return {
        "research_goal": research_goal.strip(),
        "tasks": validated_tasks,
    }


def create_research_plan(
    topic: str,
    profile: dict,
):
    prompt = f"""
You are an expert research planning agent.

Create a research plan based on the user's requirements.

RESEARCH TOPIC:
{topic}

RESEARCH PROFILE:
{json.dumps(profile, indent=2)}

Your task is to determine what needs to be researched.

The plan should:

1. Break the research into clear research tasks.
2. Cover the most important aspects of the topic.
3. Match the user's purpose, audience, and requested depth.
4. Avoid unnecessary tasks.
5. Prioritize evidence-based research.
6. Identify what types of sources would be useful.
7. Include academic evidence where appropriate.
8. Include industry evidence where appropriate.
9. Identify areas where conflicting evidence may exist.
10. Identify important research gaps.

Return ONLY valid JSON.

Use this structure:

{{
    "research_goal": "...",
    "tasks": [
        {{
            "task_id": "task_1",
            "title": "...",
            "description": "...",
            "priority": "high",
            "source_types": [
                "academic",
                "industry"
            ]
        }}
    ]
}}

Rules:

- Create between 3 and 8 tasks.
- Each task must have a clear research purpose.
- priority must be one of: high, medium, low.
- source_types must be a non-empty list of source categories.
- Do not perform the research.
- Do not invent sources.
- Do not generate findings.
- Do not generate the final report.
- Return ONLY JSON.
"""

    response = generate_response(prompt)

    # LLM returned nothing
    if not response:
        return {
            "research_goal": topic,
            "tasks": [],
            "planning_error": "LLM returned an empty response",
        }

    # Clean Markdown JSON fences
    cleaned_response = clean_llm_json(response)

    # Parse JSON
    try:
        plan = json.loads(cleaned_response)

    except json.JSONDecodeError:
        return {
            "research_goal": topic,
            "tasks": [],
            "planning_error": "LLM returned invalid JSON",
            "raw_response": response,
        }

    # Validate structure
    validated_plan = validate_research_plan(
        plan=plan,
        topic=topic,
    )

    if validated_plan is None:
        return {
            "research_goal": topic,
            "tasks": [],
            "planning_error": "LLM returned an invalid research plan structure",
            "raw_response": response,
        }

    return validated_plan