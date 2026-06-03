# Stage 1: Build/Requirements
FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc
WORKDIR /app

# Copy requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- TỐI ƯU HÓA: Tải trước Model Embedding để không phải tải lúc runtime ---
# Sử dụng chính model khai báo trong database.py
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Sao chép toàn bộ mã nguồn
COPY . .

# Xóa các file rác và dữ liệu dư thừa, CHỈ GIỮ LẠI data.json trong Database/
RUN rm -rf data/ \
    && find Back_End/Database/ -name "*.json" ! -name "data.json" -delete \
    && rm -rf Back_End/UnitTest/

# Thiết lập biến môi trường để Python không tạo file .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cổng Backend
EXPOSE 8000

# Khởi chạy server
# Quá trình nạp DB đã được xử lý tự động trong main.py @app.on_event("startup")
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
