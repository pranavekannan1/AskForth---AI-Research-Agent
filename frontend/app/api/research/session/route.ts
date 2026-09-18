import { NextResponse } from "next/server";
import { createResearchSession, getNextQuestion } from "@/lib/research/session";

export async function POST(request: Request) {
  try {
    const { topic } = await request.json();
    if (typeof topic !== "string" || topic.trim().length < 3 || topic.length > 500) return NextResponse.json({ error: "Provide a research topic between 3 and 500 characters." }, { status: 400 });
    const session = createResearchSession(topic.trim());
    return NextResponse.json({ session, nextQuestion: getNextQuestion(session) }, { status: 201 });
  } catch { return NextResponse.json({ error: "Invalid JSON request body." }, { status: 400 }); }
}
