import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API")

class LLMParser():
    def __init__(self):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash-lite'

    def JSON_response(self, user_prompt: str):
        prompt = f"""
        Nhiệm vụ của bạn là trích xuất thông tin từ câu lệnh tìm kiếm quán ăn của người dùng và trả về DUY NHẤT một đối tượng JSON hợp lệ. Không giải thích, không thêm text bên ngoài, nếu thông tin quá sơ sài, không đủ để bạn nhận biết bất cứ gì thì hãy trả về null ở mọi field.

        Quy tắc trích xuất:
        1. "budget": (Integer) Tổng ngân sách. Đổi chữ sang số (VD: "1 củ", "1 tr" -> 1000000). Nếu không đề cập, trả về null. Budget ở đây tính bình quân cho 1 người. Nếu người dùng không đề cập mấy người thì mặc định là 1 người.
        2. "num_meals": (Integer) Số bữa ăn. Mặc định là 3 nếu không nói rõ.
        3. "meal_tags": (Array of Strings) Các bữa ăn được nhắc đến (chỉ chọn từ: "sáng", "trưa", "xế", "tối", "khuya"). Trả về mảng rỗng [] nếu không đề cập.
        4. "type": (Array of Strings) Loại nhà hàng được trả về (chỉ chọn từ: "Quán Việt", "Quán Thái", "Quán nước", "Quán Âu", "Tiệm bánh"). Trả về mảng rỗng [] nếu không đề cập.
        5. "semantic_query": (String) Tập hợp CÁC TỪ KHÓA còn lại mô tả cảm xúc, không khí, phong cách, view, tiện ích vật lý (máy lạnh, wifi) hoặc trải nghiệm trừu tượng. Gom thành 1 chuỗi string cách nhau bằng dấu phẩy. Trả về null nếu không có.

        Input của người dùng: "{user_prompt}"
        Output JSON: 
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        content = response.text

        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            print("AI không trả về đúng định dạng JSON")
            return content

if __name__ == "__main__":
    parser = LLMParser()
    print(parser.JSON_response("Tôi muốn tìm nhà hành ăn sáng, trưa, tối. Kinh phí 2 triệu rưỡi"))

