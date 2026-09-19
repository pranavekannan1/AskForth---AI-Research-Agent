# AskForth

AskForth is an evidence-first AI research workspace for turning a broad question into a focused, source-backed report.

Instead of returning a single chat answer, AskForth guides the researcher through a short interview, builds a research plan, investigates the topic, and keeps the resulting work organized in a persistent workspace.

## Why use AskForth?

- **Start with a clear goal**: the short interview clarifies purpose, audience, and desired depth before research begins.
- **Save research time**: planning and source discovery are handled in one workflow instead of across many browser tabs.
- **Get structured results**: reports are organized with headings, tables, findings, uncertainty, and source links.
- **Keep context in one place**: research projects, interview answers, reports, and follow-up questions remain connected.
- **Continue the investigation**: ask follow-up questions about a completed report without starting over.
- **Return to work later**: authentication and PostgreSQL persistence restore research history and the active session after refreshes or browser restarts.
- **Share a useful deliverable**: completed reports include print-friendly formatting for saving as PDF.
- **Protect user workspaces**: Firebase Authentication and user-scoped backend queries keep each research history private to its owner.

## How it works

```text
Create an account or log in
  |
Choose a research topic
  |
Answer a short goal-setting interview
  |
Review the generated research plan
  |
Run evidence-focused web research
  |
Read and save the report as PDF
  |
Ask follow-up questions in the same session
```

## Main features

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
- Follow-up chat that can improve and rewrite the saved report
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

## Optional MCP user tools

AskForth includes a separate, credential-free MCP server for local report
review. It is not imported by the web application and does not access Firebase,
the database, provider APIs, browser storage, or user tokens.

From `backend`, after installing `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe mcp_server.py
```

Available tools:

- `validate_report`: inspect headings and source links locally.
- `classify_revision_request`: identify common edit requests such as shorter
  summaries, stronger evidence, a humanized tone, or a new section.
- `report_review`: return a local quality checklist without uploading content.

## Frontend

From `frontend`:

```powershell
npm install
npm run dev
```

## User flow

```text
Login
  -> New Research
  -> Short interview
  -> Research plan
  -> Web research
  -> Saved report
  -> Request report improvements
  -> Save the updated report as PDF
```

Refreshing the browser restores the authenticated user and the active research session from PostgreSQL.

## PDF

Open a completed report and choose **Save report as PDF**. The browser print stylesheet hides the application chrome and formats the report for A4 paper.
