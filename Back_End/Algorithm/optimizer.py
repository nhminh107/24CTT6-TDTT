import itertools
import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

from Back_End.Algorithm.models import Restaurant, RouteCandidate
from Back_End.Database.database import ChromaDBManager


def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    if max_val <= min_val:
        return 0.0
    if value <= min_val:
        return 0.0
    if value >= max_val:
        return 1.0
    return (value - min_val) / (max_val - min_val)


def _distance_score(total_km: float) -> float:
    if total_km < 1.0:
        return max(0.0, total_km / 1.0) * 0.4
    if 4.0 <= total_km <= 7.0:
        return 1.0
    if 1.0 <= total_km < 4.0:
        return 0.4 + 0.6 * normalize_score(total_km, 1.0, 4.0)
    if 7.0 < total_km <= 15.0:
        return 1.0 - 0.6 * normalize_score(total_km, 7.0, 15.0)
    return 0.0


def _diversity_score(types: Sequence[Sequence[str]]) -> float:
    unique_types = set()
    for tlist in types:
        for tval in tlist:
            if isinstance(tval, str):
                unique_types.add(tval.strip())
    count = len(unique_types)
    if count >= 3:
        return 1.0
    if count == 2:
        return 0.6
    if count == 1:
        return 0.2
    return 0.0


def _budget_score(total_price: float, user_budget: float) -> float:
    if user_budget <= 0:
        return 0.0
    ratio = total_price / user_budget
    if 0.85 <= ratio <= 0.95:
        return 1.0
    if 0.6 <= ratio < 0.85:
        return 0.4 + 0.6 * normalize_score(ratio, 0.6, 0.85)
    if 0.95 < ratio <= 1.1:
        return 1.0 - 0.6 * normalize_score(ratio, 0.95, 1.1)
    if ratio < 0.6:
        return 0.2 * normalize_score(ratio, 0.0, 0.6)
    return max(0.0, 1.0 - normalize_score(ratio, 1.1, 1.6)) * 0.3


def _rating_score(stars: Iterable[float]) -> float:
    values = [val for val in stars if val is not None]
    if not values:
        return 0.0
    avg_star = sum(values) / len(values)
    return normalize_score(avg_star, 1.0, 5.0)


def calculate_route_score(
    route: Sequence[Restaurant],
    user_budget: float,
    semantic_scores: Optional[Dict[str, float]] = None,
) -> Tuple[float, float, float]:
    if len(route) < 2:
        return 0.0, 0.0, 0.0

    total_distance = 0.0
    for first, second in zip(route[:-1], route[1:]):
        total_distance += calculate_haversine(first.lat, first.lng, second.lat, second.lng)

    total_price = sum(rest.avg_price for rest in route)
    distance_score = _distance_score(total_distance)
    diversity_score = _diversity_score([rest.types for rest in route])
    budget_score = _budget_score(total_price, user_budget)
    rating_score = _rating_score([rest.star for rest in route])

    semantic_score = 0.0
    if semantic_scores:
        values = [semantic_scores.get(rest.id, 0.0) for rest in route]
        semantic_score = sum(values) / len(values)

    w1, w2, w3, w4, w5, w6 = 0.25, 0.2, 0.2, 0.2, 0.0, 0.15
    total_score = (
        w1 * distance_score
        + w2 * diversity_score
        + w3 * budget_score
        + w4 * rating_score
        + w5 * semantic_score
        + w6 * 0.0
    )
    return total_score, total_price, total_distance


def _df_to_restaurants(df: pd.DataFrame) -> List[Restaurant]:
    if df is None or df.empty:
        return []
    return [Restaurant.from_dict(row) for row in df.to_dict(orient="records")]


def _coerce_dataframe(data: object) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame()


def _coerce_candidate_pool(
    candidate_pool: Union[Dict[str, pd.DataFrame], List[Dict[str, pd.DataFrame]]]
) -> Dict[str, pd.DataFrame]:
    if isinstance(candidate_pool, dict):
        return {key: _coerce_dataframe(value) for key, value in candidate_pool.items()}
    if isinstance(candidate_pool, list):
        merged: Dict[str, pd.DataFrame] = {}
        for item in candidate_pool:
            if isinstance(item, dict):
                for key, value in item.items():
                    merged[key] = _coerce_dataframe(value)
        return merged
    return {}


def generate_candidates(
    candidate_pool: Union[Dict[str, pd.DataFrame], List[Dict[str, pd.DataFrame]]],
    budget: int,
    top_n: int = 5,
    semantic_query: Optional[str] = None,
) -> List[Dict[str, object]]:
    pool = _coerce_candidate_pool(candidate_pool)
    meal_keys = [key for key in ["sáng", "trưa", "tối"] if key in pool]
    if len(meal_keys) < 2:
        return []

    meal_restaurants = {meal: _df_to_restaurants(pool.get(meal)) for meal in meal_keys}
    if any(not meal_restaurants[meal] for meal in meal_keys):
        return []

    candidates = []
    restaurant_ids = [rest.id for rests in meal_restaurants.values() for rest in rests]
    semantic_scores = None
    if semantic_query:
        db_manager = ChromaDBManager()
        semantic_scores = db_manager.semantic_similarity(semantic_query, restaurant_ids)

    route_iter = itertools.product(*(meal_restaurants[meal] for meal in meal_keys))
    for route_tuple in route_iter:
        if len({rest.id for rest in route_tuple}) < len(route_tuple):
            continue

        score, total_price, total_distance = calculate_route_score(
            route_tuple, budget, semantic_scores=semantic_scores
        )
        if total_price > budget * 1.2:
            continue
        candidates.append(
            RouteCandidate(
                meals=meal_keys,
                restaurants=list(route_tuple),
                score=score,
                total_price=total_price,
                total_distance_km=total_distance,
            )
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return [candidate.to_dict() for candidate in candidates[:top_n]]
