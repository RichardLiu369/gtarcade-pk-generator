import json
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
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

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --spring-settle: cubic-bezier(0.2, 0.8, 0.2, 1);
    --spring-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
    --spring-damping: cubic-bezier(0.22, 1.2, 0.36, 1);
    --shadow-sm: 0 2px 8px rgba(160,120,60,0.06), 0 1px 3px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 16px rgba(160,120,60,0.08), 0 2px 6px rgba(0,0,0,0.06);
    --shadow-lg: 0 12px 40px rgba(160,120,60,0.12), 0 4px 12px rgba(0,0,0,0.06);
    --shadow-xl: 0 20px 60px rgba(160,120,60,0.15), 0 6px 16px rgba(0,0,0,0.06);
    --blur: saturate(180%) blur(20px);
    --radius: 16px;
    --radius-lg: 20px;
    --accent: #FB923C;
    --accent-hover: #F97316;
    --accent-light: rgba(251, 146, 60, 0.1);
    --accent-glow: rgba(251, 146, 60, 0.2);
    --green: #34C759;
    --red: #FF3B30;
    --text-primary: #1d1d1f;
    --text-secondary: #6B6B6F;
    --text-tertiary: #aeaeb2;
    --surface: #FFFFFF;
    --card-bg: #FFFCF8;
    --separator: rgba(160,120,60,0.12);
    --bg: #FFF7ED;
}

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', sans-serif;
    -webkit-font-smoothing: antialiased;
    font-weight: 500;
}

p, span, label, .stCaption {
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}

/* ── Background ── */
.stApp {
    background: var(--bg);
}

/* ── Main container ── */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1280px;
    position: relative;
    z-index: 1;
}

/* ── Hero ── */
.hero {
    background: var(--accent);
    border-radius: var(--radius-lg);
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 30px var(--accent-glow);
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
    pointer-events: none;
}
.hero h1 {
    color: #fff !important;
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    margin: 0 0 0.35rem 0;
    text-shadow: 0 2px 16px rgba(0,0,0,0.25);
}
.hero p {
    color: #fff !important;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.01em;
}

/* ── Left Panel ── */
.left-panel {
    background: var(--surface);
    border-radius: var(--radius);
    border: 1px solid var(--separator);
    padding: 1.4rem;
    box-shadow: var(--shadow-md);
}
.left-panel-title {
    font-size: 0.95rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 1rem;
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #F5EDE3;
    border-radius: 12px;
    padding: 3px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-secondary);
    transition: all 0.35s var(--spring-settle);
    letter-spacing: -0.01em;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary);
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 2px 8px rgba(160,120,60,0.1);
}
.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

/* ── Card ── */
.card {
    background: var(--card-bg);
    border: 1px solid var(--separator);
    border-radius: var(--radius);
    padding: 1.3rem 1.5rem;
    margin-bottom: 12px;
    box-shadow: var(--shadow-md);
    transition: transform 0.5s var(--spring-damping), box-shadow 0.5s var(--spring-settle);
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}
.card-label {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent-hover);
    margin-bottom: 10px;
}

