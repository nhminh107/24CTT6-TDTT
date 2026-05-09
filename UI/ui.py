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




def generate_response(api_response: dict) -> dict:
    if not api_response or api_response.get("status") != "success":
        return {"text": "Lỗi hệ thống...", "data": []}

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


def call_restaurant_api(user_input):
    
    url="http://127.0.0.1:8000/prompt"
    

    payload = {"prompt": user_input}
    
    # try:
    #     response = requests.post(url, json=payload)
    #     if response.status_code == 200:
    #         return response.json() 
    #     else:
    #         return {"status": "error", "result": []}
    # except Exception as e:
    #     return {"status": "error", "message": str(e)}
    
    
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
           
            response = call_restaurant_api(user_input)

            fake_response={
                "status":"success",
                "result":[
                    {
                    "id":"0001",
                    "name":"Ăn Thôi",
                    "address":"114 Bạch Đằng, Hải Châu, Đà Nẵng",
                    "lat":16.0682463,
                    "lng":108.2248133,
                    "avg_price":150000,
                    "shu":3,
                    "star":4.8,
                    "meals":[
                    "trưa",
                    "tối"
                    ],
                    "semantic_text":"Quán Việt nổi tiếng nằm ngay bên sông Hàn, được Michelin ghi nhận. Nổi bật với cơm chiên hải sản, sò điệp nướng và tôm tỏi. Luôn đông khách, cần lấy số thứ tự chờ bàn. Không gian thoáng mát, phục vụ nhanh và thân thiện.",
                    "image_url":"https:\/\/encrypted-tbn0.gstatic.com\/images?q=tbn:ANd9GcT-1PzC5iv80HA3vJ0ziU1rzNCMnBRrLdSPgg&s",
                    "type":[
                    "Quán Việt"
                    ],
                    "phone_num":"+84 987 824 285"
                },
                {
                    "id":"0002",
                    "name":"Hải sản Mộc Quán Đà Nẵng",
                    "address":"26 Tô Hiến Thành, An Hải, Đà Nẵng",
                    "lat":16.063997,
                    "lng":108.2415015,
                    "avg_price":300000,
                    "shu":3,
                    "star":4.8,
                    "meals":[
                    "trưa",
                    "tối"
                    ],
                    "semantic_text":"Nhà hàng hải sản 5 tầng nổi tiếng nhất Đà Nẵng, được Michelin ghi nhận. Hải sản tươi sống phong phú: tôm hùm, cua, tôm, ngao. Nhân viên nhiệt tình lột vỏ tôm và xử lý hải sản trực tiếp tại bàn. Cần đặt bàn trước vì luôn đông khách.",
                    "image_url":"https:\/\/hellodanang.vn\/wp-content\/uploads\/2025\/12\/bai-viet-danh-gia-ve-hai-san-moc-quan-da-nang-1764818921.jpg",
                    "type":[
                    "Quán Việt"
                    ],
                    "phone_num":"+84 905 665 058"
                },
                {
                    "id":"0003",
                    "name":"Nhà Bếp Xưa Restaurant",
                    "address":"64B Hà Bổng, An Hải, Đà Nẵng",
                    "lat":16.066058,
                    "lng":108.2443163,
                    "avg_price":120000,
                    "shu":3,
                    "star":4.8,
                    "meals":[
                    "trưa",
                    "tối"
                    ],
                    "semantic_text":"Quán ăn kiểu xưa mang nét mộc mạc với tre, đèn lồng và không gian ấm cúng. Chuyên các món Việt đặc sắc như Mỳ Quảng, bánh xèo, bún thịt nướng. Không gian nhỏ, thường xuyên đông khách du lịch và dân địa phương.",
                    "image_url":"https:\/\/dynamic-media-cdn.tripadvisor.com\/media\/photo-o\/2c\/ed\/e7\/e6\/caption.jpg?w=900&h=500&s=1",
                    "type":[
                    "Quán Việt"
                    ],
                    "phone_num":"+84 906 123 858"
                }
            ]
        }
            response=fake_response
            
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

st.markdown("""
<div class="main-header">
    <h1>🍅 Trợ lý AI</h1>
    <p>Trợ lý tư vấn ẩm thực thông minh · Phân tích dữ liệu thời gian thực</p>
</div>
""", unsafe_allow_html=True)






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
                            st.image(res.get("image_url"), use_container_width=True)
                        with col_info:
                            st.subheader(res.get("name", "Nhà hàng"))
                            st.write(f"📍 {res.get('address')}")
                            st.write(f"⭐ {res.get('star')} | 💰 ~{res.get('avg_price', 0):,.0f}đ")
                            with st.expander("Xem chi tiết món ăn & mô tả"):
                                st.write(res.get("semantic_text"))
                                if res.get("meals"):
                                    st.write(f"🍴 Phục vụ: {', '.join(res.get('meals'))}")

if user_prompt := st.chat_input("Nhập câu hỏi tư vấn..."):
    process_prompt(user_prompt)
    st.rerun()