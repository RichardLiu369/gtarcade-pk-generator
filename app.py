import json
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv
from openai import OpenAI

from prompt_template import (
    SYSTEM_PROMPT,
    TOPIC_CATEGORIES,
    build_user_prompt,
)

# ── Config ────────────────────────────────────────────────────────────────
load_dotenv()
HISTORY_FILE = Path(__file__).parent / "history.yaml"
CUSTOM_MODELS_FILE = Path(__file__).parent / "custom_models.yaml"


# ── Data Helpers ──────────────────────────────────────────────────────────
def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    return []


def save_history(entry: dict):
    history = load_history()
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(history, f, allow_unicode=True, default_flow_style=False)


def delete_history(index: int):
    history = load_history()
    if 0 <= index < len(history):
        history.pop(index)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            yaml.dump(history, f, allow_unicode=True, default_flow_style=False)


def clear_all_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        yaml.dump([], f)


def load_custom_models() -> dict:
    if CUSTOM_MODELS_FILE.exists():
        with open(CUSTOM_MODELS_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_custom_models(models: dict):
    with open(CUSTOM_MODELS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(models, f, allow_unicode=True, default_flow_style=False)


# ── API Helpers ───────────────────────────────────────────────────────────
def make_client(api_key: str, base_url: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url)


def parse_json_response(raw: str) -> dict:
    if not raw or not raw.strip():
        raise ValueError("模型返回了空内容")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json|JSON)?\s*\n?", "", cleaned)
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"无法解析 JSON。\n\n模型原始返回:\n{raw[:1000]}")


def generate_pk(client: OpenAI, model: str, category_zh: str, extra_hint: str) -> dict:
    cat = TOPIC_CATEGORIES[category_zh]
    user_prompt = build_user_prompt(category_zh, cat["en"], cat["desc"], extra_hint)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.85,
        max_tokens=4000,
    )
    raw = resp.choices[0].message.content
    return parse_json_response(raw)


def render_markdown(data: dict) -> str:
    return f"""# 🎮 PK Activity | PK 活动

## 📌 标题 Title
**🇨🇳** {data["title_zh"]}
**🇬🇧** {data["title_en"]}

## 💬 话题 Topic
**🇨🇳** {data["topic_zh"]}
**🇬🇧** {data["topic_en"]}

## ✅ 正方 Pro
**🇨🇳** {data["pro_zh"]}
**🇬🇧** {data["pro_en"]}

## ❌ 反方 Con
**🇨🇳** {data["con_zh"]}
**🇬🇧** {data["con_en"]}

## 🎨 GPT Image2 Prompt
```
{data["gpt_image_prompt"]}
```

## 🎨 NanoBananaPro Prompt
```
{data["nanobanana_prompt"]}
```

---
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")} | GTarcade PK Generator*
"""


# ── Page Config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GTarcade PK Generator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Apple-Inspired CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --spring-settle: cubic-bezier(0.2, 0.8, 0.2, 1);
    --spring-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
    --spring-damping: cubic-bezier(0.22, 1.2, 0.36, 1);
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.08);
    --shadow-lg: 0 10px 40px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.06);
    --shadow-xl: 0 20px 60px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.05);
    --blur: saturate(180%) blur(20px);
    --radius: 16px;
    --radius-lg: 20px;
    --accent: #007AFF;
    --accent-light: rgba(0, 122, 255, 0.08);
    --green: #34C759;
    --red: #FF3B30;
    --text-primary: #1d1d1f;
    --text-secondary: #86868b;
    --text-tertiary: #aeaeb2;
    --surface: rgba(255,255,255,0.72);
    --surface-solid: #ffffff;
    --separator: rgba(0,0,0,0.06);
}

