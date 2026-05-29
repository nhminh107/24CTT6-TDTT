import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions # Import thêm error của google để bắt cho chuẩn

load_dotenv()
api_key = os.getenv("GEMINI_API")

_client = genai.Client(api_key=api_key)
_model_name = 'gemini-2.5-flash-lite'


class FinalResultLLM:
    def __init__(self):
        self.client = _client
        self.model_name = _model_name

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

    async def _select_with_llm(self, candidates_payload: dict, user_prompt: str, top_k: int = 3) -> dict:
        prompt = f"""
        Nhiệm vụ: Chọn ra {top_k} quán ăn tốt nhất cho mỗi bữa từ danh sách ứng viên.
        Sắp xếp theo thứ tự ưu tiên giảm dần. Ưu tiên phù hợp yêu cầu người dùng.
        Tránh chọn trùng id giữa các bữa nếu có thể.

        Trả về DUY NHẤT JSON hợp lệ theo schema:
        {{
          "selected": [
            {{"meal": "<meal>", "ids": ["<id1>", "<id2>", "<id3>"]}}
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
            selected = data.get('selected', []) if isinstance(data, dict) else []
            result = {}
            for item in selected:
                meal = item.get('meal')
                rids = item.get('ids', [])
                if meal and rids:
                    result[meal] = [str(rid) for rid in rids]
            return result

        except Exception as e:
            print(f"DEBUG: Lỗi API trong final_result.py: {type(e).__name__} - {e}")
            raise e

    def _select_top_k_combination(self, meal_order: list, candidate_map: dict, top_k: int = 3) -> list:
        selected_rows = []
        
        for meal in meal_order:
            candidates = candidate_map.get(meal, [])
            # Lấy tối đa top_k quán cho mỗi bữa
            selected_rows.extend(candidates[:top_k])

        return selected_rows

    async def run_final_selection(
        self,
        candidates_df: pd.DataFrame,
        user_prompt: str,
        parsed_json: dict | None = None,
        top_k: int = 3
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
            selected_ids_map = await self._select_with_llm(candidates_payload, user_prompt, top_k=top_k)
        except Exception:
            selected_ids_map = {}

        if selected_ids_map:
            for meal, selected_ids in selected_ids_map.items():
                if meal not in candidate_map:
                    continue
                rows = candidate_map[meal]
                preferred = []
                fallback = []
                selected_ids_str = [str(sid) for sid in selected_ids]
                
                # Sắp xếp lại candidate_map sao cho các quán được LLM chọn lên đầu
                for row in rows:
                    if str(row.get('id')) in selected_ids_str:
                        preferred.append(row)
                    else:
                        fallback.append(row)
                candidate_map[meal] = preferred + fallback

        final_rows = self._select_top_k_combination(meal_order, candidate_map, top_k=top_k)
        if not final_rows:
            return pd.DataFrame()

        final_df = pd.DataFrame(final_rows)
        if 'score' in final_df.columns and not final_df['score'].empty:
            itinerary_avg_score = round(final_df['score'].mean(), 4)
            final_df['itinerary_avg_score'] = itinerary_avg_score
        else:
            final_df['itinerary_avg_score'] = 0.0

        return final_df
