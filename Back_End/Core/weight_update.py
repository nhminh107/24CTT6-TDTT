import httpx
from dotenv import load_dotenv
import os
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
load_dotenv()
api_key = os.getenv("OPEN_WEATHER_API")

class Weight_Update:
    def __init__(self, user_lat, user_lng):
        self.user_lat = user_lat
        self.user_lng = user_lng
        
        self.buff_star_weight = 0
        self.buff_price_weight = 0 
        self.buff_distance_weight = 0 
        self.buff_semantic_weight = 0 

    async def _get_weather(self):
        URL = f"https://api.openweathermap.org/data/2.5/weather?lat={self.user_lat}&lon={self.user_lng}&appid={api_key}"
        if not api_key:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(URL, timeout=5.0)
            response.raise_for_status()
            res = response.json()
            return res.get("weather", [{}])[0].get("main")
        except Exception:
            return None

    def _get_local_time(self):
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=self.user_lng, lat=self.user_lat) or "UTC"
        tz = pytz.timezone(tz_name)
        return datetime.now(tz)

    def _get_time_slot(self, local_time):
        hour = local_time.hour
        if 5 <= hour < 10:
            return "morning"
        if 10 <= hour < 15:
            return "lunch"
        if 15 <= hour < 21:
            return "evening"
        return "night"

    def _apply_weather_rules(self, weather):
        if weather in {"Rain", "Drizzle", "Thunderstorm"}:
            self.buff_distance_weight += 0.06
            self.buff_price_weight -= 0.03
            self.buff_semantic_weight -= 0.02
            self.buff_star_weight -= 0.01
        elif weather == "Clear":
            self.buff_semantic_weight += 0.04
            self.buff_star_weight += 0.02
            self.buff_distance_weight -= 0.04
            self.buff_price_weight -= 0.02
        elif weather == "Clouds":
            self.buff_semantic_weight += 0.02
            self.buff_star_weight += 0.01
            self.buff_distance_weight -= 0.02
            self.buff_price_weight -= 0.01
        elif weather == "Snow":
            self.buff_distance_weight += 0.08
            self.buff_price_weight -= 0.04
            self.buff_semantic_weight -= 0.02
            self.buff_star_weight -= 0.02

    def _apply_time_rules(self, time_slot):
        if time_slot == "morning":
            self.buff_distance_weight += 0.04
            self.buff_price_weight += 0.02
            self.buff_semantic_weight -= 0.03
            self.buff_star_weight -= 0.03
        elif time_slot == "lunch":
            self.buff_price_weight += 0.03
            self.buff_distance_weight -= 0.01
            self.buff_semantic_weight -= 0.01
            self.buff_star_weight -= 0.01
        elif time_slot == "evening":
            self.buff_star_weight += 0.04
            self.buff_semantic_weight += 0.03
            self.buff_distance_weight -= 0.04
            self.buff_price_weight -= 0.03
        else:
            self.buff_distance_weight += 0.05
            self.buff_star_weight += 0.02
            self.buff_price_weight -= 0.04
            self.buff_semantic_weight -= 0.03

    def _apply_weekend_rules(self, local_time):
        if local_time.weekday() in {5, 6}:
            self.buff_star_weight += 0.03
            self.buff_semantic_weight += 0.02
            self.buff_distance_weight -= 0.03
            self.buff_price_weight -= 0.02

    def _normalize_buffs(self):
        total = (
            self.buff_star_weight
            + self.buff_price_weight
            + self.buff_distance_weight
            + self.buff_semantic_weight
        )
        if abs(total) < 1e-6:
            return
        adjust = total / 4
        self.buff_star_weight -= adjust
        self.buff_price_weight -= adjust
        self.buff_distance_weight -= adjust
        self.buff_semantic_weight -= adjust

    async def build_buff_weights(self):
        weather = await self._get_weather()
        local_time = self._get_local_time()
        time_slot = self._get_time_slot(local_time)

        self._apply_weather_rules(weather)
        self._apply_time_rules(time_slot)
        self._apply_weekend_rules(local_time)
        self._normalize_buffs()

        return {
            "buff_star_weight": self.buff_star_weight,
            "buff_price_weight": self.buff_price_weight,
            "buff_distance_weight": self.buff_distance_weight,
            "buff_semantic_weight": self.buff_semantic_weight
        }
    
