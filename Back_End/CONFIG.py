import os 
user_lat = 0.0
user_lng = 0.0

# Trọng số tổng bằng 1
distance_weight = 0.5
price_weight = 0.3
another_weight = 0.2 # Khởi tạo tạm, tạm thời chưa dùng

# Path 
DB_PATH = os.path.join(os.getcwd(), 'Back_End', 'Database')