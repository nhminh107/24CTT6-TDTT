

"""
test_health_risk_detector.py
----------------------------
Comprehensive unit & integration test suite for HealthRiskDetector v2.

Coverage:
  - normalize_text()
  - _expand_keyword()
  - _ngrams_by_size()
  - HealthRiskDetector.__init__()
  - HealthRiskDetector._load_json()
  - HealthRiskDetector._span_covered()
  - HealthRiskDetector._is_negated()
  - HealthRiskDetector._collect_risk_tags()
  - HealthRiskDetector.detect()
  - HealthRiskDetector.detect_with_scores()
  - Integration: multi-disease / synonym expansion / greedy span / negation
  
  
Khi chạy file này ae lưu ý chạy từ thư mục gốc (thư mục khởi chạy server fast API), vd ( PS D:\24CTT6-TDTT-main\24CTT6-TDTT-main> python -m Back_End.UnitTest.test_integration_health_detector)
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.Core.health_mapping import (
    HealthRiskDetector,
    _expand_keyword,
    _ngrams_by_size,
    normalize_text,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_DICTIONARY = [
    {
        "health_tag": "stomach",
        "list_idea": [
            "da day", "bao tu", "dau da day", "dau bao tu",
            "viem da day", "trao nguoc", "acid da day",
            "loet da day", "viem loet da day", "roi loan tieu hoa",
        ],
    },
    {
        "health_tag": "diabetes",
        "list_idea": [
            "tieu duong", "duong huyet cao", "benh tieu duong",
            "dai thao duong", "tieu duong type 2", "tieu duong type 1",
            "khang insulin",
        ],
    },
    {
        "health_tag": "gout",
        "list_idea": [
            "gout", "gut", "benh gut", "benh gout",
            "dau khop do gout", "acid uric cao", "tang acid uric",
        ],
    },
    {
        "health_tag": "heart",
        "list_idea": [
            "tim mach", "benh tim", "suy tim", "nhan nhip tim",
            "cao huyet ap", "huyet ap cao", "tang huyet ap",
            "mo mau cao", "cholesterol cao",
        ],
    },
    {
        "health_tag": "kidney",
        "list_idea": [
            "than", "suy than", "benh than", "viem than",
            "than yeu", "than hu", "soi than",
        ],
    },
]

SAMPLE_MAPPING = {
    "stomach":  ["Spicy", "DeepFried_Oily", "Alcohol_Pub", "Acidic_Food"],
    "diabetes": ["High_Sugar", "Refined_Carbs", "Sugary_Drinks"],
    "gout":     ["Red_Meat", "Seafood", "Alcohol_Pub", "High_Purine"],
    "heart":    ["High_Fat", "High_Sodium", "Alcohol_Pub", "Trans_Fat"],
    "kidney":   ["High_Protein", "High_Potassium", "High_Sodium", "Alcohol_Pub"],
}

# Minimal dictionary with no expansion interference for negation tests
NEGATION_DICTIONARY = [
    {"health_tag": "diabetes", "list_idea": ["tieu duong"]},
    {"health_tag": "gout",     "list_idea": ["gout"]},
    {"health_tag": "heart",    "list_idea": ["suy tim"]},
    {"health_tag": "stomach",  "list_idea": ["bao tu"]},
]

NEGATION_MAPPING = {
    "diabetes": ["High_Sugar", "Refined_Carbs"],
    "gout":     ["Red_Meat", "Seafood", "Alcohol_Pub"],
    "heart":    ["High_Fat", "High_Sodium"],
    "stomach":  ["Spicy", "DeepFried_Oily"],
}


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class _TmpDir:
    """Mixin: tạo temp dir cho mỗi test class, dọn sau khi xong."""

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls._tmp = Path(cls._tmpdir.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmpdir.cleanup()


class _BaseDetectorTest(_TmpDir, unittest.TestCase):
    """Base: tạo detector đầy đủ với SAMPLE data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dict_path = cls._tmp / "dict.json"
        cls.map_path  = cls._tmp / "map.json"
        _write_json(cls.dict_path, SAMPLE_DICTIONARY)
        _write_json(cls.map_path,  SAMPLE_MAPPING)
        cls.detector = HealthRiskDetector(
            dictionary_path=cls.dict_path,
            mapping_path=cls.map_path,
            fuzzy_threshold=85,
            ngram_max=6,
            expand_synonyms=True,
            detect_negation=True,
        )


