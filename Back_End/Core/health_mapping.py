
"""
health_risk_detector.py
-----------------------
Senior Python Engineer – v2 (enhanced)

Cải tiến so với v1:
  ① Synonym expansion   – tự sinh biến thể "bổ nghĩa" từ list_idea
  ② Multi-tag per kw    – một keyword có thể thuộc nhiều health_tag
  ③ Negation detection  – loại bỏ keyword bị phủ định ("không bị", "chưa từng")
  ④ Confidence scoring  – detect_with_scores() trả metadata đầy đủ
  ⑤ Greedy span track   – chặn sub-ngram tái fuzzy sau khi exact match thành công
  ⑥ Stopword pre-filter – bỏ token vô nghĩa trước khi gọi RapidFuzz
"""

from __future__ import annotations

import json
import re
import logging
from pathlib import Path
from typing import Any, TypedDict, cast

from unidecode import unidecode
from rapidfuzz import process as fuzz_process, fuzz

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ⑥ Vietnamese stopwords (normalized / ASCII form)
#    Các token này xuất hiện rất phổ biến nhưng không mang ý nghĩa bệnh lý.
#    Lọc trước khi chạy fuzzy giúp giảm false-positive và tăng tốc độ.
# ---------------------------------------------------------------------------
_VI_STOPWORDS: frozenset[str] = frozenset({
    "toi", "bi", "voi", "va", "hay", "lau", "nam", "dang",
    "rat", "kha", "cung", "thuong", "hay", "nhieu", "mot",
    "cac", "nhung", "la", "co", "da", "duoc", "theo",
    "trong", "ngoai", "khi", "vi", "de", "tu", "den",
    "len", "xuong", "qua", "nua", "roi", "thi", "ma",
    "nhu", "giong", "hon", "kem", "nhat", "nay", "do",
    "sau", "truoc", "dau", "cuoi", "giua", "ben", "phia",
    "gan", "xa", "cao", "thap", "lon", "nho", "moi",
    "cu", "mau", "den", "trang", "xanh", "vang",
    "toi hay", "toi bi", "bi va", "co bi",
})

# ---------------------------------------------------------------------------
# ③ Negation patterns (normalized / ASCII form)
#    Nếu window trước keyword chứa một trong các cụm này → loại bỏ keyword đó.
# ---------------------------------------------------------------------------
_NEGATION_PHRASES: tuple[str, ...] = (
    "khong bi",
    "khong co",
    "khong mac",
    "chua bi",
    "chua tung bi",
    "chua mac",
    "chua co",
    "khong phai",
    "khong he",
    "chua tung",
    "chu khong",
    "chứ không",          # raw – sẽ bị normalize ở runtime
)

