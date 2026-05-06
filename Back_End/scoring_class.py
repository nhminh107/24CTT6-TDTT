# ============================================================
# MODULE ALGORITHM — CÁCH 2: CLASS (OOP)
# INPUT : filtered_data (dict[str, DataFrame]) + parsed_json (dict)
# OUTPUT: dict[str, DataFrame] — đã có cột 'score', sorted descending
# ============================================================
from math import radians, sin, cos, sqrt, atan2
import pandas as pd
from Back_End.CONFIG import Weights, user_lat, user_lng
from Database.database import ChromaDBManager

class RestaurantScorer:
    """
    Module 3: Algorithm — Tính điểm và xếp hạng nhà hàng.

    Sử dụng:
        scorer = RestaurantScorer(user_lat=16.068, user_lng=108.224)
        result = scorer.run_scoring_pipeline(filtered_data, parsed_json)
    """

    def __init__(self):
        """
        Khởi tạo scorer với vị trí người dùng.
        INPUT:
            user_lat (float) — vĩ độ người dùng
            user_lng (float) — kinh độ người dùng
            weights (dict)   — trọng số tùy chỉnh (optional),
                               mặc định dùng DEFAULT_WEIGHTS
        """
        self.user_lat = user_lat
        self.user_lng = user_lng
        self.weights  = Weights

    # ─── PRIVATE: các hàm tính điểm thành phần ──────────────────────────

    def _score_star(self, star: float) -> float:
        """
        Normalize điểm sao về [0, 1]
        INPUT  : star (float) — VD: 4.8
        RETURN : float trong [0.0, 1.0]
        """
        return round((star - 1) / 4, 4)

    def _score_price(self, avg_price: int, budget_per_meal: float) -> float:
        """
        Tính điểm giá so với ngân sách mỗi bữa.
        INPUT  : avg_price (int), budget_per_meal (float)
        RETURN : float trong [0.0, 1.0]
        """
        if budget_per_meal <= 0:
            return 0.0
        ratio = avg_price / budget_per_meal
        if ratio <= 0.5:
            return 1.0
        elif ratio <= 0.8:
            return 0.8
        elif ratio <= 1.0:
            return 0.5
        return 0.0

    def _score_distance(self, rest_lat: float, rest_lng: float) -> float:
        """
        Tính điểm khoảng cách bằng Haversine.
        Dùng self.user_lat / self.user_lng đã lưu lúc __init__.
        INPUT  : rest_lat, rest_lng (float)
        RETURN : float trong (0.0, 1.0]
        """
        R = 6371
        dlat = radians(rest_lat - self.user_lat)
        dlng = radians(rest_lng - self.user_lng)
        a = (sin(dlat / 2) ** 2
             + cos(radians(self.user_lat))
             * cos(radians(rest_lat))
             * sin(dlng / 2) ** 2)
        dist_km = R * 2 * atan2(sqrt(a), sqrt(1 - a))
        return round(1 / (1 + dist_km), 4)


    def _score_semantic(self, semantic_text: str, semantic_query: str) -> float:
        """
        Tính điểm khớp ngữ nghĩa bằng keyword matching.
        INPUT  : semantic_text (str) từ data, semantic_query (str) từ Parsing
        RETURN : float trong [0.0, 1.0]
        """
        if not semantic_query:
            return 0.0
        keywords = [kw.strip().lower() for kw in semantic_query.split(",") if kw.strip()]
        if not keywords:
            return 0.0
        text = semantic_text.lower()
        matches = sum(1 for kw in keywords if kw in text)
        return round(matches / len(keywords), 4)

    def _compute_total_score(self,
                              row: dict,
                              budget_per_meal: float,
                              semantic_query: str) -> float:
        """
        Tính tổng điểm weighted cho 1 nhà hàng.
        INPUT  : row (dict), budget_per_meal, user_shu, semantic_query
        RETURN : float — tổng điểm trong [0.0, 1.0]
        """
        total = (
            self.weights['star']     * self._score_star(row['star']) +
            self.weights['price']    * self._score_price(row['avg_price'], budget_per_meal) +
            self.weights['distance'] * self._score_distance(row['lat'], row['lng']) +
            self.weights['semantic'] * self._score_semantic(row['semantic_text'], semantic_query)
        )
        return round(total, 4)

    # ─── PUBLIC: hàm chính giao tiếp với các module khác ────────────────

    def run_scoring_pipeline(self,
                              filtered_data: dict,
                              parsed_json: dict,
                              top_n: int = 5) -> dict:
        """
        Hàm CHÍNH của Module Algorithm.
        Chạy toàn bộ pipeline tính điểm cho từng bữa ăn.

        INPUT:
            filtered_data (dict[str, DataFrame]) — output từ Module Filter
                VD: {'sang': df1, 'trua': df2, 'toi': df3}
            parsed_json (dict) — output từ Module Parsing
                VD: {'budget': 2500000, 'num_meals': 3,
                     'user_shu': 2, 'meals_detail': [...]}
            top_n (int) — số nhà hàng trả về mỗi bữa, mặc định 5

        RETURN:
            dict[str, DataFrame]
            — key   : meal tag (str) VD: 'sang', 'trua', 'toi'
            — value : DataFrame đã có cột 'score', sorted descending, top_n hàng
            VD:
            {
                'trua': DataFrame([...], columns=[..., 'score']),
                'toi' : DataFrame([...], columns=[..., 'score']),
            }
        """
        budget       = parsed_json.get('budget') or 0
        num_meals    = parsed_json.get('num_meals') or 1
        meals_detail = parsed_json.get('meals_detail', [])

        budget_per_meal = budget / num_meals if num_meals > 0 else 0

        semantic_map = {
            m['meal']: m.get('semantic_query') or ''
            for m in meals_detail
        }

        result = {}

        for meal_tag, df in filtered_data.items():
            if df.empty:
                result[meal_tag] = df
                continue

            semantic_query = semantic_map.get(meal_tag, '')

            df = df.copy()
            df['score'] = df.apply(
                lambda row: self._compute_total_score(
                    row.to_dict(),
                    budget_per_meal,
                    semantic_query
                ),
                axis=1
            )

            result[meal_tag] = (
                df.sort_values('score', ascending=False)
                  .head(top_n)
                  .reset_index(drop=True)
            )

        return result
