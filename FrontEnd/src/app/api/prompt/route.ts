import { NextResponse } from "next/server";

const apiBaseUrl =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000/api/v1";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const response = await fetch(`${apiBaseUrl}/prompt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await response.json().catch(() => ({
      status: "error",
      message: "Phản hồi không hợp lệ.",
      result: []
    }));
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({
      status: "error",
      message: "Không thể kết nối tới máy chủ.",
      result: []
    });
  }
}
