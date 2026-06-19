

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
        # Sửa từ cls._tmpdir.cleanup() thành:
        if hasattr(cls, "_tmpdir") and cls._tmpdir:
            cls._tmpdir.cleanup()


class _BaseDetectorTest(_TmpDir, unittest.TestCase):
    """Base: tạo detector đầy đủ với SAMPLE data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        core_dir = Path(__file__).parent.parent / "Core" 
        
        cls.dict_path = core_dir / "health_condition_dictionary.json"
        cls.map_path  = core_dir / "health_tag_mapping.json"
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
        core_dir = Path(__file__).parent.parent / "Core" 
        
        cls.dict_path = core_dir / "health_condition_dictionary.json"
        cls.map_path  = core_dir / "health_tag_mapping.json"
        cls.detector = HealthRiskDetector(
            dictionary_path=cls.dict_path,
            mapping_path=cls.map_path,
            fuzzy_threshold=85,
            ngram_max=5,
            expand_synonyms=False,
            detect_negation=True,
        )

# ===========================================================================
# Test Suite cho Cơ chế Loại trừ Ngữ cảnh Chủ động (Exclusion Scopes)
# ===========================================================================

class TestExclusionContext(_NegationDetectorTest):
    """
    Kiểm thử cơ chế ngăn chặn gắn tag bệnh lý/dị ứng nhầm lẫn
    khi người dùng nhập các câu thể hiện nhu cầu, sở thích ăn uống chủ động.
    Sử dụng trực tiếp dữ liệu thật từ các file JSON của hệ thống.
    """

    def test_muon_an_hai_san_pass_test(self):
        """Người dùng muốn ăn hải sản chủ động -> Phải trả về mảng rỗng (Pass)."""
        prompt = "Tối nay tôi muốn ăn hải sản view biển, ngân sách 800k."
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống nhận diện được "muon an", kích hoạt Exclusion Scope
        # và bỏ qua việc gắn nhãn rủi ro liên quan đến dị ứng hải sản (Seafood/Shellfish)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu muốn ăn chủ động bị gắn nhầm tag: {detected_risks}"
        )
    def test_prompt_mau_1(self):
       
        prompt = "Tôi cần lộ trình ăn trưa, quán nước, ăn tối. Quán ăn trưa phải là quán Việt, quán ăn tối phải lãng mạn."
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống nhận diện được "muon an", kích hoạt Exclusion Scope
        # và bỏ qua việc gắn nhãn rủi ro liên quan đến dị ứng hải sản (Seafood/Shellfish)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu muốn ăn chủ động bị gắn nhầm tag: {detected_risks}"
        )
    def test_prompt_mau_2(self):
        prompt = "Bữa trưa là món Việt, bữa tối fine dining lãng mạn"
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống nhận diện được "muon an", kích hoạt Exclusion Scope
        # và bỏ qua việc gắn nhãn rủi ro liên quan đến dị ứng hải sản (Seafood/Shellfish)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu muốn ăn chủ động bị gắn nhầm tag: {detected_risks}"
        )
    def test_prompt_mau_3(self):
        prompt = "dạo này thời tiết hơi nóng, tôi cần tìm quán nước thoáng mát , quận 1, ngân sách 500k"
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống nhận diện được "muon an", kích hoạt Exclusion Scope
        # và bỏ qua việc gắn nhãn rủi ro liên quan đến dị ứng hải sản (Seafood/Shellfish)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu muốn ăn chủ động bị gắn nhầm tag: {detected_risks}"
        )
    def test_prompt_mau_4(self):
        prompt = "tôi muốn tìm quán hải sản, quận một, giá cả phải trăng, không gian thoáng mát và sạch sẽ"
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống nhận diện được "muon an", kích hoạt Exclusion Scope
        # và bỏ qua việc gắn nhãn rủi ro liên quan đến dị ứng hải sản (Seafood/Shellfish)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu muốn ăn chủ động bị gắn nhầm tag: {detected_risks}"
        )
    def test_prompt_mau_5(self):
        prompt = "tôi muốn tìm quán thái quận 1 ngân sách 600k, không gian phải yên tĩnh"
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống nhận diện được "muon an", kích hoạt Exclusion Scope
        # và bỏ qua việc gắn nhãn rủi ro liên quan đến dị ứng hải sản (Seafood/Shellfish)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu muốn ăn chủ động bị gắn nhầm tag: {detected_risks}"
        )
    def test_prompt_mau_6(self):
        prompt = "Tôi muốn tìm quán hải sản view biển ngân sách 500k"
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống nhận diện được "muon an", kích hoạt Exclusion Scope
        # và bỏ qua việc gắn nhãn rủi ro liên quan đến dị ứng hải sản (Seafood/Shellfish)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu muốn ăn chủ động bị gắn nhầm tag: {detected_risks}"
        )
    def test_prompt_mau_7(self):
        """Khách tìm lộ trình ăn cả ngày: ăn sáng, cà phê, ăn trưa -> Phải pass."""
        prompt = "Gợi ý lộ trình ăn uống cả ngày ở Đà Nẵng: ăn sáng mì quảng ngon, quán cà phê sống ảo, ăn trưa bánh tráng cuốn."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_8(self):
        """Khách tìm combo ăn xế nhẹ nhàng + trà sữa tụ tập -> Phải pass."""
        prompt = "Tìm quán ăn xế bánh tráng trộn hoặc chân gà sả tắc, xong có quán nước nào ngồi buôn chuyện được gần đây không."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_9(self):
        """Tìm quán ăn đêm sau khi đi quầy/đi pub về quanh Quận 1 -> Phải pass."""
        prompt = "Tầm này 2h đêm rồi muốn tìm quán ăn khuya, cháo sườn hoặc lẩu tôm mực quanh bùi viện quận 1 giá bình dân."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_prompt_mau_10(self):
        """Gõ sai chính tả 'giá cả phải chăng' thành 'phải trăng', 'mún ag' -> Phải pass."""
        prompt = "mún ag hải sản tươi sống ở bình thạnh, giá cả phải trăng, không gian sạch sẽ thoáng mát"
        for d in self.detector.detect_with_scores(prompt):
            print(d)
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_11(self):
        """Sử dụng từ lóng 'giá rổ', 'cành', 'ví lướt' -> Phải pass."""
        prompt = "Tìm quán nước view hồ tây chill chill, giá rổ tầm 50 cành đổ lại thui nha, ví dạo này đang xẹp."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_12(self):
        """Viết tắt, không viết hoa, dùng từ 'thik' -> Phải pass."""
        prompt = "mình thik uong trà sữa nướng hoặc trà trái cây mát lạnh, tìm quán bên q3 ngân sách dưới 100k"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_prompt_mau_13(self):
        """Tìm quán ăn gia đình có phòng riêng, yên tĩnh để nói chuyện -> Phải pass."""
        prompt = "Tôi muốn tìm nhà hàng hải sản có phòng VIP riêng tư, không gian ấm cúng, sang trọng để ăn gia đình cuối tuần."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_14(self):
        """Tìm quán nước/quán ăn mang được chó mèo theo (Pet-friendly) -> Phải pass."""
        prompt = "Kiếm quán cà phê hoặc tiệm trà bánh nào không gian thoáng mát, cho mang thú cưng vào ở khu vực Quận 7."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_15(self):
        """Nắng nóng cần tìm quán có máy lạnh/điều hòa chạy phèn phẹt -> Phải pass."""
        prompt = "Trời nóng quá cần tìm quán lẩu thái hoặc cua sốt có điều hòa mát lạnh, không gian rộng rãi sạch sẽ ở Tân Bình."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_prompt_mau_16(self):
        """Đặt tiệc sinh nhật đông người, cần quầy line buffet -> Phải pass."""
        prompt = "Cần tìm quán buffet hải sản tầm giá 400k một người, có chỗ decor tổ chức sinh nhật cho nhóm 15 người."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_17(self):
        """Tìm quán nhậu bình dân, vỉa hè để uống bia với bạn bè -> Phải pass."""
        prompt = "Tìm quán ốc vỉa hè hoặc quán nhậu hải sản bình dân ở quận 4, mồi ngon giá rẻ để ngồi lai rai với mấy chiến hữu."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_18(self):
        """Tìm nhà hàng cao cấp Fine Dining (Khuyết giá tiền nhưng có phân khúc) -> Phải pass."""
        prompt = "Gợi ý nhà hàng hải sản phong cách Âu cao cấp, phục vụ món đắt tiền, không gian lãng mạn thích hợp cầu hôn."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_prompt_mau_19(self):
        """Tìm quán Sashimi/Hàu sống kiểu Nhật -> Phải pass (Không được kích hoạt nhầm tag đồ sống)."""
        prompt = "Tôi muốn ăn sashimi hải sản tươi sống và sushi chuẩn vị Nhật, quán có không gian phòng chiếu tatami ở Quận 1."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_20(self):
        """Tìm quán ăn cay kiểu Trung Quốc/Tứ Xuyên -> Phải pass."""
        prompt = "Tìm quán lẩu cá cay Tứ Xuyên hoặc tôm hùm đất sốt cay kiểu Trung Quốc, không gian náo nhiệt, giá tầm trung."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_21(self):
        """Tìm đồ ăn Hàn Quốc kèm không gian chụp ảnh check-in -> Phải pass."""
        prompt = "Kiếm quán lẩu bạch tuộc cay kiểu Hàn Quốc có không gian decor hiện đại mạn Hoàn Kiếm, ngân sách tầm 300k."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_prompt_mau_22(self):
        """Khách hỏi xin review chất lượng nguyên liệu trước khi đặt món -> Phải pass."""
        prompt = "Nhìn menu cua sốt và tôm hùm bên mình ngon quá, không biết hải sản là đồ tươi sống bắt tại hồ hay đồ đông lạnh vậy shop?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_23(self):
        """Khách phân vân giữa hai lựa chọn, hỏi ý kiến bot -> Phải pass."""
        prompt = "Cuối tuần tụi mình định đi ăn hải sản, đang phân vân giữa quán vỉa hè Quận 4 với nhà hàng Quận 7, bên nào hợp lý hơn?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_24(self):
        """Tìm quán ăn theo định vị/bán kính 'gần đây' mà không ghi rõ địa danh -> Phải pass."""
        prompt = "Xung quanh vị trí của tôi có tiệm bánh ngọt hay quán nước nào thoáng mát, yên tĩnh để ngồi làm việc không?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_25(self):
        """Tìm quán ăn theo trào lưu, món đang trend trên mạng -> Phải pass."""
        prompt = "Tìm giùm mình mấy quán bán gỏi đu đủ ba khía hải sản sốt thái đang hot rần rần trên mạng, tiêu chí sạch sẽ."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    
    def test_prompt_mau_26(self):
        """Khách báo có người dị ứng nghiêm trọng -> Phải bắt được nguy cơ (Không được rỗng)."""
        prompt = "Tụi mình tính đi ăn buffet hải sản ở Quận 1 nhưng trong nhóm có đứa bạn bị dị ứng vỏ tôm cua cua ghẹ rất nặng."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, f"Lỗi! Khách báo dị ứng cua ghẹ nặng mà không detect được rủi ro.")

    def test_prompt_mau_27(self):
        """Khách mang bầu cần kiêng đồ sống -> Phải bắt được nguy cơ."""
        prompt = "Vợ chồng mình định đi ăn sushi Nhật Bản, quán nào đồ chín đa dạng không ạ vì vợ mình đang bầu cần kiêng hải sản sống."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, f"Lỗi! Phụ nữ mang thai kiêng đồ sống mà hệ thống bỏ qua.")

    def test_prompt_mau_28(self):
        """Khách báo đang bị đau dạ dày cần tìm món thanh đạm -> Phải bắt được nguy cơ."""
        prompt = "Dạo này mình đang bị viêm loét dạ dày nhẹ, muốn tìm quán nào có món cháo bồ câu hoặc súp thanh đạm dễ tiêu ở Quận 3."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, f"Lỗi! Đau dạ dày là từ khóa y tế, buộc phải ghi nhận rủi ro để lọc món cay/nóng.")
    def test_prompt_mau_29(self):
        """Khách sợ ăn trúng đồ ươn gây đau bụng nhưng bản chất là đang tìm quán -> Phải pass."""
        prompt = "Muốn thử ăn cái món gỏi gà măng cụt sống đang trend ghê, mà sợ mấy quán làm không sạch sẽ về đau bụng quá."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_30(self):
        """Khách lo ngại ngộ độc thực phẩm khi ăn vỉa hè nhưng vẫn xin địa chỉ -> Phải pass."""
        prompt = "Xung quanh khu ẩm thực quận 4 có quán ốc vỉa hè nào làm sạch sẽ không mọi người, dạo này đọc báo thấy ngộ độc thực phẩm ghê quá mà vẫn thèm ăn."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
        
    def test_prompt_mau_31(self):
        """Thời tiết mưa gió lạnh lẽo, tìm quán ăn đồ nóng ấm -> Phải pass."""
        prompt = "Sài Gòn chiều nay mưa lạnh quá, mình cần tìm quán lẩu bò hoặc lẩu hải sản nấm nghi ngút khói, giá tầm 300k quanh Quận 10."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_32(self):
        """Thời tiết nắng nóng, đi tìm món giải nhiệt -> Phải pass."""
        prompt = "Trời nắng nóng muốn héo người, tìm quán nước thoáng mát có máy lạnh bốc lửa hoặc tiệm kem dừa giải nhiệt gấp ở Quận 1."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_prompt_mau_33(self):
        """Kể chuyện quán cũ làm bẩn gây đau bụng để đi tìm quán mới sạch hơn -> Phải pass."""
        prompt = "Hôm trước ăn hải sản ở quán X xong về bị tào tháo rượt cả đêm. Hôm nay nhóm mình muốn tìm quán khác sạch sẽ, uy tín hơn để ăn lại, ngân sách không thành vấn đề."
        detected_risks = self.detector.detect(prompt)
        # Giải thích: Mệnh đề 1 chứa "tào tháo rượt" (bệnh), mệnh đề 2 độc lập chứa "muốn tìm quán khác... để ăn lại" -> Cơ chế tách clause v3 phải cô lập được vế sau và Pass.
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_34(self):
        """Phàn nàn về đồ ăn cũ dính dị ứng để tìm quán chuẩn organic -> Phải pass."""
        prompt = "Tôi ăn đồ nhà hàng khác hay bị ngứa ngáy nổi mề đay do chất bảo quản, tối nay tính đi ăn nhà hàng chay nào chuẩn vị sạch sẽ organic ở Quận 1 giới thiệu tôi với."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
        
    def test_prompt_mau_35(self):
        """Tìm không gian sang trọng đặt tiệc đầy tháng cho bé -> Phải pass."""
        prompt = "Nhà mình sắp làm tiệc đầy tháng cho bé, cần đặt bàn khoảng 3 bàn tiệc hải sản cao cấp, có hỗ trợ gói trang trí sân khấu tại tiệm luôn nha."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_36(self):
        """Câu troll/vui vẻ: Đi ăn với người yêu cũ cần không gian riêng -> Phải pass."""
        prompt = "Hẹn đi ăn tối với người yêu cũ, cần tìm quán ăn thái hoặc quán hải sản nào không gian tối tối lãng mạn, có phòng chia vách ngăn riêng tư ở Quận 3."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_37(self):
        """Tìm quán ăn phục vụ xuyên đêm cho cổ động viên xem bóng đá -> Phải pass."""
        prompt = "Tối nay có trận chung kết C1, nhóm mình muốn tìm quán nhậu hải sản hoặc quán bia nào có màn hình chiếu lớn và mở cửa xuyên đêm qua 2h sáng."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
        
    def test_prompt_mau_38(self):
        """Tìm đặc sản vùng miền cụ thể (Hải sản nhảy, tôm nhảy) -> Phải pass."""
        prompt = "Đang đi du lịch Quy Nhơn muốn thử trải nghiệm ăn bánh xèo tôm nhảy hoặc hải sản tươi sống bắt tại đầm ngon bổ rẻ."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_39(self):
        """Tìm quán buffet chay / Đồ ăn ăn kiêng giảm cân (Keto/Clean) -> Phải pass."""
        prompt = "Mình đang có kế hoạch ăn chế độ giảm cân eat clean, app gợi ý giùm mấy quán salad hoặc tiệm ăn chay nào ngon quanh Quận 1 ngân sách dưới 150k."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")

    def test_prompt_mau_40(self):
        """Tìm combo quà tặng kèm đồ ăn đem về -> Phải pass."""
        prompt = "Shop ơi mình muốn đặt bàn ăn tối 2 người món Âu lãng mạn, bên quán có dịch vụ chuẩn bị sẵn bánh kem sinh nhật nhỏ tặng kèm không?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    
    def test_fp_02(self):
        """Rủ bạn ăn hải sản, không kiêng cữ — Câu rủ rê, không có bệnh lý hay kiêng cữ."""
        prompt = "Tụi mình rủ nhau ra biển ăn hải sản tươi sống ngon quá trời, cua ghẹ tôm hùm đủ hết luôn!"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_fp_01(self):
        """Hỏi về món hải sản tươi sống (review chất lượng) — Khách hỏi nguyên liệu, không có bệnh lý."""
        prompt = "Nhìn menu cua sốt và tôm hùm bên mình ngon quá, không biết hải sản là đồ tươi sống bắt tại hồ hay đồ đông lạnh vậy shop?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_fp_03(self):
        """Hỏi quán có đồ chiên giòn không — Khách tìm đồ chiên vì thích ăn, không có bệnh lý."""
        prompt = "Cho mình hỏi quán có món gì chiên xào giòn giòn không? Mình đang thèm đồ chiên lắm."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
        
    def test_fp_04(self):
        """Hỏi về đồ ngọt / trà sữa — Muốn ăn ngọt vì thích, không phải tiểu đường."""
        prompt = "Gần đây có quán trà sữa hay bánh ngọt nào ngon không? Mình thích đồ ngọt lắm."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
        
    def test_fp_05(self):
        """Lịch trình du lịch bình thường — Chuyến đi không có yếu tố sức khỏe."""
        prompt = "Mình đi Đà Nẵng 3 ngày 2 đêm, muốn ăn hải sản, mỳ Quảng, bánh mì. Gợi ý quán nào ngon không?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    
    def test_fp_06(self):
        """Review quán ăn có đề cập nguyên liệu — Đề cập đến nguyên liệu như cách mô tả món, không phải kiêng cữ."""
        prompt = "Quán này nấu phở bằng xương bò hầm 12 tiếng, nước dùng không bột ngọt, đồ tươi sống 100%."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
        
    def test_fp_07(self):
        """Bạn bè nhắc nhau ăn ít đồ ngọt (không có bệnh) — Lời khuyên xã giao, không phải khai báo bệnh."""
        prompt = "Dạo này tụi mình hay nhắc nhau ăn ít đồ ngọt lại cho healthy, chứ không bệnh gì đâu."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    
    def test_fp_08(self):
        """Nhắc đến huyết áp trong ngữ cảnh quan tâm sức khỏe chung — Nói chuyện về sức khỏe chung, không phải bệnh nhân."""
        prompt = "Mọi người hay nói huyết áp cao là do ăn mặn, nên mình cũng tập ăn nhạt hơn cho khỏe."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    def test_fn_09(self):
        """Huyết áp cao kiêng mặn — Tăng huyết áp, bác sĩ dặn ăn nhạt."""
        prompt = "Ba mình tăng huyết áp, bác sĩ dặn phải ăn nhạt giảm muối, không ăn đồ mặn. Gợi ý quán cơm ít muối."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sodium", detected_risks)
    
    def test_fp_10(self):
        """Ăn chay theo tôn giáo, không phải bệnh lý — Ăn chay vì tín ngưỡng, không liên quan sức khỏe."""
        prompt = "Mình ăn chay trường theo đạo Phật, tìm quán buffet chay ngon gần Quận 5."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị gắn nhầm tag: {detected_risks}")
    
    def test_prompt_mau_41(self):
        """Khách ăn chay nhưng bị đau dạ dày -> Phải nhận diện được tag nguy cơ đồ cay (Spicy)."""
        prompt = "tôi là người ăn chay nhưng bị đau dạ dày"
        detected_risks = self.detector.detect(prompt)
        
        # Mong đợi: Hệ thống phải phát hiện ra rủi ro cho người đau dạ dày
        self.assertTrue(
            len(detected_risks) > 0, 
            "Thất bại! Khách khai báo bị đau dạ dày nhưng hệ thống không phát hiện rủi ro nào."
        )
        
        # Kiểm tra xem tag 'Spicy' (hoặc tag tương ứng của nhóm bạn) có nằm trong list rủi ro không
        # Lưu ý: Thay chữ 'Spicy' bằng chính xác Tên Tag đồ cay trong file JSON/Dictionary của nhóm bạn
        expected_tag = "Spicy" 
        self.assertIn(
            expected_tag, detected_risks, 
            f"Thất bại! Đau dạ dày phải cảnh báo tag '{expected_tag}'. Danh sách hiện tại: {detected_risks}"
        )
    def test_fn_01(self):
        """Tiểu đường thai kỳ kiêng ngọt — Phụ nữ mang thai bị tiểu đường thai kỳ."""
        prompt = "Mình đang mang thai tháng thứ 6, bị tiểu đường thai kỳ, bác sĩ dặn kiêng đồ ngọt và tinh bột."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(all(t in detected_risks for t in ["High_Sugar","Refined_Carbs"]), f"Thiếu tag: {detected_risks}")
    
    
    def test_fn_02(self):
        """Dị ứng đậu phộng nặng khi gọi món — Dặn dò quán về dị ứng nghiêm trọng."""
        prompt = "Mình bị dị ứng đậu phộng rất nặng, sốc phản vệ luôn, nhờ nhà bếp không cho bất kỳ loại lạc nào vào món nhé."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Peanuts_Nuts", detected_risks)
    
    def test_fn_03(self):
        """Mỡ máu cao tránh đồ chiên — Bệnh nền mỡ máu cao, cần tránh đồ chiên xào."""
        prompt = "Gia đình 4 người đi du lịch ghé Quận 1 ăn trưa món Âu, tối ăn đặc sản Nam Bộ mà mẹ mình bị mỡ máu cao nên cần tránh mấy món chiên xào nhiều dầu mỡ."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("DeepFried_Oily", detected_risks)
   
    def test_fn_04(self):
        """Bác sĩ dặn kiêng hải sản tươi sống — Lịch kết hợp kiêng cữ đồ sống theo chỉ định y tế."""
        prompt = "Sáng ăn hủ tiếu, trưa ăn đồ Nhật sashimi cá hồi ở Quận 3, bác sĩ dặn phải kiêng tuyệt đối đồ sống hải sản tươi sống."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(all(t in detected_risks for t in ["Seafood","Shellfish"]), f"Thiếu tag: {detected_risks}")
    
    def test_fn_05(self):
        """Gout kiêng hải sản và thịt đỏ — Bệnh nhân gout khai bệnh và kiêng cữ."""
        prompt = "Mình đang bị bệnh gout, bác sĩ bắt kiêng hải sản, thịt đỏ và rượu bia. Gợi ý quán ăn phù hợp."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(all(t in detected_risks for t in ["Seafood","Shellfish","Red_Meat","Alcohol_Pub"]), f"Thiếu tag: {detected_risks}")
    
    
    def test_fn_06(self):
        """Không dung nạp lactose — Uống sữa bị tiêu chảy, không dung nạp lactose."""
        prompt = "Mình uống sữa hay bị đau bụng tiêu chảy, bị bất dung nạp lactose, nhờ không bỏ phô mai hay kem vào món giúp mình."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Dairy_Product", detected_risks)
    
    def test_fn_07(self):
        """Dị ứng gluten - celiac — Bệnh celiac, cần tránh lúa mì."""
        prompt = "Mình bị bệnh celiac nên phải ăn gluten free hoàn toàn, không ăn được bột mì, bánh mì, mì gói."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Gluten_Present", detected_risks)
    
    def test_fn_08(self):
        prompt = "Dạ dày mình yếu lắm, ăn đồ cay là đau bụng ngay, nhờ gợi ý món không cay và không chiên nhiều dầu."
        
        from unidecode import unidecode
        import re
        normalized = prompt.lower()
        normalized = unidecode(normalized)
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        print("Normalized:", normalized)
        
        tokens = normalized.split()
        print("Tokens:", tokens)
        
        for d in self.detector.detect_with_scores(prompt):
            print("Match:", d)
        
        detected_risks = self.detector.detect(prompt)
        print("Final risks:", detected_risks)
        self.assertTrue(all(t in detected_risks for t in ["Spicy","DeepFried_Oily"]), f"Thiếu tag: {detected_risks}")
            
    
    def test_fn_09(self):
        """Huyết áp cao kiêng mặn — Tăng huyết áp, bác sĩ dặn ăn nhạt."""
        prompt = "Ba mình tăng huyết áp, bác sĩ dặn phải ăn nhạt giảm muối, không ăn đồ mặn. Gợi ý quán cơm ít muối."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sodium", detected_risks)
    
    # =======================================================================
    # 15. NHÓM PHỐI HỢP LỊCH TRÌNH / VỊ TRÍ / NGÂN SÁCH (MIX-CONTEXT)
    # =======================================================================

    def test_mix_schedule_no_health_pass(self):
        """Lịch trình sáng Việt trưa Thái tối Âu hoàn toàn bình thường -> Kỳ vọng []"""
        prompt = "Tôi muốn ăn sáng bằng món Việt ăn trưa bằng món Thái, ăn tối bằng món Âu ngân sách 500k, ở Quận 1."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Lỗi bắt nhầm tag từ lịch trình thông thường: {detected_risks}")

    def test_mix_schedule_with_spicy_medical(self):
        """Lịch trình kết hợp: Trưa ăn đồ Thái nhưng dạ dày yếu phải né cay -> Kỳ vọng ['Spicy']"""
        prompt = "Gợi ý lịch trình ăn uống Quận 3: sáng cafe bánh ngọt, trưa ăn món Thái mà mình bị đau dạ dày nên quán nhớ làm không cay nha, tối ăn lẩu nhẹ nhàng với bạn."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks, f"Lỗi lọt tag đồ cay khi khách khai báo đau dạ dày trong lịch trình.")

    def test_mix_schedule_with_diabetes(self):
        """Lịch trình kết hợp: Sáng muốn ăn bánh ngọt nhưng bị tiểu đường -> Kỳ vọng ['High_Sugar']"""
        prompt = "Mình cần tìm chỗ ăn cả ngày quanh Bình Thạnh, ngân sách tầm 300k. Sáng tính ăn bánh ngọt uống trà sữa mà ngặt nỗi bị tiểu đường, trưa tối ăn cơm văn phòng bình thường."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sugar", detected_risks)

    def test_mix_schedule_with_seafood_allergy(self):
        """Lịch trình kết hợp: Tối ăn buffet hải sản nhưng có người dị ứng tôm cua -> Kỳ vọng Seafood/Shellfish"""
        prompt = "Lên kế hoạch ăn uống đi chơi Quận 1: trưa ăn mỳ Ý tầm 150k, tối đi ăn buffet hải sản với công ty nhưng trong nhóm có ông anh bị dị ứng hải sản nặng, xem có món gì thay thế không."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(any(tag in detected_risks for tag in ["Seafood", "Shellfish"]))

    def test_mix_schedule_with_hypertension(self):
        """Lịch trình kết hợp: Trưa ăn mỳ cay/đồ mặn nhưng bố bị cao huyết áp -> Kỳ vọng ['High_Sodium']"""
        prompt = "Dẫn gia đình đi ăn ở Landmark 81, sáng ăn bún bò, trưa ăn món Hàn Quốc mà bố mình bị cao huyết áp nên quán làm nhạt muối giùm, tối ăn nhẹ salad thôi."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sodium", detected_risks)

    def test_mix_schedule_with_oily_medical(self):
        """Lịch trình kết hợp: Đi du lịch ăn súp cua, gà rán nhưng đang ho -> Kỳ vọng ['DeepFried_Oily']"""
        prompt = "Tôi muốn ăn sáng súp cua Quận 5, trưa dẫn mấy đứa nhỏ đi ăn gà rán kem tươi tiệc sinh nhật mà tôi đang bị ho viêm họng nên cần kiêng đồ dầu mỡ rán ngập dầu nha."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("DeepFried_Oily", detected_risks)

    def test_mix_schedule_all_clean_pass(self):
        """Lịch trình ăn chay/eat clean chủ động hoàn toàn khỏe mạnh -> Kỳ vọng []"""
        prompt = "Tìm quán ăn sáng món Việt thanh đạm, trưa ăn buffet chay Quận 10, tối ăn salad tổng hợp eat clean để giữ dáng, ngân sách cả ngày 400k."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_mix_schedule_with_low_carb(self):
        """Lịch trình kết hợp: Muốn ăn món Âu, món Nhật nhưng đang siết cơ kiêng tinh bột -> Kỳ vọng ['Refined_Carbs']"""
        prompt = "Tư vấn thực đơn cả ngày ở Quận 1, ngân sách 1 triệu. Trưa ăn sushi Nhật, tối ăn bít tết Âu nhưng mình đang ăn kiêng nghiêm ngặt, cần né tinh bột với cơm mỳ ra."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Refined_Carbs", detected_risks)

    def test_mix_location_budget_no_health_pass(self):
        """Tìm quán nhậu, uống bia cuối tuần thông thường -> Kỳ vọng []"""
        prompt = "Cuối tuần tụ tập bạn cấp 3 tầm 6 người, muốn tìm quán nhậu hoặc tiệm bia nào view chill chill ở khu Thảo Điền Quận 2, ngân sách mỗi người tầm 400k."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_mix_schedule_with_stomach_ache(self):
        """Lịch trình kết hợp: Trưa ăn mỳ cay nhưng bụng yếu hay tiêu chảy -> Kỳ vọng ['Spicy']"""
        prompt = "Sáng ăn phở bò, trưa nhóm bạn rủ ăn mỳ cay 7 cấp độ ở Quận 10 mà dạo này bụng dạ yếu hay bị tiêu chảy nên mình muốn đổi sang món khác không cay, tối ăn gì cũng được."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks)

    def test_mix_corporate_party_no_health_pass(self):
        """Đặt tiệc công ty gồm món Việt, món Hoa, tiếp khách -> Kỳ vọng []"""
        prompt = "Đặt bàn tiệc công ty 20 người trưa nay, menu kết hợp món Việt với món Hoa, có không gian riêng để tiếp khách VIP, ngân sách tổng khoảng 10 triệu ở Quận 1."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_mix_schedule_pregnancy_care(self):
        """Lịch trình kết hợp:kiêng cữ đồ sống -> Kỳ vọng Seafood/Shellfish hoặc sinh học"""
        prompt = "Sáng ăn hủ tiếu, trưa ăn đồ Nhật sashimi cá hồi ở Quận 3, bác sĩ dặn phải kiêng tuyệt đối đồ sống hải sản tươi sống."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(any(tag in detected_risks for tag in ["Seafood", "Shellfish"]))

    def test_mix_family_trip_with_elderly_fat(self):
        """Chuyến đi gia đình: Người già mỡ máu cao né đồ chiên xào -> Kỳ vọng ['DeepFried_Oily']"""
        prompt = "Gia đình 4 người đi du lịch ghé Quận 1 ăn trưa món Âu, tối ăn đặc sản Nam Bộ mà mẹ mình bị mỡ máu cao nên cần tránh mấy món chiên xào nhiều dầu mỡ."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("DeepFried_Oily", detected_risks)

    def test_mix_dating_schedule_no_health_pass(self):
        """Lịch trình hẹn hò sang chảnh tinh tế -> Kỳ vọng []"""
        prompt = "Dẫn bạn gái đi hẹn hò tối thứ 7, muốn ăn món Pháp lãng mạn có nến và hoa, sau đó đi uống cocktail bar quanh khu Quận 1, ngân sách thoải mái tầm 3 triệu."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_mix_weekend_with_gout(self):
        """Lịch trình cuối tuần: Đi ăn tiệc nướng nhưng bị gout -> Kỳ vọng Seafood/Shellfish hoặc tag tương ứng"""
        prompt = "Trưa ăn cơm tấm, tối bạn thân mời đám cưới tiệc buffet nướng hải sản bia tươi ở Quận 7, ngặt nỗi mình đang bị bệnh gout sưng khớp chân nên phải kiêng hải sản tôm cua."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(any(tag in detected_risks for tag in ["Seafood", "Shellfish"]))
    def test_app_tim_quan_review_pass_test(self):
        """Khách tìm quán theo review, không có rủi ro -> Phải pass."""
        # Tìm quán view đẹp, đi hẹn hò
        prompt_1 = "Xung quanh đây có quán hải sản nào view lãng mạn thích hợp đi date với người yêu không?"
        self.assertEqual(self.detector.detect(prompt_1), [])

        # Tìm quán theo số lượng người
        prompt_2 = "Công ty mình muốn đặt bàn khoảng 20 người ăn hải sản ngập quầy line, có chỗ nào giữ xe ô tô không?"
        self.assertEqual(self.detector.detect(prompt_2), [])

        # Tìm theo khu vực địa lý
        prompt_3 = "Kiếm giùm mình mấy quán ốc hoặc hải sản ngon bổ rẻ ở khu vực Quận 3 với."
        self.assertEqual(self.detector.detect(prompt_3), [])
    def test_app_mon_an_va_vi_tri_pass_test(self):
        """Khách tìm món + vị trí (khuyết giá, sở thích) -> Phải pass."""
        # Tìm theo quận cụ thể
        prompt_1 = "Mình muốn ăn hải sản mâm ở mạn Cầu Giấy hoặc Tây Hồ."
        self.assertEqual(self.detector.detect(prompt_1), [])

        # Tìm theo bán kính / vị trí gần đây
        prompt_2 = "Tìm quán ốc hay hải sản sốt trứng muối nào gần đây đang mở cửa."
        self.assertEqual(self.detector.detect(prompt_2), [])

        # Tìm theo tên đường / địa danh cụ thể
        prompt_3 = "Đang ở phố đi bộ Nguyễn Huệ muốn tìm chỗ ăn hải sản tươi sống."
        self.assertEqual(self.detector.detect(prompt_3), [])
    def test_app_mon_an_va_gia_tien_pass_test(self):
        """Khách tìm món + ngân sách/giá (khuyết vị trí, sở thích) -> Phải pass."""
        # Định mức giá theo đầu người (Teencode k/nghìn)
        prompt_1 = "Tập thể lớp mún đi ag buffe hải sản tầm 299k một người đổ lại."
        self.assertEqual(self.detector.detect(prompt_1), [])

        # Định mức tổng ngân sách cho cả nhóm
        prompt_2 = "Cần đặt bàn ăn hải sản cho 4 người tổng ngân sách tầm 1 triệu rưỡi."
        self.assertEqual(self.detector.detect(prompt_2), [])

        # Tìm theo phân khúc giá (rẻ, bình dân, cao cấp)
        prompt_3 = "Có quán hải sản vỉa hè nào ngon bổ rẻ, giá sinh viên không?"
        self.assertEqual(self.detector.detect(prompt_3), [])
        
    def test_app_mon_an_va_so_thich_khong_gian_pass_test(self):
        """Khách tìm món + tiêu chí không gian (khuyết giá, vị trí) -> Phải pass."""
        # Cần phòng riêng tư, trang trọng tiếp khách
        prompt_1 = "Tìm nhà hàng hải sản có phòng vip riêng biệt để tiếp đối tác làm ăn."
        self.assertEqual(self.detector.detect(prompt_1), [])

        # Cần không gian gia đình, có chỗ chơi cho trẻ em
        prompt_2 = "Nhà mình muốn đặt bàn ăn hải sản cuối tuần, quán nào rộng rãi có khu vui chơi cho trẻ em không?"
        self.assertEqual(self.detector.detect(prompt_2), [])

        # Tiêu chí tiện ích: Có máy lạnh, có chỗ đỗ ô tô
        prompt_3 = "Kiếm quán lẩu hải sản nào có phòng điều hòa mát mẻ với có chỗ đậu xe ô tô nha shop."
        self.assertEqual(self.detector.detect(prompt_3), [])
        
    def test_app_full_truong_thong_tin_pass_test(self):
        """Khách nhập đầy đủ món + vị trí + giá + sở thích cùng lúc -> Phải pass mượt mà."""
        # Trường hợp 1: View đẹp + Quận 1 + Giá cụ thể
        prompt_1 = "Tối nay mình muốn ăn hải sản view sông ở Quận 1, ngân sách tầm 500k/người, tư vấn giúp mình."
        self.assertEqual(self.detector.detect(prompt_1), [])

        # Trường hợp 2: Có phòng riêng + Gần đây + Giá bình dân (Sử dụng slang/teencode xen kẽ)
        prompt_2 = "Alo mún tìm quán ăn hải sản tươi sống quanh đây có phòng lạnh riêng, giá rổ bình dân tầm 300 cành một người."
        self.assertEqual(self.detector.detect(prompt_2), [])

        # Trường hợp 3: Quán vỉa hè + Tên đường cụ thể + Giá rẻ sinh viên
        prompt_3 = "Thèm ăn mấy món ốc hải sản vỉa hè lề đường dọc khu đường Vĩnh Khánh quận 4, tiêu chí ngon rẻ ngồi thoáng mát."
        self.assertEqual(self.detector.detect(prompt_3), [])
        
    def test_them_an_do_ngot_pass_test(self):
        """Người dùng thèm ăn ngọt chủ động -> Phải pass, không gắn tag tiểu đường."""
        prompt = "Hôm nay làm việc mệt quá thèm ăn cái gì ngọt ngọt hoặc uống trà sữa."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(
            detected_risks, [], 
            f"Thất bại! Câu thèm ăn đồ ngọt bị gắn nhầm tag: {detected_risks}"
        )
    
    def test_dat_ban_hai_san_pass_test(self):
        """Đặt bàn ăn hải sản chủ động -> Phải pass."""
        prompt = "Cho mình đặt bàn 4 người ăn lẩu cua biển với tôm nướng vào tối mai."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_benh_ly_thuc_te_van_phai_match(self):
        """
        Đảm bảo màng lọc Exclusion không 'bóp chết' các câu khai báo bệnh lý thật.
        Khi câu không chứa từ khóa loại trừ, hệ thống vẫn phải hoạt động bình thường.
        """
        # Test với từ khóa dị ứng hải sản thuần túy không có "muốn ăn"
        prompt = "Tôi bị dị ứng hải sản rất nặng, quán lưu ý giúp."
        detected_risks = self.detector.detect(prompt)
        
        # Vì đọc từ file JSON thật của Quân, tag 'di_ung_hai_san' map ra 'Seafood' và 'Shellfish'
        self.assertTrue(
            len(detected_risks) > 0, 
            "Thất bại! Câu dị ứng thật sự bị màng lọc nuốt mất tag."
        )
        self.assertIn("Seafood", detected_risks)
        self.assertIn("Shellfish", detected_risks)

    def test_vung_loi_tru_khong_anh_huong_ve_sau(self):
        """
        Kiểm tra tính chính xác của _EXCLUSION_WINDOW.
        Nếu 'muốn ăn' xuất hiện ở vế đầu, nhưng vế sau khai báo bệnh lý rõ ràng 
        (ngoài phạm vi window), hệ thống vẫn phải bắt được tag bệnh vế sau.
        """
        prompt = "Tôi muốn ăn một chút cơm thôi vì tôi đang bị đau dạ dày."
        detected_risks = self.detector.detect(prompt)
        
        # 'muon an' bọc chữ 'com' (Low_Carb bị bỏ qua là đúng), 
        # nhưng vế sau 'dau da day' cách xa > 30 ký tự nên phải bắt được tag 'Spicy'/'DeepFried_Oily'
        self.assertTrue(
            len(detected_risks) > 0,
            "Thất bại! Vùng ảnh hưởng Exclusion quá rộng làm mất tag bệnh ở vế sau."
        )
    # =======================================================================
    # 1. NHÓM TEST TIẾNG ĐỊA PHƯƠNG / TỪ ĐỒNG NGHĨA SỞ THÍCH
    # =======================================================================

    def test_tu_dia_phuong_khoai_an_pass_test(self):
        """Dùng từ 'khoái ăn/hảo ngọt' chủ động -> Phải pass, không dính tiểu đường/gout."""
        prompt = "Mình hảo ngọt cực kỳ, khoái ăn mấy món chè bánh ngọt lắm."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Bị dính tag nhầm khi dùng từ khoái ăn/hảo ngọt: {detected_risks}")

    def test_hanh_dong_tim_quan_pass_test(self):
        """Dùng hành động 'tìm quán/kiếm chỗ ăn' -> Phải pass, không gắn tag dị ứng."""
        prompt = "Cuối tuần cần tìm quán hải sản hoặc kiếm chỗ ăn tôm hùm ngon ở SG."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    # =======================================================================
    # 2. NHÓM ĐẢO NGỮ / CẤU TRÚC PHỨC TẠP
    # =======================================================================

    def test_dao_ngu_ngu_canh_so_thich_pass_test(self):
        """Đảo cấu trúc: Đưa món ăn lên trước từ khóa sở thích -> Phải pass."""
        prompt = "Hải sản thịt đỏ là món mình cực kỳ thích ăn mỗi ngày."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Đảo ngữ vẫn bị dính tag: {detected_risks}")

    def test_tu_nhieu_xen_giua_pass_test(self):
        """Từ khóa muốn ăn và từ khóa bệnh bị xen giữa bởi nhiều trạng từ -> Phải pass."""
        prompt = "Tôi đang rất là muốn đi ra ngoài để ăn hải sản tươi sống."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    # =======================================================================
    # 3. NHÓM KẾT HỢP BIẾN THỂ PHỦ ĐỊNH + LOẠI TRỪ (CRITICAL CASE)
    # =======================================================================

    def test_phu_dinh_cua_muon_an_trigger_health_tag(self):
        """
        'Không muốn ăn' -> Nghĩa là họ chủ động né tránh món đó do sức khỏe 
        -> TRƯỜNG HỢP NÀY PHẢI RA TAG (Né hải sản vì dị ứng, né đồ ngọt vì tiểu đường).
        """
        prompt = "Tôi không muốn ăn đồ ngọt đâu, đang sợ lên đường huyết."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, "Lỗi! 'Không muốn ăn' là câu né tránh bệnh lý, không được loại trừ!")

    def test_chan_them_an_trigger_health_tag(self):
        """'Chẳng thèm ăn / chưa muốn ăn' -> Phải ra tag bệnh lý/dị ứng."""
        prompt = "Bác sĩ dặn nên tôi chẳng thèm ăn hải sản thịt đỏ nữa đâu."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, "Lỗi! 'Chẳng thèm ăn' do bác sĩ dặn phải bắt được tag.")

    # =======================================================================
    # 4. NHÓM DẤU CÂU, NGẮT NGỮ CẢNH VÀ ĐỘ DÀI WINDOW
    # =======================================================================

    def test_ngat_cau_bang_dau_cham_phai_match_ve_sau(self):
        """
        Nếu câu được ngắt hẳn bằng dấu chấm/dấu phẩy, ngữ cảnh 'muốn ăn' ở câu trước 
        không được phép ảnh hưởng sang câu khai báo bệnh lý phía sau.
        """
        prompt = "Tôi muốn ăn cơm tấm. Dạo này tôi hay bị đau dạ dày quá."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks, "Dấu chấm đã ngắt câu nhưng Exclusion Scope vẫn ăn lan sang làm mất tag bệnh câu sau.")

    def test_nhieu_mong_muon_trung_lap_pass_test(self):
        """User lặp đi lặp lại nhiều từ muốn ăn, thèm ăn trong 1 đoạn văn ngắn -> Phải pass."""
        prompt = "Em thèm ăn đồ ngọt, cũng muốn uống trà sữa, thích ăn bánh kem nữa."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_viet_lien_khong_dau_co_dau_hop_le_pass_test(self):
        """Prompt hỗn hợp không dấu + có dấu 'muon an hai san' -> Phải pass."""
        prompt = "minh muon an hai san bo bien dem nay"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    # =======================================================================
    # 5. NHÓM AN TOÀN (SANITY CHECKS) - BẢO VỆ CHỨC NĂNG CŨ
    # =======================================================================

    def test_tu_khoa_benh_dung_dau_cau_van_phai_match(self):
        """Từ khóa bệnh lý đứng ngay đầu prompt (Chưa có chữ muốn ăn) -> Phải giữ nguyên tag."""
        prompt = "Đau dạ dày nên tôi muốn ăn cái gì đó thanh đạm nhẹ nhàng."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks, "Từ bệnh lý đứng đầu bị 'muốn ăn' phía sau triệt tiêu sai trái.")

    def test_khai_bao_tieu_su_benh_hop_le(self):
        """Khai báo tiền sử bệnh + muốn ăn món phù hợp thực đơn -> Phải bắt được bệnh."""
        prompt = "Tôi bị tiểu đường nên chỉ muốn ăn ức gà luộc thanh đạm thôi."
        detected_risks = self.detector.detect(prompt)
        # Phải bắt được tag tiểu đường (để tí nữa hệ thống gợi ý món không đường)
        self.assertTrue(len(detected_risks) > 0, "Có chữ 'muốn ăn' ở đuôi làm nuốt chửng mất khai báo tiểu đường ở đầu câu.")

    def test_cau_chat_dai_loằng_ngoằng_chứa_sow_thich_pass_test(self):
        """Câu chat tự nhiên, dài, kể lể sở thích ăn uống -> Phải pass mượt mà."""
        prompt = "Alo quán ơi nhóm mình tầm 6 người đang tính đi du lịch muốn ăn hải sản cua ghẹ tôm hùm ngân sách tầm 2 triệu đổ lại có set nào không?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Câu hỏi thực đơn dài bị bắt nhầm tag: {detected_risks}")
        # =======================================================================
    # 6. NHÓM EMOJI & KÝ TỰ ĐẶC BIỆT XEN KẼ (EMOJI ISOLATION)
    # =======================================================================

    def test_emoji_xen_giua_tu_khoa_pass_test(self):
        """Chứa emoji và ký tự đặc biệt ở giữa cụm từ sở thích -> Vẫn phải nhận diện được để loại trừ."""
        prompt = "Tôi muốn 🍽️🤤 ăn hải sản ngon ngon."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Emoji làm hỏng Exclusion và dính tag nhầm: {detected_risks}")

    # =======================================================================
    # 7. NHÓM TEENCODE / SAI CHÍNH TẢ PHỔ BIẾN (FUZZY ON EXCLUSION)
    # =======================================================================

    def test_teencode_mun_an_thik_an_pass_test(self):
        """User viết teencode 'mún ăn', 'thík ăn', 'món j' -> Vẫn phải bắt được ngữ cảnh loại trừ."""
        # Lưu ý: Cần đảm bảo hàm normalize_text của bạn hoặc bộ Regex có hỗ trợ fuzzy/mapping từ teencode này
        prompt = "Mình mún ăn hải sản ghê, có quán nào thík hợp ko?"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_sai_chinh_ta_gieu_uong_pass_test(self):
        """User gõ sai chính tả từ khóa hành động 'thèm ăg', 'ún sữa' -> Vẫn phải pass."""
        prompt = "Dạo này tự dưng thèm ăg đồ ngọt và ún nước mía ghê."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    # =======================================================================
    # 8. NHÓM CẤU TRÚC GIẢ ĐỊNH / ĐIỀU KIỆN (IF-ELSE PHỨC TẠP)
    # =======================================================================

    def test_cau_dieu_kien_neu_muon_an_trigger_health_tag(self):
        """
        'Nếu muốn ăn... thì có sao không?' -> Câu hỏi mang tính chất tham khảo sức khỏe 
        -> PHẢI TRẢ VỀ TAG (Vì bản chất họ đang phân vân về bệnh lý của mình).
        """
        prompt = "Nếu tôi muốn ăn hải sản mà đang bị gout thì có bị sưng khớp sưng chân lên không?"
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, "Câu hỏi giả định y tế bị nuốt mất tag bệnh lý!")

    def test_cau_hoi_tu_van_thuc_don_trigger_health_tag(self):
        """'Muốn ăn món này... nhưng bị bệnh kia' -> Phải bắt được bệnh lý."""
        prompt = "Mình thèm ăn đồ ngọt quá nhưng đang bị tiểu đường tuýp 2 thì nên chọn món nào?"
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, "Câu hỏi tư vấn thực đơn cho người bệnh bị màng lọc nuốt mất tag.")

    # =======================================================================
    # 9. NHÓM TỪ ĐỒNG ÂM KHÁC NGHĨA (TRÁNH CHẶN NHẦM TỪ KHÓA AN TOÀN)
    # =======================================================================

    def test_ten_rieng_chua_tu_khoa_trigger_health_tag(self):
        """Tên riêng chứa chữ 'An' (ví dụ: bạn An, anh An) -> Không được kích hoạt nhầm 'muốn ăn'."""
        prompt = "Bạn An bị đau dạ dày rất nặng, không ăn được đồ cay đâu nha."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks, "Chữ 'An' trong tên riêng làm kích hoạt nhầm scope loại trừ ăn uống.")

    def test_tu_nghieu_ngu_canh_khac_trigger_health_tag(self):
        """Chữ 'muốn' dùng làm trợ từ ý chí chung, không đi với hành động ăn uống -> Vẫn phải bắt tag bệnh."""
        prompt = "Tôi muốn khỏe mạnh trở lại để không còn bị hành hạ bởi căn bệnh tiểu đường này."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, "Từ 'muốn' đứng độc lập không đi với ăn uống vẫn làm mất tag bệnh vế sau.")

    # =======================================================================
    # 10. NHÓM TRẬN ĐỒ ĐOẠN VĂN DÀI (STRESS TEST LONG TEXT)
    # =======================================================================

    def test_hon_hop_nhieu_cau_vua_loai_tru_vua_benh_ly(self):
        """
        Đoạn văn hỗn hợp: Câu 1 muốn ăn (pass) -> Câu 2 khai báo bệnh lý thật (match) -> Câu 3 thèm uống (pass).
        Thử nghiệm độ chính xác của token_offset và ranh giới dấu câu.
        """
        prompt = "Tối nay em rất muốn đi ăn lẩu cua biển bồi bổ. Mà ngặt nỗi dạo này đường huyết cao, đang bị tiểu đường nữa. Thèm uống trà sữa trân châu lắm mà không dám."
        detected_risks = self.detector.detect(prompt)
        
        # Câu 1 (cua biển/hải sản) bị chặn -> Đúng
        # Câu 3 (thèm uống trà sữa) bị chặn -> Đúng
        # Câu 2 (tiểu đường) PHẢI bắt được tag rủi ro
        self.assertTrue(len(detected_risks) > 0, "Đoạn văn dài phức tạp làm nhiễu logic khiến mất tag bệnh lý ở giữa.")
        self.assertIn("High_Sugar", detected_risks) # 'tiểu đường' map ra High_Sugar từ file JSON thật

    def test_khoang_trang_bat_thuong_pass_test(self):
        """User cố tình gõ rất nhiều khoảng trắng tá lả giữa các cụm từ -> Hệ thống vẫn phải nhận diện mượt mà."""
        prompt = "Tôi    muon       an         hai     san    view     bien"
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])
        # =======================================================================
    # 11. NHÓM SỞ THÍCH / ĐẶT BÀN CHỦ ĐỘNG (KỲ VỌNG: TRẢ VỀ MẢNG RỖNG [])
    # =======================================================================

    def test_real_dat_ban_hai_san_pass(self):
        """User đặt bàn ăn hải sản chủ động, kể lể dài dòng -> Phải pass."""
        prompt = "Chào quán, tối nay mình tính dẫn gia đình tầm 5 người đi ăn hải sản, muốn tìm chỗ nào có view thoáng mát, hải sản tươi sống tí nha, ngân sách tầm 2 triệu đổ lại."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [], f"Lỗi bắt nhầm tag sở thích đặt bàn: {detected_risks}")

    def test_real_them_banh_ngot_pass(self):
        """User thèm đồ ngọt béo do áp lực công việc -> Phải pass."""
        prompt = "Shop ơi tư vấn cho mình mấy món ngọt ngọt tí đi, dạo này làm việc căng thẳng tự nhiên thèm ăn bánh kem với uống trà sữa trân châu quá trời luôn."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_real_combo_lau_nuong_pass(self):
        """User tìm kiếm combo lẩu thái hải sản cuối tuần -> Phải pass."""
        prompt = "Cuối tuần này nhóm mình muốn đặt bàn khoảng 4 người ăn lẩu thái hải sản hoặc đồ nướng á, quán có set nào combo tiết kiệm không gửi mình xem với."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_real_tim_quan_do_han_cay_pass(self):
        """User tìm quán đồ Hàn cay béo cho người yêu -> Phải pass."""
        prompt = "Mình đang tìm quán ăn nào ngon ngon quanh khu vực Quận 1 để dẫn người yêu đi ăn tối, cô ấy thích ăn đồ Hàn Quốc cay cay với gà rán béo béo."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    def test_real_muon_an_thanh_dam_pass(self):
        """User chủ động muốn ăn nhẹ nhàng thanh đạm -> Phải pass."""
        prompt = "Có món nào thanh đạm tí không ạ? Mình muốn ăn nhẹ nhàng thôi vì trưa nay ăn tiệc hơi no rồi, gợi ý giúp mình vài món súp hoặc salad nhé."
        detected_risks = self.detector.detect(prompt)
        self.assertEqual(detected_risks, [])

    # =======================================================================
    # 12. NHÓM KHAI BÁO BỆNH LÝ / DỊ ỨNG THỰC TẾ (KỲ VỌNG: PHẢI BẮT TRÚNG TAG)
    # =======================================================================

    def test_real_khai_bao_dau_bao_tu(self):
        """Khai báo kiêng đồ cay nóng, dầu mỡ do đau bao tử -> Phải dính Spicy và Oily."""
        prompt = "Dạo này đau bao tử, bác sĩ dặn phải kiêng tuyệt đối đồ cay nóng với đồ chiên rán nhiều dầu mỡ nên shop xem có món nào phù hợp không."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks)
        self.assertIn("DeepFried_Oily", detected_risks)

    def test_real_khai_bao_di_ung_hai_san(self):
        """Khai báo đoàn có người dị ứng hải sản nặng -> Phải dính Seafood/Shellfish."""
        prompt = "Nhờ quán lưu ý giùm là trong đoàn mình đi có người bị dị ứng hải sản rất nặng nha, chỉ cần dính một tí tôm hay cua là bị nổi mề đay ngay, nên lúc chế biến làm né ra giùm mình."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(any(tag in detected_risks for tag in ["Seafood", "Shellfish"]))

    def test_real_khai_bao_tieu_duong_huyet_ap(self):
        """Mẹ bị tiểu đường, huyết áp cao cần kiêng nghiêm ngặt -> Phải dính Sugar và Sodium."""
        prompt = "Mẹ mình bị tiểu đường tuýp 2 với huyết áp cao nên chế độ ăn phải cực kỳ nghiêm ngặt, quán có món nào không đường, ít gia vị ít muối không tư vấn giùm mình."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sugar", detected_risks)
        self.assertIn("High_Sodium", detected_risks)

    def test_real_khai_bao_gout_xuong_khop(self):
        """Bị bệnh gout sưng chân kiêng hải sản -> Phải dính Seafood."""
        prompt = "Mình đang bị bệnh gout, mấy khớp chân đang hơi sưng nên phải kiêng mấy món thịt đỏ với hải sản, quán xem có món cá hấp hay đồ chay nào nhẹ nhàng không giới thiệu mình."
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(any(tag in detected_risks for tag in ["Seafood", "Shellfish"]))

    def test_real_khai_bao_he_tieu_hoa_kem(self):
        """Hệ tiêu hóa kém kiêng dầu mỡ, đồ ngọt -> Phải dính Oily và Sugar."""
        prompt = "Tư vấn thực đơn cho người hay bị đầy bụng, khó tiêu với ạ, dạo này hệ tiêu hóa kém quá nên mình muốn kiêng đồ dầu mỡ với đồ ngọt."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("DeepFried_Oily", detected_risks)
        self.assertIn("High_Sugar", detected_risks)

    # =======================================================================
    # 13. NHÓM TRỘN LẪN NGỮ CẢNH PHỨC TẠP (KỲ VỌNG: KHÔNG ĐƯỢC NUỐT TAG)
    # =======================================================================

    def test_real_tron_dau_da_day_muon_an_chao(self):
        """Đau dạ dày đứng trước cụm 'muốn ăn cháo' -> Không được để chữ muốn ăn nuốt mất tag Spicy."""
        prompt = "Tôi bị đau dạ dày nên chỉ muốn ăn mấy món cháo hoặc súp gì đó thanh đạm thôi, quán nhớ dặn nhà bếp đừng bỏ ớt hay tiêu vào nha."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks)

    def test_real_tron_cao_huyet_ap_thich_ca_kho(self):
        """Bố bị cao huyết áp nhưng thích ăn cá lóc kho ít muối -> Phải giữ tag Sodium."""
        prompt = "Bố mình bị cao huyết áp nên quán nhớ làm món nào nhạt nhạt tí, ông cụ thích ăn cá lóc kho nhưng mà đừng bỏ nhiều muối với nước mắm quá nha."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sodium", detected_risks)

    def test_real_tron_an_kieng_muon_tim_low_carb(self):
        """Ăn kiêng nghiêm ngặt muốn tìm low-carb -> Phải bắt được tinh bột."""
        prompt = "Em đang trong chế độ ăn kiêng giảm cân nghiêm ngặt, muốn tìm món nào low-carb ít tinh bột tí, shop có ức gà áp chảo hay salad ức gà không?"
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Refined_Carbs", detected_risks)

    def test_real_tron_di_ung_dau_phong(self):
        """Kể chuyện đi ăn nhóm có bạn dị ứng đậu phộng -> Phải dính tag dị ứng hạt."""
        prompt = "Nhóm mình đi ăn có một bạn bị dị ứng đậu phộng, quán làm món gì thì nhớ nhắc đầu bếp đừng rắc đậu phộng hay ba cái đậu hạt lên trên mặt nha, nguy hiểm lắm."
        # Giả định hệ thống có tag hạt (nếu chưa có Quân có thể linh hoạt check qua hàm tương tự)
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(len(detected_risks) > 0, "Không bắt được dị ứng hạt trong câu kể chuyện.")

    def test_real_tron_them_ngot_nhung_tieu_duong(self):
        """Thèm ăn đồ ngọt nhưng bị tiểu đường ở vế sau -> Phải bắt trúng Sugar."""
        prompt = "Mình thèm ăn đồ ngọt quá cơ mà ngặt nỗi dạo này đang bị tiểu đường, bác sĩ bắt kiêng đường sữa nên thôi shop có nước ép nào nguyên chất không đường không?"
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sugar", detected_risks)

    # =======================================================================
    # 14. NHÓM VĂN PHONG CHAT TỰ NHIÊN / KỂ CHUYỆN (STRESS TEST LONG TEXT)
    # =======================================================================

    def test_real_chat_dat_tieng_sinh_nhat_hon_hop(self):
        """Đặt tiệc 10 người có người ăn chay và người tiểu đường -> Phải bắt được Sugar."""
        prompt = "Alo shop ơi, mình muốn đặt tiệc sinh nhật nhỏ tầm 10 người vào tối mai á, mà trong nhóm có 2 người ăn chay trường với 1 người bị tiểu đường, quán lên menu sao cho hợp lý giúp mình với."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("High_Sugar", detected_risks)

    def test_real_chat_bi_ho_muon_kieng_dau_mo(self):
        """Bị ho đau họng muốn kiêng đồ chiên xào béo -> Phải ra tag Oily."""
        prompt = "Mình tính ghé quán ăn trưa nè, mà dạo này đang bị ho với đau họng nên muốn kiêng mấy món đá lạnh với đồ chiên xào nhiều dầu mỡ, có món nước nào nóng hổi dễ nuốt không?"
        detected_risks = self.detector.detect(prompt)
        self.assertIn("DeepFried_Oily", detected_risks)

    def test_real_chat_bung_yeu_ne_lau_thai_cay(self):
        """Bụng yếu hay tiêu chảy né lẩu thái cay -> Phải ra tag Spicy."""
        prompt = "Em muốn tìm một quán lẩu để tụ tập bạn bè, cơ mà dạo này bụng dạ yếu quá, hay bị tiêu chảy nên chắc phải né mấy cái lẩu thái cay ra, có lẩu nấm hay lẩu gì thanh đạm không shop?"
        detected_risks = self.detector.detect(prompt)
        self.assertIn("Spicy", detected_risks)

    def test_real_chat_mo_mau_cao_han_che_chien_ran(self):
        """Người lớn tuổi mỡ máu cao hạn chế chiên rán -> Phải ra tag Oily."""
        prompt = "Tư vấn giúp mình set ăn gia đình 4 người nha, nhà mình có người lớn tuổi bị mỡ máu cao nên cần hạn chế tối đa đồ chiên rán, ưu tiên mấy món luộc hoặc hấp nha admin."
        detected_risks = self.detector.detect(prompt)
        self.assertIn("DeepFried_Oily", detected_risks)

    def test_real_chat_uong_thuoc_dong_y_kieng_hai_san(self):
        """Uống thuốc đông y thầy dặn kiêng hải sản -> Phải ra tag Seafood."""
        prompt = "Chào ad, mình đi du lịch muốn ghé quán thử đặc sản mà ngặt nỗi dạo này đang uống thuốc đông y nên thầy thuốc dặn phải kiêng ăn hải sản với thịt gà, quán có món thịt heo hay bò nào ngon không?"
        detected_risks = self.detector.detect(prompt)
        self.assertTrue(any(tag in detected_risks for tag in ["Seafood", "Shellfish"]))
if __name__ == "__main__":
    unittest.main(verbosity=2)
