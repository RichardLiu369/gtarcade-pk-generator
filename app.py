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

# ── Glassmorphism CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

/* ── Spring easing ── */
:root {
    --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
    --spring-soft: cubic-bezier(0.25, 1.2, 0.5, 1);
    --spring-hard: cubic-bezier(0.5, 2, 0.3, 0.8);
    --glass-bg: rgba(255, 255, 255, 0.12);
    --glass-border: rgba(255, 255, 255, 0.2);
    --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    --glass-blur: 20px;
}

/* ── Animated gradient bg ── */
.stApp {
    background: linear-gradient(-45deg, #0f0c29, #1a1a4e, #2d1b69, #1e3a5f, #0f0c29);
    background-size: 400% 400%;
    animation: gradientShift 20s ease infinite;
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ── Floating orbs ── */
.stApp::before,
.stApp::after {
    content: '';
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.3;
    z-index: 0;
    pointer-events: none;
}
.stApp::before {
    width: 400px; height: 400px;
    background: #667eea;
    top: -100px; right: -100px;
    animation: float1 15s ease-in-out infinite;
}
.stApp::after {
    width: 350px; height: 350px;
    background: #e040fb;
    bottom: -80px; left: -80px;
    animation: float2 18s ease-in-out infinite;
}
@keyframes float1 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(-60px, 80px) scale(1.1); }
    66% { transform: translate(40px, -40px) scale(0.9); }
}
@keyframes float2 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(80px, -60px) scale(1.15); }
    66% { transform: translate(-50px, 50px) scale(0.85); }
}

/* ── Main container ── */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1100px;
    position: relative;
    z-index: 1;
}

/* ── Glass card base ── */
.glass {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    box-shadow: var(--glass-shadow);
}

/* ── Hero ── */
.hero {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 24px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255,255,255,0.1);
    animation: heroIn 0.8s var(--spring) both;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
}
@keyframes heroIn {
    0% { opacity: 0; transform: translateY(-30px) scale(0.95); }
    60% { transform: translateY(8px) scale(1.02); }
    80% { transform: translateY(-3px) scale(0.99); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}
.hero h1 {
    color: #fff !important;
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 0.3rem 0;
    text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.hero p {
    color: rgba(255,255,255,0.65);
    font-size: 0.95rem;
    margin: 0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 5px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 0.88rem;
    color: rgba(255,255,255,0.5);
    transition: all 0.4s var(--spring);
}
.stTabs [data-baseweb="tab"]:hover {
    color: rgba(255,255,255,0.8);
    background: rgba(255,255,255,0.05);
}
.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.15) !important;
    color: #fff !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* ── Glass card ── */
.card-glass {
    background: rgba(255, 255, 255, 0.07);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px;
    padding: 1.5rem;
    margin-bottom: 14px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255,255,255,0.05);
    animation: cardSpring 0.6s var(--spring) both;
    transition: transform 0.4s var(--spring), box-shadow 0.4s ease;
}
.card-glass:hover {
    transform: translateY(-4px) scale(1.01);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255,255,255,0.08);
}
@keyframes cardSpring {
    0% { opacity: 0; transform: translateY(30px) scale(0.92); }
    50% { transform: translateY(-8px) scale(1.03); }
    70% { transform: translateY(3px) scale(0.99); }
    85% { transform: translateY(-1px) scale(1.005); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}
.card-glass:nth-child(2) { animation-delay: 0.1s; }
.card-glass:nth-child(3) { animation-delay: 0.2s; }
.card-glass:nth-child(4) { animation-delay: 0.3s; }

.card-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(255,255,255,0.4);
    margin-bottom: 12px;
}

