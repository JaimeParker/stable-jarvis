# Prompt System for Deep Reading

The 6 analysis prompts, system prompt, report template, and chunk-summary prompt are no longer hardcoded in `deep_read.py`. They are stored as individual `.md` files under `prompts/{category}/` and loaded at runtime.

## Architecture

```
prompts/
├── categories.toml          # Category registry (name, description, keywords, persona)
├── default/                 # Generic academic prompts (fallback)
│   ├── system.md
│   ├── section-1.md through section-6.md
│   ├── report-template.md
│   └── chunk-summary.md
└── ai-ml/                   # AI/ML-specific prompts
    ├── system.md
    ├── section-1.md through section-6.md
    ├── report-template.md
    └── chunk-summary.md
```

Each `.md` file contains the raw prompt text with `{placeholder}` variables for substitution:
- `{title}` — paper title
- `{content}` — paper full text (or chunk-summarized)
- `{kb_section}` — knowledge base context section
- `{q1}`..`{q6}` (report template only) — the 6 analysis answers

## How It Works

1. **Phase 0**: `classify_paper.py` reads `categories.toml` and matches the paper to a category via LLM
2. **Phase 4**: `deep_read.py --prompt-set {category}` loads all 9 prompt files from `prompts/{category}/`
3. The loaded prompts are used exactly as the old hardcoded constants were

## Adding a New Category

1. Create `prompts/{category}/` directory with all 9 `.md` files
2. Add a `[categories.{category}]` section to `prompts/categories.toml`
3. No code changes needed

## Category: ai-ml (AI / Machine Learning)

The prompts previously hardcoded in `deep_read.py` (before the 2025-05 refactor). Persona: "资深 AI 研究员".

### System Prompt

```
你是一位资深 AI+Robotics 研究员，正在为自己撰写论文精读笔记。
写作要求：
- 语言为学术中文，表达精确，不啰嗦
- 每个 section 至少 200 字，重要内容可更长
- 用具体数字、公式、方法名支撑论点，不写空话
- 遇到方法细节时，解释清楚其设计动机，不只是罗列
- 知识库中有相关论文时，做有实质内容的横向对比，指出异同
- 不引用知识库和论文原文之外未出现的论文
- 所有数学公式必须使用 Markdown 格式：行内公式用 $...$，独立公式用 $$...$$，不得使用 \( \) 或 \[ \]
```

### Section Prompts

See the individual files in `prompts/ai-ml/section-*.md`.

## Category: default (Generic Academic)

General-purpose prompts suitable for any academic discipline. Persona: "资深学术研究者". Uses broader, discipline-agnostic language (e.g., "方法或理论框架" instead of "模型架构", "实验/实证分析" instead of "实验设计与结果").

See `prompts/default/` for the full prompt text.

## KB Section Template

The KB context injection template remains in `deep_read.py` as it's purely structural:

```markdown
## 知识库上下文（已读论文，可用于对比）

{entries}

---
```

## Report Template

Each category has its own `report-template.md`. The section headings can differ between categories (e.g., default uses "核心方法与框架" while ai-ml uses "核心方法").
