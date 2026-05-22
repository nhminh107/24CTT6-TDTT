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

    def _score_star(self, star: float, buff_weight: float = 0.0) -> float:
        """
        Normalize điểm sao về [0, 1]
        INPUT  : star (float) — VD: 4.8
        RETURN : float trong [0.0, 1.0]
        """
        base = (star - 1) / 4
        return round(max(0.0, min(1.0, base + buff_weight)), 4)

    def _score_price(self, avg_price: int, budget_per_meal: float, buff_weight: float = 0.0) -> float:
        """
        Tính điểm giá so với ngân sách mỗi bữa.
        INPUT  : avg_price (int), budget_per_meal (float)
        RETURN : float trong [0.0, 1.0]
        """
        if budget_per_meal <= 0:
            return 0.0
        ratio = avg_price / budget_per_meal
        if ratio <= 0.5:
            base = 1.0
        elif ratio <= 0.8:
            base = 0.8
        elif ratio <= 1.0:
            base = 0.5
        else:
            base = 0.0
        return round(max(0.0, min(1.0, base + buff_weight)), 4)

    def _score_distance(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float, buff_weight: float = 0.0) -> float:
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
        base = 1 / (1 + dist_km)
        return round(max(0.0, min(1.0, base + buff_weight)), 4)


    def _score_semantic(self, list_ids: list, semantic_query: str, buff_weight: float = 0.0) -> dict:
        """
        Tính điểm khớp ngữ nghĩa bằng model từ ChromaDB.
        INPUT  : list_ids (list của id nhà hàng), semantic_query (str) từ Parsing
        RETURN : dict {id: score} với score trong [0.0, 1.0]
        """
        if not semantic_query or not list_ids:
            return {str(rid): max(0.0, min(1.0, 0.0 + buff_weight)) for rid in list_ids}
        
        # Gọi hàm semantic_similarity từ database.py cung cấp
        scores = self.db.semantic_similarity(semantic_query, [str(rid) for rid in list_ids])
        return {
            str(rid): max(0.0, min(1.0, score + buff_weight))
            for rid, score in scores.items()
        }

    def _score_semantic_from_texts(self, semantic_query: str, texts: list, ids: list, buff_weight: float = 0.0) -> dict:
        if not semantic_query or not texts or not ids:
            return {}
        query_embedding = self.db.ef([semantic_query])[0]
        text_embeddings = self.db.ef(texts)
        scores = {}
        for rid, emb in zip(ids, text_embeddings):
            similarity = self.db._cosine_similarity(query_embedding, emb)
            base = (similarity + 1.0) / 2.0
            scores[str(rid)] = max(0.0, min(1.0, base + buff_weight))
        return scores

    def _score_semantic_single(self, semantic_score: float, buff_weight: float = 0.0) -> float:
        return round(max(0.0, min(1.0, semantic_score + buff_weight)), 4)

    def _extract_semantic_terms(self, semantic_query: str) -> list:
        if not semantic_query:
            return []
        return [term.strip().lower() for term in semantic_query.split(',') if term.strip()]
    def _compute_total_score(self,
                              row: dict,
                              budget_per_meal: float,
                              semantic_score: float,
                              start_lat: float,
                              start_lng: float,
                              buff_weights: dict,
                              diet_mode) -> float:
        """
        Tính tổng điểm weighted cho 1 nhà hàng tính từ một vị trí bắt đầu.
        INPUT  : row (dict), budget_per_meal, semantic_score, start_lat, start_lng
        RETURN : float — tổng điểm trong [0.0, 1.0]
        """
        base_score = (
            self.weights['star']
            * self._score_star(row.get('star', 0), buff_weights.get("buff_star_weight", 0.0))
            + self.weights['price']
            * self._score_price(
                row.get('avg_price', 0),
                budget_per_meal,
                buff_weights.get("buff_price_weight", 0.0)
            )
            + self.weights['distance']
            * self._score_distance(
                start_lat,
                start_lng,
                row.get('lat', 0),
                row.get('lng', 0),
                buff_weights.get("buff_distance_weight", 0.0)
            )
            + self.weights['semantic']
            * self._score_semantic_single(
                semantic_score,
                buff_weights.get("buff_semantic_weight", 0.0)
            )
        )
        
        raw_penalty = row.get('penalty_score', 0)
        max_penalty_limit = 60 # Điểm phạt tối đa (12 tag * 5 điểm)
        normalized_penalty = min(raw_penalty / max_penalty_limit, 1.0)
        
        
        if diet_mode == "strict" or diet_mode is None:
            penalty_weight = self.weights['health']
        else:
            penalty_weight = 0.00  # Ăn xả láng -> Trọng số phạt bằng 0 (không trừ điểm)
        
        # 4. Tính điểm tổng kết cuối cùng
        total = base_score - (normalized_penalty * penalty_weight)
        
        # Chuẩn hóa lại tránh điểm cuối cùng bị âm
        total = max(total, 0.0) 
        
        return round(total, 4)

    # ─── PUBLIC: hàm chính giao tiếp với các module khác ────────────────

    def run_scoring_pipeline(self,
                         filtered_data: dict,
                         parsed_json: dict,
                         buff_weights: dict | None = None,
                         diet_mode: str | None = None) -> pd.DataFrame:
        
        """
        Hàm CHÍNH của Module Algorithm.
        Chạy toàn bộ pipeline tính điểm và trả về top 3 quán ăn cho mỗi bữa.

        INPUT:
            filtered_data (dict[str, DataFrame]) — output từ Module Filter
            parsed_json (dict) — output từ Module Parsing

        RETURN:
            pd.DataFrame chứa top 3 quán ăn cho mỗi bữa kèm điểm đánh giá.
        """
        budget       = parsed_json.get('budget') or 0
        num_meals    = parsed_json.get('num_meals') or 1
        meals_detail = parsed_json.get('meals_detail', [])

        if buff_weights is None:
            buff_weights = {
                "buff_star_weight": 0.0,
                "buff_price_weight": 0.0,
                "buff_distance_weight": 0.0,
                "buff_semantic_weight": 0.0
            }

        budget_per_meal = budget / num_meals if num_meals > 0 else 0

        semantic_map = {
            m['meal']: m.get('semantic_query') or ''
            for m in meals_detail
        }

        top_results = []

        for meal_tag, df in filtered_data.items():
            if df.empty:
                continue

            semantic_query = semantic_map.get(meal_tag, '')

            df = df.copy()
            list_ids = df['id'].tolist() if 'id' in df.columns else []
            semantic_scores_dict = self._score_semantic(
                list_ids,
                semantic_query,
                0.0
            )

            if semantic_query and 'semantic_text' in df.columns:
                missing_ids = [str(rid) for rid in list_ids if str(rid) not in semantic_scores_dict]
                all_zero = not any(score > 0 for score in semantic_scores_dict.values())
                if missing_ids or all_zero:
                    texts = df['semantic_text'].fillna('').tolist()
                    fallback_scores = self._score_semantic_from_texts(
                        semantic_query,
                        texts,
                        df['id'].astype(str).tolist(),
                        0.0
                    )
                    if all_zero:
                        semantic_scores_dict = fallback_scores
                    else:
                        for rid in missing_ids:
                            semantic_scores_dict[rid] = fallback_scores.get(rid, 0.0)

            df['semantic_score'] = df['id'].astype(str).apply(
                lambda rid: semantic_scores_dict.get(str(rid), 0.0)
            )

            # Tính điểm sơ bộ dựa trên khoảng cách từ user để lọc Top 3 ứng viên
            df['score'] = df.apply(
                lambda row: self._compute_total_score(
                    row.to_dict(),
                    budget_per_meal,
                    row.get('semantic_score', 0.0),
                    self.user_lat, self.user_lng,
                    buff_weights,
                    diet_mode=diet_mode
                ),
                axis=1
            )

            # Lấy top 3 quán ăn tốt nhất cho bữa này
            if semantic_query:
                terms = self._extract_semantic_terms(semantic_query)
                if terms and 'semantic_text' in df.columns:
                    df['keyword_match'] = df['semantic_text'].fillna('').str.lower().apply(
                        lambda text: any(term in text for term in terms)
                    )
                    df_for_rank = df[df['keyword_match']].copy() if df['keyword_match'].any() else df
                else:
                    df_for_rank = df

                top_df = df_for_rank.sort_values(['semantic_score', 'score'], ascending=False).head(3).copy()
                if 'keyword_match' in top_df.columns:
                    top_df.drop(columns=['keyword_match'], inplace=True)
            else:
                top_df = df.sort_values('score', ascending=False).head(3).copy()
            top_df['meal'] = meal_tag
            if not top_df.empty:
                top_results.append(top_df)

        if not top_results:
            return pd.DataFrame()

        return pd.concat(top_results, ignore_index=True)
