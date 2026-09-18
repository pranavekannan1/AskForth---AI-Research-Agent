from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.database import get_db

from services.interview_service import (
    generate_interview_question,
    process_interview_answer,
    project_to_dict,
)

from services.llm_service import generate_response
from services.research_planner import create_research_plan

from services.research_service import (
    create_research_session,
    get_research_session,
    list_research_projects,
    set_current_question,
)

from services.research_report_service import (
    generate_research_report,
)


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Askforth API",
    version="1.0.0",
    description=(
        "Askforth - AI-powered research agent "
        "that turns questions into evidence-based reports."
    ),
)


# =========================================================
# CORS
# =========================================================

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


# =========================================================
# REQUEST MODELS
# =========================================================


class ChatRequest(BaseModel):
    message: str


class ResearchSessionRequest(BaseModel):
    topic: str


class ResearchAnswerRequest(BaseModel):
    answer: str


class ResearchPlanRequest(BaseModel):
    topic: str
    profile: dict


# =========================================================
# ROOT
# =========================================================


@app.get("/")
def root():
    return {
        "name": "Askforth API",
        "message": "Askforth backend is running",
        "version": "1.0.0",
    }


# =========================================================
# BASIC HEALTH CHECK
# =========================================================


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "askforth-backend",
    }


# =========================================================
# POSTGRESQL HEALTH CHECK
# =========================================================


@app.get("/health/db")
def database_health(
    db: Session = Depends(get_db),
):
    try:
        result = db.execute(
            text("SELECT 1")
        )

        return {
            "database": "connected",
            "result": result.scalar(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {exc}",
        )


# =========================================================
# CHAT
# =========================================================


@app.post("/chat")
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
):
    try:
        response = generate_response(
            request.message
        )

        return {
            "user_id": current_user["uid"],
            "message": request.message,
            "response": response,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"LLM request failed: {exc}",
        )


# =========================================================
# CREATE RESEARCH SESSION
# =========================================================


@app.post("/research/session")
def create_session(
    request: ResearchSessionRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Research topic cannot be empty.",
        )

    project = create_research_session(
        db=db,
        user_id=current_user["uid"],
        topic=topic,
    )

    return project_to_dict(project)


# =========================================================
# GET RESEARCH SESSION
# =========================================================


@app.get("/research/session/{session_id}")
def get_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_research_session(
        db=db,
        session_id=session_id,
        user_id=current_user["uid"],
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found.",
        )

    return project_to_dict(project)


# =========================================================
# INTERVIEW
# =========================================================


@app.post("/research/session/{session_id}/interview")
def answer_interview(
    session_id: str,
    request: ResearchAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_research_session(
        db=db,
        session_id=session_id,
        user_id=current_user["uid"],
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found.",
        )

    answer = request.answer.strip()

    if not answer:
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty.",
        )

    try:
        updated_project = process_interview_answer(
            db=db,
            project=project,
            answer=answer,
        )

        return project_to_dict(
            updated_project
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Interview processing failed: {exc}",
        )


# =========================================================
# RESEARCH PROJECT HISTORY
# =========================================================


@app.get("/research/projects")
def get_research_projects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = list_research_projects(
        db=db,
        user_id=current_user["uid"],
    )

    return [
        project_to_dict(project)
        for project in projects
    ]


# =========================================================
# RESEARCH PLAN
# =========================================================


@app.post("/research/plan")
def research_plan(
    request: ResearchPlanRequest,
    current_user=Depends(get_current_user),
):
    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Research topic cannot be empty.",
        )

    try:
        plan = create_research_plan(
            topic=topic,
            profile=request.profile,
        )

        return plan

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Research planning failed: {exc}",
        )


# =========================================================
# GENERATE RESEARCH REPORT
# =========================================================


@app.post("/research/session/{session_id}/report")
def generate_report(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_research_session(
        db=db,
        session_id=session_id,
        user_id=current_user["uid"],
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Research session not found.",
        )

    # -----------------------------------------------------
    # Prevent duplicate report generation
    # -----------------------------------------------------

    if project.report_status == "completed" and project.report:
        return project_to_dict(project)

    # -----------------------------------------------------
    # Research must have a completed interview/profile
    # -----------------------------------------------------

    if project.status not in (
        "ready",
        "researching",
        "completed",
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Research interview is not complete yet."
            ),
        )

    try:

        # -------------------------------------------------
        # Mark research as running
        # -------------------------------------------------

        project.report_status = "researching"
        project.status = "researching"

        db.commit()
        db.refresh(project)

        # -------------------------------------------------
        # Generate research plan
        # -------------------------------------------------

        plan = create_research_plan(
            topic=project.topic,
            profile=project.profile or {},
        )

        if not plan:
            raise RuntimeError(
                "Research planner returned an empty plan."
            )

        if plan.get("planning_error"):
            raise RuntimeError(
                plan["planning_error"]
            )

        tasks = plan.get("tasks", [])

        if len(tasks) < 3:
            raise RuntimeError(
                "Research plan must contain at least 3 tasks."
            )

        # Save plan immediately
        project.research_plan = plan

        db.commit()
        db.refresh(project)

        # -------------------------------------------------
        # Execute real web research + report generation
        # -------------------------------------------------

        report, sources = generate_research_report(
            topic=project.topic,
            profile=project.profile or {},
            plan=plan,
        )

        if not report:
            raise RuntimeError(
                "Research report generation returned no report."
            )

        # -------------------------------------------------
        # Save final research result
        # -------------------------------------------------

        project.report = report
        project.sources = sources or []

        project.report_status = "completed"
        project.status = "completed"

        db.commit()
        db.refresh(project)

        return project_to_dict(project)

    except Exception as exc:

        # -------------------------------------------------
        # Preserve failed state
        # -------------------------------------------------

        project.report_status = "failed"
        project.status = "ready"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Research report generation failed: {exc}"
            ),
        )


# =========================================================
# END
# =========================================================