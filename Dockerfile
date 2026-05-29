# Sử dụng image Python 3.11 slim để hiệu năng tốt hơn và tránh lỗi deprecation
FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc
WORKDIR /app

# Copy và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn
COPY . .

# Xóa các file dữ liệu không dùng tới (theo yêu cầu)
RUN rm -rf data/ \
    && rm -f Back_End/Database/old_data.json \
    && rm -f Back_End/Database/test.json

# Cổng mặc định
EXPOSE 8000

# Khởi chạy server. Logic nạp DB đã được đưa vào startup event của main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
