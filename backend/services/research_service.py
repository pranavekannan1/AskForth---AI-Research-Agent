from uuid import uuid4

from sqlalchemy.orm import Session

from models.research_project import ResearchProject
from models.user import User


DEFAULT_PROFILE = {
    "purpose": None,
    "audience": None,
    "depth": None,
}


def get_or_create_user(db: Session, user_data: dict):
    uid = user_data["uid"]
    user = db.query(User).filter(User.uid == uid).first()

    if user:
        return user

    user = User(
        uid=uid,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_research_session(db: Session, topic: str, user_data: dict):
    user = get_or_create_user(db, user_data)

    project = ResearchProject(
        id=str(uuid4()),
        user_id=user.uid,
        topic=topic,
        status="interview",
        question_index=0,
        answers=[],
        profile=dict(DEFAULT_PROFILE),
        research_plan={},
        report=None,
        sources=[],
        report_status="not_started",
        messages=[],
    )

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_research_session(db: Session, session_id: str):
    return (
        db.query(ResearchProject)
        .filter(ResearchProject.id == session_id)
        .first()
    )


def list_research_projects(db: Session, user_id: str):
    return (
        db.query(ResearchProject)
        .filter(ResearchProject.user_id == user_id)
        .order_by(ResearchProject.updated_at.desc())
        .all()
    )


def delete_research_session(db: Session, session_id: str):
    project = get_research_session(db, session_id)
    if not project:
        return None

    db.delete(project)
    db.commit()
    return project


def append_message(
    db: Session,
    project: ResearchProject,
    role: str,
    content: str,
):
    messages = list(project.messages or [])
    messages.append({
        "role": role,
        "content": content,
    })
    project.messages = messages
    db.commit()
    db.refresh(project)
    return project


def add_answer(
    db: Session,
    session_id: str,
    question: str,
    answer: str,
):
    project = get_research_session(db, session_id)
    if not project:
        return None

    answers = list(project.answers or [])
    answers.append({
        "question": question,
        "answer": answer,
    })

    project.answers = answers
    project.question_index += 1

    messages = list(project.messages or [])
    messages.append({
        "role": "user",
        "content": answer,
    })
    project.messages = messages

    db.commit()
    db.refresh(project)
    return project


def set_current_question(
    db: Session,
    project: ResearchProject,
    question: str,
):
    project.current_question = question

    messages = list(project.messages or [])
    if not messages or messages[-1].get("content") != question:
        messages.append({
            "role": "assistant",
            "content": question,
        })
    project.messages = messages

    db.commit()
    db.refresh(project)
    return project


def complete_research_profile(db: Session, session_id: str):
    project = get_research_session(db, session_id)
    if not project:
        return None

    answers = project.answers or []
    profile = dict(project.profile or DEFAULT_PROFILE)

    if len(answers) >= 1:
        profile["purpose"] = answers[0]["answer"]
    if len(answers) >= 2:
        profile["audience"] = answers[1]["answer"]
    if len(answers) >= 3:
        profile["depth"] = answers[2]["answer"]

    project.profile = profile
    project.status = "ready"
    project.current_question = None

    messages = list(project.messages or [])
    messages.append({
        "role": "assistant",
        "content": (
            "Perfect. I have enough context. "
            "I’ll now build the research plan, investigate the topic, "
            "and prepare an evidence-based report."
        ),
    })
    project.messages = messages

    db.commit()
    db.refresh(project)
    return project
