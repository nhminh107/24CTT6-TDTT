from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from Back_End.Database.database import ChromaDBManager
from Back_End.API.routes import router as main_router
from Back_End.API.auth_routes import router as auth_router
from Back_End.API.routes import _get_restaurant_df_cached, user_router
from Back_End.API.share_routes import router as share_router
app = FastAPI(
    title="Trợ lý du lịch thông minh",
    description="Lên lịch trình ăn uống",
    version="1.0"
)

# Cấu hình CORS để cho phép FrontEnd kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả các nguồn (dễ dàng khi deploy FE lên Vercel)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router
app.include_router(main_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(share_router)
@app.on_event("startup")
async def warmup_models():
    # Khởi tạo DB Manager
    db_mng = ChromaDBManager()
    # Tự động nạp dữ liệu từ data.json vào ChromaDB nếu chưa có
    # Chạy trong thread riêng để không làm treo server lúc khởi động
    loop = asyncio.get_event_loop()
    await asyncio.gather(
        loop.run_in_executor(None, db_mng.add),
        loop.run_in_executor(None, _get_restaurant_df_cached),
    )
    print("✅ Database initialization completed!")

#Cổng phụ
@app.get("/")
async def root():
    return {"message": "Server đang chạy thành công! Hãy truy cập https://api.bmi-foodtour.io.vn/docs để test."}
