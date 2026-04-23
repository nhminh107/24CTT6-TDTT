import json

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API")
genai.configure(api_key=api_key)


class LLMParser():
    def __init__(self):
        self.model = genai.GenerativeModel('models/gemini-2.5-flash-lite',
                                           generation_config={"response_mime_type": "application/json"})

    def JSON_response(self, user_prompt: str):
        prompt = f"""
           Nhiệm vụ của bạn là trích xuất thông tin từ câu lệnh tìm kiếm quán ăn của người dùng và trả về DUY NHẤT một đối tượng JSON hợp lệ. Không giải thích, không thêm text bên ngoài, nếu thông tin quá sơ sài, không đủ để bạn nhận biết bất cứ gì thì hãy trả về null ở mọi field.

           Quy tắc trích xuất:
           1. "budget": (Integer) Tổng ngân sách. Đổi chữ sang số (VD: "1 củ", "1 tr" -> 1000000). Nếu không đề cập, trả về null.
           2. "num_meals": (Integer) Số bữa ăn. Mặc định là 3 nếu không nói rõ.
           3. "meal_tags": (Array of Strings) Các bữa ăn được nhắc đến (chỉ chọn từ: "sáng", "trưa", "xế", "tối", "khuya"). Trả về mảng rỗng [] nếu không đề cập.
           4. "hard_filters": (Array of Strings) Các tiện ích vật lý có thể đo đếm/xác nhận rõ ràng (VD: "máy lạnh", "chỗ để xe", "wifi", "bàn ngoài trời", "thanh toán thẻ").
           5. "location_pref": (String) Tên Quận/Huyện hoặc khu vực cụ thể được nhắc đến. Trả về null nếu không có.
           6. "semantic_query": (String) Tập hợp CÁC TỪ KHÓA còn lại mô tả cảm xúc, không khí, phong cách, view, hoặc trải nghiệm trừu tượng (VD: "yên tĩnh", "nhạc acoustic", "view hoàng hôn", "lãng mạn", "phù hợp gia đình"). Gom thành 1 chuỗi string cách nhau bằng dấu phẩy. Trả về null nếu không có.

           Input của người dùng: "{user_prompt}"
           Output JSON: 
           """

        response = self.model.generate_content(prompt)
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