/* ── Bilingual ── */
.bi-row { display: flex; gap: 10px; }
.bi-col {
    flex: 1;
    padding: 0.85rem 1rem;
    border-radius: 12px;
    font-size: 0.92rem;
    line-height: 1.7;
    color: var(--text-primary);
    font-weight: 500;
}
.bi-col.zh {
    background: rgba(0, 122, 255, 0.07);
    border-left: 3px solid #007AFF;
}
.bi-col.en {
    background: rgba(88, 86, 214, 0.07);
    border-left: 3px solid #5856D6;
}
.tag {
    display: inline-block;
    font-size: 0.64rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 5px;
    margin-bottom: 5px;
    letter-spacing: 0.04em;
}
.tag.zh { background: #007AFF; color: #fff; }
.tag.en { background: #5856D6; color: #fff; }

/* ── Pro / Con ── */
.pro-box, .con-box {
    border-radius: var(--radius);
    padding: 1.1rem 1.3rem;
    height: 100%;
    transition: transform 0.5s var(--spring-bounce);
}
.pro-box:hover, .con-box:hover {
    transform: scale(1.01);
}
.pro-box {
    background: rgba(52, 199, 89, 0.06);
    border: 1px solid rgba(52, 199, 89, 0.15);
    border-left: 4px solid #34C759;
}
.con-box {
    background: rgba(255, 59, 48, 0.06);
    border: 1px solid rgba(255, 59, 48, 0.15);
    border-left: 4px solid #FF3B30;
}
.side-title {
    font-size: 1rem;
    font-weight: 800;
    margin-bottom: 10px;
    letter-spacing: -0.01em;
}
.side-title.pro { color: var(--green); }
.side-title.con { color: var(--red); }
.pro-box .body, .con-box .body { color: var(--text-primary); font-size: 0.92rem; font-weight: 500; line-height: 1.7; }
.pro-box .en-text,
.con-box .en-text {
    color: var(--text-secondary);
    font-size: 0.86rem;
    font-weight: 500;
    font-style: italic;
    margin-top: 8px;
}

/* ── Prompt box ── */
.prompt-box {
    background: #F5EDE3;
    border: 1px solid var(--separator);
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
.prompt-box-label {
    color: var(--text-secondary);
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.prompt-box code {
    color: var(--text-primary) !important;
    font-size: 0.84rem;
    font-weight: 500;
    line-height: 1.65;
    font-family: 'SF Mono', 'Fira Code', 'Menlo', monospace;
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
    border-radius: 0 !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
}
.prompt-box .stMarkdown,
.prompt-box p,
.prompt-box span {
    background: transparent !important;
    color: var(--text-primary) !important;
}
.prompt-box pre,
.prompt-box .highlight,
.prompt-box [data-testid="stCode"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
.prompt-box div[data-testid="stMarkdown"] {
    background: transparent !important;
}

/* ── Model pill ── */
.model-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--accent-light);
    border: 1px solid rgba(251, 146, 60, 0.15);
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-primary);
    box-shadow: var(--shadow-sm);
    transition: transform 0.5s var(--spring-bounce), box-shadow 0.4s ease;
}
.model-pill:hover {
    box-shadow: 0 4px 16px var(--accent-glow);
    transform: scale(1.03);
    border-color: rgba(249, 115, 22, 0.25);
}

/* ── Yoozoo Button ── */
.yoozoo-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    padding: 12px 16px;
    border: 2px solid var(--accent);
    border-radius: 12px;
    background: var(--accent-light);
    color: var(--accent-hover);
    font-size: 0.88rem;
    font-weight: 700;
    text-decoration: none;
    letter-spacing: -0.01em;
    transition: all 0.4s var(--spring-bounce);
    box-shadow: var(--shadow-sm);
    margin-top: 12px;
}
.yoozoo-btn:hover {
    background: var(--accent);
    color: #fff;
    transform: scale(1.03) translateY(-1px);
    box-shadow: 0 6px 24px var(--accent-glow);
    text-decoration: none;
}
.yoozoo-icon {
    font-size: 1.1rem;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #fff !important;
    border: 1px solid rgba(0,0,0,0.12) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    transition: all 0.4s var(--spring-settle) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(251,146,60,0.15), var(--shadow-sm) !important;
    transition: all 0.5s var(--spring-bounce) !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--text-tertiary) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #fff !important;
    border: 1px solid rgba(0,0,0,0.12) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow-sm) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}
[data-baseweb="popover"] {
    background: rgba(255,255,255,0.95) !important;
    backdrop-filter: var(--blur) !important;
    -webkit-backdrop-filter: var(--blur) !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-xl) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    letter-spacing: -0.01em;
    border: 1px solid rgba(0,0,0,0.08) !important;
    transition: transform 0.5s var(--spring-bounce), box-shadow 0.4s var(--spring-settle) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
    transform: scale(1.03) translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}
