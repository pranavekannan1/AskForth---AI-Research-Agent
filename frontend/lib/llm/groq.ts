import "server-only";
import Groq from "groq-sdk";

const model = process.env.GROQ_MODEL ?? "openai/gpt-oss-120b";

export function isLlmConfigured() { return Boolean(process.env.GROQ_API_KEY); }

export async function generateResponse(message: string, system = "You are a careful research assistant. Be factual, precise, and clear.") {
  if (!isLlmConfigured()) return "";
  const groq = new Groq({ apiKey: process.env.GROQ_API_KEY, timeout: 25_000, maxRetries: 1 });
  const response = await groq.chat.completions.create({ model, temperature: 0.2, messages: [{ role: "system", content: system }, { role: "user", content: message }] });
  return response.choices[0]?.message?.content?.trim() ?? "";
}
