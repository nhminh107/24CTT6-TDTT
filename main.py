from fastapi import FastAPI
import asyncio
from Back_End.Database.database import ChromaDBManager
from Back_End.API.routes import router

app = FastAPI(
    title="Trợ lý du lịch thông minh",
    description="Lên lịch trình ăn uống",
    version="1.0"
)

app.include_router(router)

@app.on_event("startup")
async def warmup_models():
    asyncio.create_task(asyncio.to_thread(ChromaDBManager))

#Cổng phụ
@app.get("/")
async def root():
    return {"message": "Server đang chạy thành công! Hãy truy cập http://127.0.0.1:8000/docs để test."}
