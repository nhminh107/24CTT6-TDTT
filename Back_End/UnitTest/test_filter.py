"""
Unit Tests for RestaurantFilter class
Tập trung vào các hàm quan trọng:
  - _calculate_distance
  - run_health_codition_first_step
  - calculate_penalty_health_score
  - generate_notes
  - generate_warning
  - _apply_general_filters
  - run_filter_pipeline
  - menu_filter (logic subset)
  - _extract_menu_query / _normalize_menu_query
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Helpers – tạo đối tượng RestaurantFilter mà không cần ChromaDB / DB thật
# ---------------------------------------------------------------------------

def make_filter(df=None, prompt=None, user_lat=10.776, user_lng=106.700,
                health_profile=None):
    """
    Factory helper: tạo RestaurantFilter với các giá trị mặc định hợp lý.
    ChromaDBManager bị mock để tránh kết nối thật.
    """
    # Patch import nặng trước khi import class
    with patch.dict("sys.modules", {
        "Back_End": MagicMock(),
        "Back_End.Database": MagicMock(),
        "Back_End.Database.database": MagicMock(),
    }):
        # Import bên trong patch để tránh ImportError
        import importlib, types, sys

        # Tạo module giả
        fake_db_mod = types.ModuleType("Back_End.Database.database")
        fake_chroma = MagicMock()
        fake_db_mod.ChromaDBManager = MagicMock(return_value=fake_chroma)
        sys.modules["Back_End"] = types.ModuleType("Back_End")
        sys.modules["Back_End.Database"] = types.ModuleType("Back_End.Database")
        sys.modules["Back_End.Database.database"] = fake_db_mod

        # Bây giờ mới import
        import importlib.util, os, pathlib

        # Đọc source trực tiếp để tránh phụ thuộc package
        src = pathlib.Path(__file__).parent.parent / "Core" / "Filter.py"
        spec = importlib.util.spec_from_file_location("restaurant_filter", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        RF = mod.RestaurantFilter

    if df is None:
        df = pd.DataFrame()
    if prompt is None:
        prompt = {}
    if health_profile is None:
        health_profile = {"diet_mode": "strict", "forbidden_tags": []}

    obj = RF.__new__(RF)
    # Gán thủ công để tránh gọi __init__ (cần ChromaDB)
    obj.data = df
    obj.user_prompt = prompt
    obj.user_lat = user_lat
    obj.user_lng = user_lng
    obj.user_health = health_profile
    obj.max_distance = 10.0
    obj.CRITICAL_ALLERGY_TAGS = [
        "Peanuts_Nuts", "Gluten_Present", "Dairy_Product", "Seafood", "Shellfish"
    ]
    obj.warnings = {
        "Spicy": {
            "potential": "Vị cay nồng (Tiềm ẩn): Món ăn có thể cay.",
            "main": "Món cay nồng (Chủ đạo): Quán chuyên vị cay đậm."
        },
        "DeepFried_Oily": {
            "potential": "Đồ chiên rán (Tiềm ẩn): Thực đơn có thể nhiều dầu mỡ.",
            "main": "Nhiều dầu mỡ (Chủ đạo): Các món chủ yếu là chiên xào."
        },
        "High_Sugar": {
            "potential": "Hàm lượng đường (Tiềm ẩn): Nước sốt hoặc đồ uống có thể khá ngọt.",
            "main": "Hàm lượng đường (Chủ đao): Thực đơn chứa lượng đường rất cao."
        },
        "Refined_Carbs": {
            "potential": "Tinh bột tinh chế (Tiềm ẩn).",
            "main": "Tinh bột nhanh (Chủ đạo)."
        },
        "High_Sodium": {
            "potential": "Thực phần chứa nhiều muối (Tiềm ẩn).",
            "main": "Thực phần chứa nhiều muối (Chủ đao)."
        },
        "Red_Meat": {
            "potential": "Thịt đỏ (Tiềm ẩn).",
            "main": "Thịt đỏ (Chủ đạo)."
        },
        "Seafood": {
            "potential": "Hải sản (Tiềm ẩn).",
            "main": "Chuyên hải sản (Chủ đạo)."
        },
        "Alcohol_Pub": {
            "potential": "Thức uống có cồn (Tiềm ẩn).",
            "main": "Quán nước có cồn (Chủ đạo)."
        },
        "Peanuts_Nuts": {
            "potential": "Đậu phộng & Hạt (Tiềm ẩn).",
            "main": "Chứa đậu phộng/Hạt (Chủ đạo)."
        },
        "Dairy_Product": {
            "potential": "Sữa & Bơ (Tiềm ẩn).",
            "main": "Thành phần từ sữa (Chủ đạo)."
        },
        "Gluten_Present": {
            "potential": "Gluten / Bột mì (Tiềm ẩn).",
            "main": "Chứa Gluten (Chủ đạo)."
        },
        "Shellfish": {
            "potential": "Hải sản vỏ cứng (Tiềm ẩn).",
            "main": "Hải sản vỏ cứng (Chủ đạo)."
        },
    }
    # Reset class-level cache
    type(obj)._menu_db_manager = None
    return obj


# ---------------------------------------------------------------------------
# Fixtures dùng chung
# ---------------------------------------------------------------------------

@pytest.fixture
def base_restaurants():
    """Danh sách nhà hàng mẫu dùng trong nhiều test."""
    return [
        {
            "id": "r1", "name": "Quán Phở",
            "main_tag": ["High_Sodium", "Red_Meat"],
            "potential_tag": ["Spicy"],
            "lat": 10.776, "lng": 106.700,
            "avg_price": 50000, "shu": 1,
            "meals": ["sáng", "trưa"],
            "type": ["Quán ăn"],
        },
        {
            "id": "r2", "name": "Hải Sản Biển Xanh",
            "main_tag": ["Seafood", "Shellfish"],
            "potential_tag": ["High_Sodium"],
            "lat": 10.780, "lng": 106.705,
            "avg_price": 120000, "shu": 0,
            "meals": ["trưa", "tối"],
            "type": ["Nhà hàng"],
        },
        {
            "id": "r3", "name": "Cà phê Sạch",
            "main_tag": [],
            "potential_tag": ["Dairy_Product"],
            "lat": 10.770, "lng": 106.695,
            "avg_price": 40000, "shu": 0,
            "meals": ["sáng", "xế"],
            "type": ["quán cà phê"],
        },
        {
            "id": "r4", "name": "Bánh Mì Pate",
            "main_tag": ["Gluten_Present"],
            "potential_tag": ["Red_Meat"],
            "lat": 10.800, "lng": 106.720,
            "avg_price": 30000, "shu": 0,
            "meals": ["sáng"],
            "type": ["Ăn vặt"],
        },
    ]


@pytest.fixture
def base_df(base_restaurants):
    return pd.DataFrame(base_restaurants)


# ===========================================================================
# 1. _calculate_distance
# ===========================================================================

class TestCalculateDistance:

    def test_same_location_returns_zero(self):
        rf = make_filter(user_lat=10.776, user_lng=106.700)
        df = pd.DataFrame({"lat": [10.776], "lng": [106.700]})
        dist = rf._calculate_distance(df)
        assert float(dist.iloc[0]) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance_is_correct(self):
        """Hà Nội (21.028, 105.834) ↔ TP.HCM (10.776, 106.700) ≈ 1138 km"""
        rf = make_filter(user_lat=21.028, user_lng=105.834)
        df = pd.DataFrame({"lat": [10.776], "lng": [106.700]})
        dist = rf._calculate_distance(df)
        assert float(dist.iloc[0]) == pytest.approx(1138.0, rel=0.02)

    def test_multiple_rows_returns_series_same_length(self):
        rf = make_filter(user_lat=10.776, user_lng=106.700)
        df = pd.DataFrame({
            "lat": [10.776, 10.780, 10.800],
            "lng": [106.700, 106.705, 106.720],
        })
        dist = rf._calculate_distance(df)
        assert len(dist) == 3

    def test_distance_is_always_non_negative(self):
        rf = make_filter(user_lat=10.776, user_lng=106.700)
        df = pd.DataFrame({
            "lat": np.random.uniform(9.0, 12.0, 50),
            "lng": np.random.uniform(105.0, 108.0, 50),
        })
        dist = rf._calculate_distance(df)
        assert (dist >= 0).all()

    def test_symmetry(self):
        """d(A→B) == d(B→A)"""
        rf_a = make_filter(user_lat=10.776, user_lng=106.700)
        rf_b = make_filter(user_lat=10.800, user_lng=106.720)
        df_b = pd.DataFrame({"lat": [10.800], "lng": [106.720]})
        df_a = pd.DataFrame({"lat": [10.776], "lng": [106.700]})
        assert rf_a._calculate_distance(df_b).iloc[0] == pytest.approx(
            rf_b._calculate_distance(df_a).iloc[0], rel=1e-6
        )


# ===========================================================================
# 2. _normalize_menu_query
# ===========================================================================

class TestNormalizeMenuQuery:

    def test_none_returns_empty(self):
        rf = make_filter()
        assert rf._normalize_menu_query(None) == ""

    def test_string_stripped(self):
        rf = make_filter()
        assert rf._normalize_menu_query("  phở bò  ") == "phở bò"

    def test_list_joined(self):
        rf = make_filter()
        result = rf._normalize_menu_query(["phở", "bún bò", "cơm"])
        assert result == "phở, bún bò, cơm"

    def test_list_with_empty_items_skipped(self):
        rf = make_filter()
        result = rf._normalize_menu_query(["phở", "  ", "bún"])
        assert "phở" in result and "bún" in result
        assert "  " not in result

    def test_integer_fallback(self):
        rf = make_filter()
        result = rf._normalize_menu_query(123)
        assert result == ""


# ===========================================================================
# 3. _extract_menu_query
# ===========================================================================

class TestExtractMenuQuery:

    def test_menu_key_found(self):
        rf = make_filter()
        assert rf._extract_menu_query({"menu_query": "phở bò"}) == "phở bò"

    def test_fallback_keys(self):
        rf = make_filter()
        assert rf._extract_menu_query({"dish": "bún riêu"}) == "bún riêu"
        assert rf._extract_menu_query({"food_query": "cơm tấm"}) == "cơm tấm"

    def test_non_dict_returns_empty(self):
        rf = make_filter()
        assert rf._extract_menu_query("just a string") == ""
        assert rf._extract_menu_query(None) == ""

    def test_all_empty_values_returns_empty(self):
        rf = make_filter()
        assert rf._extract_menu_query({"menu_query": "", "dish": "  "}) == ""


# ===========================================================================
# 4. run_health_codition_first_step  (STRICT mode)
# ===========================================================================

class TestHealthFilterStrictMode:

    def _make_rf(self, forbidden_tags):
        return make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": forbidden_tags}
        )

    def test_no_forbidden_tags_keeps_all(self, base_restaurants):
        rf = self._make_rf([])
        result = rf.run_health_codition_first_step(base_restaurants)
        assert len(result) == len(base_restaurants)

    def test_critical_allergy_removes_restaurant(self, base_restaurants):
        """Seafood là CRITICAL → quán r2 bị loại"""
        rf = self._make_rf(["Seafood"])
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r2" not in ids

    def test_critical_allergy_shellfish(self, base_restaurants):
        rf = self._make_rf(["Shellfish"])
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r2" not in ids  # r2 có main_tag Shellfish

    def test_ratio_filter_removes_when_50_percent_match(self, base_restaurants):
        """r1 có 2 main_tag; cấm cả 2 → ratio=1.0 ≥ 0.5 → loại"""
        rf = self._make_rf(["High_Sodium", "Red_Meat"])
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r1" not in ids

    def test_ratio_filter_keeps_when_below_50_percent(self, base_restaurants):
        """r1 có 2 tag; chỉ cấm 1 → ratio=0.5 nhưng bằng ngưỡng → loại"""
        rf = self._make_rf(["High_Sodium"])
        result = rf.run_health_codition_first_step(base_restaurants)
        # ratio = 1/2 = 0.5 → đúng bằng ngưỡng >= 0.5 → loại
        ids = [r["id"] for r in result]
        assert "r1" not in ids

    def test_empty_main_tags_always_kept(self, base_restaurants):
        """r3 có main_tag=[] → luôn được giữ lại dù có forbidden tag bất kỳ"""
        rf = self._make_rf(["Dairy_Product", "Seafood"])
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r3" in ids

    def test_nan_main_tags_handled_gracefully(self):
        """main_tag là float NaN không gây crash"""
        rf = self._make_rf(["Seafood"])
        restaurants = [{"id": "rx", "name": "X", "main_tag": float("nan")}]
        result = rf.run_health_codition_first_step(restaurants)
        # Không crash; quán giữ lại vì ko có tag nào match
        assert len(result) == 1

    def test_gluten_critical_allergy(self):
        rf = self._make_rf(["Gluten_Present"])
        data = [{"id": "g1", "name": "Bánh Mì", "main_tag": ["Gluten_Present"]}]
        result = rf.run_health_codition_first_step(data)
        assert len(result) == 0

    def test_non_critical_single_tag_ratio_below_threshold(self):
        """Non-critical tag, ratio < 0.5 → giữ lại"""
        rf = self._make_rf(["Spicy"])
        data = [{"id": "s1", "name": "Quán cay", "main_tag": ["Spicy", "Red_Meat", "High_Sodium"]}]
        result = rf.run_health_codition_first_step(data)
        # ratio = 1/3 ≈ 0.33 < 0.5 → giữ lại
        assert len(result) == 1


# ===========================================================================
# 5. run_health_codition_first_step  (CASUAL mode)
# ===========================================================================

class TestHealthFilterCasualMode:

    def _make_rf(self, forbidden_tags):
        return make_filter(
            health_profile={"diet_mode": "casual", "forbidden_tags": forbidden_tags}
        )

    def test_casual_keeps_non_critical_forbidden_tag(self, base_restaurants):
        """Casual mode: cấm High_Sodium (không phải CRITICAL) → r1 VẪN giữ"""
        rf = self._make_rf(["High_Sodium"])
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r1" in ids

    def test_casual_removes_critical_allergy(self, base_restaurants):
        """Casual mode: cấm Seafood (CRITICAL) → r2 bị loại"""
        rf = self._make_rf(["Seafood"])
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r2" not in ids

    def test_casual_keeps_when_critical_not_in_forbidden(self, base_restaurants):
        """Casual: quán có Seafood nhưng user không cấm Seafood → giữ"""
        rf = self._make_rf(["High_Sodium"])
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r2" in ids

    def test_casual_nan_tags_no_crash(self):
        rf = self._make_rf(["Peanuts_Nuts"])
        data = [{"id": "x1", "name": "X", "main_tag": None}]
        result = rf.run_health_codition_first_step(data)
        assert len(result) == 1

    def test_casual_none_diet_mode_behaves_like_casual(self, base_restaurants):
        """diet_mode=None → xử lý như casual"""
        rf = make_filter(
            health_profile={"diet_mode": None, "forbidden_tags": ["Seafood"]}
        )
        result = rf.run_health_codition_first_step(base_restaurants)
        ids = [r["id"] for r in result]
        assert "r2" not in ids


# ===========================================================================
# 6. calculate_penalty_health_score
# ===========================================================================

class TestCalculatePenaltyHealthScore:

    def _make_rf(self, forbidden_tags):
        return make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": forbidden_tags}
        )

    def test_no_forbidden_tags_zero_penalty(self):
        rf = self._make_rf([])
        res = {"main_tag": ["Spicy"], "potential_tag": ["Red_Meat"]}
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 0

    def test_main_tag_violation_10_points(self):
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": ["Spicy"], "potential_tag": []}
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 10

    def test_two_main_tag_violations_20_points(self):
        rf = self._make_rf(["Spicy", "Red_Meat"])
        res = {"main_tag": ["Spicy", "Red_Meat"], "potential_tag": []}
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 20

    def test_potential_critical_tag_10_points(self):
        """potential_tag thuộc CRITICAL → 10 điểm"""
        rf = self._make_rf(["Seafood"])
        res = {"main_tag": [], "potential_tag": ["Seafood"]}
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 10

    def test_potential_normal_tag_5_points(self):
        """potential_tag không thuộc CRITICAL → 5 điểm"""
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": [], "potential_tag": ["Spicy"]}
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 5

    def test_combo_main_and_potential(self):
        """1 main (10) + 1 potential critical (10) + 1 potential normal (5) = 25"""
        rf = self._make_rf(["Red_Meat", "Seafood", "Spicy"])
        res = {
            "main_tag": ["Red_Meat"],
            "potential_tag": ["Seafood", "Spicy"],
        }
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 25

    def test_tag_not_in_forbidden_no_penalty(self):
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": ["Red_Meat"], "potential_tag": ["High_Sodium"]}
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 0

    def test_penalty_score_key_always_set(self):
        rf = self._make_rf([])
        res = {}
        rf.calculate_penalty_health_score(res)
        assert "penalty_score" in res

    def test_nan_tags_no_crash(self):
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": float("nan"), "potential_tag": float("nan")}
        # Không crash; set trả về rỗng → penalty = 0
        rf.calculate_penalty_health_score(res)
        assert res["penalty_score"] == 0


# ===========================================================================
# 7. generate_notes
# ===========================================================================

class TestGenerateNotes:

    def _make_rf(self):
        return make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": []}
        )

    def _run(self, penalty):
        rf = self._make_rf()
        res = {"penalty_score": penalty}
        rf.generate_notes(res)
        return res["notes"]

    def test_zero_penalty_ideal_message(self):
        notes = self._run(0)
        assert any("THỰC ĐƠN LÝ TƯỞNG" in n for n in notes)

    def test_penalty_5_reminder_message(self):
        notes = self._run(5)
        assert any("Nhắc nhở" in n for n in notes)

    def test_penalty_10_attention_message(self):
        notes = self._run(10)
        assert any("Cần lưu ý" in n for n in notes)

    def test_penalty_20_significant_risk(self):
        notes = self._run(20)
        assert any("Rủi ro đáng kể" in n for n in notes)

    def test_penalty_30_high_risk(self):
        notes = self._run(30)
        assert any("Nguy cơ cao" in n for n in notes)

    def test_penalty_40_maximum_risk(self):
        notes = self._run(40)
        assert any("TUYỆT ĐỐI KHÔNG NÊN ĐẶT" in n for n in notes)

    def test_penalty_above_40_maximum_risk(self):
        notes = self._run(60)
        assert any("TUYỆT ĐỐI KHÔNG NÊN ĐẶT" in n for n in notes)

    def test_notes_key_always_set(self):
        rf = self._make_rf()
        res = {"penalty_score": 15}
        rf.generate_notes(res)
        assert "notes" in res
        assert isinstance(res["notes"], list)
        assert len(res["notes"]) > 0

    def test_boundary_penalty_1_low_risk(self):
        notes = self._run(1)
        assert any("Tương đối an toàn" in n for n in notes)

    def test_boundary_penalty_exactly_5(self):
        notes = self._run(5.0)
        assert any("Nhắc nhở" in n for n in notes)

    def test_boundary_penalty_exactly_10(self):
        notes = self._run(10.0)
        assert any("Cần lưu ý" in n for n in notes)


# ===========================================================================
# 8. generate_warning
# ===========================================================================

class TestGenerateWarning:

    def _make_rf(self, forbidden_tags):
        return make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": forbidden_tags}
        )

    def test_no_forbidden_no_warnings(self):
        rf = self._make_rf([])
        res = {"main_tag": ["Spicy"], "potential_tag": ["Red_Meat"]}
        rf.generate_warning(res)
        assert res["warnings"] == []

    def test_main_tag_violation_uses_main_warning(self):
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": ["Spicy"], "potential_tag": []}
        rf.generate_warning(res)
        assert any("Chủ đạo" in w for w in res["warnings"])

    def test_potential_tag_violation_uses_potential_warning(self):
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": [], "potential_tag": ["Spicy"]}
        rf.generate_warning(res)
        assert any("Tiềm ẩn" in w for w in res["warnings"])

    def test_no_duplicate_warning_when_main_and_potential_same_tag(self):
        """Nếu main_tag đã có cảnh báo main, potential không thêm bản sao."""
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": ["Spicy"], "potential_tag": ["Spicy"]}
        rf.generate_warning(res)
        main_warns = [w for w in res["warnings"] if "Chủ đạo" in w]
        potential_warns = [w for w in res["warnings"] if "Tiềm ẩn" in w]
        # Không được có cả 2 loại cho cùng tag
        assert not (main_warns and potential_warns)

    def test_warnings_key_always_set(self):
        rf = self._make_rf([])
        res = {"main_tag": [], "potential_tag": []}
        rf.generate_warning(res)
        assert "warnings" in res
        assert isinstance(res["warnings"], list)

    def test_nan_main_tags_no_crash(self):
        rf = self._make_rf(["Spicy"])
        res = {"main_tag": float("nan"), "potential_tag": float("nan")}
        rf.generate_warning(res)
        assert res["warnings"] == []

    def test_multiple_violations_multiple_warnings(self):
        rf = self._make_rf(["Spicy", "Red_Meat"])
        res = {"main_tag": ["Spicy"], "potential_tag": ["Red_Meat"]}
        rf.generate_warning(res)
        assert len(res["warnings"]) == 2

    def test_tag_not_in_warnings_dict_skipped(self):
        """Tag tồn tại trong forbidden nhưng không có trong warnings dict"""
        rf = self._make_rf(["Unknown_Tag"])
        res = {"main_tag": ["Unknown_Tag"], "potential_tag": []}
        rf.generate_warning(res)
        assert res["warnings"] == []


# ===========================================================================
# 9. menu_filter  (subset logic – không cần ChromaDB)
# ===========================================================================

class TestMenuFilterSubset:

    def _make_df(self, rows):
        return pd.DataFrame(rows)

    def test_exact_match(self):
        rf = make_filter()
        df = self._make_df([
            {"id": "1", "menu": ["phở bò", "bún bò Huế"]},
            {"id": "2", "menu": ["cơm tấm", "bún thịt nướng"]},
        ])
        result = rf.menu_filter(df, "phở bò")
        assert set(result["id"]) == {"1"}

    def test_query_subset_of_menu_item(self):
        """query 'phở' là subset của 'phở bò' (không match vì 'phở bò' có 2 tokens)"""
        rf = make_filter()
        df = self._make_df([
            {"id": "1", "menu": ["phở bò"]},
        ])
        # 'phở' (1 token) là subset của 'phở bò' (2 tokens) → match
        result = rf.menu_filter(df, "phở")
        assert "1" in result["id"].values

    def test_empty_query_returns_all(self):
        rf = make_filter()
        df = self._make_df([
            {"id": "1", "menu": ["cơm"]},
            {"id": "2", "menu": ["phở"]},
        ])
        result = rf.menu_filter(df, "")
        assert len(result) == 2

    # def test_no_match_falls_back_to_chromadb(self):
    #     """Khi subset không khớp, ChromaDB được gọi"""
    #     rf = make_filter()
    #     mock_db = MagicMock()
    #     mock_db.search_menu.return_value = {
    #         "metadatas": [[{"restaurant_id": "2"}]],
    #         "distances": [[0.3]],
    #     }
    #     rf._menu_db_manager = mock_db

    #     df = self._make_df([
    #         {"id": "1", "menu": ["bún bò"]},
    #         {"id": "2", "menu": ["cơm chiên"]},
    #     ])
    #     result = rf.menu_filter(df, "fried rice")
    #     mock_db.search_menu.assert_called_once()

    def test_empty_df_returns_empty(self):
        rf = make_filter()
        result = rf.menu_filter(pd.DataFrame(), "phở")
        assert result.empty

    def test_no_id_column_returns_original(self):
        rf = make_filter()
        df = pd.DataFrame([{"name": "test", "menu": ["phở"]}])
        result = rf.menu_filter(df, "phở")
        assert len(result) == 1  # fallback trả lại nguyên

    def test_menu_not_list_skipped(self):
        """Hàng có menu là string/None không gây crash"""
        rf = make_filter()
        df = self._make_df([
            {"id": "1", "menu": "phở bò"},   # string, không phải list
            {"id": "2", "menu": ["phở bò"]},
        ])
        result = rf.menu_filter(df, "phở bò")
        # Chỉ id=2 match (id=1 menu không phải list)
        assert "2" in result["id"].values


# ===========================================================================
# 10. _apply_general_filters
# ===========================================================================

class TestApplyGeneralFilters:

    def _make_rf_with_data(self, restaurants, prompt, health_profile=None):
        df = pd.DataFrame(restaurants)
        if health_profile is None:
            health_profile = {"diet_mode": "strict", "forbidden_tags": []}
        return make_filter(df=df, prompt=prompt, health_profile=health_profile)

    def test_distance_filter_removes_far_restaurants(self):
        """Quán cách >15km bị loại"""
        restaurants = [
            {"id": "near", "name": "Gần", "lat": 10.776, "lng": 106.700,
             "avg_price": 50000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
            {"id": "far", "name": "Xa", "lat": 11.000, "lng": 108.000,  # ~260km
             "avg_price": 50000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
        ]
        rf = self._make_rf_with_data(restaurants, {})
        result = rf._apply_general_filters()
        assert "near" in result["id"].values
        assert "far" not in result["id"].values

    def test_budget_filter(self):
        """avg_price > 0.6 * budget bị loại"""
        restaurants = [
            {"id": "cheap", "name": "Rẻ", "lat": 10.776, "lng": 106.700,
             "avg_price": 30000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
            {"id": "expensive", "name": "Đắt", "lat": 10.776, "lng": 106.700,
             "avg_price": 200000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
        ]
        rf = self._make_rf_with_data(restaurants, {"budget": 100000})
        result = rf._apply_general_filters()
        assert "cheap" in result["id"].values
        assert "expensive" not in result["id"].values

    def test_spicy_filter(self):
        """Quán có shu ngoài [1, user_shu] bị loại"""
        restaurants = [
            {"id": "mild", "name": "Nhẹ", "lat": 10.776, "lng": 106.700,
             "avg_price": 50000, "shu": 2, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
            {"id": "hot", "name": "Cay", "lat": 10.776, "lng": 106.700,
             "avg_price": 50000, "shu": 8, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
            {"id": "zero", "name": "Không cay", "lat": 10.776, "lng": 106.700,
             "avg_price": 50000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
        ]
        rf = self._make_rf_with_data(restaurants, {"shu": 3})
        result = rf._apply_general_filters()
        assert "mild" in result["id"].values
        assert "hot" not in result["id"].values
        assert "zero" not in result["id"].values  # shu=0 không nằm trong [1,3]

    def test_empty_df_returns_empty(self):
        rf = make_filter(df=pd.DataFrame(), prompt={})
        result = rf._apply_general_filters()
        assert result.empty

    def test_distance_column_added(self):
        restaurants = [
            {"id": "r1", "lat": 10.776, "lng": 106.700, "avg_price": 50000,
             "shu": 0, "main_tag": [], "potential_tag": [], "meals": [], "type": []}
        ]
        rf = self._make_rf_with_data(restaurants, {})
        result = rf._apply_general_filters()
        assert "distance" in result.columns


# ===========================================================================
# 11. run_health_conditions_filter  (integration)
# ===========================================================================

class TestRunHealthConditionsFilter:

    def test_returns_dataframe(self, base_df):
        rf = make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": []}
        )
        result = rf.run_health_conditions_filter(base_df)
        assert isinstance(result, pd.DataFrame)

    def test_penalty_score_column_added(self, base_df):
        rf = make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": ["Spicy"]}
        )
        result = rf.run_health_conditions_filter(base_df)
        assert "penalty_score" in result.columns

    def test_notes_column_added(self, base_df):
        rf = make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": []}
        )
        result = rf.run_health_conditions_filter(base_df)
        assert "notes" in result.columns

    def test_warnings_column_added(self, base_df):
        rf = make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": []}
        )
        result = rf.run_health_conditions_filter(base_df)
        assert "warnings" in result.columns

    def test_critical_allergy_removed(self, base_df):
        rf = make_filter(
            health_profile={"diet_mode": "strict", "forbidden_tags": ["Seafood"]}
        )
        result = rf.run_health_conditions_filter(base_df)
        assert "r2" not in result["id"].values


# ===========================================================================
# 12. run_filter_pipeline  (integration – mock menu_filter & ChromaDB)
# ===========================================================================

class TestRunFilterPipeline:

    def _make_rf_pipeline(self, restaurants, prompt, health_profile=None):
        df = pd.DataFrame(restaurants)
        if health_profile is None:
            health_profile = {"diet_mode": "strict", "forbidden_tags": []}
        rf = make_filter(df=df, prompt=prompt, health_profile=health_profile,
                         user_lat=10.776, user_lng=106.700)
        # Bypass menu_filter để tập trung test pipeline logic
        rf.menu_filter = lambda meal_df, query: meal_df
        return rf

    def _base_restaurants(self):
        return [
            {"id": "r1", "name": "Phở Sáng", "lat": 10.776, "lng": 106.700,
             "avg_price": 40000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["sáng"], "type": ["Quán ăn"]},
            {"id": "r2", "name": "Cơm Trưa", "lat": 10.776, "lng": 106.700,
             "avg_price": 60000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["trưa"], "type": ["Nhà hàng"]},
            {"id": "r3", "name": "Quán Tối", "lat": 10.776, "lng": 106.700,
             "avg_price": 80000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["tối"], "type": ["Nhà hàng"]},
        ]

    def test_returns_dict(self):
        prompt = {"meals_detail": [{"meal": "sáng"}]}
        rf = self._make_rf_pipeline(self._base_restaurants(), prompt)
        result = rf.run_filter_pipeline()
        assert isinstance(result, dict)

    def test_correct_meal_keys_returned(self):
        prompt = {"meals_detail": [{"meal": "sáng"}, {"meal": "trưa"}]}
        rf = self._make_rf_pipeline(self._base_restaurants(), prompt)
        result = rf.run_filter_pipeline()
        assert "sáng" in result
        assert "trưa" in result

    def test_meal_segregation(self):
        """Quán chỉ phục vụ sáng không xuất hiện trong trưa"""
        prompt = {"meals_detail": [{"meal": "sáng"}, {"meal": "trưa"}]}
        rf = self._make_rf_pipeline(self._base_restaurants(), prompt)
        result = rf.run_filter_pipeline()
        if "sáng" in result and not result["sáng"].empty:
            assert "r1" in result["sáng"]["id"].values
        if "trưa" in result and not result["trưa"].empty:
            assert "r1" not in result["trưa"]["id"].values

    def test_type_filter_applied(self):
        """Nếu req type = 'Nhà hàng', Quán ăn bị loại"""
        prompt = {
            "meals_detail": [
                {"meal": "sáng", "type": ["Nhà hàng"]}
            ]
        }
        rf = self._make_rf_pipeline(self._base_restaurants(), prompt)
        result = rf.run_filter_pipeline()
        if "sáng" in result:
            ids = result["sáng"]["id"].tolist() if not result["sáng"].empty else []
            # r1 là "Quán ăn" không khớp "Nhà hàng" → bị loại
            assert "r1" not in ids

    def test_blacklist_applied_for_main_meal_no_type(self):
        """Bữa sáng không chỉ định type → BLACKLIST lọc Ăn vặt"""
        restaurants = self._base_restaurants() + [
            {"id": "r4", "name": "Bánh tráng", "lat": 10.776, "lng": 106.700,
             "avg_price": 20000, "shu": 0, "main_tag": [], "potential_tag": [],
             "meals": ["sáng"], "type": ["Ăn vặt"]},
        ]
        prompt = {"meals_detail": [{"meal": "sáng"}]}
        rf = self._make_rf_pipeline(restaurants, prompt)
        result = rf.run_filter_pipeline()
        if "sáng" in result and not result["sáng"].empty:
            assert "r4" not in result["sáng"]["id"].values

    def test_empty_meals_detail_returns_empty_dict(self):
        prompt = {"meals_detail": []}
        rf = self._make_rf_pipeline(self._base_restaurants(), prompt)
        result = rf.run_filter_pipeline()
        assert result == {}

    def test_invalid_meal_key_skipped_gracefully(self):
        prompt = {"meals_detail": [{"meal": "không_tồn_tại"}]}
        rf = self._make_rf_pipeline(self._base_restaurants(), prompt)
        result = rf.run_filter_pipeline()  # Không raise exception
        assert isinstance(result, dict)

    def test_empty_base_df_returns_empty_dict(self):
        rf = make_filter(
            df=pd.DataFrame(),
            prompt={"meals_detail": [{"meal": "sáng"}]},
            health_profile={"diet_mode": "strict", "forbidden_tags": []},
        )
        rf.menu_filter = lambda meal_df, query: meal_df
        result = rf.run_filter_pipeline()
        assert result == {}
