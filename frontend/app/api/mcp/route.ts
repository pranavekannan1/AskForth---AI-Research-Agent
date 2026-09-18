import { NextResponse } from "next/server";

const backendUrl =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "production"
    ? "https://askforth-ai-research-agent.onrender.com"
    : "http://127.0.0.1:8000");

const tools = [
  {
    name: "diagnostics",
    description: "Read safe frontend and backend connectivity diagnostics.",
    inputSchema: { type: "object", properties: {} },
  },
];

async function readDiagnostics() {
  const startedAt = Date.now();
  let backend: { status: string; detail?: string; response?: unknown };

  try {
    const response = await fetch(`${backendUrl}/health`, {
      signal: AbortSignal.timeout(8_000),
      cache: "no-store",
    });
    const responseBody = await response.text();
    let parsedBody: unknown = responseBody;
    try {
      parsedBody = JSON.parse(responseBody);
    } catch {
      // Keep non-JSON health responses safe and readable.
    }

    backend = response.ok
      ? { status: "healthy", response: parsedBody }
      : { status: "error", detail: `HTTP ${response.status}`, response: parsedBody };
  } catch (error) {
    backend = {
      status: "unreachable",
      detail: error instanceof Error ? error.message : "Health check failed",
    };
  }

  return {
    backendUrl,
    backend,
    firebaseConfigured: Boolean(process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID),
    groqConfigured: Boolean(process.env.GROQ_API_KEY),
    elapsedMs: Date.now() - startedAt,
    safeNextSteps: backend.status === "healthy"
      ? ["Check Firebase authentication and backend CORS for the deployed frontend origin."]
      : ["Confirm the backend deployment is running.", "Set NEXT_PUBLIC_API_URL to the public backend URL.", "Check the backend deployment logs."],
  };
}

export async function GET() {
  return NextResponse.json({ name: "ResearchOS diagnostics", tools });
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    if (body?.jsonrpc === "2.0") {
      if (body.method === "initialize") {
        return NextResponse.json({
          jsonrpc: "2.0",
          id: body.id,
          result: {
            protocolVersion: "2025-06-18",
            capabilities: { tools: {} },
            serverInfo: { name: "researchos-diagnostics", version: "1.0.0" },
          },
        });
      }

      if (body.method === "notifications/initialized") {
        return new NextResponse(null, { status: 202 });
      }

      if (body.method === "tools/list") {
        return NextResponse.json({ jsonrpc: "2.0", id: body.id, result: { tools } });
      }

      if (body.method === "tools/call" && body.params?.name === "diagnostics") {
        const result = await readDiagnostics();
        return NextResponse.json({
          jsonrpc: "2.0",
          id: body.id,
          result: {
            content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
            structuredContent: result,
          },
        });
      }

      return NextResponse.json({
        jsonrpc: "2.0",
        id: body.id,
        error: { code: -32601, message: "Method or tool not found" },
      }, { status: 404 });
    }

    if (body?.tool !== "diagnostics") {
      return NextResponse.json({ error: "Unknown tool" }, { status: 404 });
    }
    return NextResponse.json({ tool: "diagnostics", result: await readDiagnostics() });
  } catch {
    return NextResponse.json({ error: "Invalid diagnostics request" }, { status: 400 });
  }
}