.stButton > button:active {
    transform: scale(0.97) !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 8px var(--accent-glow) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
    box-shadow: 0 6px 20px var(--accent-glow) !important;
}
.stButton > button[kind="primary"]:active {
    background: #C2410C !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: var(--card-bg);
    border: 1px solid var(--separator);
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
    border-top: 1px solid var(--separator) !important;
    margin: 0.8rem 0;
}

/* ── Typography ── */
.stMarkdown {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
    font-weight: 700 !important;
}
.stMarkdown p, .stMarkdown li {
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
}
.stMarkdown strong, b, strong {
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

/* ── Alerts ── */
.stAlert > div {
    border-radius: 12px !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Expander ── */
details {
    background: #fff !important;
    border: 1px solid var(--separator) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-sm) !important;
}
details summary {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 1.5rem;
    color: var(--text-tertiary);
}
.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 0.8rem;
    opacity: 0.5;
}
.empty-state-text {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
}
.empty-state-hint {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-top: 0.3rem;
}

/* ── Hide defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Kill ALL Streamlit wrapper borders/backgrounds ── */
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stHorizontalBlockBorderWrapper"],
[data-testid="stHorizontalBlock"],
[data-testid="stColumn"],
[data-testid="stColumns"],
div[data-testid="stVerticalBlock"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

/* Kill any empty/nested wrappers */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div:empty),
[data-testid="stHorizontalBlockBorderWrapper"]:has(> div:empty) {
    display: none !important;
}

/* Kill form wrapper border unless it's the settings form */
[data-testid="stForm"]:not(.settings-form) {
    border: none !important;
    background: transparent !important;
}

/* Force all direct children of columns to be transparent */
[data-testid="stColumn"] > div {
    background: transparent !important;
    border: none !important;
}

/* Remove any remaining box-shadow on Streamlit internals */
.stApp div[data-testid="stVerticalBlockBorderWrapper"] > div,
.stApp [data-testid="stHorizontalBlock"] > div > div {
    box-shadow: none !important;
    border: none !important;
    background: transparent !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(0,0,0,0.12);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(0,0,0,0.2);
}

/* ══════════════════════════════════════════════════════════════════
   ANIMATIONS — CSS Keyframes
   ══════════════════════════════════════════════════════════════════ */

/* Hero entrance: drop + bounce */
@keyframes heroDrop {
    0%   { opacity: 0; transform: translateY(-40px) scale(0.96); }
    50%  { opacity: 1; transform: translateY(6px) scale(1.01); }
    70%  { transform: translateY(-3px) scale(0.995); }
    85%  { transform: translateY(1px) scale(1.002); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* Card spring entrance */
@keyframes cardIn {
    0%   { opacity: 0; transform: translateY(30px) scale(0.97); }
    60%  { opacity: 1; transform: translateY(-4px) scale(1.008); }
    80%  { transform: translateY(2px) scale(0.998); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* Slide from left */
@keyframes slideLeft {
    0%   { opacity: 0; transform: translateX(-30px); }
    70%  { opacity: 1; transform: translateX(4px); }
    100% { opacity: 1; transform: translateX(0); }
}

/* Slide from right */
@keyframes slideRight {
    0%   { opacity: 0; transform: translateX(30px); }
    70%  { opacity: 1; transform: translateX(-4px); }
    100% { opacity: 1; transform: translateX(0); }
}

/* Scale pop in */
@keyframes popIn {
    0%   { opacity: 0; transform: scale(0.85); }
    60%  { opacity: 1; transform: scale(1.05); }
    80%  { transform: scale(0.98); }
    100% { opacity: 1; transform: scale(1); }
}

/* Breathing glow */
@keyframes breatheGlow {
    0%, 100% { box-shadow: 0 4px 16px rgba(251,146,60,0.15); }
    50%      { box-shadow: 0 8px 32px rgba(251,146,60,0.3); }
}

/* Float up and down */
@keyframes gentleFloat {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-4px); }
}

/* Shimmer on hero */
@keyframes shimmer {
    0%   { left: -100%; }
    100% { left: 200%; }
}

/* Pulse ring on buttons */
@keyframes pulseRing {
    0%   { box-shadow: 0 0 0 0 rgba(251,146,60,0.4); }
    70%  { box-shadow: 0 0 0 10px rgba(251,146,60,0); }
    100% { box-shadow: 0 0 0 0 rgba(251,146,60,0); }
}

/* ══════════════════════════════════════════════════════════════════
   APPLY ANIMATIONS
   ══════════════════════════════════════════════════════════════════ */

/* Hero */
#hero-banner {
    animation: heroDrop 0.9s cubic-bezier(0.22, 1.2, 0.36, 1) both;
}
#hero-banner::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 60%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    animation: shimmer 3s ease-in-out 1s infinite;
    pointer-events: none;
}

