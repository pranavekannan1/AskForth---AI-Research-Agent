import { NextResponse } from "next/server";
import Groq from "groq-sdk";

export async function GET() {
  if (!process.env.GROQ_API_KEY) return NextResponse.json({ models: [], configured: false, message: "Set GROQ_API_KEY to enable live model access." });
  try {
    const groq = new Groq({ apiKey: process.env.GROQ_API_KEY, timeout: 10_000, maxRetries: 0 });
    const models = await groq.models.list();
    return NextResponse.json({ models: models.data.map((model) => model.id), configured: true });
  } catch { return NextResponse.json({ error: "Failed to fetch models" }, { status: 502 }); }
}
