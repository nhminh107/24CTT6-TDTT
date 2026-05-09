"""
AI Advisor Portal - Streamlit Application
Chuyên gia Python Web Developer
Giao diện chat tư vấn AI chuyên nghiệp với dark theme, sidebar lịch sử, và kết quả Markdown.
"""

import streamlit as st
import time
import random
import pandas as pd
import requests
from typing import Optional
from streamlit_searchbox import st_searchbox
from urllib.parse import quote

API_BASE_URL = "http://127.0.0.1:8000/api/v1"



st.set_page_config(
    page_title="Trợ lý ẩm thực",
    page_icon=":tomato:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Import Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

/* ── CSS Variables ── */
:root {
    --bg-deep:       #0E1117;
    --bg-panel:      #161B27;
    --bg-card:       #1C2333;
    --accent-start:  #7C3AED;
    --accent-end:    #2563EB;
    --accent-glow:   rgba(124, 58, 237, 0.35);
    --text-primary:  #F1F5F9;
    --text-muted:    #94A3B8;
    --border:        rgba(148, 163, 184, 0.12);
    --success:       #10B981;
    --radius:        14px;
    --shadow:        0 8px 32px rgba(0,0,0,0.45);
}

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--bg-deep) !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1220 0%, #111827 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* ── App logo/title area ── */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 1rem 0.5rem 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.sidebar-brand .brand-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    box-shadow: 0 4px 16px var(--accent-glow);
    flex-shrink: 0;
}
.sidebar-brand .brand-text h2 {
    margin: 0; font-size: 1rem; font-weight: 700;
    background: linear-gradient(135deg, #A78BFA, #60A5FA);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1.2;
}
.sidebar-brand .brand-text span {
    font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Sidebar section label ── */
.sidebar-section-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--text-muted);
    padding: 0 0.5rem; margin: 0.5rem 0 0.6rem;
}

/* ── History item ── */
.history-item {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.6rem 0.85rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex; align-items: flex-start; gap: 8px;
}
.history-item:hover {
    background: rgba(124, 58, 237, 0.15);
    border-color: rgba(124, 58, 237, 0.4);
    transform: translateX(3px);
}
.history-item .hi-icon { font-size: 14px; margin-top: 1px; flex-shrink: 0; }
.history-item .hi-text {
    font-size: 0.78rem; color: var(--text-muted);
    line-height: 1.4; overflow: hidden;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

/* ── Status indicator ── */
.status-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 50px;
    padding: 0.35rem 0.85rem;
    font-size: 0.75rem; color: #34D399;
    margin-top: 1rem;
}
.status-dot {
    width: 8px; height: 8px;
    background: var(--success); border-radius: 50%;
    box-shadow: 0 0 6px var(--success);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.85); }
}

/* ── Main header ── */
.main-header {
    text-align: center;
    padding: 3rem 1rem 2rem;
}
.main-header h1 {
    font-size: clamp(1.8rem, 4vw, 2.8rem);
    font-weight: 700;
    background: linear-gradient(135deg, #A78BFA 0%, #60A5FA 50%, #34D399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.main-header p {
    color: var(--text-muted); font-size: 1rem;
}

/* ── Suggestion button chips ── */
.suggestion-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.75rem;
    max-width: 800px;
    margin: 0 auto 2rem;
}
.suggestion-chip {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.9rem 1rem;
    cursor: pointer;
    transition: all 0.25s ease;
    text-align: left;
}
.suggestion-chip:hover {
    border-color: rgba(124, 58, 237, 0.5);
    background: rgba(124, 58, 237, 0.08);
    box-shadow: 0 4px 20px var(--accent-glow);
    transform: translateY(-2px);
}
.suggestion-chip .sc-icon { font-size: 1.3rem; margin-bottom: 0.4rem; }
.suggestion-chip .sc-title { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
.suggestion-chip .sc-desc { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 1rem !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background: rgba(124, 58, 237, 0.08) !important;
    border-color: rgba(124, 58, 237, 0.25) !important;
}

/* ── Advice card ── */
.advice-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid;
    border-image: linear-gradient(180deg, var(--accent-start), var(--accent-end)) 1;
    border-radius: var(--radius);
    padding: 1.5rem 1.75rem;
    margin: 1rem 0;
    box-shadow: var(--shadow), 0 0 40px rgba(124, 58, 237, 0.06);
    position: relative;
    overflow: hidden;
}
.advice-card::before {
    content: '';
    position: absolute; top: 0; right: 0;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(124,58,237,0.08) 0%, transparent 70%);
    pointer-events: none;
}

