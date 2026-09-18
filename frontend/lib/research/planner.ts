import { generateResponse, isLlmConfigured } from "@/lib/llm/groq";
import type { ResearchProfile } from "./profile";
export type ResearchPlan = { question: string; tasks: string[] };
const stripJson = (value: string) => value.replace(/```json|```/g, "").trim();
export async function createResearchPlan(profile: ResearchProfile): Promise<ResearchPlan> {
  const fallback = fallbackPlan(profile); if (!isLlmConfigured()) return fallback;
  try { const response = await generateResponse(`Create 3 to 6 focused research tasks. Return only JSON: {"question":"...","tasks":["..."]}. Profile: ${JSON.stringify(profile)}`); const parsed = JSON.parse(stripJson(response)) as ResearchPlan; if (!Array.isArray(parsed.tasks) || parsed.tasks.length < 3) return fallback; return { question: profile.topic, tasks: parsed.tasks.slice(0, 6).map(String) }; } catch { return fallback; }
}
function fallbackPlan(profile: ResearchProfile): ResearchPlan {
  const focus = profile.geographicScope ? ` with a focus on ${profile.geographicScope}` : "";
  const tasks = [`Define the scope, key concepts, and current context of ${profile.topic}${focus}.`, `Identify major evidence, findings, and debates relevant to ${profile.topic}.`, profile.purpose === "business" ? `Assess market implications, opportunities, risks, and competitors for ${profile.topic}.` : `Assess benefits, limitations, risks, and unanswered questions for ${profile.topic}.`, `Develop practical conclusions and recommendations for ${profile.audience}.`];
  return { question: profile.topic, tasks: tasks.slice(0, profile.depth === "quick" ? 3 : 4) };
}
