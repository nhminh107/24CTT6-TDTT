import pytest
from unittest.mock import MagicMock, patch
from Back_End.Core.share_manager import ShareManager

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def mock_db():
    with patch('Back_End.Core.share_manager.get_db') as mock_get_db:
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance
        yield mock_db_instance

@pytest.fixture
def share_manager():
    return ShareManager()

def test_generate_share_id(share_manager):
    share_id = share_manager.generate_share_id()
    assert isinstance(share_id, str)
    assert len(share_id) == 6
    assert share_id.isalnum()

@pytest.mark.anyio
async def test_create_share_link(share_manager, mock_db):
    # Setup mock
    mock_doc = MagicMock()
    mock_doc.get.return_value.exists = False
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc
    
    mock_db.collection.return_value = mock_collection

    # Data test
    user_id = "test_user_123"
    itinerary_data = [{"meal": "Sáng", "name": "Phở Hòa"}]

    # Run
    share_id = await share_manager.create_share_link(user_id, itinerary_data)

    # Asserts
    assert share_id is not None
    assert len(share_id) == 6
    mock_db.collection.assert_called_with("shared_itineraries")
    mock_collection.document.assert_called_with(share_id)
    mock_doc.set.assert_called_once()

@pytest.mark.anyio
async def test_get_shared_itinerary_exists(share_manager, mock_db):
    # Setup mock for existing doc
    expected_data = {"user_id": "test", "itinerary": []}
    mock_doc = MagicMock()
    mock_doc.get.return_value.exists = True
    mock_doc.get.return_value.to_dict.return_value = expected_data
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc
    mock_db.collection.return_value = mock_collection

    # Run
    result = await share_manager.get_shared_itinerary("VALID_ID")

    # Asserts
    assert result == expected_data
    mock_collection.document.assert_called_with("VALID_ID")

@pytest.mark.anyio
async def test_get_shared_itinerary_not_exists(share_manager, mock_db):
    # Setup mock for non-existing doc
    mock_doc = MagicMock()
    mock_doc.get.return_value.exists = False
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc
    mock_db.collection.return_value = mock_collection

    # Run
    result = await share_manager.get_shared_itinerary("INVALID_ID")

    # Asserts
    assert result is None