/* Cards — staggered entrance */
.card {
    animation: cardIn 0.7s cubic-bezier(0.22, 1.2, 0.36, 1) both;
}
.card:nth-child(1) { animation-delay: 0.1s; }
.card:nth-child(2) { animation-delay: 0.2s; }
.card:nth-child(3) { animation-delay: 0.3s; }
.card:nth-child(4) { animation-delay: 0.4s; }
.card:hover {
    transform: translateY(-4px) scale(1.005);
    box-shadow: 0 14px 44px rgba(160,120,60,0.15);
    border-color: rgba(251,146,60,0.2);
}
.card:active {
    transform: translateY(-1px) scale(0.998);
    transition: transform 0.15s ease;
}

/* Pro / Con */
.pro-box {
    animation: slideLeft 0.7s cubic-bezier(0.22, 1.2, 0.36, 1) 0.3s both;
}
.con-box {
    animation: slideRight 0.7s cubic-bezier(0.22, 1.2, 0.36, 1) 0.4s both;
}
.pro-box:hover {
    transform: translateX(3px) scale(1.01);
    box-shadow: 0 8px 28px rgba(52,199,89,0.12);
}
.con-box:hover {
    transform: translateX(-3px) scale(1.01);
    box-shadow: 0 8px 28px rgba(255,59,48,0.12);
}

/* Yoozoo button */
.yoozoo-btn {
    animation: popIn 0.6s cubic-bezier(0.22, 1.2, 0.36, 1) 0.5s both,
               breatheGlow 2.5s ease-in-out 1.5s infinite;
}
.yoozoo-btn:hover {
    transform: scale(1.04) translateY(-2px);
    box-shadow: 0 8px 28px rgba(251,146,60,0.35);
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
    animation: none;
}
.yoozoo-btn:active {
    transform: scale(0.97);
    transition: transform 0.1s ease;
}

/* Empty state */
.empty-state {
    animation: popIn 0.8s cubic-bezier(0.22, 1.2, 0.36, 1) 0.2s both;
}
.empty-state-icon {
    animation: gentleFloat 3s ease-in-out infinite;
}

/* Buttons — spring hover + pulse */
.stButton > button {
    position: relative;
    overflow: hidden;
}
.stButton > button:hover {
    transform: scale(1.04) translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1) !important;
}
.stButton > button:active {
    transform: scale(0.96) !important;
    transition: transform 0.08s ease !important;
}
.stButton > button[kind="primary"]:hover {
    animation: pulseRing 1.5s ease-in-out infinite;
}

/* Model pills */
.model-pill {
    animation: cardIn 0.5s cubic-bezier(0.22, 1.2, 0.36, 1) both;
}
.model-pill:nth-child(1) { animation-delay: 0.05s; }
.model-pill:nth-child(2) { animation-delay: 0.1s; }
.model-pill:nth-child(3) { animation-delay: 0.15s; }
.model-pill:hover {
    transform: scale(1.03) translateY(-1px);
    box-shadow: 0 6px 20px rgba(251,146,60,0.2);
}

/* Inputs — focus glow */
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    transform: scale(1.01);
    box-shadow: 0 0 0 3px rgba(251,146,60,0.18), 0 4px 12px rgba(0,0,0,0.06) !important;
}

