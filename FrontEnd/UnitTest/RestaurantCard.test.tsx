import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import RestaurantCard from "../src/components/ui/RestaurantCard"; 

describe("Component RestaurantCard", () => {
  const mockRestaurant = {
    id: "res-1",
    name: "Quán Chay Thanh Tịnh",
    address: "123 Lê Lợi",
    rating: 4.8,
    price: "50.000đ",
    phone: "0123456789",
    mapUrl: "#",
    imageUrl: "https://example.com/image.jpg",
    semanticText: "Ngon, bổ, rẻ",
    meals: ["trưa", "tối"],
    source: "ai" as const,
    warnings: [], // Không có cảnh báo -> Phải hiện "Phù hợp"
    notes: []
  };

  it("nên render thông tin cơ bản của quán", () => {
    render(<RestaurantCard restaurant={mockRestaurant} />);
    expect(screen.getByText("Quán Chay Thanh Tịnh")).toBeInTheDocument();
    expect(screen.getByText("123 Lê Lợi")).toBeInTheDocument();
  });

  it("nên hiển thị huy hiệu 'Phù hợp' khi không có warnings", () => {
    render(<RestaurantCard restaurant={mockRestaurant} />);
    expect(screen.getByText("Phù hợp")).toBeInTheDocument();
  });

  it("nên hiển thị huy hiệu 'Cần lưu ý' khi có warnings", () => {
    // Sửa data truyền vào để có warning
    const warningRestaurant = { ...mockRestaurant, warnings: ["Dạ dày: Đồ cay nồng"] };
    render(<RestaurantCard restaurant={warningRestaurant} />);
    
    // Nút mở accordion cảnh báo phải xuất hiện
    expect(screen.getAllByText("Cần lưu ý").length).toBeGreaterThan(0);
  });

  it("nên hiển thị huy hiệu 'Tự thêm thủ công' cho nhà hàng do user thêm", () => {
    const userRestaurant = {
      ...mockRestaurant,
      source: "user" as const,
      warnings: ["Không dùng để đánh giá sức khỏe AI"],
    };

    render(<RestaurantCard restaurant={userRestaurant} />);

    expect(screen.getByText("Tự thêm thủ công")).toBeInTheDocument();
    expect(screen.queryByText("Phù hợp")).not.toBeInTheDocument();
  });
});
