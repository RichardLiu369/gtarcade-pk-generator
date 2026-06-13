SYSTEM_PROMPT = """You are a creative content writer for GTarcade, a global gaming and lifestyle community platform. Your job is to create engaging PK (Player vs Player) debate topics that spark lively discussion.

CRITICAL RULES:
- Your ENTIRE response must be ONE valid JSON object. Nothing else. No explanation, no markdown, no text before or after.
- All Chinese and English content must be natural, not literal translations
- Both sides of the debate must be equally compelling — NO one-sided arguments
- Image prompts must be detailed, specific, and visually descriptive
- Keep the tone fun, provocative, and community-friendly
- The topic should resonate with a young, global audience
"""

TOPIC_CATEGORIES = {
    # ── Gaming ──
    "角色与养成": {
        "en": "Heroes & Progression",
        "desc": "hero leveling, equipment, skill builds, team composition",
    },
    "策略与玩法": {
        "en": "Strategy & Gameplay",
        "desc": "battle tactics, resource management, alliance strategy",
    },
    "社交与联盟": {
        "en": "Social & Alliance",
        "desc": "alliance politics, diplomacy, teamwork vs solo play",
    },
    "氪金与公平": {
        "en": "Pay-to-Win vs Fair Play",
        "desc": "spending, free-to-play experience, game economy",
    },
    "游戏文化": {
        "en": "Gaming Culture",
        "desc": "gaming nostalgia, industry trends, classic vs modern games, gaming memes",
    },
    # ── Lifestyle & Daily Life ──
    "生活方式": {
        "en": "Lifestyle",
        "desc": "daily habits, work-life balance, minimalism vs maximalism, morning routines",
    },
    "社交与人际关系": {
        "en": "Social & Relationships",
        "desc": "friendship, dating, social media, online vs offline socializing",
    },
    "美食与饮食": {
        "en": "Food & Diet",
        "desc": "cooking vs ordering, healthy eating, food culture, local delicacies",
    },
    "旅行与探索": {
        "en": "Travel & Adventure",
        "desc": "solo travel vs group trips, budget vs luxury, hidden gems vs tourist spots",
    },
    # ── Pop Culture ──
    "影视与动漫": {
        "en": "Movies, TV & Anime",
        "desc": "movie debates, anime best girl/boy, streaming vs cinema, adaptations",
    },
    "科技与未来": {
        "en": "Tech & Future",
        "desc": "AI, gadgets, social media impact, tech ethics, digital life",
    },
    "音乐与艺术": {
        "en": "Music & Art",
        "desc": "genre debates, old vs new music, creative expression, AI art",
    },
    # ── Fun & Hypothetical ──
    "脑洞与假设": {
        "en": "Hypothetical & What-If",
        "desc": "wild hypotheticals, superpowers, time travel, moral dilemmas",
    },
    "校园与青春": {
        "en": "School & Youth",
        "desc": "student life, exams, campus culture, graduation, generational differences",
    },
    # ── Sports & Competition ──
    "体育与竞技": {
        "en": "Sports & Competition",
        "desc": "team debates, sportsmanship, esports vs traditional sports, GOAT discussions",
    },
    # ── Work & Career ──
    "职场与工作": {
        "en": "Work & Career",
        "desc": "remote work vs office, side hustles, overtime culture, career choices, hustle culture",
    },
    # ── Health & Self-Discipline ──
    "健康与自律": {
        "en": "Health & Self-Discipline",
        "desc": "fitness routines, early birds vs night owls, mental health, personal trainers, discipline vs relaxation",
    },
    # ── Pets & Animals ──
    "宠物与动物": {
        "en": "Pets & Animals",
        "desc": "cats vs dogs, pet ownership debates, animal rights, indoor vs outdoor pets",
    },
    # ── Environment & Sustainability ──
    "环保与生活方式": {
        "en": "Environment & Sustainability",
        "desc": "veganism, fast fashion, zero waste, eco-friendly habits, climate action",
    },
    # ── Love & Dating ──
    "情感与恋爱": {
        "en": "Love & Dating",
        "desc": "single life vs relationships, long-distance love, dating apps, modern romance",
    },
    # ── Money & Spending ──
    "金钱与消费": {
        "en": "Money & Spending",
        "desc": "saving vs spending, consumerism, financial planning, luxury vs frugality",
    },
    # ── Family & Generations ──
    "家庭与代际": {
        "en": "Family & Generations",
        "desc": "generation gaps, parenting styles, traditional vs modern families, aging parents",
    },
    # ── Holidays & Culture ──
    "节日与文化": {
        "en": "Holidays & Culture",
        "desc": "holiday preferences, cultural differences, tradition vs commercialization, global festivals",
    },
}


def build_user_prompt(category: str, category_en: str, desc: str, extra_hint: str = "") -> str:
    hint_section = f"\nAdditional direction: {extra_hint}" if extra_hint else ""

    return f"""Generate ONE PK debate topic for the GTarcade community.

Category: {category} ({category_en})
Context: {desc}{hint_section}

Requirements:
- Title must be catchy and provocative (not boring)
- Both arguments must be ~80-120 words each, with concrete reasoning
- The debate should be genuinely divisive — roughly 50/50 split in community opinion
- Image prompts should depict a dramatic scene representing the conflict, not text or logos

Output JSON with these EXACT keys:
{{
  "title_zh": "PK活动标题（中文）",
  "title_en": "PK Activity Title (English)",
  "topic_zh": "话题描述（中文，2-3句话引导讨论）",
  "topic_en": "Topic description (English, 2-3 sentences to spark discussion)",
  "pro_zh": "正方观点（中文，80-120字，有具体论据）",
  "pro_en": "Pro argument (English, 80-120 words, with concrete reasoning)",
  "con_zh": "反方观点（中文，80-120字，有具体论据）",
  "con_en": "Con argument (English, 80-120 words, with concrete reasoning)",
  "gpt_image_prompt": "Detailed GPT Image2 prompt in English. Describe a dramatic scene: characters, setting, mood, lighting, composition. Style: cinematic, vibrant, game art.",
  "nanobanana_prompt": "Detailed NanoBananaPro prompt in English. Focus on stylized illustration: art style, color palette, character poses, dynamic action. Style: bold, expressive, stylized."
}}

Return ONLY the JSON, no markdown code fences, no extra text."""