/* ── Action buttons ── */
.action-bar {
    display: flex; gap: 0.5rem; flex-wrap: wrap;
    margin-top: 1rem; padding-top: 1rem;
    border-top: 1px solid var(--border);
}
.action-btn {
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.4rem 0.85rem;
    font-size: 0.78rem; color: var(--text-muted);
    cursor: pointer; display: inline-flex; align-items: center; gap: 5px;
    transition: all 0.2s;
}
.action-btn:hover {
    background: rgba(124,58,237,0.15); color: #A78BFA;
    border-color: rgba(124,58,237,0.4);
}

/* ── Chat input bar ── */
[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 50px !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--text-primary) !important;
}

/* ── Streamlit status widget ── */
[data-testid="stStatus"] {
    background: var(--bg-card) !important;
    border: 1px solid rgba(124,58,237,0.3) !important;
    border-radius: var(--radius) !important;
}

/* ── Tables ── */
table {
    border-collapse: collapse; width: 100%;
    font-size: 0.85rem; border-radius: 8px; overflow: hidden;
}
thead tr { background: rgba(124,58,237,0.2); }
th { padding: 0.6rem 1rem; text-align: left; color: #A78BFA; font-weight: 600; }
td { padding: 0.55rem 1rem; border-bottom: 1px solid var(--border); }
tr:hover td { background: rgba(255,255,255,0.03); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.2); border-radius: 10px; }

/* ── Mobile responsive ── */
@media (max-width: 768px) {
    .main-header { padding: 1.5rem 0.5rem 1rem; }
    .suggestion-grid { grid-template-columns: 1fr 1fr; }
    .advice-card { padding: 1rem 1.2rem; }
}
</style>
""", unsafe_allow_html=True)


def fetch_map_suggestions(query: str) -> list:
    if not query:
        return []

    url = f"{API_BASE_URL}/maps/suggestions"
    try:
        response = requests.get(url, params={"q": query}, timeout=8)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    return []


def location_search_callback(search_text: str) -> list:
    suggestions = fetch_map_suggestions(search_text)
    st.session_state.location_suggestions = suggestions
    return [item["description"] for item in suggestions]


def format_phone_number(phone_value: Optional[object]) -> str:
    if phone_value is None:
        return ""
    try:
        phone_float = float(phone_value)
        phone_int = int(phone_float)
        if phone_int == 0 and str(phone_value).strip().startswith("0"):
            phone_str = str(phone_value).strip()
            return phone_str[:-2] if phone_str.endswith(".0") else phone_str
        return f"{phone_int}"
    except (ValueError, TypeError):
        phone_str = str(phone_value).strip()
        if phone_str.endswith(".0"):
            phone_str = phone_str[:-2]
        return phone_str




def generate_response(api_response: dict) -> dict:
    if not api_response:
        return {"text": "Lỗi hệ thống...", "data": []}

    status = api_response.get("status")
    if status != "success":
        message = (
            api_response.get("message")
            or api_response.get("detail")
            or "Lỗi hệ thống..."
        )
        return {"text": message, "data": []}

    restaurant_list = api_response.get("result", [])
    
    # XỬ LÝ LỖI URL: Loại bỏ ký tự \/ bằng cách replace
    # Chúng ta lặp qua từng nhà hàng và sửa lại image_url
    for res in restaurant_list:
        if "image_url" in res and isinstance(res["image_url"], str):
            res["image_url"] = res["image_url"].replace("\/", "/")

    count = len(restaurant_list)
    message = f"Dạ, mình tìm thấy **{count} nhà hàng** nè! 👇" if count > 0 else "Không tìm thấy kết quả."

    return {
        "text": message,
        "data": restaurant_list
    }


def call_restaurant_api(user_input: str, place_id: Optional[str] = None) -> dict:
    url = f"{API_BASE_URL}/prompt"
    payload = {"prompt": user_input}
    if place_id:
        payload["place_id"] = place_id

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {
            "status": "error",
            "message": response.text,
            "result": [],
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "result": []}
    
    
def process_prompt(user_input: str):
    """Thêm tin nhắn user, hiện status spinner, rồi thêm phản hồi AI."""
    msg_id = str(int(time.time() * 1000))

    # Thêm tin nhắn người dùng
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "id": msg_id + "_u",
    })

    with st.spinner("Đang suy nghĩ..."):
        try:
            place_id = st.session_state.get("place_id")
            response = call_restaurant_api(user_input, place_id=place_id)
            
            final_result = generate_response(response)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_result["text"], # Lưu câu chào
                "restaurants": final_result["data"], # Lưu list nhà hàng để  vẽ Card
                "id": msg_id + "_a",
            })
            
        except Exception as e:
            st.error(f"Lỗi kết nối: {e}")
        


if st.session_state.get("pending_prompt"):
    prompt_to_process = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    process_prompt(prompt_to_process)
    st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "place_id" not in st.session_state:
    st.session_state.place_id = None
if "place_label" not in st.session_state:
    st.session_state.place_label = ""
if "location_suggestions" not in st.session_state:
    st.session_state.location_suggestions = []


st.markdown("""
<div class="main-header">
    <h1>🍅 Trợ lý AI</h1>
    <p>Trợ lý tư vấn ẩm thực thông minh · Phân tích dữ liệu thời gian thực</p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="sidebar-section-label">Vị trí hiện tại</div>',
    unsafe_allow_html=True,
)
selected_label = st_searchbox(
    location_search_callback,
    placeholder="Nhập vị trí hiện tại...",
    key="location_searchbox",
)

