import { auth, authPersistence } from "@/lib/firebase";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {},
) {
  await authPersistence;

  const user = auth.currentUser;

  if (!user) {
    throw new Error("User is not logged in");
  }

  const idToken = await user.getIdToken();

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      Authorization: `Bearer ${idToken}`,
    },
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : { detail: await response.text() };

  if (!response.ok) {
    throw new Error(data.detail || "Backend request failed");
  }

  return data;
}

export async function publicFetch(
  endpoint: string,
  options: RequestInit = {},
) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : { detail: await response.text() };

  if (!response.ok) {
    throw new Error(data.detail || "Backend request failed");
  }

  return data;
}
