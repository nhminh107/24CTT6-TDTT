import { getApiOrigin, getApiV1BaseUrl } from "../src/lib/apiBase";

describe("apiBase", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
    delete process.env.API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it("nên ưu tiên NEXT_PUBLIC_API_URL cho request client", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://wrong.example.com/api/v1";
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.com";

    expect(getApiOrigin()).toBe("https://api.example.com");
  });

  it("nên bỏ hậu tố /api/v1 khi caller tự nối path /api/v1", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.com/api/v1/";

    expect(getApiOrigin()).toBe("https://api.example.com");
  });

  it("nên tạo base /api/v1 đúng cho Next API proxy", () => {
    process.env.API_BASE_URL = "https://api.example.com/";

    expect(getApiV1BaseUrl()).toBe("https://api.example.com/api/v1");
  });

  it("không nhân đôi /api/v1 cho Next API proxy", () => {
    process.env.API_BASE_URL = "https://api.example.com/api/v1/";

    expect(getApiV1BaseUrl()).toBe("https://api.example.com/api/v1");
  });
});