/* Selectbox — hover lift */
.stSelectbox > div > div:hover {
    box-shadow: 0 4px 14px rgba(0,0,0,0.08) !important;
}

/* Tab switch animation */
.stTabs [data-baseweb="tab"] {
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    transform: scale(1.03);
}
.stTabs [aria-selected="true"] {
    animation: popIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

/* Prompt box hover */
.prompt-box {
    transition: transform 0.4s cubic-bezier(0.22, 1.2, 0.36, 1), box-shadow 0.4s ease;
}
.prompt-box:hover {
    transform: scale(1.01);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

/* Metric cards */
[data-testid="stMetric"] {
    animation: cardIn 0.6s cubic-bezier(0.22, 1.2, 0.36, 1) both;
    transition: transform 0.4s cubic-bezier(0.22, 1.2, 0.36, 1), box-shadow 0.4s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(160,120,60,0.12);
}

/* Alert pop */
.stAlert > div {
    animation: popIn 0.5s cubic-bezier(0.22, 1.2, 0.36, 1) both;
}

/* History rows */
.stHorizontalBlock {
    animation: cardIn 0.4s cubic-bezier(0.22, 1.2, 0.36, 1) both;
}

/* Expander */
details {
    transition: box-shadow 0.4s ease, transform 0.4s cubic-bezier(0.22, 1.2, 0.36, 1);
}
details:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
    transform: translateY(-1px);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #FFF4E6;
    border-right: 1px solid var(--separator);
}
</style>

<!-- GSAP -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
""", unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero" id="hero-banner">
    <h1>🎮 GTarcade PK Generator</h1>
    <p>一键生成中英双语 PK 文案 + AI 生图提示词</p>
</div>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("API_KEY", "")

custom_models = load_custom_models()
model_names = list(custom_models.keys())

# Always have api_key / base_url / model_name available globally
api_key = st.session_state.api_key
base_url = ""
model_name = ""
if model_names:
    _first = custom_models[model_names[0]]
    base_url = _first["base_url"]
    model_name = _first["model"]


# ── Generate Bar (compact controls above results) ────────────────────────
st.markdown('<div class="card" style="padding: 1rem 1.3rem;">', unsafe_allow_html=True)
col_cat, col_hint, col_btns = st.columns([3, 2, 2])
with col_cat:
    category = st.selectbox(
        "主题分类",
        options=list(TOPIC_CATEGORIES.keys()),
        format_func=lambda x: f"{x}  —  {TOPIC_CATEGORIES[x]['en']}",
        label_visibility="collapsed",
        placeholder="选择主题分类",
    )
with col_hint:
    extra_hint = st.text_input("特定方向", placeholder="如：PVP vs PVE（可选）", label_visibility="collapsed")
with col_btns:
    col_gen, col_test = st.columns(2)
    with col_gen:
        generate_clicked = st.button("🚀 生成", type="primary", use_container_width=True)
    with col_test:
        test_clicked = st.button("🔍 测试", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Handle test connection
if test_clicked:
    if not api_key:
        st.error("请先到「⚙️ 设置」填入 API Key")
    elif not model_names:
        st.error("请先到「⚙️ 设置」添加模型")
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

# Handle generate
if generate_clicked:
    if not api_key:
        st.error("请先到「⚙️ 设置」填入 API Key")
        st.stop()
    if not model_names:
        st.error("请先到「⚙️ 设置」添加模型")
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
            st.rerun()
        except ValueError as e:
            st.error("模型返回格式异常")
            with st.expander("查看原始返回"):
                st.code(str(e), language="text")
            st.stop()
        except Exception as e:
            st.error(f"生成失败: {e}")
            st.stop()

st.markdown("")

# ── Results Area ─────────────────────────────────────────────────────────
if "pk_data" in st.session_state:
    data = st.session_state["pk_data"]

    # Title card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">📌 标题 TITLE</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="bi-row">
        <div class="bi-col zh"><span class="tag zh">中文</span><br><strong>{data['title_zh']}</strong></div>
        <div class="bi-col en"><span class="tag en">EN</span><br><strong>{data['title_en']}</strong></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Topic card
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

    # Image Prompts
    st.markdown('<div class="card">', unsafe_allow_html=True)
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

else:
    # Empty state
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🎮</div>
        <div class="empty-state-text">在下方配置参数，点击生成按钮开始</div>
        <div class="empty-state-hint">生成的 PK 文案将在这里展示</div>
    </div>
    """, unsafe_allow_html=True)

