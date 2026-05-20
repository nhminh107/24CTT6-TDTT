# Hướng Dẫn Cài Đặt & Chạy API Đăng Ký/Đăng Nhập (Backend)

Phần Backend này được xây dựng bằng **Node.js, Express** và kết nối với **Supabase** để xử lý Xác thực (Authentication) và Phân quyền (Authorization).

---

## Bước 1: Tải Thư Viện

Vì thư mục `node_modules` không được push lên Git để giảm dung lượng, nên việc đầu tiên bạn cần làm sau khi tải code về là cài đặt lại các thư viện.

Mở Terminal tại thư mục này (`Back_End/DANGKY_DANGNHAP`) và chạy lệnh:
```bash
npm install
```

---

## Bước 2: Thiết Lập Biến Môi Trường (.env)

Tạo một file mới tên là `.env` ngang hàng với file `server.js` (do file `.env` chứa API Key nhạy cảm nên đã bị chặn đẩy lên Git).
Mở file `.env` và dán cấu hình sau vào (Hãy thay bằng URL và KEY từ dự án Supabase của nhóm):

```env
PORT=3000
SUPABASE_URL=https://<your_supabase_project_id>.supabase.co
SUPABASE_ANON_KEY=<your_supabase_anon_key>
```
*Lưu ý: Nhớ bấm `Ctrl + S` để lưu file `.env`.*

---

## Bước 3: Cài Đặt Database Trên Supabase

Để phần Xác thực và Phân quyền hoạt động đúng, chúng ta cần tạo bảng `profiles` và cài đặt một **Trigger** (robot tự động) để mỗi khi có một user đăng ký mới, thông tin sẽ được tự động đồng bộ sang bảng `profiles`. 

Bạn hãy truy cập vào trang quản trị của [Supabase](https://supabase.com), vào mục **SQL Editor**, dán toàn bộ đoạn mã dưới đây vào và bấm **Run**:

```sql
-- 1. Tạo bảng profiles
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  full_name text,
  role text default 'user'
);

-- 2. Bật Row Level Security (RLS) để bảo mật
alter table public.profiles enable row level security;

-- 3. Cấp quyền truy cập RLS để Backend có thể đọc được dữ liệu
create policy "Allow read access to profiles" on public.profiles
  for select using (true);

create policy "Allow users to update their own profile" on public.profiles
  for update using (auth.uid() = id);

-- 4. Tạo Hàm Trigger
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, role)
  values (
    new.id,
    new.raw_user_meta_data->>'full_name',
    'user'
  );
  return new;
end;
$$;

-- 5. Kích hoạt Trigger trên bảng auth.users
create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute procedure public.handle_new_user();
```

---

## Bước 4: Khởi Động Server

Sau khi đã hoàn tất các bước trên, hãy khởi động server bằng lệnh:
```bash
node server.js
```
Nếu Terminal hiện dòng chữ `Server is running on http://localhost:3000` thì bạn đã thành công!

---

## Danh Sách Các API Có Thể Test

Bạn có thể dùng Postman hoặc Thunder Client để test các API sau:

### 1. Đăng ký (Register)
- **Method:** `POST`
- **URL:** `http://localhost:3000/api/auth/register`
- **Body (JSON):**
  ```json
  {
    "email": "test1@gmail.com",
    "password": "matkhaumanh123",
    "full_name": "Nguyen Van A"
  }
  ```

### 2. Đăng nhập (Login)
- **Method:** `POST`
- **URL:** `http://localhost:3000/api/auth/login`
- **Body (JSON):**
  ```json
  {
    "email": "test1@gmail.com",
    "password": "matkhaumanh123"
  }
  ```
👉 **Lưu ý:** Khi đăng nhập thành công, bạn sẽ nhận được một đoạn mã `access_token`. Hãy copy đoạn mã này để test 2 API bên dưới.

### 3. Lấy thông tin cá nhân (Profile)
- **Method:** `GET`
- **URL:** `http://localhost:3000/api/users/profile`
- **Headers:** 
  - Key: `Authorization`
  - Value: `Bearer <dán_access_token_vào_đây>`

### 4. Lấy danh sách toàn bộ Users (Chỉ dành cho Admin)
- **Method:** `GET`
- **URL:** `http://localhost:3000/api/users/all`
- **Headers:** 
  - Key: `Authorization`
  - Value: `Bearer <dán_access_token_vào_đây>`
*(Chú ý: API này sẽ báo lỗi `403 Forbidden` nếu role của bạn đang là 'user'. Để test thành công, bạn hãy lên Supabase -> Table Editor -> profiles -> sửa thủ công chữ 'user' thành 'admin' rồi thử lại).*
