import { auth, authPersistence } from "@/lib/firebase";

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "production"
    ? "https://askforth-ai-research-agent.onrender.com"
    : "http://127.0.0.1:8000")
).replace(/\/$/, "");

async function request(endpoint: string, options: RequestInit = {}) {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, options);
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : { detail: await response.text() };

    if (!response.ok) {
      throw new Error(data.detail || "Backend request failed");
    }

    return data;
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `The browser blocked or could not reach ${API_URL}. Check the deployed backend CORS settings and NEXT_PUBLIC_API_URL.`,
      );
    }
    throw error;
  }
}

export async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {},
) {
  try {
    await authPersistence;
  } catch {
    throw new Error("Firebase authentication could not be initialized. Check the public Firebase environment variables.");
  }

  const user = auth.currentUser;

  if (!user) {
    throw new Error("User is not logged in");
  }

  const idToken = await user.getIdToken();

  return request(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      Authorization: `Bearer ${idToken}`,
    },
  });
}

export async function publicFetch(
  endpoint: string,
  options: RequestInit = {},
) {
  return request(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
}
