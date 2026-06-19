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
    r'phai kieng|nen kieng|can kieng|nen tranh|phai tranh|kieng tuyet doi|'
    r'phai ne|nen ne|'
    r'di ung|man ngua|doc hai|nguon doc|'
    r'mang thai|mang bau|co bau|ba bau|sinh de|'
    r'tieu chay|day bung|kho tieu|buon non|non|'
    r'dau bao tu|dau da day|viem da day|loet da day|'
    r'viem loet|roi loan tieu hoa|he tieu hoa kem|'
    r'suc khoe kem|co van de suc khoe|'
    r'yeu da day|da day yeu|bao tu yeu|bung da yeu|bung yeu|'
    r'tieu duong|tieu duog|huyet ap|tim mach'  # <-- BỔ SUNG "tieu duong" VÀ CÁC BỆNH NỀN TẠI ĐÂY
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
    "tim quan", "kiem quan", "dat ban", "goi mon", "muon thu", "thich thu",
    
    # --- NHÓM DỰ ĐỊNH / KẾ HOẠCH (Giống "định đi ăn") ---
    "dinh di an", "dinh di ag", "dinh an", "dinh ag",
    "tinh di an", "tinh di ag", "tinh an", "tinh ag",       # tính đi ăn / tính ăn
    "sap di an", "sap di ag", "sap an", "sap ag",           # sắp đi ăn / sắp ăn
    "chuan bi an", "chuan bi ag", "cb an", "cb ag",         # chuẩn bị ăn (cb ăn)
    "ke hoach an", "ke hoach ag",                           # kế hoạch ăn

    # --- NHÓM RỦ RÊ / TỤ TẬP / HẸN HÒ ---
    "ru di an", "ru di ag", "ru nhau an", "ru nhau ag",     # rủ đi ăn / rủ nhau ăn
    "hen di an", "hen di ag", "hen nhau an", "hen nhau ag", # hẹn đi ăn / hẹn nhau ăn
    "tu tap an", "tu tap ag", "tu tap uong",                # tụ tập ăn / tụ tập uống
    "lien hoan an", "lien hoan ag",                         # liên hoan ăn
    "ru re an", "ru re ag",                                 # rủ rê ăn

    # --- NHÓM NHU CẦU PHÁT SINH TỨC THỜI ---
    "can di an", "can di ag", "can an", "can ag",           # cần đi ăn / cần ăn
    "qua di an", "qua di ag",                               # qua đi ăn (Ví dụ: "Qua đi ăn hải sản...")
    "ghe di an", "ghe an", "ghe ag",                        # ghé đi ăn / ghé ăn
    "ra di an", "ra an", "ra ag",                           # ra đi ăn / ra ăn (Ví dụ: "Ra ăn hải sản...")
    "xuong di an", "xuong an",                              # xuống đi ăn / xuống ăn
    
    # --- NHÓM THỬ NGHIỆM ĐỒ ĂN MỚI ---
    "trai nghiem an", "trai nghiem ag",                     # trải nghiệm ăn
    "an thu", "ag thu", "uong thu"                          # ăn thử / uống thử
    ,
    "quan bia", "tiem bia", "uong bia", "quan nhau", "tiem nhau", "di nhau",
    "nguoi ta noi",
    "moi nguoi noi",
    "hay noi rang",
    "nghe noi",
    "theo nghien cuu",
    "theo bac si",        # "theo bác sĩ, huyết áp cao là..." (nói chung chung)
    "noi chung",
    "vi du nhu",
    "giai thich rang",
    

})

