from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.database import get_db
from core.firebase import resolve_password_reset_email

from services.interview_service import (
    generate_interview_question,
    process_interview_answer,
    project_to_dict,
)

from services.llm_service import generate_response

from services.research_planner import (
    create_research_plan,
)

from services.research_report_service import (
    generate_research_report,
    generate_research_followup,
)

from services.research_service import (
    create_research_session,
    delete_research_session,
    get_research_session,
    list_research_projects,
    set_current_question,
)


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="ResearchOS API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request Models
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=10000,
    )


class ResearchSessionRequest(BaseModel):
    topic: str = Field(
        min_length=2,
        max_length=5000,
    )


class InterviewAnswerRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=5000,
    )

    answer: str = Field(
        min_length=1,
        max_length=10000,
    )


class ResearchPlanRequest(BaseModel):
    topic: str = Field(
        min_length=2,
        max_length=5000,
    )

    profile: dict


class ResearchChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=10000,
    )


class PasswordResetRequest(BaseModel):
    identifier: str = Field(
        min_length=3,
        max_length=320,
    )


# ============================================================
# Basic Routes
# ============================================================

@app.get("/")
def root():
    return {
        "message": "ResearchOS API is running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


@app.post("/auth/recovery-email")
def recovery_email(request: PasswordResetRequest):
    try:
        email = resolve_password_reset_email(request.identifier)
    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail="No account was found for that email or user ID.",
        ) from exc

    return {"email": email}


# ============================================================
# Chat
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    return {
        "response": generate_response(request.message),
        "user_id": current_user["uid"],
    }


# ============================================================
# Create Research Session
# ============================================================

