export function getAuthErrorMessage(
  error: unknown,
  fallback: string,
): string {
  const code =
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string"
      ? error.code
      : "";

  switch (code) {
    case "auth/invalid-credential":
    case "auth/wrong-password":
    case "auth/user-not-found":
      return "Invalid email or password.";
    case "auth/invalid-email":
      return "Enter a valid email address.";
    case "auth/email-already-in-use":
      return "An account with this email already exists.";
    case "auth/weak-password":
      return "Choose a stronger password with at least 6 characters.";
    case "auth/too-many-requests":
      return "Too many attempts from this device. Please wait a while and try again.";
    case "auth/network-request-failed":
      return "Network error. Check your connection and try again.";
    default:
      return fallback;
  }
}
