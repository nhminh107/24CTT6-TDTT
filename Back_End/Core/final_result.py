import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import AsyncGroq
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions

load_dotenv()
api_key = os.getenv("GEMINI_API")
groq_api_key = os.getenv("GROQ_API_KEY_MAIN")

_client = genai.Client(api_key=api_key)
_model_name = 'gemini-2.5-flash-lite'

_groq_client = AsyncGroq(api_key=groq_api_key)
_groq_model_name = "llama-3.3-70b-versatile"


class FinalResultLLM:
    def __init__(self):
        self.client = _client
        self.model_name = _model_name
        self.groq_client = _groq_client
        self.groq_model = _groq_model_name

    async def _call_groq_json(self, prompt: str):
        print("[FINAL_RESULT_LOG] Gemini limit reached. Falling back to GROQ...")
        completion = await self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": "You are a selection assistant for a food itinerary. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

    def _meal_order(self, candidates_df: pd.DataFrame, parsed_json: dict | None) -> list:
        if parsed_json and parsed_json.get('meals_detail'):
            return [m.get('meal') for m in parsed_json['meals_detail'] if m.get('meal')]

        order = []
        for meal in candidates_df.get('meal', []):
            if meal not in order:
                order.append(meal)
        return order

    def _candidates_payload(self, candidates_df: pd.DataFrame, meal_order: list) -> dict:
        fields = [
            'id', 'name', 'address', 'avg_price', 'star', 'type',
            'semantic_text', 'score'
        ]
        payload = {}
        for meal in meal_order:
            meal_df = candidates_df[candidates_df['meal'] == meal].copy()
            if meal_df.empty:
                continue
            available_fields = [f for f in fields if f in meal_df.columns]
            payload[meal] = meal_df[available_fields].to_dict('records')
        return payload

    def _candidate_rows(self, candidates_df: pd.DataFrame, meal_order: list) -> dict:
        candidate_map = {}
        for meal in meal_order:
            meal_df = candidates_df[candidates_df['meal'] == meal].copy()
            if meal_df.empty:
                continue
            meal_df = meal_df.sort_values('score', ascending=False)
            candidate_map[meal] = meal_df.to_dict('records')
        return candidate_map
    
    @retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((exceptions.ServiceUnavailable, exceptions.TooManyRequests))
    )

    async def _select_with_llm(self, candidates_payload: dict, user_prompt: str) -> dict:
        prompt = f"""
        Nhiệm vụ: chọn đúng 1 quán ăn cho mỗi bữa từ danh sách ứng viên.
        Không tạo mới, chỉ chọn từ danh sách đã cho. Ưu tiên phù hợp yêu cầu người dùng.
        Tránh chọn trùng id giữa các bữa nếu có thể.

        Trả về DUY NHẤT JSON hợp lệ theo schema:
        {{
          "selected": [
            {{"meal": "<meal>", "id": "<id>"}}
          ]
        }}

        User prompt: "{user_prompt}"
        Candidates: {json.dumps(candidates_payload, ensure_ascii=False)}
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
            data = json.loads(response.text)
        except Exception as e:
            # Bắt mọi lỗi (bao gồm lỗi Key sai khi bạn test) để chuyển sang Groq
            print(f"[FINAL_RESULT_LOG] Gemini failed or limit reached: {type(e).__name__}. Falling back to GROQ...")
            data = await self._call_groq_json(prompt)

        selected = data.get('selected', []) if isinstance(data, dict) else []
        result = {}
        for item in selected:
            meal = item.get('meal')
            rid = item.get('id')
            if meal and rid:
                result[meal] = str(rid)
        return result

    def _select_unique_combination(self, meal_order: list, candidate_map: dict, max_per_meal: int = 1) -> list:
        selected_rows = []
        used_ids = set()

        for meal in meal_order:
            candidates = candidate_map.get(meal, [])
            count = 0  # Biến đếm số lượng quán đã chọn cho bữa này
            
            for row in candidates:
                if count >= max_per_meal: # Dừng khi đã đủ số lượng (ví dụ: 3)
                    break
                    
                rid = str(row.get('id'))
                if rid not in used_ids:
                    selected_rows.append(row)
                    used_ids.add(rid)
                    count += 1
                    
            if count == 0:
                print(f"[FINAL_RESULT_LOG] Warning: No available unique restaurants found for meal '{meal}'. Skipping this meal in the final itinerary.")

        return selected_rows

    async def run_final_selection(
        self,
        candidates_df: pd.DataFrame,
        user_prompt: str,
        parsed_json: dict | None = None,
        max_per_meal: int = 1
    ) -> pd.DataFrame:
        if candidates_df is None or candidates_df.empty:
            return pd.DataFrame()

        meal_order = self._meal_order(candidates_df, parsed_json)
        if not meal_order:
            return pd.DataFrame()

        candidates_payload = self._candidates_payload(candidates_df, meal_order)
        candidate_map = self._candidate_rows(candidates_df, meal_order)
        if not candidates_payload or not candidate_map:
            return pd.DataFrame()

        try:
            selected_map = await self._select_with_llm(candidates_payload, user_prompt)
        except Exception:
            selected_map = {}

        if selected_map:
            for meal, selected_id in selected_map.items():
                if meal not in candidate_map:
                    continue
                rows = candidate_map[meal]
                preferred = []
                fallback = []
                for row in rows:
                    if str(row.get('id')) == str(selected_id):
                        preferred.append(row)
                    else:
                        fallback.append(row)
                candidate_map[meal] = preferred + fallback

        final_rows = self._select_unique_combination(meal_order, candidate_map, max_per_meal=max_per_meal)
        if not final_rows:
            return pd.DataFrame()

        if not final_rows:
            return pd.DataFrame()

        final_df = pd.DataFrame(final_rows)
        if 'score' in final_df.columns and not final_df['score'].empty:
            itinerary_avg_score = round(final_df['score'].mean(), 4)
            final_df['itinerary_avg_score'] = itinerary_avg_score
        else:
            final_df['itinerary_avg_score'] = 0.0

        return final_df
