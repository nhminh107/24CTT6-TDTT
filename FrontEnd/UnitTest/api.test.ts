import { apiFetch, itineraryApi } from "../src/lib/api";
import { authStorage } from "../src/lib/auth";

describe("apiFetch", () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ ok: true }),
      })
    ) as jest.Mock;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("nên tự gắn x-user-id và Authorization khi đã có auth trong storage", async () => {
    authStorage.setGoogleUid("google-uid-123");
    authStorage.setIdToken("id-token-123");

    await apiFetch("/api/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    const headers = init.headers as Headers;

    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("x-user-id")).toBe("google-uid-123");
    expect(headers.get("Authorization")).toBe("Bearer id-token-123");
  });

  it("nên giữ nguyên request khi chưa có auth trong storage", async () => {
    await apiFetch("/api/public");

    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    const headers = init.headers as Headers;

    expect(headers.get("x-user-id")).toBeNull();
    expect(headers.get("Authorization")).toBeNull();
  });
});

describe("itineraryApi", () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ status: "success" }),
      })
    ) as jest.Mock;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("nên gọi endpoint select với method POST và body đúng contract", async () => {
    await itineraryApi.select("user-1", "Bữa trưa", { id: "res-1" });

    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];

    expect(url).toContain("/api/v1/itinerary/select");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({
      user_id: "user-1",
      meal: "Bữa trưa",
      restaurant_data: { id: "res-1" },
    });
  });

  it("nên gọi endpoint reorder với ordered_items đúng contract", async () => {
    await itineraryApi.reorder("user-1", [{ id: "item-1", meal: "Bữa tối" }]);

    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];

    expect(url).toContain("/api/v1/itinerary/reorder");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({
      user_id: "user-1",
      ordered_items: [{ id: "item-1", meal: "Bữa tối" }],
    });
  });
});
