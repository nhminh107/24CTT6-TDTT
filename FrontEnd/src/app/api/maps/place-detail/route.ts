import { NextResponse } from "next/server";

const apiBaseUrl =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://api.bmi-foodtour.io.vn/api/v1";

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
