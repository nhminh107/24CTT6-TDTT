import os
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

_client = AsyncGroq(api_key=GROQ_API_KEY)

SYSTEM_DOCS_PATH = os.path.join(os.path.dirname(__file__), "../system_docs.md")

SYSTEM_DOCS_FALLBACK = (
    "Tài liệu hướng dẫn hệ thống hiện đang được cập nhật. "
    "Vui lòng thử lại sau hoặc liên hệ đội hỗ trợ để được giải đáp."
)


class ChatBot():
    def __init__(self):
        self.client = _client
        self.routing_model_name = "llama-3.3-70b-versatile"
        self.qa_model_name = "llama-3.3-70b-versatile"

    # -------------------------------------------------------------------------
    # ROUTING
    # -------------------------------------------------------------------------

    async def routing(self, user_prompt: str, history: list = None) -> str:
        """
        Phân loại ý định người dùng thành một trong ba nhãn:
          - "Search"      : Tìm kiếm quán ăn / địa điểm ăn uống.
          - "System_QA"   : Hỏi về cách dùng ứng dụng, tính năng, báo lỗi.
          - "Knowledge_QA": Hỏi về dinh dưỡng, sức khỏe, kiến thức ẩm thực.

        Trả về chuỗi JSON: {"user_intent": "...", "isPoorInfo": 0 | 1}
        """
        system_prompt = """
        You are a routing assistant for a Vietnamese food-recommendation application.
        Your ONLY task is to classify the user's message into exactly one of three intents
        and return a JSON object — nothing else.

        Use the provided chat history to understand context for ambiguous terms like "nó", "đó", "quán này", "món đó".

        ### INTENT DEFINITIONS

        1. "Search"
        - The user wants to FIND a specific restaurant, food stall, café, or eating spot.
        - Includes requests based on location, dish type, budget, distance, rating, etc.
        - CRITICAL RULE (Priority for Meal Plans): If the user lists a series of dishes or food styles assigned to specific times of the day (e.g., breakfast, lunch, dinner, morning, noon, evening), even WITHOUT explicit action verbs like "find", "suggest", or "where to eat", you MUST classify this as "Search". The system assumes they want to find places to eat for those meals.
        - Examples: 
            * "Tìm quán phở gần quận 1"
            * "Cho tôi quán bún bò Huế ngon"
            * "Nhà hàng hải sản không quá 200k"
            * "ăn sáng bằng món thái ăn trưa bằng món âu và ăn tối bằng món việt" -> This is a meal plan to be executed. MUST BE "Search" with isPoorInfo = 0.
        - For this intent you MUST also evaluate `isPoorInfo`:
            * isPoorInfo = 1 → The prompt is extremely vague and lacks any specific actionable detail. This usually applies to single-word inputs that are just general adjectives or abstract concepts with no specific food or intent (e.g., "ngon", "rẻ", "cay", "đắt", "ăn uống", "đói").
            * isPoorInfo = 0 → The prompt contains at least one specific piece of information that the system can use to start a search. This includes a dish name, a specific type of cuisine, a meal time, a location, or a phrase expressing a desire for a specific food (e.g., "bánh canh", "tôi muốn ăn phở", "tìm quán ăn sáng", "quán nào gần đây", "ăn gì ở quận 1"). A dish name alone is SUFFICIENT info.

        2. "System_QA"
        - The user is asking HOW TO USE the application, about its features, reporting a bug,
            or requesting guidance on navigating the UI.
        - Examples: "App này dùng như thế nào?", "Làm sao để chọn cho lịch trình?",
            "Tôi không đăng nhập được", "Tính năng lọc theo giá ở đâu?", "Nhập vị trí chỗ nào thế"
        - Always set isPoorInfo = 0.

        3. "Knowledge_QA"
        - The user is asking about general food knowledge, medical/nutrition advice, health benefits, calories,
            ingredients, cooking methods, historical origins, or general theoretical restaurant/dish discussions.
        - DO NOT classify simple meal listings or menu planning here unless they explicitly ask a question about health, mechanism, or factual verification.
        - Examples: "Tiểu đường ăn bún riêu được không?",
            "Phở bò có bao nhiêu calo?", "Món này ngon không?",
            "Nước mắm có lợi ích gì cho sức khỏe?", "Nguồn gốc của món phở Nam Định"
        - Always set isPoorInfo = 0.

        ### OUTPUT FORMAT (strict JSON, no extra text)
        {
            "user_intent": "Search" | "System_QA" | "Knowledge_QA",
            "isPoorInfo": 0 | 1
        }
        """

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})

        completion = await self.client.chat.completions.create(
            model=self.routing_model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,  # Deterministic for routing
        )

        return completion.choices[0].message.content

    # -------------------------------------------------------------------------
    # SYSTEM Q&A  (Closed-domain — chỉ dùng tài liệu nội bộ)
    # -------------------------------------------------------------------------

    async def handle_system_qa(self, user_prompt: str) -> str:
        """
        Xử lý câu hỏi về cách sử dụng ứng dụng.
        Chỉ trả lời dựa trên nội dung file system_docs.md; không bịa đặt.
        """
        # Đọc tài liệu hướng dẫn
        try:
            with open(SYSTEM_DOCS_PATH, "r", encoding="utf-8") as f:
                system_docs = f.read().strip()
            if not system_docs:
                raise ValueError("Tài liệu rỗng.")
        except (FileNotFoundError, ValueError, OSError):
            system_docs = SYSTEM_DOCS_FALLBACK

        system_prompt = f"""
Bạn là Hỗ trợ viên Kỹ thuật của ứng dụng Gợi ý Món Ăn.

## TÀI LIỆU HƯỚNG DẪN HỆ THỐNG
---
{system_docs}
---

## QUY TẮC BẮT BUỘC
1. Chỉ sử dụng thông tin có trong tài liệu trên để trả lời.
2. TUYỆT ĐỐI KHÔNG tự sáng tạo, thêm hoặc suy diễn tính năng không được đề cập.
3. Nếu câu hỏi của người dùng nằm ngoài phạm vi tài liệu, hãy lịch sự thông báo rằng
   bạn chưa có thông tin về vấn đề đó và gợi ý họ liên hệ đội hỗ trợ.   
4. Trả lời súc tích, rõ ràng, dùng tiếng Việt tự nhiên.
5. Có thể dùng danh sách có đánh số hoặc bullet point nếu cần liệt kê các bước.
6. Trả kết quả về dưới dạng dễ đọc không dùng dạng markdown
"""

        completion = await self.client.chat.completions.create(
            model=self.qa_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        return completion.choices[0].message.content

    # -------------------------------------------------------------------------
    # KNOWLEDGE Q&A  (Open-domain — chuyên gia dinh dưỡng & ẩm thực)
    # -------------------------------------------------------------------------

    async def handle_knowledge_qa(self, user_prompt: str, history: list = None, system_context: str = "") -> str:
        """
        Xử lý câu hỏi về kiến thức dinh dưỡng, sức khỏe, ẩm thực.
        Sử dụng tri thức sẵn có, lịch sử chat và ngữ cảnh hệ thống (quán ăn vừa gợi ý).
        """
        system_prompt = f"""
Bạn là Chuyên gia Dinh dưỡng kiêm Nhà phê bình Ẩm thực của ứng dụng BMI (Bite Mapping Intelligent).

## NGỮ CẢNH HỆ THỐNG (QUAN TRỌNG)
Dưới đây là thông tin về các quán ăn hoặc lịch trình mà hệ thống vừa gợi ý cho người dùng:
---
{system_context}
---

## PHONG CÁCH TRẢ LỜI (BRAND PERSONALITY)
- Bạn có trí nhớ tuyệt vời. Hãy luôn kiểm tra LỊCH SỬ CHAT và NGỮ CẢNH HỆ THỐNG ở trên trước khi trả lời.
- Nếu người dùng hỏi về một quán ăn (ví dụ: "quán đó", "Hải Sản Hoàng Gia") mà quán đó CÓ TRONG ngữ cảnh hệ thống, hãy dùng dữ liệu đó (điểm số, đặc điểm) để trả lời ngay. Đừng bảo họ đi tìm kiếm nếu bạn đã thấy nó trong ngữ cảnh.
- Chỉ khi nào thông tin hoàn toàn không có trong lịch sử và ngữ cảnh, bạn mới hướng dẫn họ sử dụng tính năng tìm kiếm của BMI.

## NGUYÊN TẮC TRẢ LỜI
### 1. Câu hỏi về quán ăn cụ thể
- BƯỚC 1: Tìm quán đó trong NGỮ CẢNH HỆ THỐNG. Nếu thấy, hãy nhận xét dựa trên thông tin đó (ví dụ: "Tôi vừa gợi ý quán này cho bạn, nó có điểm đánh giá là...").
- BƯỚC 2: Nếu không thấy trong ngữ cảnh, tìm trong LỊCH SỬ CHAT.
- BƯỚC 3: Nếu vẫn không thấy, hãy nói: "Tôi chưa thấy quán này trong danh sách gợi ý vừa rồi, nhưng bạn có thể dùng tính năng 'Tìm kiếm' của BMI để xem đánh giá thực tế nhé."

### 2. Câu hỏi về sức khỏe / dinh dưỡng
- Cung cấp kiến thức và luôn kết nối với tính năng BMI (ví dụ: bộ lọc Healthy, tính calo).

### Chung
- Trả lời nhiệt tình, chuyên nghiệp, tiếng Việt tự nhiên.
- **BẮT BUỘC**: Kết thúc bằng disclaimer y tế:
  "⚠️ Lưu ý: Thông tin trên chỉ mang tính tham khảo. Vui lòng tham khảo ý kiến bác sĩ hoặc chuyên gia dinh dưỡng trước khi thay đổi chế độ ăn uống."
"""

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})

        completion = await self.client.chat.completions.create(
            model=self.qa_model_name,
            messages=messages,
            temperature=0.6,
        )

        return completion.choices[0].message.content


# -----------------------------------------------------------------------------
# Quick smoke-test (chạy trực tiếp file)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    import json

    cb = ChatBot()

    test_cases = [
        "tìm quán ngon gần đây",          # Search – isPoorInfo = 1
        "quán phở bò ngon ở quận 3",       # Search – isPoorInfo = 0
        "app này dùng sao?",               # System_QA
        "tiểu đường ăn bún riêu được không?",  # Knowledge_QA
    ]

    async def run_tests():
        for prompt in test_cases:
            result = await cb.routing(prompt)
            parsed = json.loads(result)
            print(f"[{parsed['user_intent']:12s} | isPoorInfo={parsed['isPoorInfo']}] «{prompt}»")

    asyncio.run(run_tests())
