# Researcher — AI Research Agent

Researcher is a polished Next.js research-workspace MVP. It interviews the user to build a research profile, creates a plan, runs research tasks in parallel, and returns a structured report workspace.

## Included

- Conversation-first research interview
- In-memory research sessions with validation and adaptive profile building
- Research planning and parallel task execution
- Groq-powered analysis when configured
- Transparent guided fallback when no API key is available
- A responsive three-pane research UI

## Run locally

1. Install dependencies with `npm install`.
2. Copy `.env.example` to `.env.local`.
3. Add a Groq API key if you want live model responses.
4. Run `npm run dev`, then open `http://localhost:3000`.

The application works without a key in guided mode. Guided mode never claims its generated prompts are verified research or citations.

## Notes

Sessions are intentionally stored in memory for this MVP. Use a database or durable cache before deploying multiple instances or relying on long-lived sessions.
