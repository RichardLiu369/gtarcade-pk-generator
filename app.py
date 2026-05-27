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

# ── Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1100px;
    }

    /* ── Header ── */
    .hero {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2.5rem 3rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(102,126,234,0.15) 0%, transparent 50%);
        animation: pulse 8s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 1; }
    }
    .hero h1 {
        color: #fff !important;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
        position: relative;
    }
    .hero p {
        color: rgba(255,255,255,0.7);
        font-size: 0.95rem;
        margin: 0;
        position: relative;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #f1f3f9;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* ── Cards ── */
    .card {
        background: #fff;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #eee;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }
    .card-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #999;
        margin-bottom: 10px;
    }

    /* ── Bilingual ── */
    .bi-row { display: flex; gap: 12px; }
    .bi-col {
        flex: 1;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        font-size: 0.92rem;
        line-height: 1.7;
    }
    .bi-col.zh {
        background: linear-gradient(135deg, #eef2ff, #e8ecff);
        border-left: 3px solid #667eea;
    }
    .bi-col.en {
        background: linear-gradient(135deg, #f5f0ff, #ede8ff);
        border-left: 3px solid #9b59b6;
    }
    .tag {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
        letter-spacing: 0.05em;
    }
    .tag.zh { background: #667eea; color: #fff; }
    .tag.en { background: #9b59b6; color: #fff; }

    /* ── Pro / Con ── */
    .pro-box {
        background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        border: 1px solid #c8e6c9;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        height: 100%;
    }
    .con-box {
        background: linear-gradient(135deg, #fce4ec, #fff3e0);
        border: 1px solid #f8bbd0;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        height: 100%;
    }
    .side-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .side-title.pro { color: #2e7d32; }
    .side-title.con { color: #c62828; }

    /* ── Prompt box ── */
    .prompt-card {
        background: #1a1b2e;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-top: 8px;
    }
    .prompt-card-label {
        color: #7c8db5;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .prompt-card code {
        color: #cdd6f4 !important;
        font-size: 0.82rem;
        line-height: 1.6;
    }

    /* ── Model card ── */
    .model-card {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #f8f9fb;
        border: 1px solid #e8eaef;
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 4px;
        transition: all 0.2s;
    }
    .model-card:hover {
        border-color: #667eea;
        background: #f0f2ff;
    }

    /* ── Animations ── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeInUp 0.5s ease-out;
    }

    /* ── Button override ── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #fafbfc;
    }

    /* ── Hide default ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Metric card ── */
    [data-testid="stMetric"] {
        background: #f8f9fb;
        border-radius: 10px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🎮 GTarcade PK Activity Generator</h1>
    <p>一键生成中英双语 PK 文案 + AI 生图提示词</p>
</div>
""", unsafe_allow_html=True)


# ── Session State Defaults ────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("API_KEY", "")
if "base_url" not in st.session_state:
    st.session_state.base_url = ""
if "model_name" not in st.session_state:
    st.session_state.model_name = ""


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
                <div class="model-card">
                    <strong>{name}</strong>
                    <span style="color:#999; font-size:0.8rem;">| {info['model']}</span>
                </div>
                <div style="font-size:0.78rem; color:#aaa; margin-left:8px; margin-bottom:8px;">{info['base_url']}</div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("删除", key=f"del_model_{name}", use_container_width=True):
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
                if st.button("🗑️", key=f"del_h_{real_idx}"):
                    delete_history(real_idx)
                    st.rerun()
            st.divider()


# ═══════════════════════════════════════════════════════════════════════════
# TAB: 生成 PK
# ═══════════════════════════════════════════════════════════════════════════
with tab_generate:
    # ── API Key ──
    st.markdown("#### API 配置")
    api_key = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-xxx...",
        label_visibility="collapsed",
    )
    st.session_state.api_key = api_key

    # ── Model Selector ──
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

    # ── Category & Hint ──
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

    # ── Action Buttons ──
    col_gen, col_test = st.columns([3, 1])
    with col_gen:
        generate_clicked = st.button("🚀  一键生成 PK 活动", type="primary", use_container_width=True)
    with col_test:
        test_clicked = st.button("🔍 测试连接", use_container_width=True)

    # ── Test Connection ──
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

    # ── Generate ──
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

    # ── Display Results ──
    if "pk_data" in st.session_state:
        data = st.session_state["pk_data"]

        st.markdown("---")
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

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
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
                <div style="color:#666; font-size:0.88rem; font-style:italic;">{data['pro_en']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_con:
            st.markdown(f"""
            <div class="con-box">
                <div class="side-title con">❌ 反方 CON</div>
                <div style="margin-bottom:8px;">{data['con_zh']}</div>
                <div style="color:#666; font-size:0.88rem; font-style:italic;">{data['con_en']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Image Prompts
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">🎨 生图提示词 IMAGE PROMPTS</div>', unsafe_allow_html=True)
        col_gpt, col_nano = st.columns(2)
        with col_gpt:
            st.markdown(f"""
            <div class="prompt-card">
                <div class="prompt-card-label">GPT Image2</div>
                <code>{data['gpt_image_prompt']}</code>
            </div>
            """, unsafe_allow_html=True)
        with col_nano:
            st.markdown(f"""
            <div class="prompt-card">
                <div class="prompt-card-label">NanoBananaPro</div>
                <code>{data['nanobanana_prompt']}</code>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Export
        with st.expander("📋 导出完整 Markdown", expanded=False):
            st.code(st.session_state["pk_md"], language="markdown")

        st.markdown('</div>', unsafe_allow_html=True)
