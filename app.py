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

# ── Model Presets ─────────────────────────────────────────────────────────
MODEL_PRESETS = {
    # DeepSeek
    "DeepSeek V3": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "DeepSeek R1 (推理)": {"base_url": "https://api.deepseek.com", "model": "deepseek-reasoner"},
    # 通义千问 (Qwen)
    "通义千问 Plus": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "通义千问 Max": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-max"},
    "通义千问 Turbo": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-turbo"},
    # Kimi (Moonshot)
    "Kimi 8K": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "Kimi 32K": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-32k"},
    "Kimi 128K": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-128k"},
    # 豆包 (Doubao / ByteDance)
    "豆包 Pro 4K": {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-pro-4k"},
    "豆包 Pro 32K": {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-pro-32k"},
    "豆包 Pro 128K": {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-pro-128k"},
    # 智谱 (Zhipu / GLM)
    "智谱 GLM-4": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4"},
    "智谱 GLM-4-Flash": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    # 零一万物 (Yi / 01.AI)
    "Yi-Large": {"base_url": "https://api.lingyiwanwu.com/v1", "model": "yi-large"},
    "Yi-Medium": {"base_url": "https://api.lingyiwanwu.com/v1", "model": "yi-medium"},
    # 百度文心 (ERNIE)
    "文心一言 ERNIE 4.0": {"base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop", "model": "ernie-4.0-8k"},
    # MiniMax
    "MiniMax abab6.5": {"base_url": "https://api.minimax.chat/v1", "model": "abab6.5-chat"},
    # 讯飞星火 (Spark)
    "讯飞星火 Max": {"base_url": "https://spark-api-open.xf-yun.com/v1", "model": "generalv3.5"},
    # OpenAI
    "GPT-4o": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o"},
    "GPT-4o Mini": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    # OpenRouter
    "OpenRouter: Claude Sonnet 4": {"base_url": "https://openrouter.ai/api/v1", "model": "anthropic/claude-sonnet-4"},
    "OpenRouter: GPT-4o": {"base_url": "https://openrouter.ai/api/v1", "model": "openai/gpt-4o"},
    "OpenRouter: DeepSeek V3": {"base_url": "https://openrouter.ai/api/v1", "model": "deepseek/deepseek-chat"},
    "OpenRouter: Gemini 2.5 Pro": {"base_url": "https://openrouter.ai/api/v1", "model": "google/gemini-2.5-pro-preview"},
}


# ── Helpers ───────────────────────────────────────────────────────────────
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

---

## 💬 话题 Topic

**🇨🇳** {data["topic_zh"]}

**🇬🇧** {data["topic_en"]}

---

## ✅ 正方 Pro

**🇨🇳** {data["pro_zh"]}

**🇬🇧** {data["pro_en"]}

---

## ❌ 反方 Con

**🇨🇳** {data["con_zh"]}

**🇬🇧** {data["con_en"]}

---

## 🎨 GPT Image2 Prompt

```
{data["gpt_image_prompt"]}
```

---

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
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Header banner */
    .header-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    .header-banner h1 {
        color: white !important;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .header-banner p {
        color: rgba(255,255,255,0.85);
        font-size: 1.05rem;
        margin: 0;
    }

    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e8e8ef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #888;
        margin-bottom: 0.8rem;
    }

    /* Bilingual row */
    .bilingual-row {
        display: flex;
        gap: 1rem;
    }
    .bilingual-col {
        flex: 1;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .bilingual-col.zh {
        background: #f0f4ff;
        border-left: 3px solid #667eea;
    }
    .bilingual-col.en {
        background: #f8f6ff;
        border-left: 3px solid #764ba2;
    }
    .lang-tag {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
    }
    .lang-tag.zh { background: #667eea; color: white; }
    .lang-tag.en { background: #764ba2; color: white; }

    /* Pro/Con cards */
    .pro-card {
        background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        border: 1px solid #c8e6c9;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
    }
    .con-card {
        background: linear-gradient(135deg, #fce4ec, #fff3e0);
        border: 1px solid #f8bbd0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
    }
    .pro-con-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }
    .pro-con-title.pro { color: #2e7d32; }
    .pro-con-title.con { color: #c62828; }

    /* Prompt box */
    .prompt-box {
        background: #1e1e2e;
        color: #cdd6f4;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        overflow-x: auto;
    }

    /* Generate button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1.05rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #fafbfc;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 0.9rem;
        color: #666;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <h1>🎮 GTarcade PK Activity Generator</h1>
    <p>一键生成中英双语 PK 文案 + AI 生图提示词 | Bilingual PK Content + AI Image Prompts</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ API 设置")

    api_key = st.text_input(
        "API Key",
        value=os.getenv("API_KEY", ""),
        type="password",
        help="填入你的 API Key",
        placeholder="sk-xxx...",
    )

    preset_options = list(MODEL_PRESETS.keys()) + ["🔧 自定义"]
    selected_preset = st.selectbox(
        "选择模型",
        options=preset_options,
        index=0,
    )

    if selected_preset == "🔧 自定义":
        base_url = st.text_input("Base URL", value=os.getenv("BASE_URL", "https://api.deepseek.com"))
        model_name = st.text_input("Model", value=os.getenv("MODEL_NAME", "deepseek-chat"))
    else:
        preset = MODEL_PRESETS[selected_preset]
        base_url = preset["base_url"]
        model_name = preset["model"]
        st.caption(f"Base URL: `{base_url}`")
        st.caption(f"Model: `{model_name}`")

    st.markdown("---")
    st.markdown("### 📊 历史记录")
    history = load_history()
    st.metric("已生成 PK 活动", len(history))
    if history:
        with st.expander("查看最近话题"):
            for h in reversed(history[-10:]):
                st.markdown(f"• `{h.get('date', '')}` {h.get('title', '')}")

    st.markdown("---")
    st.caption("💡 免费 API 推荐：通义千问、DeepSeek、智谱 GLM")


# ── Main Content ──────────────────────────────────────────────────────────

# Category & Hint
st.markdown("### 📝 配置")
col1, col2 = st.columns([2, 1])
with col1:
    category = st.selectbox(
        "选择主题分类",
        options=list(TOPIC_CATEGORIES.keys()),
        format_func=lambda x: f"{x}  —  {TOPIC_CATEGORIES[x]['en']}",
    )
with col2:
    extra_hint = st.text_input("特定方向（可选）", placeholder="如：PVP vs PVE")

st.markdown("")

# Buttons
col_btn, col_test, _ = st.columns([2, 1, 1])
with col_btn:
    generate_clicked = st.button("🚀  一键生成 PK 活动", type="primary", use_container_width=True)
with col_test:
    test_clicked = st.button("🔍 测试连接", use_container_width=True)

# Test connection
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

# Generate
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
            st.error("模型返回格式异常，请看下方详情")
            with st.expander("查看模型原始返回", expanded=True):
                st.code(str(e), language="text")
            st.stop()
        except Exception as e:
            st.error(f"生成失败: {e}")
            st.stop()

# ── Display Results ───────────────────────────────────────────────────────
if "pk_data" in st.session_state:
    data = st.session_state["pk_data"]

    st.markdown("---")
    st.markdown("## 📋 生成结果")

    # Title
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📌 标题 TITLE</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="bilingual-row">
        <div class="bilingual-col zh">
            <span class="lang-tag zh">中文</span><br>
            <strong>{data['title_zh']}</strong>
        </div>
        <div class="bilingual-col en">
            <span class="lang-tag en">EN</span><br>
            <strong>{data['title_en']}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Topic
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">💬 话题 TOPIC</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="bilingual-row">
        <div class="bilingual-col zh">
            <span class="lang-tag zh">中文</span><br>
            {data['topic_zh']}
        </div>
        <div class="bilingual-col en">
            <span class="lang-tag en">EN</span><br>
            {data['topic_en']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Pro / Con
    col_pro, col_con = st.columns(2)
    with col_pro:
        st.markdown(f"""
        <div class="pro-card">
            <div class="pro-con-title pro">✅ 正方 PRO</div>
            <div style="margin-bottom:0.6rem;">{data['pro_zh']}</div>
            <div style="color:#555; font-size:0.9rem; font-style:italic;">{data['pro_en']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_con:
        st.markdown(f"""
        <div class="con-card">
            <div class="pro-con-title con">❌ 反方 CON</div>
            <div style="margin-bottom:0.6rem;">{data['con_zh']}</div>
            <div style="color:#555; font-size:0.9rem; font-style:italic;">{data['con_en']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # Image Prompts
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🎨 生图提示词 IMAGE PROMPTS</div>', unsafe_allow_html=True)
    col_gpt, col_nano = st.columns(2)
    with col_gpt:
        st.markdown("**GPT Image2**")
        st.code(data["gpt_image_prompt"], language=None)
    with col_nano:
        st.markdown("**NanoBananaPro**")
        st.code(data["nanobanana_prompt"], language=None)
    st.markdown('</div>', unsafe_allow_html=True)

    # Export
    st.markdown("---")
    with st.expander("📋 导出完整 Markdown（点击展开复制）", expanded=False):
        st.code(st.session_state["pk_md"], language="markdown")
