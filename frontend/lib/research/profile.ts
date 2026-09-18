export type ResearchPurpose = "academic" | "business" | "personal" | "other";
export type ResearchDepth = "quick" | "standard" | "deep" | "academic-deep";
export type ResearchTone = "academic" | "professional" | "technical" | "human";

export type ResearchProfile = {
  topic: string;
  purpose: ResearchPurpose;
  audience: string;
  depth: ResearchDepth;
  reportType: string;
  tone: ResearchTone;
  needsCitations: boolean;
  geographicScope?: string;
};

export const DEFAULT_PROFILE: Omit<ResearchProfile, "topic"> = {
  purpose: "other", audience: "a general audience", depth: "standard",
  reportType: "research brief", tone: "professional", needsCitations: true,
};
