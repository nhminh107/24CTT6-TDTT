import itertools
from math import radians, sin, cos, sqrt, atan2
import pandas as pd
from Back_End.CONFIG import Weights
from Back_End.Database.database import ChromaDBManager

class RestaurantScorer:
    """
    Module 3: Algorithm — Tính điểm và xếp hạng nhà hàng.

    Sử dụng:
        scorer = RestaurantScorer(user_lat=16.068, user_lng=108.224)
        result = scorer.run_scoring_pipeline(filtered_data, parsed_json)
    """

    def __init__(self,user_lat: float, user_lng:float,  db: ChromaDBManager):
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
        self.db = db 
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

    def _score_distance(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> float:
        """
        Tính điểm khoảng cách bằng Haversine giữa 2 điểm.
        INPUT  : start_lat, start_lng, end_lat, end_lng (float)
        RETURN : float trong (0.0, 1.0]
        """
        R = 6371
        dlat = radians(end_lat - start_lat)
        dlng = radians(end_lng - start_lng)
        a = (sin(dlat / 2) ** 2
             + cos(radians(start_lat))
             * cos(radians(end_lat))
             * sin(dlng / 2) ** 2)
        dist_km = R * 2 * atan2(sqrt(a), sqrt(1 - a))
        return round(1 / (1 + dist_km), 4)


    def _score_semantic(self, list_ids: list, semantic_query: str) -> dict:
        """
        Tính điểm khớp ngữ nghĩa bằng model từ ChromaDB.
        INPUT  : list_ids (list của id nhà hàng), semantic_query (str) từ Parsing
        RETURN : dict {id: score} với score trong [0.0, 1.0]
        """
        if not semantic_query or not list_ids:
            return {str(rid): 0.0 for rid in list_ids}
        
        # Gọi hàm semantic_similarity từ database.py cung cấp
        return self.db.semantic_similarity(semantic_query, [str(rid) for rid in list_ids])
    def _compute_total_score(self,
                              row: dict,
                              budget_per_meal: float,
                              semantic_score: float,
                              start_lat: float,
                              start_lng: float) -> float:
        """
        Tính tổng điểm weighted cho 1 nhà hàng tính từ một vị trí bắt đầu.
        INPUT  : row (dict), budget_per_meal, semantic_score, start_lat, start_lng
        RETURN : float — tổng điểm trong [0.0, 1.0]
        """
        total = (
            self.weights['star']     * self._score_star(row.get('star', 0)) +
            self.weights['price']    * self._score_price(row.get('avg_price', 0), budget_per_meal) +
            self.weights['distance'] * self._score_distance(start_lat, start_lng, row.get('lat', 0), row.get('lng', 0)) +
            self.weights['semantic'] * semantic_score
        )
        return round(total, 4)

    # ─── PUBLIC: hàm chính giao tiếp với các module khác ────────────────

    def run_scoring_pipeline(self,
                              filtered_data: dict,
                              parsed_json: dict) -> pd.DataFrame:
        """
        Hàm CHÍNH của Module Algorithm.
        Chạy toàn bộ pipeline tính điểm và áp dụng Tối ưu toàn cục (Global Optimization)
        để tìm ra lịch trình có tính liên kết địa lý tốt nhất (Sáng -> Trưa -> Tối).

        INPUT:
            filtered_data (dict[str, DataFrame]) — output từ Module Filter
            parsed_json (dict) — output từ Module Parsing

        RETURN:
            pd.DataFrame chứa chuỗi lịch trình tối ưu nhất kèm điểm đánh giá.
        """
        budget       = parsed_json.get('budget') or 0
        num_meals    = parsed_json.get('num_meals') or 1
        meals_detail = parsed_json.get('meals_detail', [])

        budget_per_meal = budget / num_meals if num_meals > 0 else 0

        semantic_map = {
            m['meal']: m.get('semantic_query') or ''
            for m in meals_detail
        }

        meal_candidates = []
        semantic_scores_all = {}

        for meal_tag, df in filtered_data.items():
            if df.empty:
                continue

            semantic_query = semantic_map.get(meal_tag, '')

            df = df.copy()
            list_ids = df['id'].tolist() if 'id' in df.columns else []
            semantic_scores_dict = self._score_semantic(list_ids, semantic_query)
            semantic_scores_all[meal_tag] = semantic_scores_dict

            # Bước 1: Tính điểm sơ bộ dựa trên khoảng cách từ user để lọc Top 15 ứng viên
            df['score'] = df.apply(
                lambda row: self._compute_total_score(
                    row.to_dict(),
                    budget_per_meal,
                    semantic_scores_dict.get(str(row.get('id')), 0.0),
                    self.user_lat, self.user_lng
                ),
                axis=1
            )

            # Lấy top 15 quán ăn tốt nhất cho bữa này
            top_df = df.sort_values('score', ascending=False).head(15).copy()
            top_df['meal'] = meal_tag
            meal_candidates.append(top_df.to_dict('records'))

        if not meal_candidates:
            return pd.DataFrame()

        # Bước 2: Tối ưu toàn cục (Global Optimization) qua các tổ hợp hành trình
        best_itinerary = []
        best_avg_score = -1

        for combination in itertools.product(*meal_candidates):
            combo_ids = [str(rest.get('id')) for rest in combination]
            if len(set(combo_ids)) != len(combo_ids):
                continue
            current_lat, current_lng = self.user_lat, self.user_lng
            combination_scores = []
            itinerary_records = []

            for rest in combination:
                meal_tag = rest['meal']
                semantic_score = semantic_scores_all[meal_tag].get(str(rest.get('id')), 0.0)
                
                # Tính điểm dựa trên quãng đường thực tế từ quán trước đó
                score = self._compute_total_score(
                    rest,
                    budget_per_meal,
                    semantic_score,
                    current_lat,
                    current_lng
                )
                combination_scores.append(score)
                
                # Cập nhật tọa độ cho bữa ăn tiếp theo
                current_lat, current_lng = rest.get('lat', 0), rest.get('lng', 0)
                
                rest_copy = rest.copy()
                rest_copy['score'] = score
                itinerary_records.append(rest_copy)

            # Điểm của lịch trình là trung bình điểm các chặng
            avg_score = sum(combination_scores) / len(combination_scores)
            
            if avg_score > best_avg_score:
                best_avg_score = avg_score
                best_itinerary = itinerary_records

        if not best_itinerary:
            return pd.DataFrame()

        final_itinerary = pd.DataFrame(best_itinerary)
        final_itinerary['itinerary_avg_score'] = round(best_avg_score, 4)

        return final_itinerary
