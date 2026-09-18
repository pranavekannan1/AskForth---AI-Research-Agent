import { generateResponse, isLlmConfigured } from "@/lib/llm/groq";
import type { ResearchProfile } from "./profile";
export type ResearchResult = { task: string; result: string; mode: "ai" | "guided" };
export async function executeResearch(tasks: string[], profile: ResearchProfile): Promise<ResearchResult[]> {
  return Promise.all(tasks.map(async (task) => { if (isLlmConfigured()) { try { const result = await generateResponse(`Research task: ${task}\nProfile: ${JSON.stringify(profile)}\nGive a concise evidence-aware analysis. Do not invent citations.`); if (result) return { task, result, mode: "ai" as const }; } catch { /* use transparent guided fallback */ } } return { task, result: `Guided research prompt: ${task} Collect authoritative, current sources before treating any claim as evidence. Tailor the final analysis for ${profile.audience}.`, mode: "guided" as const }; }));
}
