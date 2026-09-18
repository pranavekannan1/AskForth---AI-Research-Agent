# ResearchOS

ResearchOS is a persistent, evidence-first AI research workspace.

## What is complete

- Firebase email/password authentication
- Persistent browser login
- PostgreSQL-backed users and research projects
- User-owned research history
- Short 3-step research interview
- LLM-generated research plan
- Groq Compound web research with website visits
- Evidence-aware Markdown research reports
- Compact, PDF-friendly report tables
- Retrieved source links
- Persistent conversation messages
- Follow-up chat inside the same research session
- Active-session restoration after refresh/browser restart
- Account menu with logout and switch-account behavior
- Research retry state when a report generation fails
- A4 print/save-as-PDF styling

## Backend

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe init_db.py
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Create `backend/.env` from `backend/.env.example` and set:

- `DATABASE_URL`
- `GROQ_API_KEY`
- `FIREBASE_SERVICE_ACCOUNT_PATH` for local development, or
- `FIREBASE_SERVICE_ACCOUNT_JSON` for deployment

Never commit real secrets.

## Frontend

From `frontend`:

```powershell
npm install
npm run dev
```

Create `frontend/.env.local` from `frontend/.env.local.example` and provide the Firebase web configuration plus the backend API URL.

Open `http://localhost:3000`.

## User flow

```text
Login
  -> New Research
  -> Short interview
  -> Research plan
  -> Web research
  -> Saved report
  -> Follow-up conversation
```

Refreshing the browser restores the authenticated user and the active research session from PostgreSQL.

## PDF

Open a completed report and choose **Save report as PDF**. The browser print stylesheet hides the application chrome and formats the report for A4 paper.
