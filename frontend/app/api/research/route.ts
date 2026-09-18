import { NextResponse } from "next/server";
import { executeResearch } from "@/lib/research/executor";
import { createResearchPlan } from "@/lib/research/planner";
import { createReport } from "@/lib/research/report";
import { DEFAULT_PROFILE, type ResearchProfile } from "@/lib/research/profile";

export async function POST(request: Request) {
  try {
    const { profile } = await request.json();
    if (!profile || typeof profile.topic !== "string" || !profile.topic.trim()) return NextResponse.json({ error: "A complete research profile with a topic is required." }, { status: 400 });
    const safeProfile: ResearchProfile = { ...DEFAULT_PROFILE, ...profile, topic: profile.topic.trim() };
    const plan = await createResearchPlan(safeProfile);
    const results = await executeResearch(plan.tasks, safeProfile);
    const report = await createReport(safeProfile, results);
    return NextResponse.json({ profile: safeProfile, plan, results, report, generatedAt: new Date().toISOString() });
  } catch (error) { console.error("Research error", error); return NextResponse.json({ error: "Research could not be completed. Please try again." }, { status: 500 }); }
}
