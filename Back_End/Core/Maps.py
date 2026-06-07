from typing import Any, Dict, List, Tuple
import requests
import httpx
from dotenv import load_dotenv
import os

load_dotenv() 

class CONFIG:
    GOONG_API_KEY = os.getenv("GOONG_API_KEY")
    GOONG_AUTOCOMPLETE_URL = "https://rsapi.goong.io/Place/AutoComplete"
    GOONG_DETAIL_URL = "https://rsapi.goong.io/Place/Detail"

"""Phần ở MOCK là gợi ý sẵn nếu người dùng không tìm thấy"""

MOCK_AUTOCOMPLETE = [
    {
        "description": "San bay Tan Son Nhat, Tan Binh, Ho Chi Minh",
        "place_id": "mock_tsn",
    },
    {"description": "Cho Ben Thanh, Quan 1, Ho Chi Minh", "place_id": "mock_bt"},
    {"description": "Cau Rong, Hai Chau, Da Nang", "place_id": "mock_cr"},
]

MOCK_DETAILS = {
    "mock_tsn": {
        "lat": 10.816,
        "lng": 106.667,
        "formatted_address": "San bay Tan Son Nhat, HCM",
    },
    "mock_bt": {
        "lat": 10.772,
        "lng": 106.698,
        "formatted_address": "Cho Ben Thanh, Le Loi, Q1",
    },
    "mock_cr": {
        "lat": 16.061,
        "lng": 108.227,
        "formatted_address": "Cau Rong, Nguyen Van Linh, Da Nang",
    },
}




async def suggest_locations(search_text: str) -> List[Tuple[str, str]]:
    if not search_text:
        return []

    if not CONFIG.GOONG_API_KEY:
        return [
            (item["description"], item["place_id"])
            for item in MOCK_AUTOCOMPLETE
            if search_text.lower() in item["description"].lower()
        ]

    url = (
        f"{CONFIG.GOONG_AUTOCOMPLETE_URL}?api_key={CONFIG.GOONG_API_KEY}"
        f"&input={search_text}&limit=5"
    )
    try:
        async with httpx.AsyncClient() as client: 
            response =  await client.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            if "predictions" in data:
                return [
                    (item["description"], item["place_id"])
                    for item in data["predictions"]
                ]
    except Exception:
        pass

    return [
        (item["description"], item["place_id"])
        for item in MOCK_AUTOCOMPLETE
        if search_text.lower() in item["description"].lower()
    ]

async def get_place_detail(place_id: str) -> Dict[str, Any]:
    if place_id in MOCK_DETAILS:
        return {"status": "success", "data": MOCK_DETAILS[place_id]}

    url = (
        f"{CONFIG.GOONG_DETAIL_URL}?api_key={CONFIG.GOONG_API_KEY}"
        f"&place_id={place_id}"
    )
    try:
        async with httpx.AsyncClient() as client: 
            response =  await client.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json().get("result", {})
            location = data.get("geometry", {}).get("location", {})
            if location:
                return {
                    "status": "success",
                    "data": {
                        "lat": location.get("lat"),
                        "lng": location.get("lng"),
                        "formatted_address": data.get("formatted_address", ""),
                    },
                }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    return {
        "status": "error",
        "message": "Khong the lay thong tin chi tiet dia diem.",
    }

