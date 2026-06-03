import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import ProfileSettings from "../src/components/sections/ProfileSettings"; // Thay "sections" bằng "ui" nếu file nằm trong thư mục ui nha

// 1. Giả lập AuthContext (Thêm getIdToken vì trong code ông có gọi hàm này)
jest.mock("../src/context/AuthContext", () => ({
  useAuth: () => ({
    user: { 
      uid: "test-uid-123", 
      email: "nguoilaoi@gmail.com", 
      displayName: "AnDanh",
      getIdToken: jest.fn(() => Promise.resolve("fake-token")) // Giả lập hàm lấy token
    }
  })
}));

// 2. Giả lập Firebase (Chặn nó khởi tạo thật để không bị lỗi)
jest.mock("../src/lib/firebase", () => ({
  auth: {}, // Trả về object rỗng là đủ lừa nó rồi
}));

// 3. Giả lập các hàm của thư viện firebase/auth
jest.mock("firebase/auth", () => ({
  sendPasswordResetEmail: jest.fn(() => Promise.resolve()), // Giả lập hàm gửi email thành công
}));

// 4. Giả lập lệnh "fetch" của trình duyệt để code không bị văng lỗi
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ status: "success", profile: {} }),
  })
) as jest.Mock;

describe("Component ProfileSettings", () => {
  it("nên render form thông tin cá nhân khi user đã đăng nhập", async() => {
    render(<ProfileSettings />);
    
    // Kiểm tra xem tiêu đề có xuất hiện không
    expect(screen.getByText("Thông tin cá nhân")).toBeInTheDocument();
    
    // Kiểm tra xem email của user ảo có được điền vào ô input chưa
    const emailInput = await screen.findByDisplayValue("nguoilaoi@gmail.com");
    expect(emailInput).toBeInTheDocument();
    expect(emailInput).toBeDisabled();
  });
});