if selected_label:
    matched = next(
        (
            item
            for item in st.session_state.location_suggestions
            if item["description"] == selected_label
        ),
        None,
    )
    if matched:
        st.session_state.place_id = matched["place_id"]
        st.session_state.place_label = matched["description"]

if st.session_state.place_label:
    st.markdown(f"**Đã chọn:** {st.session_state.place_label}")
else:
    st.caption("Chưa chọn vị trí, hệ thống dùng mặc định.")






# ── 7c. Render lịch sử hội thoại ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🧠"):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            # 1. Hiển thị thông báo/câu chào (Advice Card)
            st.markdown(
                f'<div class="advice-card">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
            
            # 2. HIỂN THỊ DANH SÁCH NHÀ HÀNG (Phần bổ sung quan trọng)
            if "restaurants" in msg and msg["restaurants"]:
                for res in msg["restaurants"]:
                    # Dùng container có border để tạo hiệu ứng thẻ (Card)
                    with st.container(border=True):
                        col_img, col_info = st.columns([1, 2])
                        with col_img:
                            st.image(
                                res.get("image_url"),
                                width=200,
                            )
                        with col_info:
                            st.subheader(res.get("name", "Nhà hàng"))
                            st.write(f"📍 {res.get('address')}")
                            st.write(f"⭐ {res.get('star')} | 💰 ~{res.get('avg_price', 0):,.0f}đ")
                            phone_display = format_phone_number(res.get("phone_num"))
                            if phone_display:
                                phone_link = ''.join(ch for ch in phone_display if ch.isdigit() or ch == '+')
                                if phone_link:
                                    st.markdown(
                                        f"📞 <a class='action-btn' href='tel:{phone_link}'>Gọi {phone_display}</a>",
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.write(f"📞 {phone_display}")
                            address = res.get("address")
                            if address:
                                map_link = f"https://www.google.com/maps/search/?api=1&query={quote(address)}"
                                st.markdown(f"[🧭 Xem trên Google Maps]({map_link})")
                            with st.expander("Xem chi tiết món ăn & mô tả"):
                                st.write(res.get("semantic_text"))
                                if res.get("meals"):
                                    st.write(f"🍴 Phục vụ: {', '.join(res.get('meals'))}")

if user_prompt := st.chat_input("Nhập câu hỏi tư vấn..."):
    process_prompt(user_prompt)
    st.rerun()
