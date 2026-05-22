from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import firebase_admin
from firebase_admin import auth, credentials
import os

# Đường dẫn tới tệp Service Account Key
# Lưu ý: Bạn cần đặt tệp serviceAccountKey.json vào thư mục Back_End/Database/
base_dir = os.path.dirname(os.path.dirname(__file__)) # Back_End/
json_path = os.path.join(base_dir, "Database", "serviceAccountKey.json")

# Khởi tạo Firebase Admin
if not firebase_admin._apps:
    if os.path.exists(json_path):
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred)
    else:
        # Nếu không có tệp key, chúng ta sẽ log cảnh báo
        print(f"CẢNH BÁO: Không tìm thấy tệp {json_path}. Các chức năng xác thực sẽ lỗi.")

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
