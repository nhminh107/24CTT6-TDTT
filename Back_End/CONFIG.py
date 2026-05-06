import os 
user_lat = 0.0
user_lng = 0.0

# Trọng số tổng bằng 1
Weights = {
    'star'    : 0.30,
    'price'   : 0.25,
    'distance': 0.25,
    'semantic': 0.20
}

# Path 
DB_PATH = os.path.join(os.getcwd(), 'Back_End', 'Database')