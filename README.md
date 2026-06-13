# 🎮 GTarcade PK Generator

一键生成中英双语 PK (Player vs Player) 辩论文案 + AI 生图提示词，为 GTarcade 社区活动提供内容储备。

## ✨ 功能

- **22 个话题方向** — 涵盖游戏、生活、流行文化、体育、情感等领域
- **中英双语输出** — 标题、话题、正反方论点均提供中英文版本
- **AI 生图提示词** — 同时生成 GPT Image2 和 NanoBananaPro 两套风格的图片提示词
- **历史记录** — 自动保存生成记录，方便回溯
- **多模型支持** — 可配置多个 OpenAI 兼容的 API 模型（DeepSeek、通义千问、Kimi、豆包等）
- **一键复制** — 生成结果支持 Markdown 导出

## 📋 话题分类

| 领域 | 分类 |
|------|------|
| 🎮 游戏 | 角色与养成 · 策略与玩法 · 社交与联盟 · 氪金与公平 · 游戏文化 |
| 🏠 生活 | 生活方式 · 美食与饮食 · 旅行与探索 · 职场与工作 · 健康与自律 · 宠物与动物 · 环保与生活方式 |
| 💕 人文 | 社交与人际关系 · 情感与恋爱 · 金钱与消费 · 家庭与代际 · 节日与文化 |
| 🎬 流行 | 影视与动漫 · 科技与未来 · 音乐与艺术 |
| 🎲 趣味 | 脑洞与假设 · 校园与青春 · 体育与竞技 |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- OpenAI 兼容的 API Key

### 安装

```bash
# 克隆仓库
git clone https://github.com/RichardLiu369/gtarcade-pk-generator.git
cd gtarcade-pk-generator

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置 API

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

```env
# 以 DeepSeek 为例
API_KEY=sk-your-key-here
BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

> 💡 也可以在应用内的「⚙️ 设置」页面直接配置 API Key 和模型，支持保存多个模型。

### 启动

```bash
streamlit run app.py
```

Windows 用户可直接双击 `start.bat`。

启动后访问 `http://localhost:8501`。

## 🖥️ 使用方法

1. 选择一个**话题分类**（可选填特定方向提示）
2. 点击 **🚀 生成** 按钮
3. 查看生成的双语文案和生图提示词
4. 通过「📋 导出完整 Markdown」复制内容

## 📁 项目结构

```
gtarcade-pk-generator/
├── app.py               # Streamlit 主应用
├── prompt_template.py   # Prompt 模板与话题分类定义
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量示例
├── .streamlit/          # Streamlit 配置
├── start.bat            # Windows 一键启动脚本
└── show_ip.bat          # Windows 查看本机 IP
```

## 🤖 支持的模型

任何 OpenAI 兼容 API 均可使用，推荐：

| 模型 | Base URL |
|------|----------|
| DeepSeek | `https://api.deepseek.com` |
| 通义千问 (Qwen) | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Kimi (Moonshot) | `https://api.moonshot.cn` |
| 豆包 (Doubao) | `https://ark.cn-beijing.volces.com/api/v3` |

## 📄 License

MIT
