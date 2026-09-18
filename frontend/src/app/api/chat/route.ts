import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({
    message: "Chat API is working",
  });
}
