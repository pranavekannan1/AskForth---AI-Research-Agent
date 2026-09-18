from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.database import get_db
from core.firebase import verify_firebase_token
from core.config import settings

from services.research_service import (
    create_research_session,
    get_research_session,
    list_research_projects,
    save_interview_answer,
)

from services.interview_service import (
    get_next_interview_question,
)

from services.research_planner import generate_research_plan
from services.research_report_service import generate_research_report


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Askforth AI Research Agent Backend",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ask-forth-ai-research-agent.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class ResearchSessionRequest(BaseModel):
    topic: str


class InterviewAnswerRequest(BaseModel):
    answer: str


class ResearchPlanRequest(BaseModel):
    topic: str
    profile: dict


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Askforth backend is running",
        "status": "healthy",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "askforth-backend",
    }


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {exc}",
        )


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    token = authorization.replace("Bearer ", "", 1).strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing Firebase token",
        )

    try:
        user = verify_firebase_token(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase token",
        )

    return {
        "message": f"Hello {user.get('email', 'user')}",
        "reply": f"You said: {request.message}",
    }


# ============================================================
# CREATE RESEARCH SESSION
# ============================================================

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
            detail="Research topic cannot be empty",
        )

    session = create_research_session(
        db=db,
        user_id=current_user["uid"],
        topic=topic,
    )

    return {
        "session_id": session.id,
        "topic": session.topic,
        "status": session.status,
        "question_index": session.question_index,
        "current_question": session.current_question,
    }


# ============================================================
# GET SINGLE RESEARCH SESSION
# ============================================================

@app.get("/research/session/{session_id}")
def get_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_research_session(
        db=db,
        session_id=session_id,
        user_id=current_user["uid"],
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    return {
        "session_id": session.id,
        "topic": session.topic,
        "status": session.status,
        "question_index": session.question_index,
        "current_question": session.current_question,
        "answers": session.answers or [],
        "profile": session.profile or {},
        "research_plan": session.research_plan or {},
        "report": session.report,
        "sources": session.sources or [],
        "report_status": session.report_status,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


# ============================================================
# INTERVIEW
# ============================================================

@app.post("/research/session/{session_id}/interview")
def submit_interview_answer(
    session_id: str,
    request: InterviewAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answer = request.answer.strip()

    if not answer:
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty",
        )

    session = get_research_session(
        db=db,
        session_id=session_id,
        user_id=current_user["uid"],
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    try:
        result = save_interview_answer(
            db=db,
            session=session,
            answer=answer,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save interview answer: {exc}",
        )

    return result


# ============================================================
# RESEARCH PROJECT HISTORY
# ============================================================

@app.get("/research/projects")
def get_research_projects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = list_research_projects(
        db=db,
        user_id=current_user["uid"],
    )

    return {
        "projects": [
            {
                "session_id": project.id,
                "topic": project.topic,
                "status": project.status,
                "report_status": project.report_status,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }
            for project in projects
        ]
    }


# ============================================================
# RESEARCH PLAN
# ============================================================

@app.post("/research/plan")
def create_research_plan(
    request: ResearchPlanRequest,
    current_user=Depends(get_current_user),
):
    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Research topic cannot be empty",
        )

    try:
        plan = generate_research_plan(
            topic=topic,
            profile=request.profile,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate research plan: {exc}",
        )

    return plan


# ============================================================
# GENERATE RESEARCH REPORT
# ============================================================

@app.post("/research/session/{session_id}/report")
def generate_report(
    session_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_research_session(
        db=db,
        session_id=session_id,
        user_id=current_user["uid"],
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Research session not found",
        )

    profile = session.profile or {}

    # --------------------------------------------------------
    # Generate research plan if it does not already exist
    # --------------------------------------------------------

    if not session.research_plan:
        try:
            plan = generate_research_plan(
                topic=session.topic,
                profile=profile,
            )

            session.research_plan = plan
            db.commit()
            db.refresh(session)

        except Exception as exc:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate research plan: {exc}",
            )

    # --------------------------------------------------------
    # Generate evidence-based report
    # --------------------------------------------------------

    try:
        session.report_status = "generating"
        db.commit()

        result = generate_research_report(
            topic=session.topic,
            profile=profile,
            plan=session.research_plan,
        )

    except Exception as exc:
        session.report_status = "failed"
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate research report: {exc}",
        )

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    session.report = result.get("report", "")
    session.sources = result.get("sources", [])
    session.report_status = "completed"
    session.status = "completed"

    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "report_status": session.report_status,
        "report": session.report,
        "sources": session.sources,
        "research_plan": session.research_plan,
    }