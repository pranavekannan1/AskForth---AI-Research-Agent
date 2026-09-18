export type ResearchSource = {
  title: string;
  url: string;
  content: string;
};

export async function searchWeb(
  query: string
): Promise<ResearchSource[]> {
  // Temporary implementation.
  // We will connect a real search provider next.

  return [
    {
      title: `Research source for: ${query}`,
      url: "https://example.com",
      content: `No real source retrieved yet for: ${query}`,
    },
  ];
}