import { NextResponse } from "next/server";

const apiBaseUrl =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000/api/v1";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("q")?.trim() || "";

  if (!query) {
    return NextResponse.json([]);
  }

  try {
    const response = await fetch(
      `${apiBaseUrl}/maps/suggestions?q=${encodeURIComponent(query)}`,
      { cache: "no-store" }
    );
    const data = await response.json().catch(() => []);
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json([]);
  }
}
