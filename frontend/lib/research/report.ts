import { generateResponse, isLlmConfigured } from "@/lib/llm/groq";
import type { ResearchProfile } from "./profile";
import type { ResearchResult } from "./executor";
export async function createReport(profile: ResearchProfile, results: ResearchResult[]) {
  const evidence = results.map((item) => `Task: ${item.task}\nFinding: ${item.result}`).join("\n\n");
  if (isLlmConfigured()) { try { const report = await generateResponse(`Write a ${profile.tone} ${profile.reportType} about ${profile.topic} for ${profile.audience}. Use only the supplied findings; flag uncertainty and do not fabricate sources. Include headings and recommendations. Findings:\n${evidence}`); if (report) return report; } catch { /* fallback */ } }
  return `# ${profile.topic}\n\n## Research brief\nThis project is ready for source-backed investigation. The sections below are a structured starting point, not verified evidence.\n\n${results.map((r, i) => `## ${i + 1}. ${r.task}\n${r.result}`).join("\n\n")}\n\n## Next steps\nValidate each finding against primary or authoritative sources, record citations, and revise this brief for ${profile.audience}.`;
}
