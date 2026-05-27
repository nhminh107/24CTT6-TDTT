import pytest
from unittest.mock import MagicMock, patch
from Back_End.Core.semantic_cache import SemanticCacheManager
import json

@pytest.fixture
def mock_chroma():
    with patch('chromadb.PersistentClient') as mock_client, \
         patch('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction') as mock_ef:
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        yield mock_client, mock_collection, mock_ef

def test_get_location_zone(mock_chroma):
    mock_client, mock_collection, mock_ef = mock_chroma
    manager = SemanticCacheManager()
    zone = manager._get_location_zone(10.1234, 106.5678)
    assert zone == "zone_10.12_106.57"

def test_check_cache_hit(mock_chroma):
    mock_client, mock_collection, mock_ef = mock_chroma
    manager = SemanticCacheManager()
    
    mock_data = {"result": "cached_value"}
    mock_collection.get.return_value = {
        'documents': [json.dumps(mock_data)],
        'ids': ['some_id']
    }
    
    result = manager.check_cache("test prompt", 10.12, 106.57, 100000, "health_key")
    assert result == mock_data
    mock_collection.get.assert_called_once()

def test_check_cache_miss(mock_chroma):
    mock_client, mock_collection, mock_ef = mock_chroma
    manager = SemanticCacheManager()
    
    mock_collection.get.return_value = {'documents': [], 'ids': []}
    
    result = manager.check_cache("test prompt", 10.12, 106.57, 100000, "health_key")
    assert result is None

def test_save_cache(mock_chroma):
    mock_client, mock_collection, mock_ef = mock_chroma
    manager = SemanticCacheManager()
    
    manager.save_cache("test prompt", 10.12, 106.57, 100000, "health_key", {"data": 123})
    mock_collection.upsert.assert_called_once()
