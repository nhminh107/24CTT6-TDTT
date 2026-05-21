import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API")

_client = genai.Client(api_key=api_key)
_model_name = 'gemini-2.5-flash-lite'

class LLMParser():
    def __init__(self):
        self.client = _client
        self.model_name = _model_name

    async def JSON_response(self, user_prompt: str):
        prompt = f"""
        Nhiệm vụ của bạn là trích xuất thông tin từ câu lệnh tìm kiếm quán ăn của người dùng và trả về DUY NHẤT một đối tượng JSON hợp lệ. Không giải thích, không thêm text bên ngoài, nếu thông tin quá sơ sài thì trả về null/mảng rỗng ở các field tương ứng.

        Quy tắc trích xuất:
        1. "budget": (Integer) Tổng ngân sách bình quân cho 1 người. Đổi chữ sang số (VD: "1 củ" -> 1000000). Trả về null nếu không đề cập.
        2. "num_meals": (Integer) Số địa điểm mà người dùng yêu cầu.
        3. "location_pref": (String) Tên Quận/Huyện, Tên đường hoặc khu vực cụ thể. Trả về null nếu không có.
        4. "shu": (Interger) Mức độ cay người dùng yêu cầu, chia làm 5 mức (Từ 1->5). Bắt buộc phải có nếu người dùng có đề cập đến từ "cay". Trả về null nếu không có
        5. "meals_detail": (Array of Objects) Danh sách chi tiết từng bữa ăn được yêu cầu. Số danh sách yêu cầu phải khớp với num_meals. Nếu người dùng đưa ra yêu cầu chung (không chỉ định riêng bữa nào), hãy gán yêu cầu đó vào tất cả các bữa ăn được nhắc đến. Mỗi object bao gồm:
            - "meal": (String) Bắt buộc. Chỉ chọn từ: "sáng", "trưa", "xế", "tối", "khuya".
            - "type": (Array of Strings) Loại nhà hàng (chỉ chọn từ: "Quán Việt", "Quán Thái", "Quán nước", "Quán Âu", "Tiệm bánh"). Trả về [] nếu không có.
            - "semantic_query": (String) Các từ khóa mô tả cảm xúc, không khí, view, hoặc tiện ích (máy lạnh, wifi...). Các từ cách nhau bằng dấu phẩy. Trả về null nếu không có.

        Input của người dùng: "{user_prompt}"
        Output JSON: 
        """

        response = await self.client.aio.models.generate_content(
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
    print(parser.JSON_response("Tôi đang muốn tìm quán nước, quán ăn trưa và tối. Quán trưa phải là quán Việt, quán ăn tối phải là quán Thái"))

