from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import firebase_admin
from firebase_admin import auth, credentials, firestore
import os

# Đường dẫn tuyệt đối tới tệp Service Account Key
# __file__ là path tới file hiện tại (Back_End/Core/auth_handler.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Quay lại 1 cấp vào Back_End, sau đó vào Database
json_path = os.path.join(os.path.dirname(current_dir), "Database", "serviceAccountKey.json")

# Khởi tạo Firebase Admin
if not firebase_admin._apps:
    try:
        if os.path.exists(json_path):
            cred = credentials.Certificate(json_path)
            firebase_admin.initialize_app(cred)
            print(">>> Firebase Admin SDK initialized successfully.")
        else:
            print(f">>> WARNING: Credentials file not found at {json_path}")
    except Exception as e:
        print(f">>> ERROR initializing Firebase Admin: {e}")

# Khởi tạo Firestore client
def get_db():
    global db
    if 'db' not in globals() or db is None:
        try:
            if firebase_admin._apps:
                from firebase_admin import firestore
                globals()['db'] = firestore.client()
                print(">>> Firestore connected successfully.")
            else:
                print(">>> WARNING: Firebase Admin not initialized, cannot get Firestore client.")
                return None
        except Exception as e:
            print(f">>> ERROR connecting to Firestore: {e}")
            return None
    return globals()['db']

# Initialize it immediately if possible
db = get_db()

security = HTTPBearer()

async def get_current_user(res: HTTPAuthorizationCredentials = Security(security)):
    """
    Dependency để lấy thông tin người dùng từ Firebase ID Token.
    Sử dụng: route_func(user = Depends(get_current_user))
    """
    token = res.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Xác thực thất bại hoặc Token hết hạn: {str(e)}"
        )

def check_admin_role(user: dict = Depends(get_current_user)):
    """Kiểm tra nếu user có quyền admin"""
    # Trong Firebase, bạn có thể dùng Custom Claims hoặc lưu role trong Firestore
    # Giả sử chúng ta dùng Custom Claims: user.get("admin") == True
    # Hoặc đơn giản là check email trong danh sách admin
    if not user.get("admin"):
         raise HTTPException(status_code=403, detail="Bạn không có quyền Admin.")
    return user