/* ── Bilingual ── */
.bi-row { display: flex; gap: 12px; }
.bi-col {
    flex: 1;
    padding: 1rem 1.2rem;
    border-radius: 14px;
    font-size: 0.92rem;
    line-height: 1.7;
    color: #fff;
}
.bi-col.zh {
    background: rgba(102, 126, 234, 0.15);
    border: 1px solid rgba(102, 126, 234, 0.25);
}
.bi-col.en {
    background: rgba(155, 89, 182, 0.15);
    border: 1px solid rgba(155, 89, 182, 0.25);
}
.tag {
    display: inline-block;
    font-size: 0.6rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    margin-bottom: 6px;
    letter-spacing: 0.08em;
}
.tag.zh { background: rgba(102,126,234,0.4); color: #fff; }
.tag.en { background: rgba(155,89,182,0.4); color: #fff; }

/* ── Pro / Con ── */
.pro-box {
    background: rgba(76, 175, 80, 0.1);
    border: 1px solid rgba(76, 175, 80, 0.25);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 1.3rem 1.5rem;
    height: 100%;
    color: #fff;
    animation: cardSpring 0.7s var(--spring) 0.2s both;
}
.con-box {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid rgba(244, 67, 54, 0.25);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 1.3rem 1.5rem;
    height: 100%;
    color: #fff;
    animation: cardSpring 0.7s var(--spring) 0.3s both;
}
.side-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 10px;
}
.side-title.pro { color: #81c784; }
.side-title.con { color: #ef9a9a; }

/* ── Prompt box ── */
.prompt-glass {
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
}
.prompt-label {
    color: rgba(255,255,255,0.35);
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
.prompt-glass code {
    color: rgba(255,255,255,0.8) !important;
    font-size: 0.82rem;
    line-height: 1.65;
}

/* ── Model card ── */
.model-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 0.88rem;
    font-weight: 600;
    color: #fff;
    margin: 4px;
    transition: all 0.4s var(--spring);
}
.model-pill:hover {
    background: rgba(255,255,255,0.15);
    transform: scale(1.05);
    border-color: rgba(255,255,255,0.3);
}

/* ── Inputs glass ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #fff !important;
    backdrop-filter: blur(10px);
    transition: all 0.3s var(--spring-soft);
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(102,126,234,0.5) !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
    transform: scale(1.01);
}
.stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.25) !important;
}

/* ── Selectbox glass ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.08) !important;
}
[data-baseweb="popover"] {
    background: rgba(30, 30, 60, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
}
[data-baseweb="popover"] li {
    color: #fff !important;
}
[data-baseweb="popover"] li:hover {
    background: rgba(255,255,255,0.1) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.4s var(--spring) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
.stButton > button:active {
    transform: scale(0.95) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) scale(1.03) !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.2) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(102,126,234,0.8), rgba(118,75,162,0.8)) !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(102,126,234,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 8px 30px rgba(102,126,234,0.5) !important;
}

/* ── Metric glass ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 14px 18px;
}
[data-testid="stMetric"] label { color: rgba(255,255,255,0.5) !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #fff !important; }

/* ── Divider ── */
hr {
    border-color: rgba(255,255,255,0.08) !important;
}

/* ── Caption & text ── */
.stMarkdown, .stCaption, p, span, label {
    color: rgba(255,255,255,0.75) !important;
}
h1, h2, h3, h4, h5, h6 {
    color: #fff !important;
}
.stAlert > div {
    background: rgba(255,255,255,0.06) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

/* ── Expander glass ── */
details {
    background: rgba(255,255,255,0.05) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
}
details summary { color: rgba(255,255,255,0.7) !important; }
details summary:hover { color: #fff !important; }

/* ── Code block ── */
.stCodeBlock {
    border-radius: 14px !important;
    overflow: hidden;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.95);
    backdrop-filter: blur(20px);
}

/* ── Hide defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.25);
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


# ── Session State Defaults ────────────────────────────────────────────────
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
                    <span style="opacity:0.5; font-size:0.78rem;">{info['model']}</span>
                </div>
                <div style="font-size:0.72rem; color:rgba(255,255,255,0.3); margin:4px 0 10px 8px;">{info['base_url']}</div>
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
        st.markdown('<div class="card-glass">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">📌 标题 TITLE</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="bi-row">
            <div class="bi-col zh"><span class="tag zh">中文</span><br><strong>{data['title_zh']}</strong></div>
            <div class="bi-col en"><span class="tag en">EN</span><br><strong>{data['title_en']}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Topic
        st.markdown('<div class="card-glass" style="animation-delay:0.1s">', unsafe_allow_html=True)
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
                <div style="margin-bottom:8px;">{data['pro_zh']}</div>
                <div style="opacity:0.6; font-size:0.86rem; font-style:italic;">{data['pro_en']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_con:
            st.markdown(f"""
            <div class="con-box">
                <div class="side-title con">❌ 反方 CON</div>
                <div style="margin-bottom:8px;">{data['con_zh']}</div>
                <div style="opacity:0.6; font-size:0.86rem; font-style:italic;">{data['con_en']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Image Prompts
        st.markdown('<div class="card-glass" style="animation-delay:0.2s">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">🎨 生图提示词 IMAGE PROMPTS</div>', unsafe_allow_html=True)
        col_gpt, col_nano = st.columns(2)
        with col_gpt:
            st.markdown(f"""
            <div class="prompt-glass">
                <div class="prompt-label">GPT Image2</div>
                <code>{data['gpt_image_prompt']}</code>
            </div>
            """, unsafe_allow_html=True)
        with col_nano:
            st.markdown(f"""
            <div class="prompt-glass">
                <div class="prompt-label">NanoBananaPro</div>
                <code>{data['nanobanana_prompt']}</code>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Export
        with st.expander("📋 导出完整 Markdown", expanded=False):
            st.code(st.session_state["pk_md"], language="markdown")
