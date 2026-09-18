import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    apiKey: Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY),
    authDomain: Boolean(process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN),
    projectId: Boolean(process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID),
    storageBucket: Boolean(process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET),
    messagingSenderId: Boolean(
      process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
    ),
    appId: Boolean(process.env.NEXT_PUBLIC_FIREBASE_APP_ID),
  });
}