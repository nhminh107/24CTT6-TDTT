import { NextResponse } from "next/server";
import { getApiV1BaseUrl } from "@/lib/apiBase";

const apiBaseUrl = getApiV1BaseUrl();

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const placeId = searchParams.get("place_id")?.trim() || "";

  if (!placeId) {
    return NextResponse.json({ status: "error", message: "Missing place_id" }, { status: 400 });
  }

  try {
    const response = await fetch(
      `${apiBaseUrl}/maps/place-detail?place_id=${encodeURIComponent(placeId)}`,
      { cache: "no-store" }
    );
    const data = await response.json().catch(() => ({ status: "error" }));
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ status: "error", message: "Failed to fetch place detail" }, { status: 500 });
  }
}