/* ── Spring Damping Keyframes ── */
/* Hero: overshoot → bounce back → settle */
@keyframes heroSpring {
    0%   { opacity: 0; transform: translateY(30px) scale(0.95); }
    40%  { opacity: 1; transform: translateY(-8px) scale(1.02); }
    55%  { transform: translateY(4px) scale(0.99); }
    70%  { transform: translateY(-2px) scale(1.005); }
    82%  { transform: translateY(1px) scale(0.998); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* Card: spring entrance with damping */
@keyframes cardSpring {
    0%   { opacity: 0; transform: translateY(24px) scale(0.96); }
    35%  { opacity: 1; transform: translateY(-6px) scale(1.015); }
    55%  { transform: translateY(3px) scale(0.995); }
    72%  { transform: translateY(-1.5px) scale(1.003); }
    88%  { transform: translateY(0.5px) scale(0.999); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* Breathing: subtle continuous pulse */
@keyframes breathe {
    0%, 100% { transform: scale(1); box-shadow: var(--shadow-lg); }
    50%      { transform: scale(1.003); box-shadow: 0 12px 44px rgba(0,0,0,0.1), 0 3px 10px rgba(0,0,0,0.07); }
}

/* Breathing glow on hero */
@keyframes heroGlow {
    0%, 100% { opacity: 0; }
    50%      { opacity: 1; }
}

/* Button spring press */
@keyframes btnPress {
    0%   { transform: scale(1); }
    30%  { transform: scale(0.94); }
    50%  { transform: scale(1.03); }
    70%  { transform: scale(0.98); }
    85%  { transform: scale(1.01); }
    100% { transform: scale(1); }
}

/* Subtle float for decorative elements */
@keyframes gentleFloat {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-3px); }
}

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', sans-serif;
    -webkit-font-smoothing: antialiased;
}

/* ── Background ── */
.stApp {
    background: #f5f5f7;
}
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 600px;
    background: linear-gradient(180deg, #e8eaf0 0%, #f5f5f7 100%);
    z-index: 0;
    pointer-events: none;
}

/* ── Main container ── */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1080px;
    position: relative;
    z-index: 1;
}

/* ── Hero ── */
.hero {
    background: var(--surface-solid);
    border-radius: var(--radius-lg);
    padding: 2.5rem 2.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-lg);
    animation: heroSpring 1s var(--spring-damping) both, breathe 6s ease-in-out 1.2s infinite;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(0,0,0,0.06) 50%, transparent 100%);
}
.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    border-radius: inherit;
    background: radial-gradient(ellipse at 30% 20%, rgba(0,122,255,0.03) 0%, transparent 60%);
    animation: heroGlow 6s ease-in-out 1.2s infinite;
    pointer-events: none;
}
.hero h1 {
    color: var(--text-primary) !important;
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    margin: 0 0 0.25rem 0;
}
.hero p {
    color: var(--text-secondary);
    font-size: 0.92rem;
    font-weight: 400;
    margin: 0;
    letter-spacing: -0.01em;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: rgba(0,0,0,0.04);
    border-radius: 12px;
    padding: 3px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-secondary);
    transition: all 0.35s var(--apple-spring);
    letter-spacing: -0.01em;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary);
}
.stTabs [aria-selected="true"] {
    background: #fff !important;
    color: var(--text-primary) !important;
    box-shadow: var(--shadow-sm);
}
.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

/* ── Glass Card ── */
.card {
    background: var(--surface);
    backdrop-filter: var(--blur);
    -webkit-backdrop-filter: var(--blur);
    border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    margin-bottom: 12px;
    box-shadow: var(--shadow-md);
    animation: cardSpring 0.8s var(--spring-damping) both;
    transition: transform 0.5s var(--spring-damping), box-shadow 0.5s var(--spring-settle);
}
.card:hover {
    transform: scale(1.008) translateY(-2px);
    box-shadow: var(--shadow-lg);
    transition: transform 0.6s var(--spring-bounce), box-shadow 0.4s ease;
}
.card:nth-child(2) { animation-delay: 0.08s; }
.card:nth-child(3) { animation-delay: 0.16s; }
.card:nth-child(4) { animation-delay: 0.24s; }

.card-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-tertiary);
    margin-bottom: 12px;
}

