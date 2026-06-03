import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatInterface from "@/components/sections/ChatInterface";

// Mock AuthContext y như trên
jest.mock("../src/context/AuthContext", () => ({
  useAuth: () => ({
    user: { uid: "test-uid" }
  })
}));

describe("Component ChatInterface", () => {
  it("nên render thanh chat và lời chào ban đầu", () => {
    render(
      <ChatInterface 
        placeId="place-123" 
        input="" 
        onInputChange={() => {}} 
      />
    );

    // Kiểm tra lời chào của AI có xuất hiện không
    expect(screen.getByText(/Chào bạn! Hãy cho BMI biết khẩu vị/i)).toBeInTheDocument();
    
    // Kiểm tra input chat có render không
    expect(screen.getByPlaceholderText("Nhập yêu cầu của bạn...")).toBeInTheDocument();
  });

  it("nên kích hoạt onInputChange khi bấm vào các câu gợi ý (suggestions)", () => {
    const mockOnInputChange = jest.fn();
    render(
      <ChatInterface 
        placeId="place-123" 
        input="" 
        onInputChange={mockOnInputChange} 
      />
    );

    // Tìm một nút bấm gợi ý (ví dụ câu đầu tiên)
    const suggestionBtn = screen.getByText("Tối nay tôi muốn ăn hải sản view biển, ngân sách 800k.");
    
    // Bấm vô nó
    fireEvent.click(suggestionBtn);
    
    // Nó phải truyền đúng text đó vào hàm onInputChange
    expect(mockOnInputChange).toHaveBeenCalledWith("Tối nay tôi muốn ăn hải sản view biển, ngân sách 800k.");
  });
});