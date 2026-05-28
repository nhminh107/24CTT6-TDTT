import { cn } from "../src/lib/utils";

describe("Hàm cn (classNames) trong utils", () => {
  it("nên nối các class hợp lệ lại với nhau", () => {
    const result = cn("class1", "class2");
    expect(result).toBe("class1 class2");
  });

  it("nên bỏ qua các giá trị falsy (false, null, undefined)", () => {
    const result = cn("class1", false, "class2", null, undefined);
    expect(result).toBe("class1 class2");
  });

  it("nên xử lý đúng khi có điều kiện ternary", () => {
    const isActive = true;
    const result = cn("base-class", isActive ? "active" : "inactive");
    expect(result).toBe("base-class active");
  });
});