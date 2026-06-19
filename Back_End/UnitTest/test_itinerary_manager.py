from unittest.mock import MagicMock

from Back_End.Core.itinerary_manager import ItineraryManager


def test_reorder_updates_only_order_not_meal():
    manager = ItineraryManager()
    mock_db = MagicMock()
    mock_batch = MagicMock()
    mock_collection = MagicMock()
    mock_doc_ref = MagicMock()

    mock_db.batch.return_value = mock_batch
    mock_collection.document.return_value = mock_doc_ref
    manager._get_db = MagicMock(return_value=mock_db)
    manager._get_itinerary_collection = MagicMock(return_value=mock_collection)

    success = manager._reorder_itinerary_sync(
        "user-1",
        [
            {"id": "dinner", "meal": "Sáng"},
            {"id": "lunch", "meal": "Tối"},
        ],
    )

    assert success is True
    assert mock_collection.document.call_args_list[0].args == ("dinner",)
    assert mock_collection.document.call_args_list[1].args == ("lunch",)
    assert mock_batch.update.call_args_list[0].args == (mock_doc_ref, {"order": 0})
    assert mock_batch.update.call_args_list[1].args == (mock_doc_ref, {"order": 1})
    mock_batch.commit.assert_called_once()
