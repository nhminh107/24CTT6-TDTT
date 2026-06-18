import {
  buildRestaurants,
  cn,
  formatMealDisplay,
  inferMealFromRestaurant,
} from "../src/lib/utils";

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

describe("Hàm buildRestaurants trong utils", () => {
  it("nên chuẩn hóa dữ liệu backend snake_case sang Restaurant dùng cho UI", () => {
    const restaurants = buildRestaurants([
      {
        id: "res-1",
        name: "Bún Chay An Nhiên",
        address: "12 Nguyễn Huệ",
        star: 4.6,
        avg_price: 55000,
        phone_num: "0909123456.0",
        image_url: "https:\\/\\/example.com\\/bun.jpg",
        semantic_text: "Món chay thanh đạm",
        assigned_meal: "Bữa trưa",
        warnings: [],
        notes: ["Ưu tiên món ít dầu"],
      },
    ]);

    expect(restaurants[0]).toMatchObject({
      id: "res-1",
      name: "Bún Chay An Nhiên",
      address: "12 Nguyễn Huệ",
      rating: 4.6,
      price: 55000,
      phone: "0909123456.0",
      imageUrl: "https://example.com/bun.jpg",
      semanticText: "Món chay thanh đạm",
      assignedMeal: "Bữa trưa",
      warnings: [],
      notes: ["Ưu tiên món ít dầu"],
      source: "ai",
    });
    expect(restaurants[0].mapUrl).toContain("google.com/maps/search");
  });

  it("nên phân biệt nhà hàng user tự thêm bằng source user", () => {
    const restaurants = buildRestaurants([
      {
        name: "Quán nhà tự thêm",
        address: "Gần khách sạn",
        isCustom: true,
      },
    ]);

    expect(restaurants[0].source).toBe("user");
    expect(restaurants[0].rating).toBe(0);
    expect(restaurants[0].price).toBe("Chưa cập nhật");
    expect(restaurants[0].semanticText).toBe("Chưa có mô tả.");
  });
});

describe("Hàm inferMealFromRestaurant trong utils", () => {
  it("nên chọn đúng bữa được hỗ trợ theo giờ hiện tại", () => {
    const meal = inferMealFromRestaurant(
      { meals: ["sáng", "trưa"] },
      new Date("2026-06-18T07:30:00+07:00")
    );

    expect(meal).toBe("Bữa sáng");
  });

  it("nên fallback theo thứ tự trưa, tối, sáng, phụ khi không có bữa theo giờ", () => {
    const meal = inferMealFromRestaurant(
      { meals: ["sáng", "tối"] },
      new Date("2026-06-18T12:00:00+07:00")
    );

    expect(meal).toBe("Bữa tối");
  });

  it("nên trả về null khi không có meal hợp lệ", () => {
    const meal = inferMealFromRestaurant({ meals: ["buffet"] });

    expect(meal).toBeNull();
  });
});

describe("Hàm formatMealDisplay trong utils", () => {
  it("nên đổi xế thành Bữa phụ", () => {
    expect(formatMealDisplay("xế")).toBe("Bữa phụ");
  });

  it("nên viết hoa chữ cái đầu cho meal thông thường", () => {
    expect(formatMealDisplay("trưa")).toBe("Trưa");
  });

  it("nên trả chuỗi rỗng khi không có meal", () => {
    expect(formatMealDisplay(null)).toBe("");
  });
});