@app.post("/research/session")
def create_session(
    request: ResearchSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = request.topic.strip()

    project = create_research_session(
        db,
        topic,
        current_user,
    )

    question = generate_interview_question(
        topic,
        [],
    )

    project = set_current_question(
        db,
        project,
        question,
    )

    return {
        **project_to_dict(project),
        "question": question,
        "message": "Research session created successfully",
    }


# ============================================================
# Get Research Session
# ============================================================

@app.get("/research/session/{session_id}")
def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_research_session(
        db,
        session_id,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    if project.user_id != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this research session",
        )

    return project_to_dict(project)


# ============================================================
# Research Interview
# ============================================================

@app.post("/research/session/{session_id}/interview")
def interview(
    session_id: str,
    request: InterviewAnswerRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_research_session(
        db,
        session_id,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    if project.user_id != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this research session",
        )

    if project.status != "interview":
        raise HTTPException(
            status_code=409,
            detail="Research interview is already complete",
        )

    if (
        project.current_question
        and request.question.strip()
        != project.current_question.strip()
    ):
        raise HTTPException(
            status_code=409,
            detail="Question does not match the current interview question",
        )

    result = process_interview_answer(
        db,
        session_id,
        project.topic,
        request.question.strip(),
        request.answer.strip(),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    return result


# ============================================================
# Research History
# ============================================================

@app.get("/research/projects")
def research_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = list_research_projects(
        db,
        current_user["uid"],
    )

    return {
        "projects": [
            project_to_dict(project)
            for project in projects
        ],
        "count": len(projects),
    }


@app.delete("/research/session/{session_id}")
def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_research_session(db, session_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    if project.user_id != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this research session",
        )

    delete_research_session(db, session_id)
    return {"session_id": session_id, "deleted": True}


# ============================================================
# Continue Research Conversation
# ============================================================

@app.post("/research/session/{session_id}/chat")
def research_chat(
    session_id: str,
    request: ResearchChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_research_session(
        db,
        session_id,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    if project.user_id != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this research session",
        )

    if (
        project.report_status != "completed"
        or not project.report
    ):
        raise HTTPException(
            status_code=409,
            detail="Research report is not ready yet",
        )

    user_message = request.message.strip()

    messages = list(project.messages or [])

    messages.append({
        "role": "user",
        "content": user_message,
    })

    project.messages = messages

    db.commit()
    db.refresh(project)

    try:
        response, new_sources = generate_research_followup(
            topic=project.topic,
            profile=project.profile or {},
            plan=project.research_plan or {},
            report=project.report or "",
            conversation=messages,
        )

        if not response or not response.strip():
            raise RuntimeError(
                "Research follow-up returned an empty response."
            )

        messages = list(project.messages or [])

        messages.append({
            "role": "assistant",
            "content": response,
        })

        project.messages = messages

        existing_sources = list(
            project.sources or []
        )

        for source in new_sources:
            if source not in existing_sources:
                existing_sources.append(source)

        project.sources = existing_sources[:100]

        db.commit()
        db.refresh(project)

        return {
            "session_id": project.id,
            "message": response,
            "messages": project.messages or [],
            "sources": project.sources or [],
        }

    except Exception as exc:

        # Remove the unsent user message so that
        # a retry does not duplicate it.
        messages = list(project.messages or [])

        if (
            messages
            and messages[-1].get("role") == "user"
            and messages[-1].get("content") == user_message
        ):
            messages.pop()

        project.messages = messages

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Research chat failed: {exc}",
        )


# ============================================================
# Research Planner
# ============================================================

@app.post("/research/plan")
def create_plan(
    request: ResearchPlanRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = request.topic.strip()

    plan = create_research_plan(
        topic=topic,
        profile=request.profile,
    )

    return {
        "topic": topic,
        "plan": plan,
        "user_id": current_user["uid"],
    }


# ============================================================
# Generate Research Report
# ============================================================

@app.post("/research/session/{session_id}/report")
def generate_report(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Find project
    # --------------------------------------------------------

    project = get_research_session(
        db,
        session_id,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    # --------------------------------------------------------
    # Security
    # --------------------------------------------------------

    if project.user_id != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this research session",
        )

    # --------------------------------------------------------
    # Interview must be completed
    # --------------------------------------------------------

    if project.status not in {
        "ready",
        "researching",
        "completed",
    }:
        raise HTTPException(
            status_code=409,
            detail="Complete the research interview first",
        )

    # --------------------------------------------------------
    # If report already exists, return it
    # --------------------------------------------------------

    if (
        project.report_status == "completed"
        and project.report
    ):
        return project_to_dict(project)

    try:

        # ----------------------------------------------------
        # Step 1: Research planning
        # ----------------------------------------------------

        project.report_status = "planning"
        project.status = "researching"

        db.commit()
        db.refresh(project)

        plan = create_research_plan(
            topic=project.topic,
            profile=project.profile or {},
        )

        # ----------------------------------------------------
        # Validate research plan
        # ----------------------------------------------------

        if not plan:
            raise RuntimeError(
                "Research planner returned an empty plan."
            )

        if (
            plan.get("planning_error")
            or len(plan.get("tasks", [])) < 3
        ):
            raise RuntimeError(
                plan.get(
                    "planning_error",
                    "Unable to create a valid research plan",
                )
            )

        # ----------------------------------------------------
        # Save research plan
        # ----------------------------------------------------

        project.research_plan = plan
        project.report_status = "researching"

        db.commit()
        db.refresh(project)

        # ----------------------------------------------------
        # Step 2: Perform research + generate report
        # ----------------------------------------------------

        # IMPORTANT:
        # generate_research_report expects:
        # topic
        # profile
        # plan
        #
        # Do NOT pass project.messages here.

        report, sources = generate_research_report(
            topic=project.topic,
            profile=project.profile or {},
            plan=plan,
        )

        # ----------------------------------------------------
        # Validate report
        # ----------------------------------------------------

        if not report or not report.strip():
            raise RuntimeError(
                "Research engine returned an empty report."
            )

        # ----------------------------------------------------
        # Step 3: Save final report
        # ----------------------------------------------------

        project.report = report
        project.sources = sources or []

        project.report_status = "completed"
        project.status = "completed"

        messages = list(
            project.messages or []
        )

        messages.append({
            "role": "assistant",
            "content": (
                "Your research report is ready. "
                "You can open the report or continue "
                "asking follow-up questions in this "
                "same workspace."
            ),
        })

        project.messages = messages

        db.commit()
        db.refresh(project)

        return project_to_dict(project)

    except Exception as exc:

        # ----------------------------------------------------
        # Research failed
        # ----------------------------------------------------

        project.report_status = "failed"

        # Keep the interview completed so the
        # user can retry research without doing
        # the interview again.
        project.status = "ready"

        db.commit()

        print()
        print("=" * 70)
        print("RESEARCH REPORT ERROR")
        print("=" * 70)
        print(str(exc))
        print("=" * 70)
        print()

        raise HTTPException(
            status_code=500,
            detail=(
                "Research report generation failed: "
                f"{exc}"
            ),
        )