class _NegationDetectorTest(_TmpDir, unittest.TestCase):
    """Base: detector với expand_synonyms=False để test negation thuần."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dict_path = cls._tmp / "neg_dict.json"
        cls.map_path  = cls._tmp / "neg_map.json"
        _write_json(cls.dict_path, NEGATION_DICTIONARY)
        _write_json(cls.map_path,  NEGATION_MAPPING)
        cls.detector = HealthRiskDetector(
            dictionary_path=cls.dict_path,
            mapping_path=cls.map_path,
            fuzzy_threshold=85,
            ngram_max=5,
            expand_synonyms=False,
            detect_negation=True,
        )


# ===========================================================================
# 1. normalize_text
# ===========================================================================

class TestNormalizeText(unittest.TestCase):

    def test_lowercase(self):
        self.assertEqual(normalize_text("ABC"), "abc")

    def test_removes_diacritics_da_day(self):
        self.assertEqual(normalize_text("Dã Dày"), "da day")

    def test_removes_special_chars(self):
        self.assertEqual(normalize_text("Dã Dày!!!"), "da day")

    def test_collapses_whitespace(self):
        self.assertEqual(normalize_text("  đau   bao  tử  "), "dau bao tu")

    def test_empty_string(self):
        self.assertEqual(normalize_text(""), "")

    def test_only_special_chars(self):
        self.assertEqual(normalize_text("!!!???###"), "")

    def test_mixed_accent_and_punctuation(self):
        self.assertEqual(normalize_text("Tiểu Đường, Gout!"), "tieu duong gout")

    def test_numbers_preserved(self):
        self.assertIn("2", normalize_text("type 2"))

    def test_already_normalized(self):
        self.assertEqual(normalize_text("tieu duong"), "tieu duong")

    def test_unicode_cafe(self):
        result = normalize_text("café")
        self.assertNotIn("é", result)
        self.assertIsInstance(result, str)

    def test_tab_and_newline_collapsed(self):
        self.assertEqual(normalize_text("bao\ttu\nnang"), "bao tu nang")

    def test_full_sentence_negation(self):
        self.assertEqual(normalize_text("Không bị Tiểu Đường"), "khong bi tieu duong")

    def test_leading_trailing_stripped(self):
        result = normalize_text("  gout  ")
        self.assertEqual(result, "gout")

    def test_multiple_spaces_collapsed_to_one(self):
        result = normalize_text("bao    tu")
        self.assertEqual(result, "bao tu")

    def test_accented_vowels_all_removed(self):
        result = normalize_text("ạ ắ ẹ ộ ứ")
        for char in result:
            self.assertIn(char, "abcdefghijklmnopqrstuvwxyz0123456789 ")

    def test_return_type_is_str(self):
        self.assertIsInstance(normalize_text("test"), str)

    def test_tieu_duong(self):
        self.assertEqual(normalize_text("Tiểu Đường"), "tieu duong")

    def test_gout_unchanged(self):
        self.assertEqual(normalize_text("gout"), "gout")

    def test_question_mark_removed(self):
        result = normalize_text("bị tiểu đường?")
        self.assertNotIn("?", result)

    def test_comma_removed(self):
        result = normalize_text("gout, tiểu đường")
        self.assertNotIn(",", result)


# ===========================================================================
# 2. _expand_keyword
# ===========================================================================

class TestExpandKeyword(unittest.TestCase):

    def test_original_always_first(self):
        variants = _expand_keyword("bao tu")
        self.assertEqual(variants[0], "bao tu")

    def test_original_included(self):
        self.assertIn("bao tu", _expand_keyword("bao tu"))

    def test_prefix_dau(self):
        self.assertIn("dau bao tu", _expand_keyword("bao tu"))

    def test_prefix_bi(self):
        self.assertIn("bi bao tu", _expand_keyword("bao tu"))

    def test_prefix_mac(self):
        self.assertIn("mac bao tu", _expand_keyword("bao tu"))

    def test_prefix_mac_benh(self):
        self.assertIn("mac benh bao tu", _expand_keyword("bao tu"))

    def test_prefix_mac_phai(self):
        self.assertIn("mac phai bao tu", _expand_keyword("bao tu"))

    def test_prefix_bi_mac(self):
        self.assertIn("bi mac bao tu", _expand_keyword("bao tu"))

    def test_prefix_co(self):
        self.assertIn("co bao tu", _expand_keyword("bao tu"))

    def test_suffix_nang(self):
        self.assertIn("bao tu nang", _expand_keyword("bao tu"))

    def test_suffix_nhe(self):
        self.assertIn("bao tu nhe", _expand_keyword("bao tu"))

    def test_suffix_man_tinh(self):
        self.assertIn("bao tu man tinh", _expand_keyword("bao tu"))

    def test_suffix_cap_tinh(self):
        self.assertIn("bao tu cap tinh", _expand_keyword("bao tu"))

    def test_suffix_lau_nam(self):
        self.assertIn("bao tu lau nam", _expand_keyword("bao tu"))

    def test_no_duplicates(self):
        variants = _expand_keyword("gout")
        self.assertEqual(len(variants), len(set(variants)))

    def test_returns_list(self):
        self.assertIsInstance(_expand_keyword("tieu duong"), list)

    def test_all_strings(self):
        for v in _expand_keyword("suy tim"):
            self.assertIsInstance(v, str)

    def test_length_greater_than_one(self):
        self.assertGreater(len(_expand_keyword("gout")), 1)

    def test_no_empty_string_in_results_for_nonempty_kw(self):
        for v in _expand_keyword("gout"):
            self.assertTrue(v.strip())


# ===========================================================================
# 3. _ngrams_by_size
# ===========================================================================

class TestNgramsBySize(unittest.TestCase):

    def _texts(self, tokens, max_n):
        return [t for t, _, _ in _ngrams_by_size(tokens, max_n)]

    def test_single_token(self):
        result = _ngrams_by_size(["abc"], 3)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "abc")

    def test_descending_order_first_is_longest(self):
        tokens = ["a", "b", "c"]
        texts = self._texts(tokens, 3)
        self.assertEqual(len(texts[0].split()), 3)

    def test_descending_order_last_is_unigram(self):
        tokens = ["a", "b", "c"]
        texts = self._texts(tokens, 3)
        self.assertEqual(len(texts[-1].split()), 1)

    def test_span_indices_reconstruct_correctly(self):
        tokens = ["x", "y", "z"]
        for text, start, end in _ngrams_by_size(tokens, 3):
            self.assertEqual(text, " ".join(tokens[start:end]))

    def test_end_exclusive(self):
        for _, start, end in _ngrams_by_size(["a", "b"], 2):
            self.assertGreater(end, start)

    def test_max_n_larger_than_tokens(self):
        tokens = ["a", "b"]
        texts = self._texts(tokens, 10)
        self.assertIn("a b", texts)

    def test_empty_tokens(self):
        self.assertEqual(_ngrams_by_size([], 5), [])

    def test_unigrams_present(self):
        tokens = ["tieu", "duong"]
        texts = self._texts(tokens, 3)
        self.assertIn("tieu", texts)
        self.assertIn("duong", texts)

    def test_bigrams_present(self):
        tokens = ["tieu", "duong"]
        texts = self._texts(tokens, 3)
        self.assertIn("tieu duong", texts)

    def test_total_count_three_tokens(self):
        # 3-gram:1 + 2-gram:2 + 1-gram:3 = 6
        self.assertEqual(len(_ngrams_by_size(["a", "b", "c"], 3)), 6)

    def test_total_count_two_tokens_max2(self):
        # 2-gram:1 + 1-gram:2 = 3
        self.assertEqual(len(_ngrams_by_size(["a", "b"], 2)), 3)

    def test_max_n_one_returns_unigrams_only(self):
        texts = self._texts(["a", "b", "c"], 1)
        self.assertEqual(texts, ["a", "b", "c"])

    def test_spans_are_tuples(self):
        for item in _ngrams_by_size(["x", "y"], 2):
            self.assertEqual(len(item), 3)

    def test_start_always_nonnegative(self):
        for _, start, _ in _ngrams_by_size(["a", "b", "c"], 3):
            self.assertGreaterEqual(start, 0)


# ===========================================================================
# 4. HealthRiskDetector.__init__ & _load_json
# ===========================================================================

class TestConstructor(_TmpDir, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _paths(self, name=""):
        d = self._tmp / f"dict{name}.json"
        m = self._tmp / f"map{name}.json"
        return d, m

    def _make(self, name="", dictionary=None, mapping=None, **kwargs):
        d, m = self._paths(name)
        _write_json(d, dictionary if dictionary is not None else SAMPLE_DICTIONARY)
        _write_json(m, mapping if mapping is not None else SAMPLE_MAPPING)
        return HealthRiskDetector(d, m, **kwargs)

    def test_loads_successfully(self):
        det = self._make("ok")
        self.assertIsNotNone(det)

    def test_keyword_index_populated(self):
        det = self._make("kw")
        self.assertGreater(len(det._keyword_index), 0)

    def test_all_keywords_populated(self):
        det = self._make("ak")
        self.assertGreater(len(det._all_keywords), 0)

    def test_expand_true_more_keywords_than_false(self):
        det_exp   = self._make("exp1",  expand_synonyms=True)
        det_noexp = self._make("exp0",  expand_synonyms=False)
        self.assertGreater(len(det_exp._keyword_index), len(det_noexp._keyword_index))

    def test_custom_fuzzy_threshold_stored(self):
        det = self._make("ft", fuzzy_threshold=90)
        self.assertEqual(det.fuzzy_threshold, 90)

    def test_custom_ngram_max_stored(self):
        det = self._make("nm", ngram_max=3)
        self.assertEqual(det.ngram_max, 3)

    def test_missing_dict_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            HealthRiskDetector(self._tmp / "ghost_d.json", self._tmp / "ghost_m.json")

    def test_missing_map_raises_file_not_found(self):
        d, _ = self._paths("mis")
        _write_json(d, SAMPLE_DICTIONARY)
        with self.assertRaises(FileNotFoundError):
            HealthRiskDetector(d, self._tmp / "ghost_map.json")

    def test_invalid_json_dict_raises_decode_error(self):
        d, m = self._paths("bjd")
        d.write_text("{not json", encoding="utf-8")
        _write_json(m, SAMPLE_MAPPING)
        with self.assertRaises(json.JSONDecodeError):
            HealthRiskDetector(d, m)

    def test_invalid_json_map_raises_decode_error(self):
        d, m = self._paths("bjm")
        _write_json(d, SAMPLE_DICTIONARY)
        m.write_text("[broken", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            HealthRiskDetector(d, m)

    def test_empty_dictionary_list_zero_keywords(self):
        det = self._make("emd", dictionary=[])
        self.assertEqual(len(det._keyword_index), 0)

    def test_empty_mapping_stored(self):
        det = self._make("emm", mapping={})
        self.assertEqual(det._tag_mapping, {})

    def test_entry_missing_health_tag_skipped(self):
        det = self._make("mht", dictionary=[{"list_idea": ["test"]}])
        self.assertEqual(len(det._keyword_index), 0)

    def test_entry_empty_list_idea_skipped(self):
        det = self._make("eli", dictionary=[{"health_tag": "stomach", "list_idea": []}])
        self.assertEqual(len(det._keyword_index), 0)

    def test_multi_tag_same_keyword_both_stored(self):
        shared = [
            {"health_tag": "tagA", "list_idea": ["shared kw"]},
            {"health_tag": "tagB", "list_idea": ["shared kw"]},
        ]
        det = self._make("mts", dictionary=shared, mapping={"tagA": [], "tagB": []},
                         expand_synonyms=False)
        tags = det._keyword_index.get("shared kw", [])
        self.assertIn("tagA", tags)
        self.assertIn("tagB", tags)

    def test_all_keywords_no_duplicates(self):
        det = self._make("aknd")
        self.assertEqual(len(det._all_keywords), len(set(det._all_keywords)))

    def test_string_path_accepted(self):
        d, m = self._paths("sp")
        _write_json(d, SAMPLE_DICTIONARY)
        _write_json(m, SAMPLE_MAPPING)
        det = HealthRiskDetector(str(d), str(m))
        self.assertIsNotNone(det)

    def test_detect_negation_flag_stored(self):
        det = self._make("dn", detect_negation=False)
        self.assertFalse(det.detect_negation)

    def test_expand_synonyms_flag_stored(self):
        det = self._make("es", expand_synonyms=False)
        self.assertFalse(det.expand_synonyms)

    def test_keyword_index_values_are_lists(self):
        det = self._make("kvl")
        for v in det._keyword_index.values():
            self.assertIsInstance(v, list)

    def test_no_duplicate_tags_in_single_keyword_index(self):
        shared = [
            {"health_tag": "tagA", "list_idea": ["kw"]},
            {"health_tag": "tagA", "list_idea": ["kw"]},
        ]
        det = self._make("ndt", dictionary=shared, mapping={"tagA": []},
                         expand_synonyms=False)
        self.assertEqual(det._keyword_index.get("kw", []).count("tagA"), 1)


# ===========================================================================
# 5. _load_json static method
# ===========================================================================

class TestLoadJson(_TmpDir, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _p(self, name):
        return self._tmp / f"{name}.json"

    def test_loads_dict(self):
        p = self._p("ld")
        _write_json(p, {"k": "v"})
        self.assertEqual(HealthRiskDetector._load_json(p), {"k": "v"})

    def test_loads_list(self):
        p = self._p("ll")
        _write_json(p, [1, 2, 3])
        self.assertEqual(HealthRiskDetector._load_json(p), [1, 2, 3])

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            HealthRiskDetector._load_json(self._tmp / "ghost.json")

    def test_invalid_json_raises(self):
        p = self._p("ij")
        p.write_text("{bad}", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            HealthRiskDetector._load_json(p)

    def test_accepts_string_path(self):
        p = self._p("sp")
        _write_json(p, {"a": 1})
        self.assertEqual(HealthRiskDetector._load_json(str(p)), {"a": 1})

    def test_accepts_path_object(self):
        p = self._p("po")
        _write_json(p, {"b": 2})
        self.assertEqual(HealthRiskDetector._load_json(p), {"b": 2})

    def test_utf8_vietnamese_content(self):
        p = self._p("utf")
        data = {"tiếng": "Việt"}
        _write_json(p, data)
        self.assertEqual(HealthRiskDetector._load_json(p)["tiếng"], "Việt")

    def test_empty_list(self):
        p = self._p("el")
        _write_json(p, [])
        self.assertEqual(HealthRiskDetector._load_json(p), [])

    def test_empty_dict(self):
        p = self._p("ed")
        _write_json(p, {})
        self.assertEqual(HealthRiskDetector._load_json(p), {})

    def test_nested_structure(self):
        p = self._p("ns")
        data = [{"health_tag": "x", "list_idea": ["a", "b"]}]
        _write_json(p, data)
        loaded = HealthRiskDetector._load_json(p)
        self.assertEqual(loaded[0]["health_tag"], "x")


# ===========================================================================
# 6. _span_covered
# ===========================================================================

class TestSpanCovered(unittest.TestCase):

    sc = HealthRiskDetector._span_covered

    def test_exact_boundary_covered(self):
        self.assertTrue(TestSpanCovered.sc(2, 5, [(2, 5)]))

    def test_contained_within_span(self):
        self.assertTrue(TestSpanCovered.sc(3, 4, [(2, 5)]))

    def test_not_covered(self):
        self.assertFalse(TestSpanCovered.sc(6, 8, [(2, 5)]))

    def test_empty_spans_always_false(self):
        self.assertFalse(TestSpanCovered.sc(0, 3, []))

    def test_partial_overlap_left(self):
        self.assertFalse(TestSpanCovered.sc(1, 4, [(2, 5)]))

    def test_partial_overlap_right(self):
        self.assertFalse(TestSpanCovered.sc(3, 7, [(2, 5)]))

    def test_multiple_spans_one_covers(self):
        self.assertTrue(TestSpanCovered.sc(4, 6, [(0, 2), (3, 7)]))

    def test_multiple_spans_none_covers(self):
        self.assertFalse(TestSpanCovered.sc(10, 12, [(0, 2), (3, 7)]))

    def test_start_equals_span_end_not_covered(self):
        # [5, 7) vs span [2, 5) — start == span_end → not contained
        self.assertFalse(TestSpanCovered.sc(5, 7, [(2, 5)]))

    def test_end_equals_span_start_not_covered(self):
        # [0, 2) vs span [2, 5) — not contained
        self.assertFalse(TestSpanCovered.sc(0, 2, [(2, 5)]))

    def test_span_fully_covers_large_range(self):
        self.assertTrue(TestSpanCovered.sc(1, 4, [(0, 10)]))

    def test_single_token_span_covered(self):
        self.assertTrue(TestSpanCovered.sc(3, 4, [(0, 5)]))

    def test_single_token_span_not_covered(self):
        self.assertFalse(TestSpanCovered.sc(6, 7, [(0, 5)]))


# ===========================================================================
# 7. _is_negated
# ===========================================================================

class TestIsNegated(unittest.TestCase):

    @staticmethod
    def _tok(text: str) -> list[str]:
        return normalize_text(text).split()

    def test_not_negated_simple(self):
        tokens = self._tok("toi bi tieu duong")
        self.assertFalse(HealthRiskDetector._is_negated(tokens, 2))

    def test_negated_khong_bi_window_contains_phrase(self):
        tokens = self._tok("toi khong bi tieu duong")
        tieu_idx = tokens.index("tieu")
        self.assertTrue(HealthRiskDetector._is_negated(tokens, tieu_idx))

    def test_negated_chua_tung(self):
        tokens = self._tok("toi chua tung bi gout")
        gout_idx = tokens.index("gout")
        self.assertTrue(HealthRiskDetector._is_negated(tokens, gout_idx))

    def test_negated_khong_co(self):
        tokens = self._tok("khong co benh gout")
        benh_idx = tokens.index("benh")
        self.assertTrue(HealthRiskDetector._is_negated(tokens, benh_idx))

    def test_negated_khong_mac(self):
        tokens = self._tok("toi khong mac tieu duong")
        tieu_idx = tokens.index("tieu")
        self.assertTrue(HealthRiskDetector._is_negated(tokens, tieu_idx))

    def test_negated_chua_co(self):
        tokens = self._tok("toi chua co benh gout")
        benh_idx = tokens.index("benh")
        self.assertTrue(HealthRiskDetector._is_negated(tokens, benh_idx))

    def test_keyword_at_position_zero_never_negated(self):
        tokens = self._tok("gout nang")
        self.assertFalse(HealthRiskDetector._is_negated(tokens, 0))

    def test_negation_beyond_window_not_triggered(self):
        # 'khong bi' is 5+ tokens before keyword
        tokens = self._tok("khong bi a b c d e tieu duong")
        tieu_idx = tokens.index("tieu")
        self.assertFalse(HealthRiskDetector._is_negated(tokens, tieu_idx))

    def test_gout_not_negated_after_nhung(self):
        tokens = self._tok("khong bi tieu duong nhung bi gout")
        gout_idx = tokens.index("gout")
        self.assertFalse(HealthRiskDetector._is_negated(tokens, gout_idx))

    def test_negated_khong_phai(self):
        tokens = self._tok("day khong phai gout")
        gout_idx = tokens.index("gout")
        self.assertTrue(HealthRiskDetector._is_negated(tokens, gout_idx))

    def test_no_negation_just_positive(self):
        tokens = self._tok("toi bi gout nang")
        gout_idx = tokens.index("gout")
        self.assertFalse(HealthRiskDetector._is_negated(tokens, gout_idx))

    def test_chua_bi_triggers(self):
        tokens = self._tok("toi chua bi tieu duong")
        tieu_idx = tokens.index("tieu")
        self.assertTrue(HealthRiskDetector._is_negated(tokens, tieu_idx))

    def test_returns_bool(self):
        tokens = self._tok("tieu duong")
        result = HealthRiskDetector._is_negated(tokens, 0)
        self.assertIsInstance(result, bool)


# ===========================================================================
# 8. _collect_risk_tags
# ===========================================================================

class TestCollectRiskTags(_BaseDetectorTest):

    def test_single_tag_stomach(self):
        result = self.detector._collect_risk_tags({"stomach"})
        for tag in SAMPLE_MAPPING["stomach"]:
            self.assertIn(tag, result)

    def test_single_tag_diabetes(self):
        result = self.detector._collect_risk_tags({"diabetes"})
        for tag in SAMPLE_MAPPING["diabetes"]:
            self.assertIn(tag, result)

    def test_multiple_tags_all_risks_present(self):
        result = self.detector._collect_risk_tags({"diabetes", "gout"})
        self.assertIn("High_Sugar", result)
        self.assertIn("Red_Meat", result)

    def test_no_duplicates_shared_alcohol(self):
        result = self.detector._collect_risk_tags({"stomach", "gout"})
        self.assertEqual(result.count("Alcohol_Pub"), 1)

    def test_empty_input_returns_empty(self):
        self.assertEqual(self.detector._collect_risk_tags(set()), [])

    def test_unknown_tag_ignored(self):
        self.assertEqual(self.detector._collect_risk_tags({"nonexistent"}), [])

    def test_returns_list(self):
        self.assertIsInstance(self.detector._collect_risk_tags({"stomach"}), list)

    def test_result_all_strings(self):
        for tag in self.detector._collect_risk_tags({"heart"}):
            self.assertIsInstance(tag, str)

    def test_all_five_tags_no_duplicates(self):
        result = self.detector._collect_risk_tags(
            {"stomach", "diabetes", "gout", "heart", "kidney"}
        )
        self.assertEqual(len(result), len(set(result)))

    def test_partial_unknown_mixed(self):
        result = self.detector._collect_risk_tags({"diabetes", "unknown_tag"})
        self.assertIn("High_Sugar", result)

    def test_kidney_risks_present(self):
        result = self.detector._collect_risk_tags({"kidney"})
        for tag in SAMPLE_MAPPING["kidney"]:
            self.assertIn(tag, result)


# ===========================================================================
# 9. detect() — exact match
# ===========================================================================

class TestDetectExact(_BaseDetectorTest):

    def test_stomach_bao_tu(self):
        self.assertIn("Spicy", self.detector.detect("Tôi bị đau bao tử"))

    def test_stomach_trao_nguoc(self):
        self.assertIn("Spicy", self.detector.detect("Tôi hay bị trào ngược"))

    def test_stomach_loet_da_day(self):
        self.assertIn("Spicy", self.detector.detect("loét dạ dày"))

    def test_stomach_viem_da_day(self):
        self.assertIn("Spicy", self.detector.detect("viêm dạ dày"))

    def test_diabetes_tieu_duong(self):
        self.assertIn("High_Sugar", self.detector.detect("Tôi bị tiểu đường"))

    def test_diabetes_duong_huyet_cao(self):
        self.assertIn("High_Sugar", self.detector.detect("đường huyết cao"))

    def test_diabetes_type2(self):
        self.assertIn("High_Sugar", self.detector.detect("tiểu đường type 2"))

    def test_gout_keyword(self):
        self.assertIn("Red_Meat", self.detector.detect("Tôi bị gout"))

    def test_gout_acid_uric(self):
        self.assertIn("Red_Meat", self.detector.detect("acid uric cao"))

    def test_heart_suy_tim(self):
        self.assertIn("High_Fat", self.detector.detect("Tôi bị suy tim"))

    def test_heart_cholesterol(self):
        self.assertIn("High_Fat", self.detector.detect("cholesterol cao"))

    def test_heart_tang_huyet_ap(self):
        self.assertIn("High_Sodium", self.detector.detect("tăng huyết áp"))

    def test_kidney_suy_than(self):
        self.assertIn("High_Protein", self.detector.detect("suy thận"))

    def test_kidney_soi_than(self):
        self.assertIn("High_Protein", self.detector.detect("sỏi thận"))

    def test_no_duplicate_risk_tags(self):
        result = self.detector.detect("Tôi bị tiểu đường và gout và suy tim")
        self.assertEqual(len(result), len(set(result)))

    def test_two_diseases_all_risks_present(self):
        result = set(self.detector.detect("Tôi bị tiểu đường và gout"))
        self.assertIn("High_Sugar", result)
        self.assertIn("Red_Meat", result)

    def test_shared_risk_dedup(self):
        result = self.detector.detect("Tôi bị bao tử và gout")
        self.assertEqual(result.count("Alcohol_Pub"), 1)

    def test_same_tag_two_keywords_single_risk_set(self):
        result = self.detector.detect("Tôi bị đau bao tử với viêm dạ dày")
        self.assertEqual(result.count("Spicy"), 1)

    def test_returns_list(self):
        self.assertIsInstance(self.detector.detect("bao tu"), list)

    def test_keyword_without_diacritics(self):
        self.assertIn("High_Sugar", self.detector.detect("toi bi tieu duong"))

    def test_keyword_uppercase(self):
        self.assertIn("High_Sugar", self.detector.detect("TÔI BỊ TIỂU ĐƯỜNG"))

    def test_keyword_mixed_case(self):
        self.assertIn("High_Sugar", self.detector.detect("Tôi bị Tiểu Đường"))

    def test_result_all_strings(self):
        for tag in self.detector.detect("tiểu đường"):
            self.assertIsInstance(tag, str)


# ===========================================================================
# 10. detect() — fuzzy match
# ===========================================================================

class TestDetectFuzzy(_BaseDetectorTest):

    def test_typo_tieu_duong_double_e(self):
        self.assertIn("High_Sugar", self.detector.detect("tieeu duong"))

    def test_typo_gout_double_o(self):
        self.assertIn("Red_Meat", self.detector.detect("bị goout"))

    def test_typo_suy_tim_double_i(self):
        self.assertIn("High_Fat", self.detector.detect("suy tiim"))

    def test_typo_bao_tu_double_o(self):
        self.assertIn("Spicy", self.detector.detect("baoo tu"))

    def test_high_threshold_blocks_weak_matches(self):
        det_strict = HealthRiskDetector(
            self.dict_path, self.map_path,
            fuzzy_threshold=99, expand_synonyms=False,
        )
        self.assertEqual(det_strict.detect("xyz randomword"), [])

    def test_fuzzy_score_in_valid_range(self):
        for d in self.detector.detect_with_scores("tieeu duong"):
            if d["method"] == "fuzzy":
                self.assertGreaterEqual(d["score"], 0.0)
                self.assertLessEqual(d["score"], 1.0)

    def test_unrelated_gibberish_no_match(self):
        self.assertEqual(self.detector.detect("xyzabc qwerty"), [])


# ===========================================================================
# 11. detect() — synonym expansion (①)
# ===========================================================================

class TestSynonymExpansion(_BaseDetectorTest):

    def test_mac_benh_tim(self):
        self.assertIn("High_Fat", self.detector.detect("mắc bệnh tim"))

    def test_bi_suy_than(self):
        self.assertIn("High_Protein", self.detector.detect("bị suy thận"))

    def test_gout_nang_suffix(self):
        self.assertIn("Red_Meat", self.detector.detect("gout nặng"))

    def test_tieu_duong_man_tinh(self):
        self.assertIn("High_Sugar", self.detector.detect("tiểu đường mãn tính"))

    def test_viem_da_day_cap_tinh(self):
        self.assertIn("Spicy", self.detector.detect("viêm dạ dày cấp tính"))

    def test_bao_tu_lau_nam(self):
        self.assertIn("Spicy", self.detector.detect("bao tử lâu năm"))

    def test_mac_phai_tieu_duong(self):
        self.assertIn("High_Sugar", self.detector.detect("mắc phải tiểu đường"))

    def test_expansion_more_results_than_no_expansion(self):
        det_noexp = HealthRiskDetector(
            self.dict_path, self.map_path, expand_synonyms=False
        )
        r_exp   = self.detector.detect("mắc bệnh tim nặng")
        r_noexp = det_noexp.detect("mắc bệnh tim nặng")
        self.assertGreaterEqual(len(r_exp), len(r_noexp))

    def test_mac_benh_stomach(self):
        self.assertIn("Spicy", self.detector.detect("mắc bệnh dạ dày"))

    def test_bi_dau_gout(self):
        self.assertIn("Red_Meat", self.detector.detect("bị đau gout"))


# ===========================================================================
# 12. detect() — negation (③) — uses expand_synonyms=False for clarity
# ===========================================================================

class TestNegationDetection(_NegationDetectorTest):

    def test_khong_bi_removes_diabetes(self):
        self.assertNotIn("High_Sugar", self.detector.detect("Tôi không bị tiểu đường"))

    def test_chua_bi_removes_gout(self):
        self.assertNotIn("Red_Meat", self.detector.detect("Tôi chưa bị gout"))

    def test_chua_tung_removes_heart(self):
        self.assertNotIn("High_Fat", self.detector.detect("Tôi chưa từng bị suy tim"))

    def test_khong_co_removes_gout(self):
        self.assertNotIn("Red_Meat", self.detector.detect("tôi không có gout"))

    def test_khong_mac_removes_diabetes(self):
        self.assertNotIn("High_Sugar", self.detector.detect("tôi không mắc tiểu đường"))

    def test_negation_removes_only_negated_disease(self):
        result = self.detector.detect("Tôi không bị tiểu đường nhưng bị gout")
        self.assertNotIn("High_Sugar", result)
        self.assertIn("Red_Meat", result)

    def test_negation_disabled_keeps_tag(self):
        det_no_neg = HealthRiskDetector(
            self.dict_path, self.map_path,
            detect_negation=False, expand_synonyms=False,
        )
        self.assertIn("High_Sugar", det_no_neg.detect("Tôi không bị tiểu đường"))

    def test_positive_disease_after_negated_disease(self):
        result = self.detector.detect("Không bị gout nhưng bị tiểu đường")
        self.assertIn("High_Sugar", result)
        self.assertNotIn("Red_Meat", result)

    def test_all_negated_returns_empty(self):
        result = self.detector.detect(
            "Tôi không bị tiểu đường, không bị gout, chưa bị suy tim"
        )
        self.assertEqual(result, [])

    def test_negated_tag_in_detect_with_scores(self):
        scores = self.detector.detect_with_scores("Tôi không bị tiểu đường")
        exact_diabetes = [
            d for d in scores
            if d["health_tag"] == "diabetes" and d["method"] == "exact"
        ]
        if exact_diabetes:
            self.assertTrue(any(d["negated"] for d in exact_diabetes))

    def test_two_negated_one_confirmed(self):
        result = self.detector.detect(
            "Không bị tiểu đường, không bị gout, nhưng bị suy tim"
        )
        self.assertIn("High_Fat", result)
        self.assertNotIn("High_Sugar", result)
        self.assertNotIn("Red_Meat", result)

    def test_negation_at_sentence_start(self):
        self.assertNotIn("High_Sugar", self.detector.detect("Không bị tiểu đường"))


# ===========================================================================
# 13. detect() — greedy span tracking (⑤)
# ===========================================================================

class TestGreedySpanTracking(_BaseDetectorTest):

    def test_long_keyword_prevents_wrong_sub_match(self):
        result = self.detector.detect("Tôi hay bị trào ngược")
        self.assertIn("Spicy", result)
        self.assertNotIn("Red_Meat", result)

    def test_two_overlapping_same_tag_no_dup_risk(self):
        result = self.detector.detect("đau bao tử với viêm dạ dày")
        self.assertEqual(result.count("Spicy"), 1)

    def test_longest_match_returns_correct_tag(self):
        result = self.detector.detect("đau bao tử")
        self.assertIn("Spicy", result)

    def test_no_cross_contamination_between_tags(self):
        result = set(self.detector.detect("Tôi bị trào ngược dạ dày"))
        self.assertIn("Spicy", result)
        self.assertNotIn("Red_Meat", result)


# ===========================================================================
# 14. detect() — edge cases
# ===========================================================================

class TestDetectEdgeCases(_BaseDetectorTest):

    def test_empty_string(self):
        self.assertEqual(self.detector.detect(""), [])

    def test_whitespace_only(self):
        self.assertEqual(self.detector.detect("   "), [])

    def test_unrelated_food_order(self):
        self.assertEqual(self.detector.detect("Cho tôi một tô phở đặc biệt"), [])

    def test_numbers_only(self):
        self.assertEqual(self.detector.detect("123 456 789"), [])

    def test_special_chars_only(self):
        self.assertEqual(self.detector.detect("!!! ??? ###"), [])

    def test_very_long_prompt_single_disease(self):
        long = "tôi bị tiểu đường " * 50
        result = self.detector.detect(long)
        self.assertIn("High_Sugar", result)
        self.assertEqual(result.count("High_Sugar"), 1)

    def test_single_stopword(self):
        self.assertEqual(self.detector.detect("tôi"), [])

    def test_mixed_language_with_keyword(self):
        self.assertIn("Spicy", self.detector.detect("I have bao tử problems"))

    def test_repeated_disease_no_duplicate_risk(self):
        result = self.detector.detect("gout gout gout")
        self.assertEqual(result.count("Red_Meat"), 1)

    def test_punctuation_around_keyword(self):
        self.assertIn("High_Sugar", self.detector.detect("(tiểu đường)!"))

    def test_newline_in_prompt(self):
        self.assertIn("High_Sugar", self.detector.detect("tôi bị\ntiểu đường"))

    def test_comma_separated_diseases(self):
        result = set(self.detector.detect("tiểu đường, gout, suy tim"))
        self.assertIn("High_Sugar", result)
        self.assertIn("Red_Meat", result)
        self.assertIn("High_Fat", result)

    def test_three_diseases_no_dup_risks(self):
        result = self.detector.detect("tiểu đường gout suy tim")
        self.assertEqual(len(result), len(set(result)))

    def test_returns_list_always(self):
        self.assertIsInstance(self.detector.detect("random text"), list)

    def test_tab_separated_keywords(self):
        self.assertIn("High_Sugar", self.detector.detect("tôi bị\ttiểu đường"))

    def test_ellipsis_around_keyword(self):
        self.assertIn("Spicy", self.detector.detect("...bao tử..."))


# ===========================================================================
# 15. detect_with_scores() — metadata (④)
# ===========================================================================

class TestDetectWithScores(_BaseDetectorTest):

    def test_returns_list(self):
        self.assertIsInstance(self.detector.detect_with_scores("bao tu"), list)

    def test_all_required_keys_present(self):
        for item in self.detector.detect_with_scores("tiểu đường"):
            for key in ("health_tag", "matched_keyword", "score", "method", "negated"):
                self.assertIn(key, item)

    def test_exact_match_score_equals_one(self):
        for item in self.detector.detect_with_scores("bao tu"):
            if item["method"] == "exact":
                self.assertEqual(item["score"], 1.0)

    def test_exact_match_method_label(self):
        methods = {d["method"] for d in self.detector.detect_with_scores("bao tu")}
        self.assertIn("exact", methods)

    def test_fuzzy_method_label_for_typo(self):
        items = [d for d in self.detector.detect_with_scores("tieeu duong")
                 if d["method"] == "fuzzy"]
        self.assertGreater(len(items), 0)

    def test_health_tag_in_known_set(self):
        valid = {e["health_tag"] for e in SAMPLE_DICTIONARY}
        for item in self.detector.detect_with_scores("tiểu đường và gout"):
            self.assertIn(item["health_tag"], valid)

    def test_negated_false_for_positive_prompt(self):
        for item in self.detector.detect_with_scores("tôi bị tiểu đường"):
            if item["health_tag"] == "diabetes" and item["method"] == "exact":
                self.assertFalse(item["negated"])

    def test_matched_keyword_is_nonempty_string(self):
        for item in self.detector.detect_with_scores("bao tu"):
            self.assertIsInstance(item["matched_keyword"], str)
            self.assertTrue(item["matched_keyword"])

    def test_no_duplicate_tag_negated_pairs(self):
        items = self.detector.detect_with_scores("tiểu đường và gout")
        pairs = [(d["health_tag"], d["negated"]) for d in items]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_empty_prompt_returns_empty(self):
        self.assertEqual(self.detector.detect_with_scores(""), [])

    def test_score_range_for_all_items(self):
        for item in self.detector.detect_with_scores("tiểu đường tieeu duong"):
            self.assertGreaterEqual(item["score"], 0.0)
            self.assertLessEqual(item["score"], 1.0)

    def test_negated_is_bool(self):
        for item in self.detector.detect_with_scores("tiểu đường"):
            self.assertIsInstance(item["negated"], bool)

    def test_method_is_exact_or_fuzzy(self):
        for item in self.detector.detect_with_scores("tiểu đường tieeu duong"):
            self.assertIn(item["method"], ("exact", "fuzzy"))

    def test_multiple_diseases_multiple_items(self):
        items = self.detector.detect_with_scores("tiểu đường và gout")
        tags = {d["health_tag"] for d in items}
        self.assertGreater(len(tags), 1)

    def test_score_one_only_for_exact(self):
        for item in self.detector.detect_with_scores("tiểu đường tieeu duong"):
            if item["score"] == 1.0:
                self.assertEqual(item["method"], "exact")


# ===========================================================================
# 16. Stopword pre-filter (⑥)
# ===========================================================================

class TestStopwordFilter(_BaseDetectorTest):

    def test_stopwords_only_no_result(self):
        self.assertEqual(self.detector.detect("tôi bị với và hay"), [])

    def test_stopword_plus_keyword_matches(self):
        self.assertIn("High_Sugar", self.detector.detect("tôi và bị với tiểu đường"))

    def test_pure_stopword_tokens_no_false_positive(self):
        self.assertEqual(self.detector.detect("tôi bị với hay lâu năm đang dần"), [])

    def test_stopword_in_ngram_with_keyword_still_matches(self):
        self.assertIn("Spicy", self.detector.detect("tôi bị bao tử"))


# ===========================================================================
# 17. Multi-tag per keyword (②)
# ===========================================================================

class TestMultiTagPerKeyword(_TmpDir, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _make(self, name, dictionary, mapping, **kwargs):
        d = self._tmp / f"mt_d_{name}.json"
        m = self._tmp / f"mt_m_{name}.json"
        _write_json(d, dictionary)
        _write_json(m, mapping)
        return HealthRiskDetector(d, m, expand_synonyms=False,
                                  detect_negation=False, **kwargs)

    def test_shared_keyword_triggers_both_tags(self):
        det = self._make("a",
            [{"health_tag": "tagA", "list_idea": ["shared kw"]},
             {"health_tag": "tagB", "list_idea": ["shared kw"]}],
            {"tagA": ["RiskA"], "tagB": ["RiskB"]})
        result = det.detect("shared kw")
        self.assertIn("RiskA", result)
        self.assertIn("RiskB", result)

    def test_keyword_index_value_is_list(self):
        det = self._make("b",
            [{"health_tag": "tagA", "list_idea": ["kw"]},
             {"health_tag": "tagB", "list_idea": ["kw"]}],
            {"tagA": [], "tagB": []})
        self.assertIsInstance(det._keyword_index.get("kw"), list)

    def test_no_duplicate_tags_same_keyword(self):
        det = self._make("c",
            [{"health_tag": "tagA", "list_idea": ["kw"]},
             {"health_tag": "tagA", "list_idea": ["kw"]}],
            {"tagA": ["R1"]})
        self.assertEqual(det._keyword_index.get("kw", []).count("tagA"), 1)

    def test_three_tags_one_keyword(self):
        det = self._make("d",
            [{"health_tag": "t1", "list_idea": ["x"]},
             {"health_tag": "t2", "list_idea": ["x"]},
             {"health_tag": "t3", "list_idea": ["x"]}],
            {"t1": ["R1"], "t2": ["R2"], "t3": ["R3"]})
        result = set(det.detect("x"))
        self.assertEqual(result, {"R1", "R2", "R3"})


# ===========================================================================
# 18. Integration — realistic Vietnamese prompts
# ===========================================================================

class TestIntegrationRealistic(_BaseDetectorTest):

    def test_colloquial_stomach_and_diabetes(self):
        rs = set(self.detector.detect("Em bị đau bao tử với lại bị tiểu đường"))
        self.assertIn("Spicy", rs)
        self.assertIn("High_Sugar", rs)

    def test_no_diacritic_stomach(self):
        self.assertIn("Spicy", self.detector.detect("toi bi dau da day"))

    def test_gout_with_acid_uric_context(self):
        self.assertIn("Red_Meat", self.detector.detect(
            "Bác sĩ kết luận acid uric tăng cao, khả năng bị gout"
        ))

    def test_kidney_stone_and_viem_than(self):
        rs = set(self.detector.detect("Tôi bị sỏi thận và viêm thận"))
        self.assertIn("High_Protein", rs)

    def test_hypertension_keyword(self):
        self.assertIn("High_Sodium", self.detector.detect(
            "người nhà mình bị tăng huyết áp nặng"
        ))

    def test_all_five_diseases_present(self):
        rs = set(self.detector.detect(
            "Tôi bị tiểu đường, gout, suy tim, suy thận, và viêm dạ dày"
        ))
        for risk in ("High_Sugar", "Red_Meat", "High_Fat", "High_Protein", "Spicy"):
            self.assertIn(risk, rs)

    def test_shared_alcohol_pub_dedup(self):
        result = self.detector.detect("Tôi bị gout và suy thận")
        self.assertEqual(result.count("Alcohol_Pub"), 1)

    def test_question_format_prompt(self):
        self.assertIn("High_Sugar", self.detector.detect(
            "Em bị tiểu đường thì không nên ăn gì ạ?"
        ))

    def test_informal_stomach_complaint(self):
        self.assertIn("Spicy", self.detector.detect(
            "mình hay bị đau bao tử lắm, nhất là sau khi ăn đồ cay"
        ))

    def test_long_clinical_sentence(self):
        self.assertIn("Spicy", self.detector.detect(
            "Dạo này tôi hay bị đau vùng bụng trên sau khi ăn, bác sĩ nghi ngờ "
            "là viêm loét dạ dày, cần kiêng các loại thức ăn gây kích ứng"
        ))

    def test_diabetes_type2_explicit(self):
        self.assertIn("High_Sugar", self.detector.detect("tiểu đường type 2"))

    def test_unrelated_food_order_empty(self):
        self.assertEqual(self.detector.detect("Cho tôi một phần cơm tấm sườn nhiều mỡ"), [])

    def test_cholesterol_triggers_heart(self):
        self.assertIn("High_Fat", self.detector.detect("cholesterol cao nguy hiểm"))

    def test_result_is_list_of_strings(self):
        for tag in self.detector.detect("tiểu đường"):
            self.assertIsInstance(tag, str)

    def test_no_duplicate_risks_multi_disease(self):
        result = self.detector.detect("tiểu đường gout suy tim suy thận")
        self.assertEqual(len(result), len(set(result)))

    def test_cao_huyet_ap_triggers_heart(self):
        self.assertIn("High_Sodium", self.detector.detect("cao huyết áp"))

    def test_benh_than_triggers_kidney(self):
        self.assertIn("High_Protein", self.detector.detect("bệnh thận mạn tính"))

    def test_comma_list_of_diseases(self):
        rs = set(self.detector.detect("tiểu đường, gout, suy tim"))
        self.assertIn("High_Sugar", rs)
        self.assertIn("Red_Meat", rs)
        self.assertIn("High_Fat", rs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
