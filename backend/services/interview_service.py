from sqlalchemy.orm import Session

from services.llm_service import generate_response
from services.research_service import (
    add_answer,
    complete_research_profile,
    set_current_question,
)


def generate_interview_question(topic: str, previous_answers: list[dict]):
    prompt = f"""
You are ResearchOS, an AI research assistant.

Research topic:
{topic}

Previous answers:
{previous_answers}

Collect only these three basic requirements, in order:
1. Purpose — what the report is needed for.
2. Audience — who will read/use it.
3. Depth — quick, normal, or deep.

Ask exactly ONE unanswered question. Keep it short and conversational.
Do not ask about research methodology, datasets, hypotheses, statistics,
citation style, or technical implementation.
Do not perform research and do not generate a report yet.
Return ONLY the question.
"""
    return generate_response(prompt).strip()


def project_to_dict(project):
    return {
        "session_id": project.id,
        "user_id": project.user_id,
        "topic": project.topic,
        "status": project.status,
        "question_index": project.question_index,
        "current_question": project.current_question,
        "question": project.current_question,
        "answers": project.answers or [],
        "profile": project.profile or {},
        "research_plan": project.research_plan or {},
        "report": project.report,
        "sources": project.sources or [],
        "report_status": project.report_status,
        "messages": project.messages or [],
    }


def process_interview_answer(
    db: Session,
    session_id: str,
    topic: str,
    question: str,
    answer: str,
):
    project = add_answer(
        db,
        session_id,
        question,
        answer,
    )

    if not project:
        return None

    if project.question_index >= 3:
        completed = complete_research_profile(
            db,
            session_id,
        )

        return {
            **project_to_dict(completed),
            "message": "Research requirements collected successfully.",
        }

    next_question = generate_interview_question(
        topic,
        project.answers,
    )

    project = set_current_question(
        db,
        project,
        next_question,
    )

    return {
        **project_to_dict(project),
        "question": next_question,
    }
