"use client";

import {
  FormEvent,
  KeyboardEvent,
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { onAuthStateChanged, signOut, User } from "firebase/auth";

import { auth, authPersistence } from "@/lib/firebase";
import { authenticatedFetch } from "@/lib/api";


type Answer = {
  question: string;
  answer: string;
};

type Profile = {
  purpose?: string | null;
  audience?: string | null;
  depth?: string | null;
};

type Task = {
  task_id: string;
  title: string;
  description: string;
  priority: string;
  source_types: string[];
};

type Plan = {
  research_goal?: string;
  tasks?: Task[];
  planning_error?: string;
};

type StoredMessage = {
  role: "assistant" | "user";
  content: string;
};

type Project = {
  session_id: string;
  user_id: string;
  topic: string;
  status: string;
  question_index: number;
  current_question?: string | null;
  question?: string | null;
  answers: Answer[];
  profile: Profile;
  research_plan?: Plan;
  report?: string | null;
  sources?: string[];
  report_status?: string;
  messages?: StoredMessage[];
};

type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  text: string;
};

type ContextMenu = {
  project: Project;
  x: number;
  y: number;
};

const ACTIVE_SESSION_KEY = "researchos_active_session";

function formatInlineMarkdown(text: string): ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*)/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    return <span key={index}>{part}</span>;
  });
}

function splitTableRow(line: string): string[] {
  let value = line.trim();
  if (value.startsWith("|")) value = value.slice(1);
  if (value.endsWith("|")) value = value.slice(0, -1);

  return value.split("|").map((cell) => cell.trim());
}

function isTableSeparator(line: string): boolean {
  const cells = splitTableRow(line);
  return cells.length > 0 && cells.every((cell) => /^:?-{2,}:?$/.test(cell));
}

