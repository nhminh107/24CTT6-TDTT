import { authStorage } from "../src/lib/auth";

describe("authStorage", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it("nên lưu và đọc id token từ localStorage", () => {
    const dispatchSpy = jest.spyOn(window, "dispatchEvent");

    authStorage.setIdToken("token-123");

    expect(authStorage.getIdToken()).toBe("token-123");
    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(Event));
  });

  it("nên lưu và đọc google uid từ localStorage", () => {
    const dispatchSpy = jest.spyOn(window, "dispatchEvent");

    authStorage.setGoogleUid("uid-123");

    expect(authStorage.getGoogleUid()).toBe("uid-123");
    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(Event));
  });

  it("nên clear toàn bộ thông tin auth", () => {
    authStorage.setIdToken("token-123");
    authStorage.setGoogleUid("uid-123");

    authStorage.clear();

    expect(authStorage.getIdToken()).toBeNull();
    expect(authStorage.getGoogleUid()).toBeNull();
  });
});