# Yoozoo AI button - right below results
st.markdown("""
<a href="https://yoozoo.ai/images" target="_blank" class="yoozoo-btn">
    <span class="yoozoo-icon">🎨</span>
    <span>前往 Yoozoo AI 生图平台</span>
</a>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# BOTTOM TABS: Settings + History
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("")
tab_settings, tab_history = st.tabs(["⚙️ 设置", "📊 历史记录"])


# ── Tab: Settings (API Key + Models) ─────────────────────────────────────
with tab_settings:
    # API Key section
    st.markdown("### 🔑 API 配置")
    with st.form("api_config", clear_on_submit=False):
        api_key_input = st.text_input(
            "API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-xxx...",
        )
        if st.form_submit_button("💾 保存 API Key", use_container_width=True, type="primary"):
            st.session_state.api_key = api_key_input
            st.success("API Key 已保存")

    api_key = st.session_state.api_key

    # Model selection (only if models exist)
    if model_names:
        selected_name = st.selectbox("当前使用的模型", options=model_names)
        selected_info = custom_models[selected_name]
        base_url = selected_info["base_url"]
        model_name = selected_info["model"]
        st.caption(f"Base URL: `{base_url}` · Model: `{model_name}`")

    st.markdown("---")

    # Model list
    st.markdown("### 🤖 已保存的模型")
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
                    <span style="color:var(--text-secondary); font-size:0.84rem; font-weight:600;">{info['model']}</span>
                </div>
                <div style="font-size:0.78rem; color:var(--text-secondary); margin:4px 0 10px 6px; font-weight:500;">{info['base_url']}</div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("删除", key=f"dm_{name}", use_container_width=True):
                    del custom_models[name]
                    save_custom_models(custom_models)
                    st.rerun()

    st.markdown("---")

    # Add new model
    st.markdown("### ➕ 添加新模型")
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
        st.info("暂无历史记录。去生成第一个吧！")
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


# ── GSAP via components.html ──────────────────────────────────────────────
components.html("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
<script>
(function() {
    function init() {
        try {
            var doc = window.parent.document;
            if (!doc || typeof gsap === 'undefined') { setTimeout(init, 300); return; }

            // Hero
            var hero = doc.getElementById('hero-banner');
            if (hero) gsap.from(hero, { y: 40, opacity: 0, duration: 0.9, ease: 'back.out(1.7)', delay: 0.1 });

            // Cards stagger
            var cards = doc.querySelectorAll('.card');
            if (cards.length) gsap.from(cards, { y: 30, opacity: 0, duration: 0.7, stagger: 0.12, ease: 'back.out(1.4)', delay: 0.3 });

            // Pro/Con
            var proBox = doc.querySelector('.pro-box');
            var conBox = doc.querySelector('.con-box');
            if (proBox) gsap.from(proBox, { x: -25, opacity: 0, duration: 0.7, ease: 'power3.out', delay: 0.5 });
            if (conBox) gsap.from(conBox, { x: 25, opacity: 0, duration: 0.7, ease: 'power3.out', delay: 0.6 });

            // Yoozoo button
            var yooBtn = doc.querySelector('.yoozoo-btn');
            if (yooBtn) {
                gsap.from(yooBtn, { y: 20, opacity: 0, duration: 0.6, ease: 'back.out(1.5)', delay: 0.7 });
                gsap.to(yooBtn, { boxShadow: '0 8px 32px rgba(251,146,60,0.35)', duration: 2, repeat: -1, yoyo: true, ease: 'sine.inOut', delay: 1.5 });
            }

            // Empty state
            var emptyState = doc.querySelector('.empty-state');
            if (emptyState) gsap.from(emptyState, { scale: 0.9, opacity: 0, duration: 0.8, ease: 'back.out(1.6)', delay: 0.3 });

            // Hover effects
            doc.querySelectorAll('.stButton > button').forEach(function(btn) {
                btn.addEventListener('mouseenter', function() { gsap.to(btn, { scale: 1.05, y: -2, duration: 0.3, ease: 'back.out(2)' }); });
                btn.addEventListener('mouseleave', function() { gsap.to(btn, { scale: 1, y: 0, duration: 0.4, ease: 'elastic.out(1, 0.4)' }); });
            });
            doc.querySelectorAll('.card').forEach(function(card) {
                card.addEventListener('mouseenter', function() { gsap.to(card, { y: -4, scale: 1.005, duration: 0.35, ease: 'back.out(1.5)' }); });
                card.addEventListener('mouseleave', function() { gsap.to(card, { y: 0, scale: 1, duration: 0.4, ease: 'power2.out' }); });
            });
            doc.querySelectorAll('.prompt-box').forEach(function(box) {
                box.addEventListener('mouseenter', function() { gsap.to(box, { scale: 1.02, duration: 0.3, ease: 'back.out(1.5)' }); });
                box.addEventListener('mouseleave', function() { gsap.to(box, { scale: 1, duration: 0.35, ease: 'power2.out' }); });
            });
            if (proBox) {
                proBox.addEventListener('mouseenter', function() { gsap.to(proBox, { x: 3, scale: 1.01, duration: 0.3, ease: 'back.out(1.5)' }); });
                proBox.addEventListener('mouseleave', function() { gsap.to(proBox, { x: 0, scale: 1, duration: 0.35, ease: 'power2.out' }); });
            }
            if (conBox) {
                conBox.addEventListener('mouseenter', function() { gsap.to(conBox, { x: -3, scale: 1.01, duration: 0.3, ease: 'back.out(1.5)' }); });
                conBox.addEventListener('mouseleave', function() { gsap.to(conBox, { x: 0, scale: 1, duration: 0.35, ease: 'power2.out' }); });
            }
            doc.querySelectorAll('.model-pill').forEach(function(pill) {
                pill.addEventListener('mouseenter', function() { gsap.to(pill, { scale: 1.04, y: -1, duration: 0.3, ease: 'back.out(2)' }); });
                pill.addEventListener('mouseleave', function() { gsap.to(pill, { scale: 1, y: 0, duration: 0.35, ease: 'elastic.out(1, 0.4)' }); });
            });

            // MutationObserver for dynamic content
            var observer = new MutationObserver(function(mutations) {
                var hasNew = false;
                mutations.forEach(function(m) { if (m.addedNodes.length) hasNew = true; });
                if (hasNew) {
                    setTimeout(function() {
                        doc.querySelectorAll('.card:not(.gsap-done)').forEach(function(c) {
                            c.classList.add('gsap-done');
                            gsap.from(c, { y: 25, opacity: 0, duration: 0.6, ease: 'back.out(1.3)' });
                        });
                        doc.querySelectorAll('.pro-box:not(.gsap-done)').forEach(function(el) {
                            el.classList.add('gsap-done');
                            gsap.from(el, { x: -20, opacity: 0, duration: 0.6, ease: 'power3.out' });
                        });
                        doc.querySelectorAll('.con-box:not(.gsap-done)').forEach(function(el) {
                            el.classList.add('gsap-done');
                            gsap.from(el, { x: 20, opacity: 0, duration: 0.6, ease: 'power3.out' });
                        });
                    }, 150);
                }
            });
            observer.observe(doc.body, { childList: true, subtree: true });
        } catch(e) { setTimeout(init, 500); }
    }
    if (document.readyState === 'complete') init();
    else window.addEventListener('load', init);
})();
</script>
</body>
</html>
""", height=0, scrolling=False)
