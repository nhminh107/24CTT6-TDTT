# Báo cáo Kỹ thuật: Triển khai Bản Đồ Khám Phá (Maps Explore)

Tài liệu này chi tiết các công nghệ, logic xử lý và các giải pháp kỹ thuật đã áp dụng để xây dựng tính năng bản đồ cho dự án.

## 1. Công nghệ & Thư viện sử dụng
- **Cốt lõi:** `maplibre-gl` v4.x. Engine render bản đồ bằng WebGL mạnh mẽ nhất trong giới mã nguồn mở.
- **Wrapper:** `react-map-gl/maplibre`. Tối ưu hóa bản đồ cho vòng đời React/Next.js.
- **Nguồn bản đồ:** Goong Maps Tiles (Vector Tiles).
- **Icons:** Lucide-React & Native OS Emojis.

## 2. Logic xử lý dữ liệu & Render

### 2.1 Chuyển đổi GeoJSON & Phân loại dữ liệu
Dữ liệu từ `data.json` được chuẩn hóa qua hàm `convertToGeoJSON` tại `src/lib/utils.ts`. 
- **Style Mapping:** Tự động gán màu sắc và icon theo loại quán:
  - `Việt` -> `#EA4335` (Đỏ Google) + 🍜
  - `nước/cafe` -> `#03A9F4` (Xanh dương) + ☕
  - ... (Thiết kế theo phong cách Google Maps).

### 2.2 Thuật toán Gom cụm (Clustering)
Sử dụng **Supercluster** để xử lý ~600 bản ghi mượt mà:
- **Tham số:** `clusterRadius: 50`, `clusterMaxZoom: 13`.
- **Logic:** Tự động gộp điểm khi zoom xa và rã cụm khi zoom gần.

### 2.3 Bản đồ sạch (Style Filtering)
Loại bỏ nhiễu thông tin bằng cách lọc trực tiếp Style JSON:
- Lọc bỏ toàn bộ các lớp (`layers`) có kiểu `symbol` và ID chứa từ khóa địa điểm rác (`poi`, `transit`, `food`, `business`).
- Kết quả: Bản đồ chỉ hiển thị duy nhất dữ liệu quán ăn của project.

### 2.4 Render Marker màu sắc (HTML Overlay)
Sử dụng giải pháp **HTML Marker Overlay** thay cho WebGL Symbol để Emoji hiển thị đúng màu sắc rực rỡ của hệ điều hành, thay vì bị biến thành màu đen đơn sắc.

### 2.5 Highlight quán trong lịch trình (Smart Highlighting)
Để nâng cao trải nghiệm người dùng, hệ thống tự động làm nổi bật các quán ăn đã được chọn vào lịch trình hiện tại:
- **Hiệu ứng xung kích (Pulsing):** Một vòng tròn mờ màu cam san hô (brand-coral) liên tục co giãn xung quanh marker, thu hút sự chú ý.
- **Checkmark Badge:** Một huy hiệu dấu tích nhỏ xuất hiện ở góc Marker để xác nhận trạng thái "Đã chọn".
- **Tương tác động:** Marker đã chọn sẽ có kích thước lớn hơn 10% và viền màu cam san hô thay vì viền trắng mặc định.
- **Nhãn tên đồng bộ:** Tên quán của các địa điểm đã chọn cũng chuyển sang màu cam san hô để tạo sự thống nhất.

## 3. Cải tiến Luồng điều hướng (User Flow Optimization)
- **Primary Entry Point:** Nút "XEM BẢN ĐỒ KHÁM PHÁ" được đặt ngay dưới tiêu đề lịch trình ở khung bên phải Dashboard.
- **Full-page Navigation:** Chuyển đổi từ hiển thị bản đồ trong khung Sidebar sang trang toàn màn hình `/explore` để tối ưu diện tích quan sát.
- **Direct Add to Itinerary:** Cho phép người dùng thêm quán ăn vào lịch trình ngay tại Popup trên bản đồ. Hệ thống hỗ trợ:
  - **Gợi ý tự động:** AI phân tích giờ mở cửa để gợi ý bữa ăn phù hợp nhất.
  - **Chọn thủ công:** Người dùng chủ động chọn Bữa sáng/trưa/tối/phụ.
- **Seamless Return:** Nút "Quay lại Chat AI" nổi bật giúp người dùng chuyển đổi qua lại giữa việc "Hỏi AI" và "Xem bản đồ" một cách nhanh chóng.

## 4. Các lỗi đã xử lý (Bug Fixes)
1. **ReferenceError: Link:** Khắc phục việc thiếu import component điều hướng.
2. **TypeError: map is not a function:** Kiểm tra `Array.isArray()` cho dữ liệu bữa ăn để tránh crash trang.
3. **Black Icons:** Chuyển từ WebGL Symbol sang HTML Marker để lấy lại màu sắc cho icon.
4. **Blank Map:** Sửa lỗi logic lọc layer (sai biến vòng lặp) làm mất nền bản đồ.
5. **Syntax Errors:** Dọn dẹp code dư thừa và đóng ngoặc sai tại `SidebarNav.tsx`.

---
*Tài liệu này được cập nhật liên tục để phản ánh trạng thái mới nhất của tính năng.*

# Kiểm tra tên user hệ thống của máy tính
whoami

git config --global user.name
# hoặc kiểm tra trong file config local
cat .git/config