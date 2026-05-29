import pytest
import pandas as pd
from unittest.mock import MagicMock
from Back_End.Core.scoring_class import RestaurantScorer

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.semantic_similarity.return_value = {"1": 0.9, "2": 0.5}
    db.ef.return_value = [[0.1, 0.2], [0.3, 0.4]]
    db._cosine_similarity.return_value = 0.8
    return db

@pytest.fixture
def scorer(mock_db):
    scorer_obj = RestaurantScorer(user_lat=16.068, user_lng=108.224, db=mock_db)
    scorer_obj.weights = {
        'star': 0.1,
        'price': 0.3,
        'distance': 0.2,
        'semantic': 0.4,
        'health': 0.1
    }
    return scorer_obj

def test_score_star(scorer):
    assert scorer._score_star(5.0) == 1.0
    assert scorer._score_star(1.0) == 0.0

def test_score_price(scorer):
    assert scorer._score_price(50000, 100000) == 1.0
    assert scorer._score_price(70000, 100000) == 0.8
    assert scorer._score_price(90000, 100000) == 0.5
    assert scorer._score_price(120000, 100000) == 0.0
    assert scorer._score_price(50000, 0) == 0.0

def test_score_distance(scorer):
    score = scorer._score_distance(16.068, 108.224, 16.068, 108.224)
    assert score == 1.0
    score2 = scorer._score_distance(16.068, 108.224, 16.1, 108.3)
    assert 0.0 < score2 < 1.0

def test_score_semantic(scorer):
    # Semantic query empty
    res = scorer._score_semantic([1, 2], "")
    assert res == {"1": 0.0, "2": 0.0}
    
    # List empty
    res2 = scorer._score_semantic([], "query")
    assert res2 == {}

def test_score_semantic_from_texts(scorer):
    # Semantic query empty
    res = scorer._score_semantic_from_texts("", ["text1"], [1])
    assert res == {}
    
    # Normal case
    res2 = scorer._score_semantic_from_texts("query", ["text1", "text2"], [1, 2])
    assert "1" in res2
    assert "2" in res2

def test_extract_semantic_terms(scorer):
    assert scorer._extract_semantic_terms("") == []
    assert scorer._extract_semantic_terms("Phở, Bún") == ["phở", "bún"]

def test_compute_total_score(scorer):
    row = {
        'star': 4.0,
        'avg_price': 50000,
        'lat': 16.068,
        'lng': 108.224,
        'penalty_score': 60 # max penalty
    }
    
    # strict mode
    score_strict = scorer._compute_total_score(
        row, 100000, 0.8, 16.068, 108.224, {}, "strict"
    )
    
    # non-strict mode
    score_loose = scorer._compute_total_score(
        row, 100000, 0.8, 16.068, 108.224, {}, "normal"
    )
    
    assert score_strict < score_loose

def test_run_scoring_pipeline_empty(scorer):
    res = scorer.run_scoring_pipeline({'Sáng': pd.DataFrame()}, {})
    assert res.empty
    
    res2 = scorer.run_scoring_pipeline({}, {})
    assert res2.empty

def test_run_scoring_pipeline_no_semantic(scorer):
    filtered_data = {
        'Sáng': pd.DataFrame([
            {'id': 1, 'star': 4.0, 'avg_price': 30000, 'lat': 16.068, 'lng': 108.224, 'penalty_score': 0},
            {'id': 2, 'star': 5.0, 'avg_price': 50000, 'lat': 16.069, 'lng': 108.225, 'penalty_score': 10}
        ])
    }
    parsed_json = {
        'budget': 100000,
        'num_meals': 1,
        'meals_detail': [{'meal': 'Sáng'}] # No semantic_query
    }
    
    result_df = scorer.run_scoring_pipeline(filtered_data, parsed_json)
    assert not result_df.empty
    assert len(result_df) == 2

def test_run_scoring_pipeline_with_semantic_fallback(scorer):
    # Ensure missing_ids logic is hit
    scorer.db.semantic_similarity.return_value = {"1": 0.9} # missing "2"
    
    filtered_data = {
        'Sáng': pd.DataFrame([
            {'id': 1, 'star': 4.0, 'avg_price': 30000, 'lat': 16.068, 'lng': 108.224, 'penalty_score': 0, 'semantic_text': 'Phở bò'},
            {'id': 2, 'star': 5.0, 'avg_price': 50000, 'lat': 16.069, 'lng': 108.225, 'penalty_score': 10, 'semantic_text': 'Bún chả'}
        ])
    }
    parsed_json = {
        'budget': 100000,
        'num_meals': 1,
        'meals_detail': [{'meal': 'Sáng', 'semantic_query': 'Phở'}]
    }
    
    result_df = scorer.run_scoring_pipeline(filtered_data, parsed_json)
    assert not result_df.empty

def test_run_scoring_pipeline_no_keyword_match(scorer):
    filtered_data = {
        'Sáng': pd.DataFrame([
            {'id': 1, 'star': 4.0, 'avg_price': 30000, 'lat': 16.068, 'lng': 108.224, 'penalty_score': 0, 'semantic_text': 'Cơm tấm'}
        ])
    }
    parsed_json = {
        'budget': 100000,
        'num_meals': 1,
        'meals_detail': [{'meal': 'Sáng', 'semantic_query': 'Phở'}] # Keyword won't match
    }
    result_df = scorer.run_scoring_pipeline(filtered_data, parsed_json)
    assert not result_df.empty
