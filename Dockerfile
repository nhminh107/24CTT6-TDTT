# Sử dụng image Python chính thức, phiên bản 3.10 slim để giảm dung lượng
FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết cho việc biên dịch
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép requirements.txt vào container
COPY requirements.txt .

# Cài đặt các thư viện từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Xóa các file dữ liệu json không dùng tới (theo yêu cầu)
# Giữ lại Back_End/Database/data.json
RUN rm -rf data/ \
    && rm -f Back_End/Database/old_data.json \
    && rm -f Back_End/Database/test.json

# Mở cổng 8000
EXPOSE 8000

# Lệnh khởi chạy server bằng Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
