# Tài liệu Hệ thống Intent Routing (Phân luồng ý định)

Tài liệu này mô tả chi tiết quá trình triển khai và tích hợp module Intent Routing vào hệ thống gợi ý món ăn.

## 1. Mục tiêu
Xây dựng một lớp lọc đầu tiên để phân loại ý định người dùng ngay khi nhận prompt, nhằm:
- Phân biệt giữa ý định **Tìm kiếm (Search)** và **Hỏi đáp (QA)**.
- Đánh giá chất lượng thông tin (thông qua field `isPoorInfo`) để tránh việc tốn tài nguyên xử lý các prompt quá sơ sài.

## 2. Chi tiết triển khai Backend

### 2.1. Module QA_Chatbot.py (`Back_End/Core/QA_Chatbot.py`)
Lớp `ChatBot` được nâng cấp để hỗ trợ xử lý bất đồng bộ (`AsyncGroq`) và mô hình `llama-3.3-70b-versatile`.

**Hàm `routing(user_prompt)`:**
- **System Prompt:** Chỉ định rõ mô hình phải trả về JSON với 2 intent chính.
- **Phân loại intent:**
    - `QA`: Câu hỏi về văn hóa ẩm thực, sức khỏe, hệ thống.
    - `Search`: Ý định tìm địa điểm ăn uống cụ thể.
- **Logic `isPoorInfo` (Chỉ dành cho Search):**
    - `1`: Prompt quá ngắn, chỉ gồm các tính từ hoặc từ đơn (ví dụ: "cay", "ngon", "đắt") không đủ ngữ cảnh để tìm kiếm.
    - `0`: Prompt có đầy đủ thông tin tối thiểu (ví dụ: "Tìm quán ăn sáng", "Ăn gì ở quận 1").
- **Output:** Trả về JSON string: `{"user_intent": "QA" | "Search", "isPoorInfo": 0 | 1}`.

### 2.2. Tích hợp vào API Pipeline (`Back_End/API/routes.py`)
Quy trình xử lý tại endpoint `/prompt` được bổ sung **Bước 0: Intent Routing**:

1. **Interception (Đánh chặn):**
   - Nếu `user_intent == "Search"` VÀ `isPoorInfo == 1`:
     - Hệ thống ngay lập tức trả về status `poor_info`.
     - Phản hồi cho người dùng bằng một câu hỏi gợi ý để họ bổ sung thông tin (Món ăn, địa điểm, ngân sách).
     - **Dừng luồng xử lý tại đây**, không gọi tới module Parsing hay Database để tiết kiệm tài nguyên.
2. **Tiếp tục luồng cũ:**
   - Nếu `user_intent == "Search"` VÀ `isPoorInfo == 0`: Luồng xử lý tiếp tục đi qua module Parsing, Filtering và Scoring như cũ.

**Xử lý trường hợp `user_intent == "QA"`:**
- Theo yêu cầu hiện tại, hệ thống **bỏ qua việc xử lý đặc biệt** cho intent "QA". 
- Nghĩa là khi nhận diện được "QA", mã nguồn sẽ không thực hiện đánh chặn (interception) mà để prompt tiếp tục đi xuống module `LLMParser` (Step 1). Tuy nhiên, vì `LLMParser` hiện tại được thiết kế chuyên sâu cho Search (trích xuất budget, location, meals_detail), kết quả cho các câu hỏi QA có thể chưa tối ưu. Đây là phần dự kiến sẽ được tách luồng hoàn toàn trong tương lai.

## 3. Triển khai Frontend (`FrontEnd/src/components/sections/ChatInterface.tsx`)

UI đã được refactor hàm `buildAssistantMessage` để xử lý các trạng thái phản hồi mới:
- **`status: "poor_info"`**: Hiển thị nội dung tin nhắn hướng dẫn người dùng cung cấp thêm thông tin.
- **`status: "empty"`**: Hiển thị thông báo không tìm thấy kết quả phù hợp sau khi đã tìm kiếm kỹ.
- **Tách bạch logic:** Việc tách riêng giúp UI có các thông điệp fallback (dự phòng) chính xác và chuyên nghiệp hơn, thay vì báo lỗi hệ thống chung chung.

## 4. Kiểm thử (Unit Test)
Tạo file `Back_End/UnitTest/test_routing_logic.py` để kiểm tra logic phân luồng:
- Sử dụng `unittest.IsolatedAsyncioTestCase` để test các hàm async.
- Mock kết quả trả về từ Groq API để kiểm tra 3 trường hợp:
    1. Search với đầy đủ thông tin (`isPoorInfo: 0`).
    2. Search với thông tin sơ sài (`isPoorInfo: 1`).
    3. Ý định hỏi đáp (`QA`).

---
*Người soạn: Gemini CLI*
*Ngày: 06/06/2026*