/* ── Bilingual ── */
.bi-row { display: flex; gap: 10px; }
.bi-col {
    flex: 1;
    padding: 0.9rem 1.1rem;
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.65;
    color: var(--text-primary);
}
.bi-col.zh {
    background: rgba(0, 122, 255, 0.05);
    border: 0.5px solid rgba(0, 122, 255, 0.12);
}
.bi-col.en {
    background: rgba(88, 86, 214, 0.05);
    border: 0.5px solid rgba(88, 86, 214, 0.12);
}
.tag {
    display: inline-block;
    font-size: 0.58rem;
    font-weight: 600;
    padding: 1px 7px;
    border-radius: 5px;
    margin-bottom: 5px;
    letter-spacing: 0.04em;
}
.tag.zh { background: rgba(0,122,255,0.1); color: var(--accent); }
.tag.en { background: rgba(88,86,214,0.1); color: #5856D6; }

/* ── Pro / Con ── */
.pro-box, .con-box {
    border-radius: var(--radius);
    padding: 1.2rem 1.4rem;
    height: 100%;
    animation: cardSpring 0.85s var(--spring-damping) 0.16s both;
    transition: transform 0.5s var(--spring-bounce);
}
.pro-box:hover, .con-box:hover {
    transform: scale(1.01);
}
.pro-box {
    background: rgba(52, 199, 89, 0.06);
    border: 0.5px solid rgba(52, 199, 89, 0.15);
}
.con-box {
    background: rgba(255, 59, 48, 0.06);
    border: 0.5px solid rgba(255, 59, 48, 0.15);
}
.side-title {
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 10px;
    letter-spacing: -0.01em;
}
.side-title.pro { color: var(--green); }
.side-title.con { color: var(--red); }
.pro-box .body { color: var(--text-primary); }
.pro-box .en-text,
.con-box .en-text {
    color: var(--text-secondary);
    font-size: 0.84rem;
    font-style: italic;
    margin-top: 8px;
}

/* ── Prompt box ── */
.prompt-box {
    background: #1d1d1f;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
}
.prompt-box-label {
    color: rgba(255,255,255,0.35);
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.prompt-box code {
    color: rgba(255,255,255,0.82) !important;
    font-size: 0.8rem;
    line-height: 1.6;
    font-family: 'SF Mono', 'Fira Code', 'Menlo', monospace;
}

/* ── Model pill ── */
.model-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #fff;
    border: 0.5px solid var(--separator);
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    box-shadow: var(--shadow-sm);
    transition: transform 0.6s var(--spring-bounce), box-shadow 0.4s ease;
}
.model-pill:hover {
    box-shadow: var(--shadow-md);
    transform: scale(1.05);
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #fff !important;
    border: 0.5px solid rgba(0,0,0,0.1) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 0.9rem !important;
    transition: all 0.3s var(--apple-spring) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px rgba(0,122,255,0.12), var(--shadow-sm) !important;
    transform: scale(1.01);
    transition: all 0.5s var(--spring-bounce) !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--text-tertiary) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #fff !important;
    border: 0.5px solid rgba(0,0,0,0.1) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow-sm) !important;
    color: var(--text-primary) !important;
}
[data-baseweb="popover"] {
    background: rgba(255,255,255,0.9) !important;
    backdrop-filter: var(--blur) !important;
    -webkit-backdrop-filter: var(--blur) !important;
    border: 0.5px solid rgba(0,0,0,0.1) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-xl) !important;
}

/* ── Buttons with spring damping ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: -0.01em;
    border: 0.5px solid rgba(0,0,0,0.08) !important;
    transition: transform 0.6s var(--spring-bounce), box-shadow 0.4s var(--spring-settle) !important;
    box-shadow: var(--shadow-sm) !important;
    animation: gentleFloat 4s ease-in-out infinite;
    animation-play-state: paused;
}
.stButton > button:hover {
    transform: scale(1.04) translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
    animation-play-state: running;
}
.stButton > button:active {
    animation: btnPress 0.5s var(--spring-damping) !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(0,122,255,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(0,122,255,0.35) !important;
}
.stButton > button[kind="primary"]:active {
    background: #0066d6 !important;
    box-shadow: 0 1px 4px rgba(0,122,255,0.2) !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: #fff;
    border: 0.5px solid var(--separator);
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: var(--shadow-sm);
}
[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

/* ── Divider ── */
hr {
    border: none;
    border-top: 0.5px solid var(--separator) !important;
    margin: 0.8rem 0;
}

