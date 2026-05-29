import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions # Import thêm error của google để bắt cho chuẩn

load_dotenv()
api_key = os.getenv("GEMINI_API")

_client = genai.Client(api_key=api_key)
_model_name = 'gemini-2.5-flash-lite'

class LLMParser():
    def __init__(self):
        self.client = _client
        self.model_name = _model_name

    @retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((exceptions.ServiceUnavailable, exceptions.TooManyRequests))
    )

    async def JSON_response(self, user_prompt: str, current_itinerary: list = None):
        print(f"[LLM_PARSER_LOG] Parsing intent for prompt: '{user_prompt}'")
        
        itinerary_context = ""
        if current_itinerary:
            itinerary_context = f"\nLịch trình hiện tại của người dùng: {json.dumps(current_itinerary, ensure_ascii=False)}"

        prompt = f"""
        Nhiệm vụ của bạn là trích xuất thông tin từ câu lệnh tìm kiếm quán ăn của người dùng và trả về DUY NHẤT một đối tượng JSON hợp lệ. Không giải thích, không thêm text bên ngoài. {itinerary_context}

        Quy tắc trích xuất:
        1. "budget": (Integer) Tổng ngân sách bình quân cho 1 người. Đổi chữ sang số (VD: "1 củ" -> 1000000). Trả về null nếu không đề cập.
        2. "num_meals": (Integer) Số địa điểm mà người dùng yêu cầu (không tính các bữa đã có trong lịch trình hiện tại trừ khi người dùng muốn thay đổi).
        3. "location_pref": (String) Tên Quận/Huyện, Tên đường hoặc khu vực cụ thể. Trả về null nếu không có.
        4. "shu": (Interger) Mức độ cay người dùng yêu cầu, chia làm 5 mức (Từ 1->5). Bắt buộc phải có nếu người dùng có đề cập đến từ "cay". Trả về null nếu không có
        5. "meals_detail": (Array of Objects) Danh sách chi tiết từng bữa ăn được yêu cầu. Mỗi "meal" chỉ xuất hiện tối đa 1 lần. 
            - Nếu người dùng muốn đổi một bữa đã có trong "Lịch trình hiện tại", hãy trích xuất bữa đó.
            - Nếu người dùng yêu cầu thêm bữa mới, hãy trích xuất bữa đó.
            - "meal": (String) Bắt buộc. Chỉ chọn từ: "sáng", "trưa", "xế", "tối", "khuya".
            - "type": (Array of Strings) Loại nhà hàng (chỉ chọn từ: "Quán Việt", "Quán Thái", "Quán nước", "Quán Âu", "Tiệm bánh"). Trả về [] nếu không có.
            - "semantic_query": (String) Các từ khóa mô tả cảm xúc, không khí, view, hoặc tiện ích (máy lạnh, wifi...). Các từ cách nhau bằng dấu phẩy. Trả về null nếu không có.
            - "dish": (String) Một món ăn duy nhất người dùng yêu cầu trong bữa đó, trả về "" nếu người dùng không yêu cầu
        Input của người dùng: "{user_prompt}"
        Output JSON: 
        """

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            content = response.text
            print(f"[LLM_PARSER_LOG] Raw Gemini response (JSON_response): {content.strip()}")
            # Trả về data ngay lập tức
            return json.loads(content)
            
        except Exception as e:
            # In lỗi ra để debug
            print(f"[LLM_PARSER_LOG] Error in Gemini API (JSON_response): {type(e).__name__} - {e}")
            # Raise lên để @retry bắt được và thử lại
            raise e

    async def phrase_health_description(self, user_prompt: str):
        print(f"[LLM_PARSER_LOG] Phrasing health description for: '{user_prompt}'")
        ALL_AVAILABLE_TAGS = [
            "Red_Meat", "Seafood", "Alcohol_Pub", "Shellfish", 
            "Spicy", "DeepFried_Oily", "High_Sugar", "Refined_Carbs", 
            "Low_GI_Diet", "Peanuts_Nuts", "Dairy_Product", "Gluten_Present"
        ]

        prompt = f"""
            You are an expert medical and dietary restriction parser.

            Your task:
            Analyze the user's health condition, symptoms, or dietary descriptions. 
            Use your general medical and nutrition knowledge to infer which dietary restriction tags apply to them, then return ONLY a JSON array of matching tags.

            Allowed tags and their medical meanings:
            - Red_Meat: Avoid for Gout, high uric acid.
            - Seafood / Shellfish: Avoid for Gout, seafood allergies.
            - Alcohol_Pub: Avoid for Gout, stomach issues, weight loss.
            - Spicy: Avoid for Stomach issues (dạ dày), gastritis, reflux (trào ngược), digestive pains.
            - DeepFried_Oily: Avoid for Stomach issues, weight loss, obesity, fatty liver.
            - High_Sugar / Refined_Carbs: Avoid for Diabetes (tiểu đường), weight loss, obesity.
            - Low_GI_Diet: Suitable for Diabetes, low GI requirements.
            - Peanuts_Nuts: Avoid for peanut/nut allergies.
            - Dairy_Product: Avoid for lactose intolerance (bất dung nạp lactose), milk allergy.
            - Gluten_Present: Avoid for Celiac disease, gluten allergy/intolerance.

            Rules:
            - Use medical reasoning: If a user mentions a symptom or disease (e.g., "đau dạ dày"), infer the restricted food groups (e.g., "Spicy", "DeepFried_Oily").
            - Return ONLY tags from the allowed list above.
            - No markdown, no explanations, no comments.
            - Output must be a valid JSON array.
            - If nothing matches or applies, return [].

            Examples:

            User:
            "Tôi hay bị đau bụng và đôi khi là đau dạ dày"
            Output:
            ["Spicy", "DeepFried_Oily"]

            User:
            "Bác sĩ bảo tôi có chỉ số đường huyết cao và cần giảm cân"
            Output:
            ["High_Sugar", "Refined_Carbs", "DeepFried_Oily"]

            User:
            "Tôi bị gout khớp ngón chân cái sưng to"
            Output:
            ["Red_Meat", "Seafood", "Shellfish", "Alcohol_Pub"]

            User:
            "{user_prompt}"

            Output:
            """

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0  # Giữ bằng 0 để đảm bảo suy luận nhất quán, không đoán mò lung tung
                )
            )

            content = response.text.strip()
            print(f"[LLM_PARSER_LOG] Raw Gemini response (phrase_health_description): {content}")

            try:
                data = json.loads(content)

                if not isinstance(data, list):
                    print(f"[LLM_PARSER_LOG] Warning: Response is not a list: {data}")
                    return []

                # Lọc lại một lần nữa bằng Python cho chắc chắn
                filtered_tags = list({
                    tag for tag in data
                    if tag in ALL_AVAILABLE_TAGS
                })
                print(f"[LLM_PARSER_LOG] Extracted tags: {filtered_tags}")

                return filtered_tags

            except json.JSONDecodeError:
                print(f"[LLM_PARSER_LOG] JSON Decode Error: {content}")
                return []

        except Exception as e:
            print(f"[LLM_PARSER_LOG] !!! Error in phrase_health_description: {e}")
            return []
    
if __name__ == "__main__":
    parser = LLMParser()
    print(parser.JSON_response("Tôi đang muốn tìm quán nước, quán ăn trưa và tối. Quán trưa phải là quán Việt, quán ăn tối phải là quán Thái"))