function renderReportMarkdown(markdown: string): ReactNode[] {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const elements: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i].trimEnd();

    if (!line.trim()) {
      i += 1;
      continue;
    }

    if (line.startsWith("# ")) {
      elements.push(<h1 key={key++}>{formatInlineMarkdown(line.slice(2).trim())}</h1>);
      i += 1;
      continue;
    }

    if (line.startsWith("## ")) {
      elements.push(<h2 key={key++}>{formatInlineMarkdown(line.slice(3).trim())}</h2>);
      i += 1;
      continue;
    }

    if (line.startsWith("### ")) {
      elements.push(<h3 key={key++}>{formatInlineMarkdown(line.slice(4).trim())}</h3>);
      i += 1;
      continue;
    }

    if (line.startsWith("#### ")) {
      elements.push(<h4 key={key++}>{formatInlineMarkdown(line.slice(5).trim())}</h4>);
      i += 1;
      continue;
    }

    if (line.trim().startsWith("|") && i + 1 < lines.length && lines[i + 1].trim().startsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i]);
        i += 1;
      }

      if (tableLines.length >= 2 && isTableSeparator(tableLines[1])) {
        const headers = splitTableRow(tableLines[0]);
        const body = tableLines.slice(2).map(splitTableRow);

        elements.push(
          <div className="report-table-wrapper" key={key++}>
            <table className="report-table">
              <thead>
                <tr>
                  {headers.map((header, index) => (
                    <th key={index}>{formatInlineMarkdown(header)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {headers.map((_, cellIndex) => (
                      <td key={cellIndex}>{formatInlineMarkdown(row[cellIndex] || "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>,
        );
        continue;
      }
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i += 1;
      }
      elements.push(
        <ul key={key++}>
          {items.map((item, index) => <li key={index}>{formatInlineMarkdown(item)}</li>)}
        </ul>,
      );
      continue;
    }

    if (/^\s*\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+[.)]\s+/, ""));
        i += 1;
      }
      elements.push(
        <ol key={key++}>
          {items.map((item, index) => <li key={index}>{formatInlineMarkdown(item)}</li>)}
        </ol>,
      );
      continue;
    }

    if (line.startsWith("> ")) {
      elements.push(<blockquote key={key++}>{formatInlineMarkdown(line.slice(2))}</blockquote>);
      i += 1;
      continue;
    }

    elements.push(<p key={key++}>{formatInlineMarkdown(line.trim())}</p>);
    i += 1;
  }

  return elements;
}

async function exportReportToPdf() {
  window.print();
}

function projectMessages(project: Project): ChatMessage[] {
  if (project.messages?.length) {
    return project.messages.map((message, index) => ({
      id: `stored-${index}`,
      role: message.role,
      text: message.content,
    }));
  }

  const result: ChatMessage[] = [
    {
      id: "workspace",
      role: "assistant",
      text: `Research workspace: ${project.topic}`,
    },
  ];

  project.answers.forEach((answer, index) => {
    result.push({
      id: `question-${index}`,
      role: "assistant",
      text: answer.question,
    });
    result.push({
      id: `answer-${index}`,
      role: "user",
      text: answer.answer,
    });
  });

  const question = project.question || project.current_question;
  if (question && !project.answers.some((answer) => answer.question === question)) {
    result.push({ id: "current-question", role: "assistant", text: question });
  }

  return result;
}

function sourceLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export default function ResearchPage() {
  const router = useRouter();
  const conversationRef = useRef<HTMLDivElement>(null);

  const [authReady, setAuthReady] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [session, setSession] = useState<Project | null>(null);
  const [topic, setTopic] = useState("");
  const [answer, setAnswer] = useState("");
  const [followup, setFollowup] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState<"chat" | "report">("chat");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState(false);

  const refreshSession = useCallback(async (id: string) => {
    const data = await authenticatedFetch(`/research/session/${id}`) as Project;
    setSession(data);
    setTopic(data.topic || "");
    setMessages(projectMessages(data));
    setActiveView(data.report ? "report" : "chat");
    return data;
  }, []);

  const loadHistory = useCallback(async () => {
    const data = await authenticatedFetch("/research/projects");
    setProjects(Array.isArray(data) ? data : data.projects || []);
  }, []);

  useEffect(() => {
    let mounted = true;
    let unsubscribe: (() => void) | undefined;

    async function initializeAuth() {
      try {
        await authPersistence;
        if (!mounted) return;

        unsubscribe = onAuthStateChanged(auth, (currentUser) => {
          if (!mounted) return;
          setUser(currentUser);
          setAuthReady(true);

          if (!currentUser) {
            setRestoring(false);
            router.replace("/login");
          }
        });
      } catch (err) {
        console.error("Auth initialization failed", err);
        if (mounted) {
          setAuthReady(true);
          setRestoring(false);
          setError("Unable to restore your account. Please log in again.");
        }
      }
    }

    initializeAuth();
    return () => {
      mounted = false;
      unsubscribe?.();
    };
  }, [router]);

  useEffect(() => {
    if (!authReady || !user) return;

    let cancelled = false;

    async function restoreWorkspace() {
      setRestoring(true);
      setError("");

      try {
        await loadHistory();
        const activeId = localStorage.getItem(ACTIVE_SESSION_KEY);

        if (activeId) {
          try {
            await refreshSession(activeId);
          } catch {
            localStorage.removeItem(ACTIVE_SESSION_KEY);
            setSession(null);
            setMessages([]);
            setActiveView("chat");
          }
        }
      } catch (err) {
        console.error("Workspace restore failed", err);
        if (!cancelled) setError("Could not load your research history.");
      } finally {
        if (!cancelled) setRestoring(false);
      }
    }

    restoreWorkspace();
    return () => { cancelled = true; };
  }, [authReady, user, loadHistory, refreshSession]);

  // Keep the UI synchronized with a report that is being generated in another tab
  // or while the browser was refreshed during research.
  useEffect(() => {
    if (!session?.session_id) return;
    if (
      session.report_status !== "planning" &&
      session.report_status !== "researching" &&
      session.report_status !== "generating" &&
      session.report_status !== "revising"
    ) return;

    const timer = window.setInterval(async () => {
      try {
        const data = await authenticatedFetch(`/research/session/${session.session_id}`) as Project;
        setSession(data);
        setMessages(projectMessages(data));
        if (data.report) setActiveView("report");
        if (data.report_status === "completed" || data.report_status === "failed") {
          await loadHistory();
        }
      } catch (err) {
        console.error("Research status polling failed", err);
      }
    }, 4000);

    return () => window.clearInterval(timer);
  }, [session?.session_id, session?.report_status, loadHistory]);

  useEffect(() => {
    const element = conversationRef.current;
    if (!element) return;
    element.scrollTo({ top: element.scrollHeight, behavior: "smooth" });
  }, [messages, activeView, loading]);

  useEffect(() => {
    function closeContextMenu() {
      setContextMenu(null);
    }

    window.addEventListener("click", closeContextMenu);
    window.addEventListener("resize", closeContextMenu);
    return () => {
      window.removeEventListener("click", closeContextMenu);
      window.removeEventListener("resize", closeContextMenu);
    };
  }, []);

  function appendMessage(role: "assistant" | "user", text: string) {
    setMessages((current) => [
      ...current,
      {
        id: `${Date.now()}-${Math.random()}`,
        role,
        text,
      },
    ]);
  }

  async function startResearch() {
    if (!topic.trim()) {
      setError("Enter a research topic first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessages([]);
    setSession(null);
    localStorage.removeItem(ACTIVE_SESSION_KEY);

    try {
      const data = await authenticatedFetch("/research/session", {
        method: "POST",
        body: JSON.stringify({ topic: topic.trim() }),
      }) as Project & { message?: string };

      localStorage.setItem(ACTIVE_SESSION_KEY, data.session_id);
      setSession(data);
      setTopic(data.topic);
      setActiveView("chat");

      const restored = projectMessages(data);
      if (restored.length) {
        setMessages(restored);
      } else {
        appendMessage("assistant", `Great. I’ll help you research “${data.topic}”.`);
        if (data.question) appendMessage("assistant", data.question);
      }

      await loadHistory();
    } catch (err) {
      console.error("Start research failed", err);
      setError(err instanceof Error ? err.message : "Could not start research. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function submitInterviewAnswer(e?: FormEvent) {
    e?.preventDefault();
    if (!session || session.status !== "interview") return;

    const question = session.question || session.current_question || "";
    const text = answer.trim();
    if (!question) return;
    if (!text) {
      setError("Please enter an answer.");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");
    appendMessage("user", text);

    try {
      const data = await authenticatedFetch(
        `/research/session/${session.session_id}/interview`,
        {
          method: "POST",
          body: JSON.stringify({ question, answer: text }),
        },
      ) as Project & { message?: string };

      setSession(data);
      setMessages(projectMessages(data));

      if (data.status === "ready") {
        await generateReport(data.session_id);
      }

      await loadHistory();
    } catch (err) {
      console.error("Saving interview answer failed", err);
      setError("Could not save your answer. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function generateReport(id = session?.session_id) {
    if (!id) return;

    setLoading(true);
    setError("");
    setActiveView("chat");

    try {
      const data = await authenticatedFetch(`/research/session/${id}/report`, {
        method: "POST",
      }) as Project;

      localStorage.setItem(ACTIVE_SESSION_KEY, id);
      setSession(data);
      setMessages(projectMessages(data));
      setActiveView(data.report ? "report" : "chat");
      await loadHistory();
    } catch (err) {
      console.error("Research report generation failed", err);
      setError(
        err instanceof Error
          ? err.message
          : "Research report generation failed. Please try again.",
      );
      try {
        await refreshSession(id);
      } catch {
        // Keep the original error visible.
      }
    } finally {
      setLoading(false);
    }
  }

  async function sendFollowup(e?: FormEvent) {
    e?.preventDefault();
    if (!session || !session.report || session.report_status !== "completed") return;

    const text = followup.trim();
    if (!text) return;

    setLoading(true);
    setError("");
    setFollowup("");
    appendMessage("user", text);
    setSession((current) => current ? {
      ...current,
      report_status: "revising",
    } : current);

    try {
      const data = await authenticatedFetch(
        `/research/session/${session.session_id}/chat`,
        {
          method: "POST",
          body: JSON.stringify({ message: text }),
        },
      ) as Project;

      setMessages(
        (data.messages || []).map((message: StoredMessage, index: number) => ({
          id: `chat-${index}`,
          role: message.role,
          text: message.content,
        })),
      );

      setSession((current) => current ? {
        ...current,
        status: "ready",
        report_status: "completed",
        report: data.report || current.report,
        messages: data.messages || current.messages || [],
        sources: data.sources || current.sources || [],
      } : current);

      if (data.report && data.report !== session.report) {
        setActiveView("report");
      }
      await loadHistory();
    } catch (err) {
      console.error("Sending research message failed", err);
      setError(err instanceof Error ? err.message : "Could not improve the report. Please try again.");
      try {
        await refreshSession(session.session_id);
      } catch {
        // Keep the original error visible.
      }
    } finally {
      setLoading(false);
    }
  }

  async function openProject(id: string) {
    setSidebarOpen(false);
    setLoading(true);
    setError("");

    try {
      localStorage.setItem(ACTIVE_SESSION_KEY, id);
      await refreshSession(id);
    } catch (err) {
      console.error("Opening research failed", err);
      setError("Could not open research. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function deleteProject() {
    if (!deleteTarget) return;

    const id = deleteTarget.session_id;
    setDeleting(true);
    setError("");

    try {
      await authenticatedFetch(`/research/session/${id}`, { method: "DELETE" });
      setProjects((current) => current.filter((project) => project.session_id !== id));
      setDeleteTarget(null);
      setContextMenu(null);

      if (session?.session_id === id) {
        newResearch();
      }
    } catch (err) {
      console.error("Deleting research failed", err);
      setError("Could not delete research. Please try again.");
    } finally {
      setDeleting(false);
    }
  }

  function newResearch() {
    setSidebarOpen(false);
    localStorage.removeItem(ACTIVE_SESSION_KEY);
    setSession(null);
    setTopic("");
    setAnswer("");
    setFollowup("");
    setMessages([]);
    setError("");
    setActiveView("chat");
  }

  async function logout() {
    setSidebarOpen(false);
    setAccountOpen(false);
    localStorage.removeItem(ACTIVE_SESSION_KEY);
    await signOut(auth);
    router.replace("/login");
  }

  function handleComposerKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
    form: HTMLFormElement | null,
  ) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form?.requestSubmit();
    }
  }

  const progress = session ? Math.min((session.answers.length / 3) * 100, 100) : 0;
  const interviewActive = session?.status === "interview";
  const reportReady = session?.report_status === "completed" && !!session.report;
  const researching =
    loading ||
    session?.report_status === "planning" ||
    session?.report_status === "researching" ||
    session?.report_status === "generating" ||
    session?.report_status === "revising";

  const history = useMemo(() => projects.slice(0, 30), [projects]);
  const displayName = user?.displayName || user?.email?.split("@")[0] || "Researcher";
  const initials = displayName.slice(0, 1).toUpperCase();

  if (!authReady || restoring) {
    return (
      <div className="research-shell">
        <main className="research-main restoring-screen">
          <div className="restoring-content">
            <div className="welcome-icon">✦</div>
            <h2>Restoring your ResearchOS workspace…</h2>
            <p>Your account, research history, and active session are being restored.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="research-shell">
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`research-sidebar ${sidebarOpen ? "open" : ""}`}>
        <button
          className="sidebar-close"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        >
          ×
        </button>
        <div className="research-brand">
          <span>✦</span>
          AskForth
        </div>

        <button className="new-research" onClick={newResearch}>
          <span>＋</span> New research
        </button>

        <div className="history-title">YOUR RESEARCH</div>
        <div className="history-list">
          {history.map((project) => (
            <button
              key={project.session_id}
              className={`history-item ${session?.session_id === project.session_id ? "active" : ""}`}
              onClick={() => openProject(project.session_id)}
              onContextMenu={(event) => {
                event.preventDefault();
                setContextMenu({ project, x: event.clientX, y: event.clientY });
              }}
              title={project.topic}
            >
              <span className="history-icon">◌</span>
              <span className="history-topic">{project.topic}</span>
            </button>
          ))}
          {!history.length && (
            <div className="history-empty">Your research projects will appear here.</div>
          )}
        </div>

        {contextMenu && (
          <div
            className="history-context-menu"
            style={{ left: contextMenu.x, top: contextMenu.y }}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              onClick={() => {
                setDeleteTarget(contextMenu.project);
                setContextMenu(null);
              }}
            >
              Delete conversation
            </button>
          </div>
        )}

        <div className="sidebar-bottom">
          <div className="engine-status">
            <span className="online-dot" />
            Research engine ready
          </div>
          <div className="sidebar-note">Evidence-first research workspace</div>

          <div className="account-wrap">
            {accountOpen && (
              <div className="account-menu">
                <div className="account-menu-header">
                  <div className="account-avatar large">{initials}</div>
                  <div>
                    <strong>{displayName}</strong>
                    <span>{user?.email}</span>
                  </div>
                </div>
                <button onClick={logout}>↪ Log out</button>
                <button onClick={logout}>⇄ Switch account</button>
              </div>
            )}

            <button
              className="account-button"
              onClick={() => setAccountOpen((open) => !open)}
              aria-expanded={accountOpen}
            >
              <span className="account-avatar">{initials}</span>
              <span className="account-info">
                <strong>{displayName}</strong>
                <small>{user?.email}</small>
              </span>
              <span className="account-more">⋮</span>
            </button>
          </div>
        </div>
      </aside>

      <main className="research-main">
        <header className="research-topbar">
          <button
            className="mobile-menu-button"
            aria-label="Open navigation"
            aria-expanded={sidebarOpen}
            onClick={() => setSidebarOpen(true)}
          >
            ☰
          </button>
          <div className="topbar-title">
            <div className="top-kicker">RESEARCH WORKSPACE</div>
            <h1>{session?.topic || "What would you like to research?"}</h1>
          </div>
          <div className="top-actions">
            <span className="engine-pill">AskForth · Research Engine</span>
            {session?.report && (
              <button
                className="view-toggle"
                onClick={() => setActiveView((view) => view === "report" ? "chat" : "report")}
              >
                {activeView === "report" ? "Conversation" : "Report"}
              </button>
            )}
          </div>
        </header>

        <section className="conversation" ref={conversationRef}>
          {!session && (
            <div className="welcome">
              <div className="welcome-icon">✦</div>
              <div className="welcome-eyebrow">ASKFORTH</div>
              <h2>Research, not just answers.</h2>
              <p>
                Give me a topic. I’ll clarify the goal, build a research plan,
                investigate evidence, identify uncertainty and contradictions,
                and produce a professional report you can save as PDF.
              </p>
              <div className="starter-grid">
                {[
                  "Impact of generative AI on software development",
                  "AI adoption in healthcare",
                  "Future of renewable energy",
                  "AI in education: opportunities and risks",
                ].map((suggestion) => (
                  <button key={suggestion} onClick={() => setTopic(suggestion)}>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {session && activeView === "chat" && (
            <div className="chat-workspace">
              <div className="progress-card">
                <div>
                  <strong>
                    {reportReady ? "Research complete" : researching ? "Research in progress" : "Research interview"}
                  </strong>
                  <span>
                    {reportReady
                      ? "Your report is saved. You can continue asking questions."
                      : `${session.answers.length} / 3 requirements collected`}
                  </span>
                </div>
                <div className="progress-track">
                  <i style={{ width: `${progress}%` }} />
                </div>
              </div>

              <div className="message-list">
                {messages.map((message) => (
                  <div key={message.id} className={`chat-message ${message.role}`}>
                    <div className="message-avatar">
                      {message.role === "assistant" ? "✦" : initials}
                    </div>
                    <div className="message-bubble">
                      {message.text}
                    </div>
                  </div>
                ))}

                {researching && !reportReady && (
                  <div className="chat-message assistant">
                    <div className="message-avatar">✦</div>
                    <div className="message-bubble research-progress-message">
                      <span className="dots">A is researching<span>.</span><span>.</span><span>.</span></span>
                      <small>Searching sources, comparing evidence, and preparing your report.</small>
                    </div>
                  </div>
                )}
              </div>

              {session.status === "ready" && !session.report && !researching && (
                <div className="ready-card">
                  <div>
                    <strong>Requirements complete.</strong>
                    <span>AskForth is ready to investigate the topic.</span>
                  </div>
                  <button onClick={() => generateReport()} disabled={loading}>
                    Start research →
                  </button>
                </div>
              )}

              {session.report_status === "failed" && (
                <div className="ready-card failed-card">
                  <div>
                    <strong>Research could not be completed.</strong>
                    <span>Your research session is still saved. You can retry.</span>
                  </div>
                  <button onClick={() => generateReport()} disabled={loading}>Retry research →</button>
                </div>
              )}

              {reportReady && (
                <div className="report-ready-card">
                  <div>
                    <span className="success-mark">✓</span>
                    <div>
                      <strong>Research report ready</strong>
                      <span>Ask follow-up questions below without starting a new research project.</span>
                    </div>
                  </div>
                  <button onClick={() => setActiveView("report")}>Open report</button>
                </div>
              )}
            </div>
          )}

          {session && activeView === "report" && (
            <div className="report-page">
              <div className="report-heading">
                <div className="report-label">RESEARCH REPORT</div>
                <h2>{session.topic}</h2>
                <p>Evidence-aware synthesis generated from the research plan and retrieved sources.</p>
                <div className="report-meta">
                  <span>AskForth</span>
                  <span>•</span>
                  <span>{session.profile?.depth || "Evidence-based"}</span>
                </div>
              </div>

              {researching && (
                <div className="researching-banner">
                  <strong>Research in progress</strong>
                  <span>Your report will appear here automatically when the research finishes.</span>
                </div>
              )}

              {session.report && (
                <article className="report-body">
                  {renderReportMarkdown(session.report)}
                </article>
              )}

              {!!session.sources?.length && (
                <section className="sources">
                  <h3>Retrieved sources</h3>
                  <ol>
                    {session.sources.map((source) => (
                      <li key={source}>
                        <a href={source} target="_blank" rel="noreferrer">
                          {sourceLabel(source)}
                        </a>
                      </li>
                    ))}
                  </ol>
                </section>
              )}

              {session.report && (
                <button className="print-report" onClick={exportReportToPdf}>
                  Save report as PDF
                </button>
              )}
            </div>
          )}
        </section>

        {error && (
          <div className="workspace-error">
            <span>{error}</span>
          </div>
        )}

        {session?.report && session.report_status === "completed" ? (
          <form className="research-composer" onSubmit={sendFollowup}>
            <textarea
              value={followup}
              onChange={(event) => setFollowup(event.target.value)}
              placeholder="Ask the agent to improve this report…"
              rows={2}
              onKeyDown={(event) => handleComposerKeyDown(event, event.currentTarget.form)}
              disabled={loading}
            />
            <div className="composer-footer">
              <span>Request edits, added detail, a different structure, or clearer conclusions</span>
              <button disabled={loading || !followup.trim()}>{loading ? "…" : "↑"}</button>
            </div>
          </form>
        ) : session && activeView === "report" ? (
          <div className="report-footer">
            <button onClick={() => setActiveView("chat")}>← Back to conversation</button>
            {session.report && <button onClick={exportReportToPdf}>Save as PDF</button>}
          </div>
        ) : (
          <form
            className="research-composer"
            onSubmit={session ? submitInterviewAnswer : (event) => {
              event.preventDefault();
              startResearch();
            }}
          >
            <textarea
              value={session ? answer : topic}
              onChange={(event) => session ? setAnswer(event.target.value) : setTopic(event.target.value)}
              placeholder={session ? "Answer the question…" : "Describe what you want to research…"}
              rows={2}
              disabled={loading || (session ? !interviewActive : false)}
              onKeyDown={(event) => handleComposerKeyDown(event, event.currentTarget.form)}
            />
            <div className="composer-footer">
              <span>{session ? "Enter to send · Shift + Enter for a new line" : "AskForth will ask a few short questions first"}</span>
              <button
                disabled={loading || !(session ? answer.trim() : topic.trim()) || (session ? !interviewActive : false)}
              >
                {loading ? "…" : "↑"}
              </button>
            </div>
          </form>
        )}
      </main>

      {deleteTarget && (
        <div className="confirmation-backdrop" role="presentation">
          <div
            className="confirmation-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
            aria-describedby="delete-dialog-description"
          >
            <h2 id="delete-dialog-title">Delete this conversation?</h2>
            <p id="delete-dialog-description">
              “{deleteTarget.topic}” will be permanently removed. This action cannot be undone.
            </p>
            <div className="confirmation-actions">
              <button onClick={() => setDeleteTarget(null)} disabled={deleting}>Cancel</button>
              <button className="danger-button" onClick={deleteProject} disabled={deleting}>
                {deleting ? "Deleting…" : "Delete conversation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
