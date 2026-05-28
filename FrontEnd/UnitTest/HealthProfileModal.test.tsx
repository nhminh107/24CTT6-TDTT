import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import HealthProfileModal from "@/components/ui/HealthProfileModal";

// Giả lập AuthContext
jest.mock("../src/context/AuthContext", () => ({
  useAuth: () => ({ user: { uid: "test-user-123" } })
}));

describe("Component HealthProfileModal", () => {
  const mockProfile = {
    selected_conditions: [],
    selected_allergies: [],
    diet_mode: "strict" as const,
    more_descriptions: ""
  };

  it("nên hiển thị modal khi open = true", () => {
    render(
      <HealthProfileModal
        open={true}
        onClose={() => {}}
        profile={mockProfile}
        onChange={() => {}}
      />
    );
    expect(screen.getByText("Hồ sơ sức khỏe")).toBeInTheDocument();
  });

  it("có thể click chọn bệnh 'Gout' mà không bị văng lỗi", () => {
    render(
      <HealthProfileModal
        open={true}
        onClose={() => {}}
        profile={mockProfile}
        onChange={() => {}}
      />
    );
    
    const goutButton = screen.getByText("Gout");
    fireEvent.click(goutButton);
    // UI không văng lỗi là thành công bước đầu
    expect(goutButton).toBeInTheDocument();
  });
});