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
    # Claude (via OpenAI-compatible proxy)
    "Claude Sonnet 4": {"base_url": "https://api.anthropic.com/v1", "model": "claude-sonnet-4-20250514"},
    # OpenRouter (聚合平台，一个 Key 用所有模型)
    "OpenRouter: Claude Sonnet 4": {"base_url": "https://openrouter.ai/api/v1", "model": "anthropic/claude-sonnet-4"},
    "OpenRouter: GPT-4o": {"base_url": "https://openrouter.ai/api/v1", "model": "openai/gpt-4o"},
    "OpenRouter: DeepSeek V3": {"base_url": "https://openrouter.ai/api/v1", "model": "deepseek/deepseek-chat"},
    "OpenRouter: Gemini 2.5 Pro": {"base_url": "https://openrouter.ai/api/v1", "model": "google/gemini-2.5-pro-preview"},
}


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
    """Robustly extract JSON from model response, handling various formats."""
    if not raw or not raw.strip():
        raise ValueError("模型返回了空内容")

    # 1. Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json|JSON)?\s*\n?", "", cleaned)
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    # 2. Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Try to find JSON object in the text (greedy match on outermost braces)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 4. All attempts failed — raise with raw content for debugging
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


# ── Streamlit UI ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GTarcade PK Generator",
    page_icon="🎮",
    layout="wide",
)

st.title("🎮 GTarcade PK Activity Generator")
st.caption("一键生成中英双语 PK 文案 + AI 生图提示词")

# ── Sidebar: API Config ───────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ API 配置")

    api_key = st.text_input(
        "API Key",
        value=os.getenv("API_KEY", ""),
        type="password",
        help="填入你的 API Key",
    )

    # ── Model Preset Selector ──
    preset_options = list(MODEL_PRESETS.keys()) + ["🔧 自定义"]
    selected_preset = st.selectbox(
        "选择模型",
        options=preset_options,
        index=0,
        help="选择预置模型，或选「自定义」手动填写",
    )

    if selected_preset == "🔧 自定义":
        base_url = st.text_input(
            "Base URL",
            value=os.getenv("BASE_URL", "https://api.deepseek.com"),
        )
        model_name = st.text_input(
            "Model",
            value=os.getenv("MODEL_NAME", "deepseek-chat"),
        )
    else:
        preset = MODEL_PRESETS[selected_preset]
        base_url = preset["base_url"]
        model_name = preset["model"]
        st.caption(f"Base URL: `{base_url}`")
        st.caption(f"Model: `{model_name}`")

    st.divider()
    st.header("📊 历史记录")
    history = load_history()
    st.write(f"已生成 **{len(history)}** 个 PK 活动")
    if history:
        with st.expander("查看最近话题"):
            for h in reversed(history[-10:]):
                st.write(f"• {h.get('date', '')} — {h.get('title', '')}")

# ── Main Area ─────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    category = st.selectbox(
        "📂 选择主题分类",
        options=list(TOPIC_CATEGORIES.keys()),
        format_func=lambda x: f"{x} ({TOPIC_CATEGORIES[x]['en']})",
    )

with col2:
    extra_hint = st.text_input(
        "💡 特定方向（可选）",
        placeholder="如：PVP vs PVE",
    )

# ── Generate Button ───────────────────────────────────────────────────────
col_btn, col_test = st.columns([3, 1])
with col_btn:
    generate_clicked = st.button("🚀 一键生成 PK 活动", type="primary", use_container_width=True)
with col_test:
    test_clicked = st.button("🔍 测试连接", use_container_width=True)

if test_clicked:
    if not api_key:
        st.error("请在左侧填入 API Key")
    else:
        with st.spinner("测试中..."):
            try:
                client = make_client(api_key, base_url)
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "Reply with: OK"}],
                    max_tokens=10,
                )
                st.success(f"连接成功！模型返回: {resp.choices[0].message.content}")
            except Exception as e:
                st.error(f"连接失败: {e}")

if generate_clicked:
    if not api_key:
        st.error("请在左侧填入 API Key")
        st.stop()

    with st.spinner("正在生成中，请稍候..."):
        try:
            client = make_client(api_key, base_url)
            data = generate_pk(client, model_name, category, extra_hint)
            st.session_state["pk_data"] = data
            st.session_state["pk_md"] = render_markdown(data)
            # Save to history
            save_history({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "title": data["title_zh"],
                "category": category,
            })
            st.success("✅ 生成完成！")
        except ValueError as e:
            st.error("模型返回格式异常，请看下方详情")
            with st.expander("查看模型原始返回", expanded=True):
                st.code(str(e), language="text")
        except Exception as e:
            st.error(f"生成失败: {e}")

# ── Display Result ────────────────────────────────────────────────────────
if "pk_data" in st.session_state:
    data = st.session_state["pk_data"]

    st.divider()

    # Title
    st.subheader("📌 标题 Title")
    col_zh, col_en = st.columns(2)
    col_zh.info(f"**🇨🇳** {data['title_zh']}")
    col_en.info(f"**🇬🇧** {data['title_en']}")

    # Topic
    st.subheader("💬 话题 Topic")
    col_zh, col_en = st.columns(2)
    col_zh.write(data["topic_zh"])
    col_en.write(data["topic_en"])

    # Arguments
    st.subheader("⚔️ 正反方观点")
    col_pro, col_con = st.columns(2)
    with col_pro:
        st.success("**✅ 正方 Pro**")
        st.write(data["pro_zh"])
        st.caption(data["pro_en"])
    with col_con:
        st.error("**❌ 反方 Con**")
        st.write(data["con_zh"])
        st.caption(data["con_en"])

    # Image Prompts
    st.subheader("🎨 生图提示词")
    col_gpt, col_nano = st.columns(2)
    with col_gpt:
        st.text_area(
            "GPT Image2 Prompt",
            value=data["gpt_image_prompt"],
            height=200,
            key="gpt_prompt",
        )
    with col_nano:
        st.text_area(
            "NanoBananaPro Prompt",
            value=data["nanobanana_prompt"],
            height=200,
            key="nano_prompt",
        )

    # Export
    st.divider()
    st.subheader("📋 导出")
    st.code(st.session_state["pk_md"], language="markdown")
