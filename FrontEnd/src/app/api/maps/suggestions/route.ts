import { NextResponse } from "next/server";
import { getApiV1BaseUrl } from "@/lib/apiBase";

const apiBaseUrl = getApiV1BaseUrl();

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
