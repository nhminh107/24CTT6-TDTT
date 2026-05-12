# Hướng dẫn chạy và test code trong Pharse1 

## Cài đặt môi trường - Thư viện 
**Cài thư viện Python**
Chạy lệnh 
```text
pip install -r requirements.txt
```
Để cài đặt các thư viện cần thiết

**Cài NodeJS**
Tải NodeJS tại: <a href ="https://nodejs.org/en/download"> NodeJS Download </a>

Vào Powershell chạy lệnh ``` npm -v``` để xác nhận đã tải thành công

## Chạy và Test 
Mở 2 terminal
Terminal 1: Chạy lệnh
```
uvicorn main:app --reload
```

Terminal 2: Chạy lệnh 
```
npm run dev
```

**LƯU Ý**: Để tiết kiệm API Key chung thì mọi người có thể tự vào <a href="https://aistudio.google.com/welcome"> Google AI Studio </a> tạo key và bỏ vào .env để sử dụng. Ngoài ra, những tính năng, kiểm tra không cần dùng đến
vị trí thì mọi người có thể test trực tiếp sau khi chạy Terminal 1, vào link 127.0.0.1
