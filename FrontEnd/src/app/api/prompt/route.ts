import { NextResponse } from "next/server";
import { getApiV1BaseUrl } from "@/lib/apiBase";

const apiBaseUrl = getApiV1BaseUrl();

export async function POST(request: Request) {
  const timestamp = new Date().toISOString();
  console.log(`[FRONTEND_API_LOG] [${timestamp}] POST /api/prompt received.`);
  
  try {
    const body = await request.json();
    console.log(`[FRONTEND_API_LOG] Request body:`, JSON.stringify(body));

    console.log(`[FRONTEND_API_LOG] Proxying request to backend: ${apiBaseUrl}/prompt`);
    const response = await fetch(`${apiBaseUrl}/prompt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    console.log(`[FRONTEND_API_LOG] Backend responded with status: ${response.status}`);

    const data = await response.json().catch(() => {
      console.error(`[FRONTEND_API_LOG] Failed to parse backend JSON response.`);
      return {
        status: "error",
        message: "Phản hồi không hợp lệ.",
        result: []
      };
    });

    if (data.status === "error") {
      console.warn(`[FRONTEND_API_LOG] Backend returned error status:`, data.message);
    } else {
      console.log(`[FRONTEND_API_LOG] Backend success. Result count: ${data.result?.length || 0}`);
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error(`[FRONTEND_API_LOG] !!! Error in frontend proxy:`, error);
    return NextResponse.json({
      status: "error",
      message: "Không thể kết nối tới máy chủ.",
      result: []
    });
  }
}
