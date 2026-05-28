from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from Back_End.Database.database import ChromaDBManager
from Back_End.API.routes import router as main_router
from Back_End.API.auth_routes import router as auth_router
from Back_End.API.routes import user_router
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
@app.on_event("startup")
async def warmup_models():
    asyncio.create_task(asyncio.to_thread(ChromaDBManager))

#Cổng phụ
@app.get("/")
async def root():
    return {"message": "Server đang chạy thành công! Hãy truy cập http://127.0.0.1:8000/docs để test."}
