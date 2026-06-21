# Báo cáo Bình luận Vi phạm - Hướng dẫn Triển khai

## 📋 Tổng quan

Tính năng này cho phép người dùng báo cáo bình luận vi phạm, và Admin có thể quản lý/xử lý các báo cáo này từ Dashboard riêng.

---

## 🏗️ Kiến trúc Dữ liệu

### Firestore Collections:

#### 1. `reports` (Collection mới)
Lưu trữ tất cả báo cáo bình luận
```json
{
  "report_id": "uuid",
  "restaurant_id": "77",
  "comment_id": "X8XYviIyUA00VnhV18h0",
  "comment_text": "Good",
  "reason": "Spam hoặc nội dung không phù hợp",
  "user_id": "user_id_reporter",
  "status": "pending|resolved",
  "created_at": "2026-06-21T10:00:00Z",
  "updated_at": "2026-06-21T11:00:00Z" 
}
```

#### 2. `restaurant_comments` (Existing)
Cấu trúc không thay đổi:
```
restaurant_comments/
  ├─ [restaurant_id]/
      └─ comments/
          └─ [comment_id]
```

---

## 📱 Frontend Components & Files

### 1. **reportsApi.ts** (`src/lib/reportsApi.ts`)
API client cho giao tiếp với backend
- `reportComment(payload)` - Gửi báo cáo
- `getReports(filters)` - Lấy danh sách báo cáo (Admin)
- `deleteCommentAsAdmin(restaurantId, commentId)` - Xóa comment (Admin)
- `updateReportStatus(reportId, status)` - Cập nhật trạng thái báo cáo (Admin)

### 2. **RestaurantDetailModal.tsx** (Updated)
- ✅ Thêm nút Flag "Báo cáo" cho mỗi comment (chỉ hiện cho non-owner comments)
- ✅ Modal báo cáo cho người dùng nhập lý do
- ✅ ID element: `id={`comment-${comment.comment_id}`}` để dễ scroll
- ✅ useEffect scroll tới comment được report từ sessionStorage

### 3. **MapExplore.tsx** (Updated)
- ✅ Bắt URL query params: `?action=review_report&resId=[restaurant_id]&commentId=[comment_id]`
- ✅ Tự động fly to location nhà hàng
- ✅ Mở modal chi tiết
- ✅ Lưu commentId vào sessionStorage

### 4. **Admin Dashboard** (`src/app/admin/page.tsx`)
Trang quản lý báo cáo (chỉ dành cho admin)
- ✅ Hiển thị avatar admin
- ✅ Stats cards: Tổng báo cáo, Chưa xử lý, Đã xử lý
- ✅ Filter tabs: Tất cả, Chưa xử lý, Đã xử lý
- ✅ Danh sách báo cáo với:
  - Nút "Xem ngữ cảnh" → điều hướng sang `/explore?action=review_report&resId=...`
  - Nút "Xóa" → Xóa comment + Đóng báo cáo
  - Nút "Bỏ qua" → Chỉ đóng báo cáo mà không xóa

---

## 🔌 Backend API Endpoints

### Tất cả endpoint sử dụng prefix: `/api/user`

#### 1. **POST /report-comment**
Gửi báo cáo bình luận
```bash
curl -X POST http://localhost:8000/api/user/report-comment \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "77",
    "comment_id": "X8XYviIyUA00VnhV18h0",
    "comment_text": "Good",
    "reason": "Spam hoặc nội dung không phù hợp",
    "user_id": "user123"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Báo cáo của bạn đã được gửi...",
  "report_id": "uuid"
}
```

#### 2. **GET /reports?status=pending|resolved**
Lấy danh sách báo cáo (Admin only)
```bash
curl -X GET "http://localhost:8000/api/user/reports?status=pending" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "report_id": "uuid",
      "restaurant_id": "77",
      "comment_id": "X8XYviIyUA00VnhV18h0",
      "comment_text": "Good",
      "reason": "Spam",
      "status": "pending",
      "created_at": "2026-06-21T10:00:00Z"
    }
  ]
}
```

#### 3. **PATCH /reports/{report_id}**
Cập nhật trạng thái báo cáo (Admin only)
```bash
curl -X PATCH http://localhost:8000/api/user/reports/uuid \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved"}'
```

**Response:**
```json
{
  "status": "success",
  "message": "Cập nhật trạng thái báo cáo thành 'resolved' thành công."
}
```

