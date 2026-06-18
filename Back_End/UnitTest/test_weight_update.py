import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from Back_End.Core.weight_update import Weight_Update
from datetime import datetime
import pytz

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def weight_updater():
    return Weight_Update(10.762622, 106.660172) # HCM City coords

@pytest.mark.anyio
async def test_get_weather_success(weight_updater):
    mock_res = MagicMock()
    mock_res.json.return_value = {"weather": [{"main": "Rain"}]}
    mock_res.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_res
        weather = await weight_updater._get_weather()
        assert weather == "Rain"

def test_get_time_slot(weight_updater):
    morning = MagicMock(hour=8)
    assert weight_updater._get_time_slot(morning) == "morning"
    
    lunch = MagicMock(hour=12)
    assert weight_updater._get_time_slot(lunch) == "lunch"
    
    evening = MagicMock(hour=18)
    assert weight_updater._get_time_slot(evening) == "evening"
    
    night = MagicMock(hour=23)
    assert weight_updater._get_time_slot(night) == "night"

def test_apply_weather_rules(weight_updater):
    weight_updater._apply_weather_rules("Rain")
    assert weight_updater.buff_distance_weight > 0
    assert weight_updater.buff_price_weight < 0

def test_apply_time_rules(weight_updater):
    weight_updater._apply_time_rules("evening")
    assert weight_updater.buff_star_weight > 0
    assert weight_updater.buff_semantic_weight > 0

def test_normalize_buffs(weight_updater):
    weight_updater.buff_star_weight = 0.5
    weight_updater.buff_price_weight = 0.5
    weight_updater.buff_distance_weight = 0.5
    weight_updater.buff_semantic_weight = 0.5
    
    weight_updater._normalize_buffs()
    # Total sum should be 0 after normalization
    total = (weight_updater.buff_star_weight + weight_updater.buff_price_weight + 
             weight_updater.buff_distance_weight + weight_updater.buff_semantic_weight)
    assert abs(total) < 1e-6

@pytest.mark.anyio
async def test_build_buff_weights(weight_updater):
    with patch.object(weight_updater, '_get_weather', new_callable=AsyncMock) as mock_weather, \
         patch.object(weight_updater, '_get_local_time') as mock_time:
        
        mock_weather.return_value = "Clear"
        mock_time.return_value = datetime(2023, 10, 21, 18, 0, tzinfo=pytz.UTC) # Saturday
        
        weights = await weight_updater.build_buff_weights()
        assert "buff_star_weight" in weights
        assert "buff_price_weight" in weights
        assert "buff_distance_weight" in weights
        assert "buff_semantic_weight" in weights
