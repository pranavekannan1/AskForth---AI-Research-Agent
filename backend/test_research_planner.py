from services.research_planner import create_research_plan


import json

from services import research_planner


def test_create_research_plan_validates_mocked_model_response(monkeypatch):
    response = {
        "research_goal": "Assess the impact",
        "tasks": [
            {
                "task_id": "task_1",
                "title": "Benefits",
                "description": "Assess documented benefits.",
                "priority": "high",
                "source_types": ["academic"],
            },
            {
                "task_id": "task_2",
                "title": "Risks",
                "description": "Assess documented risks.",
                "priority": "medium",
                "source_types": ["official"],
            },
            {
                "task_id": "task_3",
                "title": "Gaps",
                "description": "Identify evidence gaps.",
                "priority": "low",
                "source_types": ["industry"],
            },
        ],
    }
    monkeypatch.setattr(
        research_planner,
        "generate_response",
        lambda _: json.dumps(response),
    )

    plan = research_planner.create_research_plan(
        topic="Impact of generative AI",
        profile={"purpose": "Academic project"},
    )

    assert plan["research_goal"] == "Assess the impact"
    assert len(plan["tasks"]) == 3
    assert plan["tasks"][0]["priority"] == "high"


def test_validate_research_plan_rejects_too_few_tasks():
    assert research_planner.validate_research_plan(
        {"research_goal": "Goal", "tasks": []},
        "Topic",
    ) is None