# Pattern dùng chung — định nghĩa 1 lần ở đầu file, dùng lại ở mọi chỗ
_CLAUSE_SEPARATOR: str = (
    r'[.!?,;]|\b(nhung|tuy nhien|song|the nhung|co ma|nhung ma|nen|vi vay|ma)\b'
)

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
    pattern = _CLAUSE_SEPARATOR
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

        # Tách danh sách _EXCLUSION_PHRASES thành 2 nhóm: Cụm cố định và Cụm linh hoạt (có chứa ăn/uống/ag/un)
        fixed_phrases = []
        flexible_first = set()
        flexible_second = set()

        for phrase in _EXCLUSION_PHRASES:
            parts = phrase.split()
            if len(parts) == 2:
                # Nếu là các cụm cố định không có cấu trúc hành động xen kẽ, giữ nguyên chuỗi
                if parts[0] in ["quan", "tiem", "di", "uong", "eat", "giam", "an"] and parts[1] in ["bia", "nhau", "chay", "clean", "can", "kieng"]:
                    fixed_phrases.append(re.escape(phrase))
                else:
                    flexible_first.add(parts[0])
                    flexible_second.add(parts[1])
            else:
                fixed_phrases.append(re.escape(phrase))

        # Build regex cho nhóm linh hoạt (cho phép xen giữa 0-4 từ)
        pattern_1 = "|".join(re.escape(w) for w in sorted(list(flexible_first), key=len, reverse=True))
        pattern_2 = "|".join(re.escape(w) for w in sorted(list(flexible_second), key=len, reverse=True))
        
        flexible_regex = r'\b(' + pattern_1 + r')\b(?:(?!\b(?:bi|co|nhung|mac)\b)\s+\w+){0,4}\s+\b(' + pattern_2 + r')\b'
        
        # Build regex cho nhóm cụm cố định (match chính xác dính liền)
        fixed_regex = r'\b(' + "|".join(sorted(fixed_phrases, key=len, reverse=True)) + r')\b'

        # Gom chung lại thành pattern hoàn chỉnh
        exclusion_pattern = (
            r'(?<!\bkhong\b )(?<!\bchang\b )(?<!\bchua\b )'
            r'(?:' + flexible_regex + r'|' + fixed_regex + r')'
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
            for m in re.finditer(_CLAUSE_SEPARATOR, normalized[:ex_start]):
                clause_start = m.end()

            # Tìm điểm kết thúc mệnh đề (dấu câu tiếp theo sau ex_start)
            clause_end = len(normalized)
            for m in re.finditer(_CLAUSE_SEPARATOR, normalized[ex_start:]):
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
            
            if len(ngram_text) <= 3:
                continue

            tokens_count = len(ngram_text.split())
            dynamic_threshold = self.fuzzy_threshold
            if tokens_count <= 2:
                dynamic_threshold = 95
            elif tokens_count == 3:
                dynamic_threshold = 90

            result = fuzz_process.extractOne(
                ngram_text,
                self._all_keywords,
                scorer=fuzz.ratio,
                score_cutoff=dynamic_threshold,
            )
            if result is not None:
                best_kw: str = result[0]
                raw_score: float = result[1]
                if len(ngram_text) <= 4 and abs(len(best_kw) - len(ngram_text)) > 0:
                    continue
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

    # def detect_with_scores(self, prompt: str) -> list[MatchDetail]:
    #     normalized = normalize_text(prompt)
    #     words_original = prompt.split()

    #     # --- BƯỚC 1: QUÉT N-GRAM ĐẠI TRÀ ĐỂ THU THẬP TẤT CẢ CÁC MATCH TIỀM NĂNG ---
    #     tokens = normalized.split()
    #     ngrams = _ngrams_by_size(tokens, self.ngram_max)

    #     matched_spans: list[tuple[int, int]] = []
    #     raw_matches: list[dict] = []  # Nơi lưu tạm các match trước khi thẩm định

    #     for ngram_text, start, end in ngrams:
    #         if self._span_covered(start, end, matched_spans):
    #             continue

    #         # Tính toán vị trí ký tự chính xác của n-gram trong chuỗi normalized
    #         char_start = self._token_span_to_char(normalized, tokens, start)
    #         char_end = char_start + len(ngram_text)

    #         # 1. Thử nghiệm Exact Match
    #         if ngram_text in self._keyword_index:
    #             tags = self._keyword_index[ngram_text]
    #             if len(tags) > 0:
    #                 for tag in tags:
    #                     raw_matches.append({
    #                         "health_tag": tag,
    #                         "matched_keyword": ngram_text,
    #                         "score": 1.0,
    #                         "method": "exact",
    #                         "char_start": char_start,
    #                         "char_end": char_end
    #                     })
    #                 matched_spans.append((start, end))
    #                 continue

    #         # 2. Thử nghiệm Fuzzy Match
    #         tokens_in_ngram = ngram_text.split()
    #         all_stopwords = all(t in _VI_STOPWORDS for t in tokens_in_ngram)
    #         all_stopwords = (ngram_text in _VI_STOPWORDS) or all_stopwords
    #         if all_stopwords or not self._all_keywords or len(ngram_text) <= 3:
    #             continue

    #         result = fuzz_process.extractOne(
    #             ngram_text,
    #             self._all_keywords,
    #             scorer=fuzz.ratio,
    #             score_cutoff=self.fuzzy_threshold,
    #         )
    #         if result is not None:
    #             best_kw: str = result[0]
    #             raw_score: float = result[1]
    #             if len(ngram_text) <= 4 and abs(len(best_kw) - len(ngram_text)) > 0:
    #                 continue
                
    #             tags = self._keyword_index.get(best_kw, [])
    #             if len(tags) > 0:
    #                 for tag in tags:
    #                     raw_matches.append({
    #                         "health_tag": tag,
    #                         "matched_keyword": best_kw,
    #                         "score": raw_score / 100.0,
    #                         "method": "fuzzy",
    #                         "char_start": char_start,
    #                         "char_end": char_end
    #                     })
    #                 matched_spans.append((start, end))

    #     # --- BƯỚC 2: THẨM ĐỊNH NGỮ CẢNH CHO TỪNG MATCH (ĐẢO NGƯỢC LOGIC) ---
    #     results: list[MatchDetail] = []
    #     seen_tags: set[str] = set()
        
    #     # Tiền phân tách pattern để phục vụ việc xác định mệnh đề
    #     clause_separator = r'[.!?,;]|\b(nhung|tuy nhien|nen|vi vay|co ma|ma|nhung ma)\b'

    #     for match in raw_matches:
    #         tag = match["health_tag"]
    #         c_start = match["char_start"]
            
    #         # Nếu tag này đã được ghi nhận rồi thì bỏ qua để tránh trùng lặp
    #         if tag in seen_tags:
    #             continue

    #         # A. Xác định ranh giới mệnh đề chứa từ khóa (Clause Bound)
    #         clause_start = 0
    #         for m in re.finditer(clause_separator, normalized[:c_start]):
    #             clause_start = m.end()

    #         clause_end = len(normalized)
    #         for m in re.finditer(clause_separator, normalized[c_start:]):
    #             clause_end = c_start + m.start()
    #             break

    #         current_clause = normalized[clause_start:clause_end]

    #         # B. Thẩm định điều kiện PHỦ ĐỊNH (Negation Check)
    #         is_neg = False
    #         if self.detect_negation:
    #             normalized_neg_phrases = [normalize_text(p) for p in _NEGATION_PHRASES]
    #             negation_pattern = r'\b(' + '|'.join(map(re.escape, normalized_neg_phrases)) + r')\b'
                
    #             for neg_m in re.finditer(negation_pattern, current_clause):
    #                 if clause_start + neg_m.start() < c_start:
    #                     sub_seg = current_clause[neg_m.start(): c_start - clause_start]
    #                     if not re.search(r'\b(nhung)\b', sub_seg):
    #                         is_neg = True
    #                         break

    #         # C. Thẩm định điều kiện LOẠI TRỪ SỞ THÍCH (Exclusion Check)
    #         fixed_phrases = []
    #         flexible_first = set()
    #         flexible_second = set()
    #         for phrase in _EXCLUSION_PHRASES:
    #             parts = phrase.split()
    #             if len(parts) == 2:
    #                 if parts[0] in ["quan", "tiem", "di", "uong", "eat", "giam", "an"] and parts[1] in ["bia", "nhau", "chay", "clean", "can", "kieng"]:
    #                     fixed_phrases.append(re.escape(phrase))
    #                 else:
    #                     flexible_first.add(parts[0])
    #                     flexible_second.add(parts[1])
    #             else:
    #                 fixed_phrases.append(re.escape(phrase))

    #         pattern_1 = "|".join(re.escape(w) for w in sorted(list(flexible_first), key=len, reverse=True))
    #         pattern_2 = "|".join(re.escape(w) for w in sorted(list(flexible_second), key=len, reverse=True))
    #         flexible_regex = r'\b(' + pattern_1 + r')\b(?:(?!\b(?:bi|co|nhung|mac)\b)\s+\w+){0,4}\s+\b(' + pattern_2 + r')\b'
    #         fixed_regex = r'\b(' + "|".join(sorted(fixed_phrases, key=len, reverse=True)) + r')\b'
    #         exclusion_pattern = r'(?<!\bkhong\b )(?<!\bchang\b )(?<!\bchua\b )(?:' + flexible_regex + r'|' + fixed_regex + r')'

    #         has_exclusion_trigger = False
    #         is_saved_by_medical = False

    #         for ex_m in re.finditer(exclusion_pattern, current_clause):
    #             ex_match_start_global = clause_start + ex_m.start()
                
    #             # Chỉ xử lý nếu trigger sở thích xuất hiện trước từ khóa rủi ro
    #             if ex_match_start_global < c_start:
    #                 has_exclusion_trigger = True
                    
    #                 # --- NÚT THẮT CHÍ MẠNG: GIỚI HẠN PHẠM VI ẢNH HƯỞNG ---
    #                 # Tính toán ex_end ảo dựa trên bán kính hẹp (25 kí tự) tính từ trigger sở thích
    #                 ex_end_virtual = min(clause_end, ex_match_start_global + 25)
                    
    #                 # Kiểm tra xem ngay vế sau của từ sở thích (vùng hẹp) có chứa ngữ cảnh y tế ngay không
    #                 # Ví dụ: "trưa ăn đồ Nhật sashimi... mà bác sĩ dặn kiêng" -> "đồ Nhật sashimi" không chứa từ y tế
    #                 # Nhưng nếu cấu trúc câu lồng ghép y tế cục bộ, bộ lọc này bảo vệ tag.
    #                 if _sentence_has_medical_context(normalized[ex_match_start_global:ex_end_virtual]):
    #                     is_saved_by_medical = True
    #                 break

    #         # Kiểm tra bối cảnh y tế cục bộ ngay trong mệnh đề hiện tại
    #         # Bỏ kiểm tra toàn cục normalized để tránh bị leak từ mệnh đề quá khứ của câu chuyện cũ (Test 33)
    #         has_medical_in_clause = _sentence_has_medical_context(current_clause) or is_saved_by_medical

    #         # LOGIC QUYẾT ĐỊNH CHỐT:
    #         # Nếu dính trigger sở thích VÀ mệnh đề hiện tại hoàn toàn trống thông tin y tế 
    #         # -> Kích hoạt loại trừ (loại bỏ tag này)
    #         if has_exclusion_trigger and not has_medical_in_clause:
    #             continue

    #         # D. Nếu vượt qua tất cả các bộ lọc, chính thức ghi nhận tag rủi ro
    #         seen_tags.add(tag)
    #         results.append({
    #             "health_tag": tag,
    #             "matched_keyword": match["matched_keyword"],
    #             "score": match["score"],
    #             "method": match["method"],
    #             "negated": is_neg,
    #         })

    #     return results
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