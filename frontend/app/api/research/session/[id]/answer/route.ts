import { NextResponse } from "next/server";
import { completeProfile, getNextQuestion, getResearchSession, recordAnswer } from "@/lib/research/session";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    const session = getResearchSession(id);
    if (!session) return NextResponse.json({ error: "Research session not found or expired." }, { status: 404 });
    const { answer } = await request.json();
    if (!(typeof answer === "string" || typeof answer === "boolean") || (typeof answer === "string" && (!answer.trim() || answer.length > 1000))) return NextResponse.json({ error: "Provide a valid answer up to 1000 characters." }, { status: 400 });
    recordAnswer(session, typeof answer === "string" ? answer.trim() : answer);
    return NextResponse.json({ session, nextQuestion: getNextQuestion(session), profile: session.completed ? completeProfile(session) : undefined });
  } catch (error) { return NextResponse.json({ error: error instanceof Error ? error.message : "Failed to save answer." }, { status: 400 }); }
}
