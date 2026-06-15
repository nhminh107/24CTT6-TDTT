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
        - ALWAYS use CHAT HISTORY and SYSTEM CONTEXT to understand short, vague, or follow-up prompts.
        - CONTEXT MERGING & INHERITANCE: If the user adds a filter or constraint (e.g., "Ở Quận 1", "Rẻ thôi", "Không cay") or requests an alternative (e.g., "Khác", "Đổi quán") to a search started in previous messages, you MUST INHERIT the ENTIRE previous search intent (including num_meals, location_pref, dish, type, semantic_query) and only update the specified field.
        - If the user previously requested a multi-meal itinerary (e.g., 3 meals), any follow-up adjustment (like "rẻ hơn") MUST maintain the same number of meals and types unless they explicitly change it.
        - Example:
            * History: "Tìm quán mì cay lãng mạn ở Quận 1"
            * Current: "Rẻ hơn chút"
            * Result: dish="mì cay", semantic_query="lãng mạn", location_pref="Quận 1, TP.HCM", budget=<smaller_value>, num_meals=1.
        - Example 2 (Itinerary):
            * History: "Lên lịch ăn cả ngày hôm nay" -> System suggested 3 meals.
            * Current: "Đổi quán khác rẻ hơn"
            * Result: wants_alternative=true, feedback_reason="expensive", num_meals=3, meals_detail=[inherited meals from history].
        - Set "wants_alternative" to true if they express dissatisfaction or want another option.
        - Cross-reference the query with the contexts to identify the exact "target_shop_id" they are referring to.
        """

        prompt = f"""
        Extract intent information from the user's query and return ONLY a valid JSON object. If information is missing but exists in CHAT HISTORY or SYSTEM CONTEXT, you MUST carry it over (Inherit) to maintain the conversation flow.
        Only return null when it cannot be inferred from the current prompt OR history.

        Extraction Rules:
        1. "budget": (Integer) Total average budget per person. Convert slang/text to numbers (e.g., "1 củ" -> 1000000, "trăm rưỡi" -> 150000). Return null if not mentioned.
        2. "num_meals": (Integer) Determine the number of meals. 
           - If not mentioned in the current prompt, INHERIT from CHAT HISTORY if a multi-meal itinerary was previously discussed.
           - Examples: "ăn sáng" -> 1, "cả ngày" -> 3, "nửa ngày" -> 2.
           - Only default to 1 when it's a completely new, single-meal request.
        3. "location_pref": (String) Specific area. ALWAYS inherit from CHAT HISTORY if not mentioned in the current prompt. Try to append city name (e.g., "Quận 1, TP.HCM").
        4. "shu": (Integer) Spiciness level (1-5). Inherit if applicable.
        5. "wants_alternative": (Boolean) Set to true if the user wants to change the shop, find another option, or expresses dislike.
        6. "feedback_reason": (String) MUST ONLY choose from: "expensive", "far", "unhealthy", "not_style", "low_rating".
        7. "meals_detail": (Array of Objects) **The array length must match "num_meals"**.
            - If `wants_alternative` is true or it's a follow-up, you MUST populate this array by inheriting the meal types (sáng, trưa, tối...) and dishes/types from the previous turns in history.
            - Fields:
                - "meal": (String) Required. MUST ONLY choose from: "sáng", "trưa", "xế", "tối", "khuya".
                - "type": (Array of Strings) (MUST ONLY choose from: "Quán Việt", "Quán Chay", "Quán Thái", "Quán nước","Quán Nhật", "Quán Âu", "Tiệm bánh").
                - "semantic_query": (String) Flavor profiles, atmosphere, or generic terms like "ăn vặt".
                - "dish": (String) Specific food item.
        8. "target_shop_id": (String) The ID of the specific restaurant discussed, resolved from SYSTEM CONTEXT.

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
            "Low_GI_Diet", "Peanuts_Nuts", "Dairy_Product", "Gluten_Present"
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