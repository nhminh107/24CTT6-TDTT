import os
from dotenv import load_dotenv

# Trọng số tổng bằng 1
Weights = {
    'star'    : 0.15,
    'price'   : 0.25,
    'distance': 0.25,
    'semantic': 0.35,
    
    'health':0.3
    # ý tưởng mới:
    # $Score_{final} = (star * 0.15 + price * 0.25 + distance * 0.25 + semantic * 0.35) - (penalty_score * W_{penalty})$
}

# Path
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, 'Database')
