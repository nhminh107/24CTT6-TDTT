# Tài liệu Unit Test - Back End Core

Thư mục này chứa các unit test cho các thành phần cốt lõi (Core) của hệ thống Back End. Các bài kiểm tra được thiết kế theo tiêu chuẩn công nghiệp: **Nhanh, Độc lập và Tiết kiệm chi phí.**

## 1. Chiến lược kiểm thử (Testing Strategy)

Toàn bộ các bài kiểm tra ở đây đều sử dụng kỹ thuật **Mocking** (giả lập).

### Tại sao sử dụng Mock?
- **Tiết kiệm chi phí (Token efficiency):** Không gọi trực tiếp đến Google Gemini API hay OpenWeather API, giúp tránh tiêu tốn tiền bạc và giới hạn lượt gọi (quota) trong quá trình phát triển.
- **Tốc độ:** Unit test chạy gần như tức thời (dưới 2 giây cho toàn bộ suite) vì không phụ thuộc vào độ trễ mạng.
- **Tính dự đoán (Determinism):** Test luôn trả về kết quả giống nhau, không bị ảnh hưởng bởi việc API thay đổi nội dung ngẫu nhiên hoặc bị sập mạng.
- **Kiểm thử các trường hợp ngoại lệ:** Dễ dàng giả lập các tình huống khó xảy ra trong thực tế như API trả về lỗi 500, JSON bị hỏng, hoặc tọa độ không xác định.

---

## 2. Chi tiết các file Test

### `test_parsing.py` (Kiểm thử `LLMParser`)
- **Mục tiêu:** Kiểm tra khả năng xử lý kết quả trả về từ mô hình ngôn ngữ lớn (LLM).
- **Các hàm được test:** `JSON_response`, `phrase_health_description`.
- **Các kịch bản:**
    - Trích xuất thành công thông tin từ prompt người dùng sang JSON.
    - Phân tích mô tả sức khỏe thành các tag y tế chính xác.
    - Xử lý khi LLM trả về các tag không nằm trong danh sách cho phép (Filtering).
    - Xử lý lỗi khi API gặp sự cố (Error handling).

### `test_semantic_cache.py` (Kiểm thử `SemanticCacheManager`)
- **Mục tiêu:** Đảm bảo hệ thống lưu trữ cache hoạt động đúng mà không cần cài đặt database thật.
- **Các hàm được test:** `_get_location_zone`, `check_cache`, `save_cache`.
- **Các kịch bản:**
    - Kiểm tra công thức làm tròn tọa độ để phân vùng (zone).
    - Giả lập trường hợp **Cache Hit** (tìm thấy dữ liệu) và **Cache Miss** (không thấy dữ liệu).
    - Đảm bảo dữ liệu được lưu vào database dưới dạng JSON string chính xác.
    - **Lưu ý:** Đã mock cả Embedding Function để không phải tải model AI nặng (hàng trăm MB) về máy khi chạy test.

### `test_weight_update.py` (Kiểm thử `Weight_Update`)
- **Mục tiêu:** Kiểm tra logic toán học của các quy tắc điều chỉnh trọng số gợi ý.
- **Các hàm được test:** `_apply_weather_rules`, `_apply_time_rules`, `_normalize_buffs`, `build_buff_weights`.
- **Các kịch bản:**
    - Thay đổi trọng số khi trời mưa (ưu tiên quán gần, giá rẻ).
    - Thay đổi trọng số theo buổi (Sáng, Trưa, Tối, Khuya).
    - Kiểm tra tính toán cân bằng (Normalization) để đảm bảo tổng các buff không làm lệch kết quả quá mức (tổng thay đổi tiến về 0).
    - Giả lập thời gian vào cuối tuần để kiểm tra các rule ưu tiên trải nghiệm/không gian.

---

## 3. Hướng dẫn chạy Test

### Yêu cầu hệ thống
- Python 3.x
- Thư viện: `pytest`, `anyio` (đã được cấu hình để chạy async).

### Lệnh thực thi
Mở terminal tại thư mục gốc của dự án và chạy:
```bash
pytest Back_End/UnitTest/
```

Nếu bạn muốn xem chi tiết các hàm nào đang chạy, hãy thêm cờ `-v`:
```bash
pytest -v Back_End/UnitTest/
```

---

## 4. Cấu trúc thư mục liên quan
- `Back_End/Core/`: Chứa mã nguồn thực tế.
- `Back_End/UnitTest/`: Chứa các file test tương ứng (bắt đầu bằng tiền tố `test_`).
- `Back_End/__init__.py`: Giúp Python nhận diện thư mục là một package để import module dễ dàng.
