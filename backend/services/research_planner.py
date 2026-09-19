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
You are an expert research planning agent responsible for designing a rigorous, efficient, evidence-based research plan.

Your output will be passed to downstream research agents that will search for sources, extract evidence, verify claims, synthesize findings, and generate a final report.

RESEARCH TOPIC:
{topic}

RESEARCH PROFILE:
{json.dumps(profile, indent=2)}

YOUR OBJECTIVE:

Determine exactly what must be researched to produce an accurate, relevant, current, well-supported report.

Do NOT perform the research yourself.
Do NOT invent sources or findings.
Do NOT write the final report.

Instead, create a structured research blueprint that tells downstream agents:

* What questions need to be answered
* What evidence is required
* Which sources should be prioritized
* How recent the evidence should be
* Which claims require cross-verification
* Where conflicting evidence may exist
* What limitations and research gaps should be investigated

RESEARCH PLANNING REQUIREMENTS:

1. Define the central research goal.

2. Break the topic into 3–8 focused research tasks.

3. Each task must answer a distinct research question or fulfill a distinct research purpose.

4. Prioritize tasks based on their importance to answering the user's actual question.

5. Match the research depth to the user's:

   * purpose
   * audience
   * requested depth
   * technical level

6. Prioritize primary and authoritative evidence where available.

7. Identify appropriate source categories for every task, such as:

   * academic papers
   * systematic reviews
   * official documentation
   * government publications
   * standards organizations
   * company technical reports
   * industry reports
   * reputable news organizations
   * expert analysis
   * datasets
   * benchmark results

8. Use academic evidence when the topic involves scientific, technical, medical, economic, or research claims.

9. Use industry and primary sources when the topic involves:

   * products
   * technologies
   * companies
   * software
   * current market conditions
   * implementation practices

10. Prefer recent evidence for rapidly changing topics.

11. Identify which parts of the research require historical/background sources versus current sources.

12. Identify claims that should be verified using multiple independent sources.

13. Identify areas where evidence may conflict, be uncertain, incomplete, or biased.

14. Identify important research gaps that downstream researchers should investigate.

15. Avoid redundant or low-value research tasks.

16. Make tasks specific enough that another research agent can execute them without guessing.

17. Optimize the plan for efficient research:

* avoid unnecessary searches
* combine closely related questions
* prioritize high-value evidence
* avoid researching information that will not contribute to the final report

18. For each task, specify the key questions that researchers should answer.

19. For each task, specify the evidence requirements.

20. For each task, specify whether current evidence, historical evidence, academic evidence, industry evidence, or multiple source types are required.

21. For topics involving comparisons, ensure the research plan identifies consistent comparison criteria.

22. For topics involving quantitative claims, require verification of:

* methodology
* sample/population
* date
* measurement
* assumptions
* limitations

23. For controversial or uncertain topics, require multiple perspectives and explicit identification of disagreement rather than assuming one interpretation is correct.

24. For rapidly changing technologies, products, policies, or markets, prioritize the most recent reliable evidence while retaining older sources when they provide necessary historical context.

25. The final research plan should support a report that distinguishes:

* established facts
* evidence-supported conclusions
* expert interpretations
* unresolved questions
* uncertainty

OUTPUT FORMAT:

Return ONLY valid JSON.

Use exactly this structure:

{
"research_goal": "...",
"research_strategy": {
"depth": "...",
"recency_requirement": "...",
"evidence_standard": "...",
"verification_strategy": "..."
},
"tasks": [
{
"task_id": "task_1",
"title": "...",
"description": "...",
"research_questions": [
"...",
"..."
],
"evidence_requirements": [
"...",
"..."
],
"priority": "high",
"source_types": [
"academic",
"industry"
],
"requires_cross_verification": true
}
],
"cross_cutting_requirements": [
"...",
"..."
],
"potential_conflicts": [
"...",
"..."
],
"research_gaps": [
"...",
"..."
]
}

RULES:

* Create between 3 and 8 tasks.
* Every task must have a clear and non-overlapping research purpose.
* Every task must contain at least one research question.
* Every task must contain at least one evidence requirement.
* priority must be exactly one of:
  "high", "medium", "low"
* source_types must be a non-empty list.
* requires_cross_verification must be a boolean.
* Do not perform research.
* Do not invent sources.
* Do not invent findings.
* Do not answer the research questions.
* Do not generate the final report.
* Do not include citations.
* Do not include markdown.
* Do not include commentary outside the JSON.
* Return ONLY valid JSON.
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