from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Restaurant:
    id: str
    name: str
    lat: float
    lng: float
    avg_price: float
    star: float
    types: List[str]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Restaurant":
        types = data.get("type")
        if isinstance(types, str):
            types = [types]
        if not isinstance(types, list):
            types = []

        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            lat=float(data.get("lat", 0.0) or 0.0),
            lng=float(data.get("lng", 0.0) or 0.0),
            avg_price=float(data.get("avg_price", 0.0) or 0.0),
            star=float(data.get("star", 0.0) or 0.0),
            types=types,
            raw=data,
        )


@dataclass(frozen=True)
class RouteCandidate:
    meals: List[str]
    restaurants: List[Restaurant]
    score: float
    total_price: float
    total_distance_km: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meals": self.meals,
            "score": self.score,
            "total_price": self.total_price,
            "total_distance_km": self.total_distance_km,
            "route": [restaurant.raw for restaurant in self.restaurants],
        }
