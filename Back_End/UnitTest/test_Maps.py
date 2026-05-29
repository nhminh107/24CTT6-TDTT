import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from Back_End.Core.Maps import suggest_locations, get_place_detail, MOCK_AUTOCOMPLETE, MOCK_DETAILS

@pytest.mark.asyncio
async def test_suggest_locations_empty():
    res = await suggest_locations("")
    assert res == []

@pytest.mark.asyncio
async def test_suggest_locations_mock():
    with patch('Back_End.Core.Maps.CONFIG.GOONG_API_KEY', None):
        res = await suggest_locations("Cho Ben Thanh")
        assert len(res) == 1
        assert res[0][1] == "mock_bt"

@pytest.mark.asyncio
@patch('Back_End.Core.Maps.CONFIG.GOONG_API_KEY', 'fake_key')
@patch('Back_End.Core.Maps.httpx.AsyncClient.get', new_callable=AsyncMock)
async def test_suggest_locations_api_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"predictions": [{"description": "Test Desc", "place_id": "test_id"}]}
    mock_get.return_value = mock_response

    res = await suggest_locations("Test")
    assert len(res) == 1
    assert res[0] == ("Test Desc", "test_id")

@pytest.mark.asyncio
@patch('Back_End.Core.Maps.CONFIG.GOONG_API_KEY', 'fake_key')
@patch('Back_End.Core.Maps.httpx.AsyncClient.get', new_callable=AsyncMock)
async def test_suggest_locations_api_failure(mock_get):
    mock_get.side_effect = Exception("API error")
    res = await suggest_locations("Cho Ben Thanh")
    # Should fallback to mock
    assert len(res) == 1
    assert res[0][1] == "mock_bt"

@pytest.mark.asyncio
async def test_get_place_detail_mock():
    res = await get_place_detail("mock_bt")
    assert res['status'] == 'success'
    assert res['data']['lat'] == MOCK_DETAILS['mock_bt']['lat']

@pytest.mark.asyncio
@patch('Back_End.Core.Maps.CONFIG.GOONG_API_KEY', 'fake_key')
@patch('Back_End.Core.Maps.httpx.AsyncClient.get', new_callable=AsyncMock)
async def test_get_place_detail_api_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "geometry": {"location": {"lat": 1.23, "lng": 4.56}},
            "formatted_address": "Test Addr"
        }
    }
    mock_get.return_value = mock_response

    res = await get_place_detail("real_id")
    assert res['status'] == 'success'
    assert res['data']['lat'] == 1.23
    assert res['data']['formatted_address'] == "Test Addr"

@pytest.mark.asyncio
@patch('Back_End.Core.Maps.CONFIG.GOONG_API_KEY', 'fake_key')
@patch('Back_End.Core.Maps.httpx.AsyncClient.get', new_callable=AsyncMock)
async def test_get_place_detail_api_exception(mock_get):
    mock_get.side_effect = Exception("API error")
    res = await get_place_detail("real_id")
    assert res['status'] == 'error'
    assert 'API error' in res['message']

@pytest.mark.asyncio
@patch('Back_End.Core.Maps.CONFIG.GOONG_API_KEY', 'fake_key')
@patch('Back_End.Core.Maps.httpx.AsyncClient.get', new_callable=AsyncMock)
async def test_get_place_detail_api_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    res = await get_place_detail("real_id")
    assert res['status'] == 'error'
    assert res['message'] == "Khong the lay thong tin chi tiet dia diem."
