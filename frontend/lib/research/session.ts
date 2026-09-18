import { DEFAULT_PROFILE, type ResearchProfile } from "./profile";

export type InterviewField = Exclude<keyof ResearchProfile, "topic">;
export type InterviewQuestion = { field: InterviewField; prompt: string; help: string; options?: string[] };
export type ResearchSession = { id: string; profile: Partial<ResearchProfile>; answers: Partial<Record<InterviewField, string | boolean>>; currentQuestion: number; completed: boolean; createdAt: string; updatedAt: string };

const sessions = new Map<string, ResearchSession>();
const QUESTIONS: InterviewQuestion[] = [
  { field: "purpose", prompt: "What will you use this research for?", help: "This changes the approach and evidence standard.", options: ["Academic work", "Business decision", "Personal learning", "Something else"] },
  { field: "audience", prompt: "Who will read the finished report?", help: "For example: a professor, leadership team, clients, or a general audience." },
  { field: "depth", prompt: "How deeply should we investigate it?", help: "Choose a depth that matches your deadline.", options: ["Quick overview", "Standard brief", "Deep analysis", "Academic deep dive"] },
  { field: "reportType", prompt: "What kind of deliverable do you need?", help: "For example: literature review, market scan, briefing note, or comparison." },
  { field: "tone", prompt: "Which writing style fits the audience?", help: "We will use this when drafting the report.", options: ["Academic", "Professional", "Technical", "Clear and human"] },
  { field: "needsCitations", prompt: "Should the report include source citations?", help: "Citations are recommended for academic and decision-making work.", options: ["Yes, include citations", "No citations needed"] },
  { field: "geographicScope", prompt: "Is there a geographic focus we should use?", help: "You can enter a country, region, or ‘global’." },
];

export function createResearchSession(topic: string): ResearchSession {
  const now = new Date().toISOString();
  const session: ResearchSession = { id: crypto.randomUUID(), profile: { topic }, answers: {}, currentQuestion: 0, completed: false, createdAt: now, updatedAt: now };
  sessions.set(session.id, session); return session;
}
export function getResearchSession(id: string) { return sessions.get(id); }
export function getNextQuestion(session: ResearchSession): InterviewQuestion | null { return session.completed ? null : QUESTIONS[session.currentQuestion] ?? null; }
function toPurpose(value: string): ResearchProfile["purpose"] { const text = value.toLowerCase(); return text.includes("academic") || text.includes("thesis") ? "academic" : text.includes("business") || text.includes("market") ? "business" : text.includes("personal") ? "personal" : "other"; }
function toDepth(value: string): ResearchProfile["depth"] { const text = value.toLowerCase(); return text.includes("academic") ? "academic-deep" : text.includes("deep") ? "deep" : text.includes("quick") ? "quick" : "standard"; }
function toTone(value: string): ResearchProfile["tone"] { const text = value.toLowerCase(); return text.includes("academic") ? "academic" : text.includes("technical") ? "technical" : text.includes("human") ? "human" : "professional"; }

export function recordAnswer(session: ResearchSession, answer: string | boolean): ResearchSession {
  const question = getNextQuestion(session); if (!question) throw new Error("This interview is already complete.");
  session.answers[question.field] = answer;
  if (question.field === "purpose") session.profile.purpose = toPurpose(String(answer));
  else if (question.field === "depth") session.profile.depth = toDepth(String(answer));
  else if (question.field === "tone") session.profile.tone = toTone(String(answer));
  else if (question.field === "needsCitations") session.profile.needsCitations = typeof answer === "boolean" ? answer : /^(yes|true)/i.test(answer);
  else session.profile[question.field] = String(answer);
  session.currentQuestion += 1; session.completed = session.currentQuestion >= QUESTIONS.length; session.updatedAt = new Date().toISOString(); return session;
}
export function completeProfile(session: ResearchSession): ResearchProfile { if (!session.completed) throw new Error("Complete the interview before starting research."); return { topic: session.profile.topic ?? "", ...DEFAULT_PROFILE, ...session.profile } as ResearchProfile; }
