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
        Phân loại ý định người dùng thành một trong bốn nhãn:
          - "Search"      : Tìm kiếm quán ăn / địa điểm ăn uống.
          - "System_QA"   : Hỏi về cách dùng ứng dụng, tính năng, báo lỗi.
          - "Knowledge_QA": Hỏi về dinh dưỡng, sức khỏe, kiến thức ẩm thực.
          - "Out_Scope"   : Các nội dung không liên quan (chính trị, tôn giáo, toán học, coding, v.v.)

        Trả về chuỗi JSON: {"user_intent": "...", "isPoorInfo": 0 | 1}
        """
        system_prompt = """
        You are a routing assistant for BMI (Bite Mapping Intelligent), a Vietnamese food and health application.
        Your ONLY task is to classify the user's message into exactly one of FOUR intents and return a JSON object.

        ### HOW TO USE CHAT HISTORY (CRITICAL)
        - ALWAYS check the chat history to understand short or ambiguous prompts.
        - If the user provides a short answer (e.g., "Quận 1", "Bún bò", "Có", "Ok"), check if the last message from the Assistant was asking for missing information.
        - If the previous Assistant message asked "Bạn muốn ăn ở đâu?" and user replies "Quận 1" -> Intent is "Search" and isPoorInfo = 0.
        - If the prompt uses pronouns like "nó", "quán đó", "ở đó", refer to the last mentioned restaurant or dish in the history.

        ### INTENT DEFINITIONS

        1. "Search"
        - Finding restaurants, food, or places to eat.
        - Examples: "bánh canh", "tìm quán ăn sáng", "quán nào gần đây".
        - Evaluation of `isPoorInfo`:
            * isPoorInfo = 1 → Extremely vague with NO context in history (e.g., just "ngon", "đói").
            * isPoorInfo = 0 → A specific food/place OR the next answer that fulfills the previous search query. Simply understand that anything related to food/place will have a value of 0.

        2. "System_QA"
        - Asking HOW TO USE the BMI app or reporting bugs.

        3. "Knowledge_QA"
        - Asking about nutrition, health benefits, calories, OR details about a SPECIFIC restaurant's menu, quality, and offerings.
        - If the user asks "Quán đó có món X không?", "Thực đơn quán này có gì?", "Quán này ăn ngon không?" -> This is "Knowledge_QA".

        4. "Out_Scope"
        - Completely unrelated to food, health, travel, or the BMI app.

        ### OUTPUT FORMAT (strict JSON)
        {
            "user_intent": "Search" | "System_QA" | "Knowledge_QA" | "Out_Scope",
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
You are the Technical Support Assistant for the "Gợi ý Món Ăn" (Food Recommendation) application.

## SYSTEM DOCUMENTATION
---
{system_docs}
---

## STRICT RULES
1. Rely ONLY on the provided documentation above to answer the user.
2. ABSOLUTELY NO fabrication, invention, or extrapolation of features not explicitly mentioned.
3. If the user's question falls outside the scope of the documentation, politely inform them that you do not have information on that matter and suggest they contact the support team.
4. Keep the response concise, clear, and written in natural Vietnamese.
5. You may use numbered or bulleted lists if needed to enumerate steps.
6. Return the final result in a clean, easily readable plain text format. DO NOT use markdown formatting in the final response.
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
You are the Nutrition Expert and Food Critic for the BMI (Bite Mapping Intelligent) application.

## SYSTEM CONTEXT (CRITICAL)
Here is the information about the restaurants or itineraries that the system has just recommended to the user:
---
{system_context}
---

## BRAND PERSONALITY
- You have an excellent memory. ALWAYS check the CHAT HISTORY and the SYSTEM CONTEXT above before answering.
- If the user asks about a specific restaurant (e.g., "quán đó", "Hải Sản Hoàng Gia") and that restaurant EXISTS in the system context, use that data (scores, characteristics) to answer immediately. Do not tell them to search if you can already see it in the context.
- Guide them to use BMI's search feature only when the information is completely missing from both the history and context.

## RESPONSE PRINCIPLES
### 1. Questions about a specific restaurant
- STEP 1: Look for the restaurant in the SYSTEM CONTEXT. If found, comment based on that data (e.g., "Tôi vừa gợi ý quán này cho bạn, nó có điểm đánh giá là...").
- STEP 2: If not found in the context, search within the CHAT HISTORY.
- STEP 3: If still not found, reply: "Tôi chưa thấy quán này trong danh sách gợi ý vừa rồi, nhưng bạn có thể dùng tính năng 'Tìm kiếm' của BMI để xem đánh giá thực tế nhé."

### 2. Questions about health / nutrition
- Provide expert knowledge and always link it back to BMI features (e.g., Healthy filter, calorie tracking).

### General Guidelines
- Respond enthusiastically, professionally, and in natural Vietnamese.
- **MANDATORY**: When users ask about health issues, Always end your response with the following medical disclaimer:
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
