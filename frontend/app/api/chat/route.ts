import { NextResponse } from "next/server";

import { generateResponse } from "@/lib/llm/groq";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const response = await generateResponse(body.message);

    return NextResponse.json({
      response,
    });
  } catch (error) {
    console.error("LLM error:", error);

    return NextResponse.json(
      {
        error: "Failed to generate response",
      },
      { status: 500 }
    );
  }
}