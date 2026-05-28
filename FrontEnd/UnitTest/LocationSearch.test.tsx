import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import LocationSearch from "@/components/ui/LocationSearch";

describe("Component LocationSearch", () => {
  it("nên render input đúng với value truyền vào", () => {
    render(
      <LocationSearch 
        value="Hồ Chí Minh" 
        onChange={() => {}} 
        onSelect={() => {}} 
      />
    );
    
    // Tìm input thông qua placeholder
    const inputEl = screen.getByPlaceholderText("Nhập khu vực bạn đang ở");
    expect(inputEl).toBeInTheDocument();
    expect(inputEl).toHaveValue("Hồ Chí Minh");
  });

  it("nên gọi hàm onChange khi người dùng gõ text", () => {
    const mockOnChange = jest.fn(); // Giả lập một hàm
    render(
      <LocationSearch 
        value="" 
        onChange={mockOnChange} 
        onSelect={() => {}} 
      />
    );

    const inputEl = screen.getByPlaceholderText("Nhập khu vực bạn đang ở");
    
    // Giả lập hành động gõ chữ "Đà Lạt"
    fireEvent.change(inputEl, { target: { value: "Đà Lạt" } });
    
    // Kiểm tra xem hàm onChange có được gọi đúng với chữ "Đà Lạt" chưa
    expect(mockOnChange).toHaveBeenCalledWith("Đà Lạt");
  });
});