# Số token tối đa nhìn về phía trái để phát hiện phủ định
_NEGATION_WINDOW: int = 4


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Chuẩn hoá tiếng Việt thành ASCII lowercase để so khớp.

    Pipeline:
        lowercase → bỏ dấu (unidecode) → xoá ký tự đặc biệt → chuẩn hoá space

    Examples:
        >>> normalize_text("Dã Dày!!!")
        'da day'
        >>> normalize_text("Không bị Tiểu Đường")
        'khong bi tieu duong'
    """
    text = text.lower()
    text = unidecode(text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ngrams_by_size(tokens: list[str], max_n: int) -> list[tuple[str, int, int]]:
    """
    Sinh n-grams từ DÀI đến NGẮN, trả kèm (text, start_idx, end_idx).
    end_idx là exclusive để tiện so sánh span [start, end).
    """
    n_tokens = len(tokens)
    result: list[tuple[str, int, int]] = []
    for n in range(min(max_n, n_tokens), 0, -1):
        for i in range(n_tokens - n + 1):
            result.append((" ".join(tokens[i : i + n]), i, i + n))
    return result


# ---------------------------------------------------------------------------
# ① Synonym / variant expansion
# ---------------------------------------------------------------------------

# Prefix mức độ / trạng từ thường đứng trước tên bệnh
_DEGREE_PREFIXES: tuple[str, ...] = (
    "dau",        # đau …
    "bi dau",     # bị đau …
    "mac",        # mắc …
    "bi mac",     # bị mắc …
    "mac phai",   # mắc phải …
    "mac benh",   # mắc bệnh …
    "bi",         # bị …
    "co",         # có …
    "co van de",  # có vấn đề …
    "chuan doan", # chẩn đoán …
)

# Suffix mức độ thường đứng sau tên bệnh
_DEGREE_SUFFIXES: tuple[str, ...] = (
    "nang",       # … nặng
    "nhe",        # … nhẹ
    "man tinh",   # … mãn tính
    "cap tinh",   # … cấp tính
    "truong dien",# … trường diễn
    "lau nam",    # … lâu năm
    "lau",        # … lâu
    "tiet",       # Không thêm suffix nào → giữ nguyên
)


def _expand_keyword(kw: str) -> list[str]:
    """
    ① Sinh các biến thể bổ nghĩa cho một keyword.

    Chiến lược:
    - Thêm các prefix mức độ phổ biến trước keyword gốc.
    - Thêm các suffix mức độ phổ biến sau keyword gốc.
    - Tất cả đều được normalize để đồng nhất với index.

    Args:
        kw: Keyword đã normalize (ví dụ "bao tu").

    Returns:
        Danh sách biến thể kể cả keyword gốc.
    """
    variants: list[str] = [kw]
    for pre in _DEGREE_PREFIXES:
        variants.append(f"{pre} {kw}")
    for suf in _DEGREE_SUFFIXES:
        variants.append(f"{kw} {suf}")
    # Loại trùng lặp, giữ thứ tự
    seen: set[str] = set()
    unique: list[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique


# ---------------------------------------------------------------------------
# TypedDict cho output detect_with_scores
# ---------------------------------------------------------------------------

class MatchDetail(TypedDict):
    health_tag: str
    matched_keyword: str
    score: float          # 1.0 = exact, 0.0–1.0 cho fuzzy (tỉ lệ normalised)
    method: str           # "exact" | "fuzzy"
    negated: bool


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class HealthRiskDetector:
    """
    Nhận diện rủi ro sức khỏe từ prompt tiếng Việt tự do.

    Cải tiến v2:
    ① Synonym expansion  – index chứa cả biến thể prefix/suffix
    ② Multi-tag per kw   – keyword_index: dict[str, list[str]]
    ③ Negation detection – phát hiện và loại bỏ trường hợp phủ định
    ④ Confidence scoring – detect_with_scores() trả MatchDetail
    ⑤ Greedy span track  – chặn sub-ngram tái chạy sau exact match
    ⑥ Stopword pre-filter– bỏ token thuần stopword trước fuzzy

    Args:
        dictionary_path: Đường dẫn đến health_condition_dictionary.json
        mapping_path:    Đường dẫn đến health_tag_mapping.json
        fuzzy_threshold: Ngưỡng score RapidFuzz (0–100). Mặc định 85.
        ngram_max:       Số token tối đa trong một n-gram. Mặc định 6.
        expand_synonyms: Bật/tắt ① synonym expansion. Mặc định True.
        detect_negation: Bật/tắt ③ negation detection. Mặc định True.
    """

    _DEFAULT_FUZZY_THRESHOLD: int = 85

    def __init__(
        self,
        dictionary_path: str | Path = Path(__file__).parent / "health_condition_dictionary.json",
        mapping_path: str | Path = Path(__file__).parent / "health_tag_mapping.json",
        fuzzy_threshold: int = _DEFAULT_FUZZY_THRESHOLD,
        ngram_max: int = 6,
        expand_synonyms: bool = True,
        detect_negation: bool = True,
    ) -> None:
        self.fuzzy_threshold = fuzzy_threshold
        self.ngram_max = ngram_max
        self.expand_synonyms = expand_synonyms
        self.detect_negation = detect_negation

        raw_dictionary: list[dict[str, Any]] = self._load_json(dictionary_path)
        self._tag_mapping: dict[str, list[str]] = self._load_json(mapping_path)

        # ② Multi-tag index: normalized_keyword → [tag1, tag2, ...]
        self._keyword_index: dict[str, list[str]] = {}
        # Tập hợp tất cả keyword (bao gồm biến thể) cho fuzzy
        self._all_keywords: list[str] = []

        for entry in raw_dictionary:
            tag: str = entry.get("health_tag", "")
            if not tag:
                logger.warning("Dictionary entry thiếu 'health_tag': %s", entry)
                continue

            for idea in entry.get("list_idea", []):
                base = normalize_text(idea)
                if not base:
                    continue

                # ① Sinh biến thể nếu được bật
                candidates = _expand_keyword(base) if expand_synonyms else [base]

                for kw in candidates:
                    # ② Gắn tag vào danh sách (tránh trùng trong cùng keyword)
                    existing = self._keyword_index.setdefault(kw, [])
                    if tag not in existing:
                        existing.append(tag)
                    if kw not in self._all_keywords:
                        self._all_keywords.append(kw)

        logger.debug(
            "Loaded %d unique keywords (expand_synonyms=%s).",
            len(self._keyword_index),
            expand_synonyms,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, prompt: str) -> list[str]:
        """
        Phân tích prompt và trả về danh sách risk tags cần tránh.
        """
        details = self.detect_with_scores(prompt)
        # Chỉ giữ lại các tag không bị gắn cờ phủ định
        active_tags: set[str] = {d["health_tag"] for d in details if not d["negated"]}
        return self._collect_risk_tags(active_tags)

    def detect_with_scores(self, prompt: str) -> list[MatchDetail]:
        """
        ④ Trả về metadata đầy đủ cho mỗi lần match.
        Sử dụng cơ chế Regex Scope dựa trên văn bản đã chuẩn hóa để nhận diện phủ định tuyệt đối.
        """
        normalized = normalize_text(prompt)
        
        # --- BƯỚC THAY THẾ: Tìm vị trí của tất cả các cụm phủ định trong chuỗi ký tự ---
        # Chuẩn hóa toàn bộ cụm phủ định để quét regex trùng khớp hoàn toàn
        normalized_phrases = [normalize_text(p) for p in _NEGATION_PHRASES]
        negation_pattern = r'\b(' + '|'.join(map(re.escape, normalized_phrases)) + r')\b'
        
        # Lưu các khoảng ký tự bị phủ định (Từ vị trí từ phủ định kéo dài về sau 35 ký tự hoặc đến hết câu)
        negation_scopes: list[tuple[int, int]] = []
        for neg_match in re.finditer(negation_pattern, normalized):
            neg_start = neg_match.start()
            # Giới hạn phạm vi phủ định trong khoảng 35 ký tự tiếp theo (khoảng 5-6 từ tiếng Việt)
            # Hoặc dừng lại nếu gặp từ nối chặn phủ định như "nhung", "nhung bi"
            neg_end = min(len(normalized), neg_start + 45)
            
            # Nếu trong tầm phủ định có từ "nhung" (nhưng), cắt bớt scope tại từ đó
            but_match = re.search(r'\b(nhung)\b', normalized[neg_start:neg_end])
            if but_match:
                neg_end = neg_start + but_match.start()
                
            negation_scopes.append((neg_start, neg_end))

        # --- BƯỚC TRUY TRUYỀN THỐNG: Quét n-gram dựa trên token ---
        tokens = normalized.split()
        ngrams = _ngrams_by_size(tokens, self.ngram_max)

        matched_spans: list[tuple[int, int]] = []
        results: list[MatchDetail] = []
        seen_tags: set[str] = set()

        for ngram_text, start, end in ngrams:
            if self._span_covered(start, end, matched_spans):
                continue

            # Tính toán vị trí ký tự (character index) tương đối của ngram_text trong chuỗi `normalized`
            # Điều này giúp khớp chính xác với hệ tọa độ của negation_scopes
            # Tìm kiếm vị trí xuất hiện của cụm từ này trong văn bản gốc
            char_start = normalized.find(ngram_text)
            char_end = char_start + len(ngram_text)

            # Xác định xem vị trí ký tự này có rơi vào vùng phủ định nào không
            is_neg = False
            if self.detect_negation:
                for n_s, n_e in negation_scopes:
                    # Nếu từ khóa nằm sau từ phủ định và nằm trong phạm vi ảnh hưởng của nó
                    if n_s <= char_start < n_e:
                        is_neg = True
                        break

            # --- So khớp Exact Match ---
            if ngram_text in self._keyword_index:
                tags = self._keyword_index[ngram_text]
                match_happened = False
                for tag in tags:
                    if tag not in seen_tags:
                        seen_tags.add(tag)
                        match_happened = True
                        results.append(cast(MatchDetail, {
                            "health_tag": tag,
                            "matched_keyword": ngram_text,
                            "score": 1.0,
                            "method": "exact",
                            "negated": is_neg,
                        }))
                if match_happened or len(tags) > 0:
                    matched_spans.append((start, end))
                continue

            # --- So khớp Fuzzy Match ---
            tokens_in_ngram = ngram_text.split()
            all_stopwords = all(t in _VI_STOPWORDS for t in tokens_in_ngram)
            all_stopwords = (ngram_text in _VI_STOPWORDS) or all_stopwords
            if all_stopwords or not self._all_keywords:
                continue

            result = fuzz_process.extractOne(
                ngram_text,
                self._all_keywords,
                scorer=fuzz.ratio,
                score_cutoff=self.fuzzy_threshold,
            )
            if result is not None:
                best_kw: str = result[0]
                raw_score: float = result[1]
                tags = self._keyword_index.get(best_kw, [])
                match_happened = False
                for tag in tags:
                    if tag not in seen_tags:
                        seen_tags.add(tag)
                        match_happened = True
                        results.append(cast(MatchDetail, {
                            "health_tag": tag,
                            "matched_keyword": best_kw,
                            "score": raw_score / 100.0,
                            "method": "fuzzy",
                            "negated": is_neg,
                        }))
                if match_happened or len(tags) > 0:
                    matched_spans.append((start, end))

        return results
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _span_covered(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
        """⑤ Kiểm tra xem [start, end) có bị phủ bởi một span đã match không."""
        for s, e in spans:
            if s <= start and end <= e:
                return True
        return False

    @staticmethod
    def _is_negated(tokens: list[str], keyword_start: int) -> bool:
        """
        ③ Kiểm tra xem keyword tại vị trí keyword_start có bị phủ định không.
        Sửa lỗi: Sử dụng Regex Word Boundary để so khớp chính xác cụm phủ định 
        trong window context, tránh trùng lặp substring bị dính chữ.
        """
        if keyword_start == 0:
            return False
            
        # Lấy window bên trái
        window_start = max(0, keyword_start - _NEGATION_WINDOW)
        window_tokens = tokens[window_start:keyword_start]
        window_text = " ".join(window_tokens)
        window_norm = normalize_text(window_text)
        
        for phrase in _NEGATION_PHRASES:
            phrase_norm = normalize_text(phrase)
            # Dùng \b để bọc ranh giới từ một cách tường minh, chuẩn hóa kết quả so khớp chuỗi
            if re.search(r'\b' + re.escape(phrase_norm) + r'\b', window_norm):
                return True
                
        return False

    def _collect_risk_tags(self, health_tags: set[str]) -> list[str]:
        """Gộp và dedup risk tags từ mapping, giữ thứ tự insertion."""
        seen: set[str] = set()
        ordered: list[str] = []
        for tag in health_tags:
            for risk in self._tag_mapping.get(tag, []):
                if risk not in seen:
                    seen.add(risk)
                    ordered.append(risk)
        return ordered

    @staticmethod
    def _load_json(path: str | Path) -> Any:
        """Load JSON với xử lý lỗi rõ ràng."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File không tồn tại: '{path.resolve()}'")
        try:
            with path.open(encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise json.JSONDecodeError(
                f"JSON không hợp lệ trong '{path}': {exc.msg}", exc.doc, exc.pos
            ) from exc