/* ── Typography ── */
.stMarkdown, p, span, label, .stCaption {
    color: var(--text-secondary) !important;
}
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
}

/* ── Alerts ── */
.stAlert > div {
    border-radius: 12px !important;
    border: 0.5px solid rgba(0,0,0,0.06) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Expander ── */
details {
    background: #fff !important;
    border: 0.5px solid var(--separator) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-sm) !important;
}
details summary {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #f5f5f7;
    border-right: 0.5px solid var(--separator);
}

/* ── Hide defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Scrollbar (thin, minimal) ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(0,0,0,0.12);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🎮 GTarcade PK Generator</h1>
    <p>一键生成中英双语 PK 文案 + AI 生图提示词</p>
</div>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("API_KEY", "")


# ── Tabs ──────────────────────────────────────────────────────────────────
tab_generate, tab_models, tab_history = st.tabs(["🚀 生成 PK", "⚙️ 模型管理", "📊 历史记录"])


# ═══════════════════════════════════════════════════════════════════════════
# TAB: 模型管理
# ═══════════════════════════════════════════════════════════════════════════
with tab_models:
    st.markdown("### 已保存的模型")
    custom_models = load_custom_models()

    if not custom_models:
        st.info("还没有保存任何模型，请在下方添加。")
    else:
        for name, info in custom_models.items():
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div class="model-pill">
                    <strong>{name}</strong>
                    <span style="color:var(--text-tertiary); font-size:0.78rem;">{info['model']}</span>
                </div>
                <div style="font-size:0.7rem; color:var(--text-tertiary); margin:4px 0 10px 6px;">{info['base_url']}</div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("删除", key=f"dm_{name}", use_container_width=True):
                    del custom_models[name]
                    save_custom_models(custom_models)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 添加新模型")
    with st.form("add_model", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("模型名称", placeholder="如：DeepSeek V4")
        with c2:
            new_url = st.text_input("Base URL", placeholder="https://api.deepseek.com/v1")
        new_model = st.text_input("Model ID", placeholder="deepseek-chat")
        if st.form_submit_button("💾 保存模型", use_container_width=True, type="primary"):
            if new_name and new_url and new_model:
                custom_models[new_name] = {"base_url": new_url, "model": new_model}
                save_custom_models(custom_models)
                st.success(f"已保存: {new_name}")
                st.rerun()
            else:
                st.error("请填写所有字段")


# ═══════════════════════════════════════════════════════════════════════════
# TAB: 历史记录
# ═══════════════════════════════════════════════════════════════════════════
with tab_history:
    history = load_history()

    col_m, col_c = st.columns([4, 1])
    with col_m:
        st.metric("已生成 PK 活动", len(history))
    with col_c:
        if history and st.button("🗑️ 清空全部", use_container_width=True):
            clear_all_history()
            st.rerun()

    if not history:
        st.info("暂无历史记录。去「生成 PK」标签页创建第一个吧！")
    else:
        for i, h in enumerate(reversed(history)):
            real_idx = len(history) - 1 - i
            col_date, col_title, col_cat, col_del = st.columns([1.5, 3, 1.5, 0.8])
            with col_date:
                st.caption(h.get("date", ""))
            with col_title:
                st.markdown(f"**{h.get('title', '')}**")
            with col_cat:
                st.caption(h.get("category", ""))
            with col_del:
                if st.button("🗑️", key=f"dh_{real_idx}"):
                    delete_history(real_idx)
                    st.rerun()
            st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# TAB: 生成 PK
# ═══════════════════════════════════════════════════════════════════════════
with tab_generate:
    st.markdown("#### API 配置")
    api_key = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-xxx...",
        label_visibility="collapsed",
    )
    st.session_state.api_key = api_key

    custom_models = load_custom_models()
    model_names = list(custom_models.keys())

    if not model_names:
        st.warning("请先到「⚙️ 模型管理」标签页添加模型")
        st.stop()

    selected_name = st.selectbox("选择模型", options=model_names)
    selected_info = custom_models[selected_name]
    base_url = selected_info["base_url"]
    model_name = selected_info["model"]
    st.caption(f"Base URL: `{base_url}` · Model: `{model_name}`")

    st.markdown("")
    st.markdown("#### 活动配置")

    col_cat, col_hint = st.columns([2, 1])
    with col_cat:
        category = st.selectbox(
            "主题分类",
            options=list(TOPIC_CATEGORIES.keys()),
            format_func=lambda x: f"{x}  —  {TOPIC_CATEGORIES[x]['en']}",
        )
    with col_hint:
        extra_hint = st.text_input("特定方向（可选）", placeholder="如：PVP vs PVE")

    st.markdown("")

    col_gen, col_test = st.columns([3, 1])
    with col_gen:
        generate_clicked = st.button("🚀  一键生成 PK 活动", type="primary", use_container_width=True)
    with col_test:
        test_clicked = st.button("🔍 测试连接", use_container_width=True)

    if test_clicked:
        if not api_key:
            st.error("请先填入 API Key")
        else:
            with st.spinner("测试中..."):
                try:
                    client = make_client(api_key, base_url)
                    resp = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Reply with: OK"}],
                        max_tokens=10,
                    )
                    st.success(f"连接成功 ✓  模型返回: {resp.choices[0].message.content}")
                except Exception as e:
                    st.error(f"连接失败: {e}")

    if generate_clicked:
        if not api_key:
            st.error("请先填入 API Key")
            st.stop()
        with st.spinner("✨ 正在生成中，请稍候..."):
            try:
                client = make_client(api_key, base_url)
                data = generate_pk(client, model_name, category, extra_hint)
                st.session_state["pk_data"] = data
                st.session_state["pk_md"] = render_markdown(data)
                save_history({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "title": data["title_zh"],
                    "category": category,
                })
            except ValueError as e:
                st.error("模型返回格式异常")
                with st.expander("查看原始返回"):
                    st.code(str(e), language="text")
                st.stop()
            except Exception as e:
                st.error(f"生成失败: {e}")
                st.stop()

    if "pk_data" in st.session_state:
        data = st.session_state["pk_data"]

        st.markdown("---")

        # Title
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">📌 标题 TITLE</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="bi-row">
            <div class="bi-col zh"><span class="tag zh">中文</span><br><strong>{data['title_zh']}</strong></div>
            <div class="bi-col en"><span class="tag en">EN</span><br><strong>{data['title_en']}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Topic
        st.markdown('<div class="card" style="animation-delay:0.06s">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">💬 话题 TOPIC</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="bi-row">
            <div class="bi-col zh"><span class="tag zh">中文</span><br>{data['topic_zh']}</div>
            <div class="bi-col en"><span class="tag en">EN</span><br>{data['topic_en']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Pro / Con
        col_pro, col_con = st.columns(2)
        with col_pro:
            st.markdown(f"""
            <div class="pro-box">
                <div class="side-title pro">✅ 正方 PRO</div>
                <div class="body">{data['pro_zh']}</div>
                <div class="en-text">{data['pro_en']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_con:
            st.markdown(f"""
            <div class="con-box">
                <div class="side-title con">❌ 反方 CON</div>
                <div class="body">{data['con_zh']}</div>
                <div class="en-text">{data['con_en']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Image Prompts
        st.markdown('<div class="card" style="animation-delay:0.12s">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">🎨 生图提示词 IMAGE PROMPTS</div>', unsafe_allow_html=True)
        col_gpt, col_nano = st.columns(2)
        with col_gpt:
            st.markdown(f"""
            <div class="prompt-box">
                <div class="prompt-box-label">GPT Image2</div>
                <code>{data['gpt_image_prompt']}</code>
            </div>
            """, unsafe_allow_html=True)
        with col_nano:
            st.markdown(f"""
            <div class="prompt-box">
                <div class="prompt-box-label">NanoBananaPro</div>
                <code>{data['nanobanana_prompt']}</code>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Export
        with st.expander("📋 导出完整 Markdown", expanded=False):
            st.code(st.session_state["pk_md"], language="markdown")
