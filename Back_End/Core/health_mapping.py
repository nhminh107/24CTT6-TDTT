"""
health_risk_detector.py
-----------------------
Senior Python Engineer – v3 (bug fixes)

Cải tiến so với v2:
  ⑦ Exclusion scope refinement  – scope "muốn ăn" chỉ bao phủ PHẦN TRƯỚC dấu kiêng cữ,
                                   không kéo đến hết câu khi có từ khóa y tế phía sau
  ⑧ Medical avoidance keywords  – nhận diện thêm các dạng "né X", "tránh X", "kiêng X"
                                   ngay cả khi không có context bệnh tật rõ ràng
  ⑨ Symptom-first detection     – ưu tiên match triệu chứng TRƯỚC khi check exclusion
  ⑩ Exclusion pattern tightening – thu hẹp exclusion pattern, chỉ áp dụng khi không
                                   có vế kiêng cữ / y tế trong cùng câu (cùng clause)
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
# ③ Negation patterns
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
    "chứ không",
)

# ---------------------------------------------------------------------------
# ⑧ Medical avoidance / kiêng cữ keywords
#    Khi xuất hiện các từ này trong sentence, ưu tiên detect bệnh lý
#    và KHÔNG áp dụng exclusion scope cho phần sau chúng.
# ---------------------------------------------------------------------------
_MEDICAL_AVOIDANCE_KEYWORDS: re.Pattern = re.compile(
     r'\b('
    r'kieng|ne|tranh|han che|giam thieu|'
    r'bac si|bac si dan|bac si khuyen|bac si bao|'
    r'phai kieng|nen kieng|can kieng|nen tranh|phai tranh|'
    r'phai ne|nen ne|'
    r'tieu chay|day bung|kho tieu|buon non|non|'
    r'dau bao tu|dau da day|viem da day|loet da day|'
    r'viem loet|roi loan tieu hoa|he tieu hoa kem|'
    r'suc khoe kem|co van de suc khoe|'
    r'yeu da day|da day yeu|bao tu yeu|bung da yeu|bung yeu'
    r')\b'
)

# ---------------------------------------------------------------------------
# ⑩ Exclusion phrases – chỉ dùng khi câu KHÔNG có từ y tế/kiêng cữ
# ---------------------------------------------------------------------------
_EXCLUSION_PHRASES: frozenset[str] = frozenset({
    "muon an", "mun an", "muon ag", "mun ag",
    "thich an", "thik an", "thich ag", "thik ag",
    "them an", "them ag", "khoai an", "ghoai an", "hao an",
    "muon uong", "mun uong", "muon un", "mun un",
    "thich uong", "thik uong", "them uong",
    "tim quan", "kiem quan", "dat ban", "goi mon", "muon thu", "thich thu"
})

_EXCLUSION_WINDOW: int = 40
_NEGATION_WINDOW: int = 4

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    text = text.lower()
    text = unidecode(text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ngrams_by_size(tokens: list[str], max_n: int) -> list[tuple[str, int, int]]:
    n_tokens = len(tokens)
    result: list[tuple[str, int, int]] = []
    for n in range(min(max_n, n_tokens), 0, -1):
        for i in range(n_tokens - n + 1):
            result.append((" ".join(tokens[i : i + n]), i, i + n))
    return result


# ---------------------------------------------------------------------------
# ① Synonym / variant expansion
# ---------------------------------------------------------------------------
_DEGREE_PREFIXES: tuple[str, ...] = (
    "dau",
    "bi dau",
    "mac",
    "bi mac",
    "mac phai",
    "mac benh",
    "bi",
    "co",
    "co van de",
    "chuan doan",
)

_DEGREE_SUFFIXES: tuple[str, ...] = (
    "nang",
    "nhe",
    "man tinh",
    "cap tinh",
    "truong dien",
    "lau nam",
    "lau",
    "tiet",
)


def _expand_keyword(kw: str) -> list[str]:
    variants: list[str] = [kw]
    for pre in _DEGREE_PREFIXES:
        variants.append(f"{pre} {kw}")
    for suf in _DEGREE_SUFFIXES:
        variants.append(f"{kw} {suf}")
    seen: set[str] = set()
    unique: list[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique


# ---------------------------------------------------------------------------
# TypedDict
# ---------------------------------------------------------------------------
class MatchDetail(TypedDict):
    health_tag: str
    matched_keyword: str
    score: float
    method: str
    negated: bool


# ---------------------------------------------------------------------------
# ⑦ Helper: Tách câu theo dấu câu và mệnh đề
# ---------------------------------------------------------------------------
def _split_into_clauses(text: str) -> list[tuple[str, int, int]]:
    """
    Tách văn bản thành các mệnh đề dựa trên dấu câu và liên từ đối lập.
    Trả về list[(clause_text, char_start, char_end)].
    """
    # Tách tại dấu câu và các từ nối đối lập
    pattern = r'[.!?,;]|\b(nhung|tuy nhien|song|the nhung|co ma|nhung ma|nen|vi vay)\b'
    clauses = []
    prev_end = 0
    for m in re.finditer(pattern, text):
        clause = text[prev_end:m.start()].strip()
        if clause:
            clauses.append((clause, prev_end, m.start()))
        prev_end = m.end()
    # Phần cuối còn lại
    remainder = text[prev_end:].strip()
    if remainder:
        clauses.append((remainder, prev_end, len(text)))
    return clauses


def _sentence_has_medical_context(sentence_norm: str) -> bool:
    """
    ⑩ Kiểm tra một câu/mệnh đề có chứa từ khóa y tế/kiêng cữ không.
    Nếu có → không áp exclusion scope cho câu này.
    """
    return bool(_MEDICAL_AVOIDANCE_KEYWORDS.search(sentence_norm))


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class HealthRiskDetector:
    """
    Nhận diện rủi ro sức khỏe từ prompt tiếng Việt tự do.

    Cải tiến v3 (so với v2):
    ⑦ Exclusion scope refinement  – không kéo exclusion đến hết câu nếu câu chứa từ kiêng cữ
    ⑧ Medical avoidance keywords  – pattern nhận diện "né", "kiêng", triệu chứng
    ⑨ Clause-level exclusion check – kiểm tra exclusion theo mệnh đề, không theo toàn câu
    ⑩ Exclusion pattern tightening – chỉ áp dụng exclusion khi không có vế kiêng cữ trong clause
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

        self._keyword_index: dict[str, list[str]] = {}
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

                candidates = _expand_keyword(base) if expand_synonyms else [base]

                for kw in candidates:
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
    def _normalize_keep_punct(self,text: str) -> str:
        """
        ⑦ Chuẩn hoá tiếng Việt thành ASCII lowercase, GIỮ dấu câu (,;.!?).
        Đồng thời cô lập dấu câu bằng khoảng trắng để đồng bộ Index Token 100%.
        """
        if not text:
            return ""
            
        text = text.lower()
        text = unidecode(text)
        
        # 1. Thay thế các ký tự đặc biệt khác (ngoài bộ dấu câu cho phép) thành khoảng trắng
        text = re.sub(r"[^a-z0-9\s,;.!?]", " ", text)
        
        # 2. FIX CHÍ MẠNG: Thêm khoảng trắng bọc quanh dấu câu để khi .split() 
        # các từ không bị dính dấu câu vào đuôi (ví dụ: "san," -> "san ,")
        text = re.sub(r"([,;.!?])", r" \1 ", text)
        
        # 3. Làm sạch khoảng trắng thừa
        text = re.sub(r"\s+", " ", text).strip()
        return text
    
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, prompt: str) -> list[str]:
        details = self.detect_with_scores(prompt)
        active_tags: set[str] = {d["health_tag"] for d in details if not d["negated"]}
        return self._collect_risk_tags(active_tags)

    
    def detect_with_scores(self, prompt: str) -> list[MatchDetail]:
        normalized = normalize_text(prompt)
        words_original = prompt.split()

      
        
        # --- BƯỚC 1: Vùng phủ định ---
        normalized_phrases = [normalize_text(p) for p in _NEGATION_PHRASES]
        negation_pattern = r'\b(' + '|'.join(map(re.escape, normalized_phrases)) + r')\b'

        negation_scopes: list[tuple[int, int]] = []
        for neg_match in re.finditer(negation_pattern, normalized):
            neg_start = neg_match.start()
            neg_end = min(len(normalized), neg_start + 45)

            but_match = re.search(r'\b(nhung)\b', normalized[neg_start:neg_end])
            if but_match:
                neg_end = neg_start + but_match.start()

            negation_scopes.append((neg_start, neg_end))

        # --- BƯỚC 2 [v3]: Exclusion scope với kiểm tra y tế theo mệnh đề ---
        exclusion_scopes: list[tuple[int, int]] = []

        # 1. Tách danh sách _EXCLUSION_PHRASES thành 2 nhóm từ đầu (muon, thich...) và từ sau (an, uong...)
        first_words: set[str] = set()
        second_words: set[str] = set()
        
        for phrase in _EXCLUSION_PHRASES:
            parts = phrase.split()
            if len(parts) == 2:
                first_words.add(parts[0])
                second_words.add(parts[1])

        # 2. Tạo Regex linh hoạt: Cho phép xen giữa từ 0 đến 4 từ ngẫu nhiên
        # Sắp xếp theo chiều dài giảm dần để ưu tiên match chính xác
        pattern_1 = "|".join(re.escape(w) for w in sorted(list(first_words), key=len, reverse=True))
        pattern_2 = "|".join(re.escape(w) for w in sorted(list(second_words), key=len, reverse=True))

        exclusion_pattern = (
            r'(?<!\bkhong\b )(?<!\bchang\b )(?<!\bchua\b )'
            r'\b(' + pattern_1 + r')\b'
            r'(?:\s+\w+){0,4}\s+\b(' + pattern_2 + r')\b'
        )

        for ex_match in re.finditer(exclusion_pattern, normalized):
            ex_start = ex_match.start()

            # Kiểm tra "nếu" ở vế trước
            prefix_sentence = normalized[:ex_start]
            if re.search(r'\bneu\b', prefix_sentence):
                continue

            # ⑦ v3 FIX: Xác định ranh giới mệnh đề chứa exclusion match
            # Tìm điểm bắt đầu của mệnh đề hiện tại (sau dấu câu gần nhất)
            clause_start_match = re.search(
                r'[.!?,;]|\b(nhung|tuy nhien|song|the nhung|co ma|nhung ma)\b',
                normalized[:ex_start][::-1]  # tìm ngược
            )
            # Vì search ngược khó, dùng cách khác: tìm dấu câu cuối cùng trước ex_start
            clause_start = 0
            for m in re.finditer(r'[.!?,;]|\b(nhung|tuy nhien|nen|vi vay)\b', normalized[:ex_start]):
                clause_start = m.end()

            # Tìm điểm kết thúc mệnh đề (dấu câu tiếp theo sau ex_start)
            clause_end = len(normalized)
            for m in re.finditer(r'[.!?,;]|\b(nhung|tuy nhien|nen|vi vay|co ma)\b', normalized[ex_start:]):
                clause_end = ex_start + m.start()
                break

            # Lấy nội dung mệnh đề chứa exclusion trigger
            current_clause = normalized[clause_start:clause_end]

            # ⑩ v3: Nếu mệnh đề chứa từ y tế/kiêng cữ → KHÔNG áp exclusion
            if _sentence_has_medical_context(current_clause):
                continue

            # Nếu không có ngữ cảnh y tế, áp dụng exclusion scope
            # nhưng chỉ đến hết mệnh đề hiện tại (không kéo đến hết chuỗi)
            ex_end = clause_end

            # Bảo vệ ngữ cảnh: Bẻ gãy nếu xuất hiện "NHUNG"
            sub_segment = normalized[ex_start:ex_end]
            but_match = re.search(r'\b(nhung)\b', sub_segment)
            if but_match:
                ex_end = ex_start + but_match.start()

            # Chặt scope tại dấu chấm câu thực tế trong văn bản gốc
            tokens_before = normalized[:ex_start].split()
            token_idx = len(tokens_before)
            tokens_match = sub_segment.split()

            for i in range(len(tokens_match)):
                orig_arr_idx = token_idx + i
                if orig_arr_idx >= len(words_original):
                    break

                orig_word = words_original[orig_arr_idx]
                if any(c in orig_word for c in ['.', '?', '!']):
                    sub_words_str = " ".join(tokens_match[:i + 1])
                    find_pos = sub_segment.find(sub_words_str)
                    if find_pos != -1:
                        ex_end = ex_start + find_pos + len(sub_words_str)
                    break

            exclusion_scopes.append((ex_start, ex_end))
        
        # --- BƯỚC 3: Quét n-gram ---
        tokens = normalized.split()
        ngrams = _ngrams_by_size(tokens, self.ngram_max)

        matched_spans: list[tuple[int, int]] = []
        results: list[MatchDetail] = []
        seen_tags: set[str] = set()

        for ngram_text, start, end in ngrams:
            if self._span_covered(start, end, matched_spans):
                continue

            # Tìm char position của ngram trong normalized string
            # Dùng vị trí token để tính char offset chính xác hơn
            char_start = self._token_span_to_char(normalized, tokens, start)

            # --- BƯỚC 4: Kiểm tra exclusion scope ---
            is_excluded = False
            for e_s, e_e in exclusion_scopes:
                if e_s <= char_start < e_e:
                    is_excluded = True
                    break

            if is_excluded:
                continue

            # --- BƯỚC 5: Phủ định ---
            is_neg = False
            if self.detect_negation:
                for n_s, n_e in negation_scopes:
                    if n_s <= char_start < n_e:
                        is_neg = True
                        break

            # --- Exact Match ---
            if ngram_text in self._keyword_index:
                tags = self._keyword_index[ngram_text]
                match_happened = False
                for tag in tags:
                    if tag not in seen_tags:
                        seen_tags.add(tag)
                        match_happened = True
                        results.append({
                            "health_tag": tag,
                            "matched_keyword": ngram_text,
                            "score": 1.0,
                            "method": "exact",
                            "negated": is_neg,
                        })
                if match_happened or len(tags) > 0:
                    matched_spans.append((start, end))
                continue

            # --- Fuzzy Match ---
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
                        results.append({
                            "health_tag": tag,
                            "matched_keyword": best_kw,
                            "score": raw_score / 100.0,
                            "method": "fuzzy",
                            "negated": is_neg,
                        })
                if match_happened or len(tags) > 0:
                    matched_spans.append((start, end))

        return results

    
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _token_span_to_char(normalized: str, tokens: list[str], token_start: int) -> int:
        """
        Tính char offset trong normalized string từ token index.
        Chính xác hơn str.find() vì tránh match sai khi chuỗi con xuất hiện nhiều lần.
        """
        pos = 0
        for i, tok in enumerate(tokens):
            if i == token_start:
                return pos
            pos += len(tok) + 1  # +1 cho khoảng trắng
        return pos

    @staticmethod
    def _span_covered(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
        """⑤ Kiểm tra xem [start, end) có bị phủ bởi span đã match không."""
        for s, e in spans:
            if s <= start and end <= e:
                return True
        return False

    @staticmethod
    def _is_negated(tokens: list[str], keyword_start: int) -> bool:
        """③ Kiểm tra keyword có bị phủ định không."""
        if keyword_start == 0:
            return False

        window_start = max(0, keyword_start - _NEGATION_WINDOW)
        window_tokens = tokens[window_start:keyword_start]
        window_text = " ".join(window_tokens)
        window_norm = normalize_text(window_text)

        for phrase in _NEGATION_PHRASES:
            phrase_norm = normalize_text(phrase)
            if re.search(r'\b' + re.escape(phrase_norm) + r'\b', window_norm):
                return True

        return False

    def _collect_risk_tags(self, health_tags: set[str]) -> list[str]:
        """Gộp và dedup risk tags từ mapping."""
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