import { NextResponse } from "next/server";

import { generateInterviewQuestions } from "@/lib/research/interviewer";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    if (!body.topic || typeof body.topic !== "string") {
      return NextResponse.json(
        { error: "A research topic is required" },
        { status: 400 }
      );
    }

    const result = await generateInterviewQuestions(body.topic);

    return NextResponse.json(result);
  } catch (error) {
    console.error("Research interview error:", error);

    return NextResponse.json(
      { error: "Failed to generate interview questions" },
      { status: 500 }
    );
  }
}