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

    async def JSON_response(self, user_prompt: str, system_context: str = ""):
        print(f"[LLM_PARSER_LOG] Parsing intent for prompt: '{user_prompt}'")
        
        # System instruction in English to optimize token usage and reasoning
        system_instruction = f"""
        Your task is to extract information from the user's food/restaurant search query and return ONLY a valid JSON object matching the requested structure.
        
        CURRENT SYSTEM CONTEXT (User's current itinerary & previously suggested shops):
        {system_context}

        SPECIAL ROUTING RULES:
        - If the user wants to change the restaurant, find another place, or expresses dissatisfaction with the current suggestion (e.g., "không thích", "không ăn quán này", "chỗ này chán", "đổi quán"), set "wants_alternative" to true.
        - SIMULTANEOUSLY, cross-reference their query with the CURRENT SYSTEM CONTEXT above to identify the exact ID of the restaurant they are referring to, and fill it in the "target_shop_id" field. If the specific shop cannot be identified, return null.
        """

        prompt = f"""
        Extract intent information from the user's query and return ONLY a valid JSON object. No explanations, no markdown formatting outside the JSON, no extra text. If the information is missing or vague, return null or an empty array/string in the corresponding fields.

        Extraction Rules:
        1. "budget": (Integer) Total average budget per person. Convert slang/text to numbers (e.g., "1 củ" -> 1000000, "trăm rưỡi" -> 150000). Return null if not mentioned.
        2. "num_meals": (Integer) Number of places/meals the user is requesting. Default to 1 if not specified.
        3. "location_pref": (String) District, street name, or specific area in Vietnam (e.g., "Quận 1", "Sư Vạn Hạnh"). Return null if not provided.
        4. "shu": (Integer) Spiciness level requested by the user, on a scale of 1 to 5. Mandatory if the user mentions keywords related to spicy ("cay", "cay vừa", "siêu cay"). Return null if not mentioned.
        5. "wants_alternative": (Boolean) Set to true if the user wants to change the shop, find another option, or expresses dislike for the current shop.
        6. "feedback_reason": (String) Reason for dissatisfaction or change request (if any). MUST ONLY choose from: "expensive", "far", "unhealthy", "not_style", "low_rating". Return null if no specific reason is given.
        7. "meals_detail": (Array of Objects) Detailed list of each requested meal. Each "meal" type can only appear at most once. The array length must match "num_meals". If the user makes a general request without specifying the meal time, assign it to an appropriate meal; café/bakery/snacks ("quán nước/tiệm bánh/ăn vặt") defaults to "xế" if not specified. Each object includes:
            - "meal": (String) Required. MUST ONLY choose from: "sáng", "trưa", "xế", "tối", "khuya".
            - "type": (Array of Strings) Restaurant type (MUST ONLY choose from: "Quán Việt", "Quán Thái", "Quán nước", "Quán Âu", "Tiệm bánh"). Return [] if not mentioned.
            - "semantic_query": (String) Keywords describing mood, atmosphere, view, or amenities (e.g., "máy lạnh", "yên tĩnh", "vỉa hè"). Separated by commas. Return null if none.
            - "dish": (String) A single specific dish requested for that meal (lowercase). Return "" if no specific dish is requested.
        8. "target_shop_id": (String) The ID of the specific restaurant the user is complaining about or wants to change, resolved from the SYSTEM CONTEXT. Return null if not applicable.

        User Input (in Vietnamese): "{user_prompt}"
        Output JSON:
        """

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            content = response.text
            print(f"[LLM_PARSER_LOG] Raw Gemini response (JSON_response): {content.strip()}")
            return json.loads(content)
        
        except Exception as e:
            print(f"[LLM_PARSER_LOG] Error in Gemini API (JSON_response): {type(e).__name__} - {e}")
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

