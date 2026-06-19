import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions

load_dotenv()
api_key = os.getenv("GEMINI_API")
groq_api_key = os.getenv("GROQ_API_KEY_MAIN")

_client = genai.Client(api_key=api_key)
_model_name = 'gemini-2.5-flash-lite'

_groq_client = AsyncGroq(api_key=groq_api_key)
_groq_model_name = "llama-3.3-70b-versatile"

class LLMParser():
    def __init__(self):
        self.client = _client
        self.model_name = _model_name
        self.groq_client = _groq_client
        self.groq_model = _groq_model_name

    async def _call_groq_json(self, system_instruction: str, user_prompt: str):
        print("[LLM_PARSER_LOG] Gemini limit reached. Falling back to GROQ...")
        completion = await self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

    @retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((exceptions.ServiceUnavailable, exceptions.TooManyRequests))
    )
    async def JSON_response(self, user_prompt: str, history: list = None, system_context: str = ""):
        print(f"[LLM_PARSER_LOG] Parsing intent for prompt: '{user_prompt}'")
        
        system_instruction = f"""
        Your task is to extract information from the user's food/restaurant search query and return ONLY a valid JSON object matching the requested structure.
        
        CHAT HISTORY (Conversation context):
        {history if history else "No history available."}

        CURRENT SYSTEM CONTEXT (User's current itinerary & previously suggested shops):
        {system_context}

        HOW TO USE CONTEXT & HISTORY (INHERITANCE RULES):
        - Use CHAT HISTORY and SYSTEM CONTEXT only when the current prompt is clearly contextual.
        - Do NOT inherit fields by default. A prompt with a concrete new dish/type/cuisine and no reference words is a standalone new search.
        - Standalone new search: extract only from the current prompt. Do NOT inherit location_pref, meal, target_shop_id, dish, type, or semantic_query from history.
        - Contextual follow-up: the prompt modifies, rejects, compares, or refers to previous results/context. In this case, inherit only the missing fields needed to preserve the user's previous intent.
        - Treat the prompt as contextual if it contains signals like:
          * rejection/dislike: "không thích", "không muốn", "không ăn", "né", "tránh", "đừng", "bỏ", "loại"
          * alternative/change: "đổi", "khác", "quán khác", "thay", "rẻ hơn", "gần hơn", "ngon hơn"
          * reference words: "quán này", "quán đó", "chỗ này", "ở đó", "như trên", "vừa rồi", "mấy quán đó"
          * adjustment/comparison: "đắt quá", "xa quá", "không hợp", "không đúng món", "không đúng vibe"
        - If the user previously requested a multi-meal itinerary, a contextual adjustment must maintain the same number of meals unless the user explicitly changes it.
        - Set "wants_alternative" to true if the user expresses dissatisfaction, rejects a previous suggestion, or asks for another option.
        - Only set "target_shop_id" when the current prompt explicitly refers to a previous restaurant using reference words or a restaurant name from SYSTEM CONTEXT. For standalone new searches, target_shop_id must be null.
        """

        prompt = f"""
        Extract intent information from the user's query and return ONLY a valid JSON object. If information is missing but exists in CHAT HISTORY or SYSTEM CONTEXT, you MUST carry it over (Inherit) to maintain the conversation flow.
        Only return null when it cannot be inferred from the current prompt OR history.

        Extraction Rules:
        1. "budget": (Integer) Total average budget per person. Convert slang/text to numbers (e.g., "1 củ" -> 1000000, "trăm rưỡi" -> 150000). Return null if not mentioned.
        2. "num_meals": (Integer) Determine the number of meals. 
           - If not mentioned in the current prompt, INHERIT from CHAT HISTORY only when the current prompt is contextual.
           - Examples: "ăn sáng" -> 1, "cả ngày" -> 3, "nửa ngày" -> 2.
           - Only default to 1 when it's a completely new, single-meal request.
        3. "location_pref": (String|null) Specific area. Append city name when possible (e.g., "Quận 1, TP.HCM").
           - For standalone new searches, return null unless the current prompt explicitly mentions a location.
           - For contextual follow-ups, inherit location_pref only if the prompt refers to prior context or only adds a constraint.
        4. "shu": (Integer|null) Spiciness level (1-5). Inherit only for contextual follow-ups. Return null if not mentioned for standalone searches.
        5. "wants_alternative": (Boolean) Set to true if the user wants to change the shop, find another option, or expresses dislike.
        6. "feedback_reason": (String|null) MUST ONLY choose from: "expensive", "far", "unhealthy", "not_style", "low_rating". If wants_alternative=false, feedback_reason must be null.
        7. "meals_detail": (Array of Objects) **The array length must match "num_meals"**.
            - If `wants_alternative` is true or it is a contextual follow-up, populate this array by inheriting only the missing meal types/dishes/types from previous turns.
            - If it is a standalone new search, do NOT inherit meal, dish, type, or semantic_query from history.
            - Do NOT infer meal from current time or history for a standalone search. If the user does not explicitly mention "ăn sáng", "ăn trưa", "ăn tối", "ăn xế", or "ăn khuya", use meal="any".
            - Multi-stop splitting:
                * If the user connects distinct eating/drinking stops with "và", "rồi", "sau đó", "kèm", create separate meals_detail items.
                * A main meal request plus a drink/snack venue request is two stops, not one merged stop.
                * Example meaning: "quán ăn trưa và quán nước" = one lunch stop plus one snack/drink stop.
                * Do NOT attach "Quán nước" to meal="trưa" unless the user explicitly says the drink venue is for lunch, e.g. "quán nước cho bữa trưa".
            - Snack/drink venue mapping:
                * Venue types "Quán nước", "Trà sữa", "Tiệm bánh", "Ăn vặt", "cafe", "quán cà phê" should use meal="xế" when they appear as a separate stop or when no explicit main meal is attached.
                * "quán nước", "cafe", "trà sữa" are venue types, not concrete dish names. Put them in "type", not "dish".
            - Dish/Menu vs Semantic separation:
                * "dish" is ONLY a concrete food or drink item, e.g. "bún bò", "cơm tấm", "ốc", "trà sữa".
                * "semantic_query" is ONLY atmosphere, style, taste, occasion, or restaurant vibe, e.g. "lãng mạn", "yên tĩnh", "view đẹp", "gia đình", "sang trọng".
                * NEVER put concrete dish names into semantic_query.
                * If user says "bún bò lãng mạn", output dish="bún bò" and semantic_query="lãng mạn".
                * If user only asks for a vibe without a concrete dish, output dish=null and semantic_query=<that vibe>.
            - Negative food constraints:
                * If the user says they do NOT like/want/eat a food, do NOT set that rejected food as dish.
                * Treat it as contextual rejection if there is prior context; preserve the previous dish/type/meal/location only if needed.
                * Put the rejected food into semantic_query as "exclude: <food>" only when no dedicated exclusion field exists.
            - Fields:
                - "meal": (String) MUST ONLY choose from: "sáng", "trưa", "xế", "tối", "khuya", "any". Use "any" if no meal is explicitly mentioned.
                - "type": (Array of Strings) (**MUST ONLY choose from: "Quán Việt", "Quán Chay", "Quán Thái", "Quán nước","Quán Nhật", "Quán Âu", "Tiệm bánh"**).
                - "semantic_query": (String|null) Atmosphere/style/taste/occasion/vibe only. Do not include dish names.
                - "dish": (String|null) Concrete food or drink item only.
        8. "target_shop_id": (String|null) The ID of the specific restaurant discussed, resolved from SYSTEM CONTEXT only when the current prompt explicitly refers to it.

        Examples:
        - Current: "Tìm quán bún bò"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "any", "type": ["Quán Việt"], "semantic_query": null, "dish": "bún bò"}}], target_shop_id=null.
        - Current: "Tìm quán bún bò lãng mạn ở Quận 1"
          Output: location_pref="Quận 1, TP.HCM", meals_detail=[{{"meal": "any", "type": ["Quán Việt"], "semantic_query": "lãng mạn", "dish": "bún bò"}}].
        - Current: "Tối nay ăn bún bò"
          Output: meals_detail=[{{"meal": "tối", "type": ["Quán Việt"], "semantic_query": null, "dish": "bún bò"}}].
        - Current: "Tìm quán ăn trưa và quán nước"
          Output: location_pref=null, num_meals=2, meals_detail=[
            {{"meal": "trưa", "type": [], "semantic_query": null, "dish": null}},
            {{"meal": "xế", "type": ["Quán nước"], "semantic_query": null, "dish": null}}
          ], target_shop_id=null.
        - Current: "Tìm quán nước"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "xế", "type": ["Quán nước"], "semantic_query": null, "dish": null}}], target_shop_id=null.
        - Current: "Tìm quán phở, cà phê rồi ăn tối hải sản"
          Output: location_pref=null, num_meals=3, meals_detail=[
            {{"meal": "any", "type": ["Quán Việt"], "semantic_query": null, "dish": "phở"}},
            {{"meal": "xế", "type": ["Quán nước"], "semantic_query": null, "dish": null}},
            {{"meal": "tối", "type": [], "semantic_query": null, "dish": "hải sản"}}
          ], target_shop_id=null.
        - Current: "Sáng mai ăn nhẹ, chiều uống cà phê, tối ăn lẩu"
          Output: location_pref=null, num_meals=3, meals_detail=[
            {{"meal": "sáng", "type": [], "semantic_query": "ăn nhẹ", "dish": null}},
            {{"meal": "xế", "type": ["Quán nước"], "semantic_query": null, "dish": null}},
            {{"meal": "tối", "type": [], "semantic_query": null, "dish": "lẩu"}}
          ], target_shop_id=null.
        - Current: "Đi với gia đình, có trẻ em, cần chỗ rộng để ăn tối"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "tối", "type": [], "semantic_query": "gia đình, có trẻ em, chỗ rộng", "dish": null}}], target_shop_id=null.
        - Current: "Không ăn hải sản, tìm quán trưa không cay"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "trưa", "type": [], "semantic_query": "không cay, exclude: hải sản", "dish": null}}], target_shop_id=null.
        - Current: "Ưu tiên gần hơn, giá rẻ, quán cơm trưa"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "trưa", "type": ["Quán Việt"], "semantic_query": "ưu tiên gần, giá rẻ", "dish": "cơm"}}], target_shop_id=null.
        - Current: "Kiếm chỗ chill chill uống nước"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "xế", "type": ["Quán nước"], "semantic_query": "chill", "dish": null}}], target_shop_id=null.
        - Current: "Làm cái kèo ăn trưa nhẹ nhẹ"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "trưa", "type": [], "semantic_query": "ăn nhẹ", "dish": null}}], target_shop_id=null.
        - Current: "Tìm quán ngon gần đây"
          Output: location_pref=null, num_meals=1, meals_detail=[{{"meal": "any", "type": [], "semantic_query": "ngon, gần đây", "dish": null}}], target_shop_id=null.
        - Current: "Rẻ hơn chút"
          Output: contextual follow-up; inherit previous dish/location/meal as needed, wants_alternative=true, feedback_reason="expensive".
        - Current: "Tôi không thích ăn heo quay"
          Output: contextual rejection if prior context exists; do NOT set dish="heo quay"; inherit previous intent if needed; semantic_query may contain "exclude: heo quay".

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
            # Bắt mọi lỗi (bao gồm lỗi Key sai khi bạn test) để chuyển sang Groq
            print(f"[LLM_PARSER_LOG] Gemini failed or limit reached: {type(e).__name__}. Falling back to GROQ...")
            return await self._call_groq_json(system_instruction, prompt)

    async def phrase_health_description(self, user_prompt: str):
        print(f"[LLM_PARSER_LOG] Phrasing health description for: '{user_prompt}'")
        ALL_AVAILABLE_TAGS = [
            "Red_Meat", "Seafood", "Alcohol_Pub", "Shellfish", 
            "Spicy", "DeepFried_Oily", "High_Sugar", "Refined_Carbs", 
            "Low_GI_Diet", "Peanuts_Nuts", "Dairy_Product", "Gluten_Present","High_Sodium"
        ]

        system_instruction = "You are an expert medical and dietary restriction parser. Return ONLY a JSON array of matching tags."
        prompt = f"""
            Analyze the user's health condition, symptoms, or dietary descriptions. 
            Use your general medical and nutrition knowledge to infer which dietary restriction tags apply to them, then return ONLY a JSON array of matching tags.

            Allowed tags and their medical meanings:
            - Red_Meat: Avoid for Gout, high uric acid.
            - Seafood / Shellfish: Avoid for Gout, seafood allergies.
            - Alcohol_Pub: Avoid for Gout, stomach issues, weight loss.
            - Spicy: Avoid for Stomach issues (dạ dày), gastritis, reflux (trào ngược), digestive pains.
            - DeepFried_Oily: Avoid for Stomach issues, weight loss, obesity, fatty liver.
            - High_Sugar / Refined_Carbs: Avoid for Diabetes (tiểu đường), weight loss, obesity.
            - High_Sodium: Fast food, hotpot and another dish with same semantic.
            - Peanuts_Nuts: Avoid for peanut/nut allergies.
            - Dairy_Product: Avoid for lactose intolerance (bất dung nạp lactose), milk allergy.
            - Gluten_Present: Avoid for Celiac disease, gluten allergy/intolerance.

            Rules:
            - Use medical reasoning: If a user mentions a symptom or disease (e.g., "đau dạ dày"), infer the restricted food groups (e.g., "Spicy", "DeepFried_Oily").
            - Return ONLY tags from the allowed list above.
            - No markdown, no explanations, no comments.
            - Output must be a valid JSON array.
            - If nothing matches or applies, return [].

            User: "{user_prompt}"
            Output:
            """

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0
                )
            )

            content = response.text.strip()
            print(f"[LLM_PARSER_LOG] Raw Gemini response (phrase_health_description): {content}")
            data = json.loads(content)
        except Exception as e:
            print(f"[LLM_PARSER_LOG] Gemini failed (health description): {type(e).__name__}. Falling back to GROQ...")
            data = await self._call_groq_json(system_instruction, prompt)

        # Lọc lại một lần nữa bằng Python cho chắc chắn
        if isinstance(data, list):
            filtered_tags = list({
                tag for tag in data
                if tag in ALL_AVAILABLE_TAGS
            })
            print(f"[LLM_PARSER_LOG] Extracted tags: {filtered_tags}")
            return filtered_tags
        return []
    
if __name__ == "__main__":
    parser = LLMParser()
    import asyncio
    async def test():
        history = [
            {"role": "user", "content": "Tìm quán bún bò"},
            {"role": "assistant", "content": "Dạ, tôi tìm thấy quán Bún Bò O Xuân..."}
        ]
        res = await parser.JSON_response("Khác", history=history)
        print(json.dumps(res, indent=4, ensure_ascii=False))
    asyncio.run(test())
