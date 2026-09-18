import { generateResponse } from "@/lib/llm/groq";

export async function generateInterviewQuestions(topic: string) {
  const prompt = `
You are an AI research preparation assistant.

The user wants to research:

"${topic}"

Before researching, determine what information is necessary
to understand the user's research goal.

Generate 3 to 5 natural questions.

You MUST determine:
- purpose
- audience
- desired depth
- report type
- tone
- citation requirements

Ask questions conversationally.

Return ONLY valid JSON:

{
  "questions": [
    "question 1",
    "question 2",
    "question 3"
  ]
}
`;

  const response = await generateResponse(prompt);

  const cleaned = response
    .replace(/```json/g, "")
    .replace(/```/g, "")
    .trim();

  return JSON.parse(cleaned);
}