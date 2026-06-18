import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os

os.environ.setdefault("GEMINI_API", "test-gemini-key")
os.environ.setdefault("GROQ_API_KEY_MAIN", "test-groq-key")

from Back_End.Core.parsing import LLMParser

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_json_response_success():
    parser = LLMParser()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "budget": 500000,
        "num_meals": 1,
        "location_pref": "Quận 1",
        "shu": None,
        "meals_detail": [{"meal": "trưa", "type": ["Quán Việt"], "semantic_query": "máy lạnh", "dish": "phở"}]
    })
    
    with patch.object(parser.client.aio.models, 'generate_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        result = await parser.JSON_response("Tìm quán phở máy lạnh ở Quận 1 tầm 500k")
        
        assert result["budget"] == 500000
        assert result["location_pref"] == "Quận 1"
        assert len(result["meals_detail"]) == 1
        assert result["meals_detail"][0]["meal"] == "trưa"

@pytest.mark.anyio
async def test_phrase_health_description_success():
    parser = LLMParser()
    mock_response = MagicMock()
    mock_response.text = '["Spicy", "DeepFried_Oily"]'
    
    with patch.object(parser.client.aio.models, 'generate_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        result = await parser.phrase_health_description("Tôi bị đau dạ dày")
        
        assert "Spicy" in result
        assert "DeepFried_Oily" in result
        assert len(result) == 2

@pytest.mark.anyio
async def test_phrase_health_description_invalid_tags():
    parser = LLMParser()
    mock_response = MagicMock()
    mock_response.text = '["Spicy", "Invalid_Tag"]'
    
    with patch.object(parser.client.aio.models, 'generate_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        result = await parser.phrase_health_description("Tôi bị đau dạ dày")
        
        assert "Spicy" in result
        assert "Invalid_Tag" not in result
        assert len(result) == 1

@pytest.mark.anyio
async def test_phrase_health_description_error():
    parser = LLMParser()
    
    with patch.object(parser.client.aio.models, 'generate_content', side_effect=Exception("API Error")), \
         patch.object(parser, '_call_groq_json', new_callable=AsyncMock) as mock_fallback:
        mock_fallback.return_value = []
        result = await parser.phrase_health_description("Error case")
        assert result == []
