import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, AsyncMock
from Back_End.Core.final_result import FinalResultLLM

@pytest.fixture
def mock_genai():
    with patch('Back_End.Core.final_result._client') as mock_client:
        mock_response = MagicMock()
        mock_response.text = '{"selected": [{"meal": "Sáng", "id": "1"}, {"meal": "Trưa", "id": "3"}]}'
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        yield mock_client

@pytest.fixture
def llm(mock_genai):
    return FinalResultLLM()

def test_meal_order(llm):
    df = pd.DataFrame({'meal': ['Sáng', 'Trưa', 'Sáng']})
    order = llm._meal_order(df, None)
    assert order == ['Sáng', 'Trưa']
    
    parsed = {'meals_detail': [{'meal': 'Trưa'}, {'meal': 'Tối'}]}
    order_parsed = llm._meal_order(df, parsed)
    assert order_parsed == ['Trưa', 'Tối']

def test_candidates_payload(llm):
    df = pd.DataFrame({
        'id': [1, 2],
        'meal': ['Sáng', 'Tối'],
        'name': ['A', 'B'],
        'score': [0.9, 0.8]
    })
    payload = llm._candidates_payload(df, ['Sáng', 'Trưa', 'Tối'])
    assert 'Sáng' in payload
    assert 'Tối' in payload
    assert 'Trưa' not in payload  # Trưa is empty in df

def test_candidate_rows(llm):
    df = pd.DataFrame({
        'id': [1, 2],
        'meal': ['Sáng', 'Tối'],
        'score': [0.9, 0.8]
    })
    rows = llm._candidate_rows(df, ['Sáng', 'Trưa', 'Tối'])
    assert 'Sáng' in rows
    assert 'Tối' in rows
    assert 'Trưa' not in rows

@pytest.mark.asyncio
async def test_select_with_llm(llm):
    payload = {"Sáng": [{"id": 1}], "Trưa": [{"id": 3}]}
    res = await llm._select_with_llm(payload, "test")
    assert res == {"Sáng": "1", "Trưa": "3"}

@pytest.mark.asyncio
async def test_select_with_llm_exception(llm):
    # Error handling when API raises Exception
    llm.client.aio.models.generate_content.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        await llm._select_with_llm({}, "test")

def test_select_unique_combination(llm, capsys):
    candidate_map = {
        'Sáng': [{'id': 1, 'name': 'A'}, {'id': 2, 'name': 'B'}],
        'Trưa': [{'id': 1, 'name': 'A'}], # only 1 available, but it's taken
        'Tối': [] # empty
    }
    res = llm._select_unique_combination(['Sáng', 'Trưa', 'Tối'], candidate_map)
    # Sáng gets 1, Trưa has no unique available, Tối has none
    assert len(res) == 1
    assert res[0]['id'] == 1
    
    # Verify the warning print
    captured = capsys.readouterr()
    assert "No available unique restaurants found for meal 'Trưa'" in captured.out

@pytest.mark.asyncio
async def test_run_final_selection_empty(llm):
    df = pd.DataFrame()
    res = await llm.run_final_selection(df, "prompt")
    assert res.empty
    
    # Test when meal_order returns empty list
    with patch.object(llm, '_meal_order', return_value=[]):
        df_valid = pd.DataFrame({'meal': ['Sáng'], 'score': [0.9]})
        res2 = await llm.run_final_selection(df_valid, "prompt")
        assert res2.empty
        
    # Test when candidate generation fails
    with patch.object(llm, '_candidates_payload', return_value={}):
        res3 = await llm.run_final_selection(df_valid, "prompt")
        assert res3.empty

@pytest.mark.asyncio
async def test_run_final_selection_full(llm):
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'meal': ['Sáng', 'Sáng', 'Trưa'],
        'name': ['A', 'B', 'C'],
        'score': [0.9, 0.8, 0.85],
        'address': ['Addr A', 'Addr B', 'Addr C'],
        'avg_price': [10, 20, 30],
        'star': [5, 4, 3],
        'type': ['A', 'B', 'C'],
        'semantic_text': ['Txt', 'Txt', 'Txt']
    })
    
    res = await llm.run_final_selection(df, "prompt")
    assert not res.empty
    assert len(res) == 2
    assert 'itinerary_avg_score' in res.columns
    
@pytest.mark.asyncio
async def test_run_final_selection_exception_fallback(llm):
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'meal': ['Sáng', 'Sáng', 'Trưa'],
        'name': ['A', 'B', 'C'],
        'score': [0.9, 0.8, 0.85]
    })
    llm.client.aio.models.generate_content.side_effect = Exception("Fail")
    res = await llm.run_final_selection(df, "prompt")
    assert not res.empty # Fallback to score greedy
    assert len(res) == 2