#### 4. **DELETE /restaurant-comment/{restaurant_id}/{comment_id}** (Existing)
Xóa comment (thường dùng bởi Admin hoặc owner)

---

## 🔄 Luồng Xử lý (User Flow)

### **Luồng User Báo cáo Comment:**
1. User nhìn thấy comment vi phạm trong RestaurantDetailModal
2. Click nút Flag "Báo cáo" (chỉ hiện cho comments của người khác)
3. Modal báo cáo hiện lên với:
   - Hiển thị nội dung comment
   - Textarea để nhập lý do
4. User submit → API gửi dữ liệu lên `/api/user/report-comment`
5. Dữ liệu được lưu vào Firestore collection `reports` với status `"pending"`
6. Toast notification: "Báo cáo của bạn đã được gửi..."

### **Luồng Admin Xử lý Báo cáo:**
1. Admin truy cập `/admin` → Admin Dashboard
2. Xem danh sách báo cáo "Chưa xử lý"
3. Chọn một báo cáo:
   - **Xem ngữ cảnh**: Điều hướng sang `/explore?action=review_report&resId=...&commentId=...`
     - MapExplore tự động fly to location
     - Mở RestaurantDetailModal
     - Scroll tới comment được report (highlight ring amber)
   - **Xóa**: Xóa comment gốc + Cập nhật report status → "resolved"
   - **Bỏ qua**: Chỉ cập nhật report status → "resolved" (không xóa)

---

## 🔐 Bảo Mật & Quyền Hạn

### **Hiện tại (TODO - Cần bổ sung):**
- ⚠️ Backend endpoints không có kiểm tra admin role
- ⚠️ Frontend dùng `isCurrentUserAdmin` từ user object

### **Nên Cải thiện:**
1. Thêm JWT token verification ở backend
2. Kiểm tra admin role trong middleware
3. Rate limiting cho API report-comment

---

## 🚀 Cách Sử Dụng

### **Für Developer:**

1. **Kiểm tra tính năng báo cáo:**
   - Đăng nhập
   - Tìm một comment không phải của bạn
   - Click nút Flag → Báo cáo
   - Kiểm tra Firestore collection `reports`

2. **Kiểm tra Admin Dashboard:**
   - Đảm bảo user có role `"admin"` (kiểm tra Firestore users collection)
   - Truy cập `/admin`
   - Xem danh sách báo cáo
   - Click "Xem ngữ cảnh" → Xác nhận navigate đến `/explore`

3. **Xóa comment qua Admin:**
   - Tại Admin Dashboard, chọn báo cáo
   - Click "Xóa" → Comment sẽ bị xóa khỏi Firestore
   - Report status → "resolved"

---

## 📁 Danh sách File Thay đổi

| File | Thay đổi |
|------|----------|
| `src/lib/reportsApi.ts` | **✨ Tạo mới** - API client |
| `src/components/ui/RestaurantDetailModal.tsx` | **📝 Cập nhật** - Thêm nút báo cáo + modal |
| `src/components/ui/MapExplore.tsx` | **📝 Cập nhật** - Bắt URL params + navigate |
| `src/app/admin/page.tsx` | **✨ Tạo mới** - Admin Dashboard |
| `Back_End/API/routes.py` | **📝 Cập nhật** - Thêm 3 endpoint |

---

## 🐛 Known Issues & Improvements

### **Hiện tại:**
1. ⚠️ Không có kiểm tra admin role ở backend
2. ⚠️ Không có rate limiting cho API report-comment
3. ⚠️ Không có email notification cho admin khi có report mới
4. ⚠️ UI Admin Dashboard có thể cần styling tinh chỉnh

### **Cải thiện trong tương lai:**
1. ✅ Thêm JWT token verification
2. ✅ Thêm email notification
3. ✅ Thêm pagination cho danh sách reports
4. ✅ Thêm export reports to CSV
5. ✅ Thêm comment filtering (by reason, date range, etc.)

---

## 📞 Hỗ trợ & Câu hỏi

Nếu có vấn đề, kiểm tra:
1. Firestore collections `reports` có tồn tại không
2. Backend endpoints có response đúng không
3. Admin user role có được set trong Firestore không
4. sessionStorage được clear sau khi sử dụng

---

**Phát triển: 2026-06-21**
**Status: ✅ Hoàn thành triển khai**
