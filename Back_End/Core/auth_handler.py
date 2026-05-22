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
            print(">>> Firebase Admin SDK khởi tạo thành công.")
        else:
            print(f">>> CẢNH BÁO: Không tìm thấy tệp xác thực tại {json_path}")
    except Exception as e:
        print(f">>> LỖI khởi tạo Firebase Admin: {e}")

# Khởi tạo Firestore client
db = None
try:
    if firebase_admin._apps:
        db = firestore.client()
        print(">>> Kết nối Firestore thành công.")
except Exception as e:
    print(f">>> LỖI kết nối Firestore: {e}")

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
