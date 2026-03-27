#!/bin/bash
#
# Stable-JARVIS Installation Script
# This script automates the installation of skills, agents, and commands
# by creating symbolic links for the selected client and scope.

# --- Color Definitions ---
C_RESET='\e[0m'
C_BOLD='\e[1m'
C_CYAN='\e[0;36m'
C_GREEN='\e[0;32m'
C_YELLOW='\e[0;33m'
C_BLUE='\e[0;34m'
C_MAGENTA='\e[0;35m'
C_WHITE_BOLD='\e[1;37m'
C_YELLOW_BOLD='\e[1;33m'
C_GREEN_BOLD='\e[1;32m'

# --- Asset & Description Definitions ---

# Use associative arrays for descriptions for easier lookup.
# English Descriptions
declare -A DESC_EN
DESC_EN["arxiv-search"]="Search arXiv preprint repository for papers in various fields."
DESC_EN["deep-research"]="Multi-source deep research using firecrawl and exa MCPs."
DESC_EN["exa-search"]="Neural search via Exa MCP for web, code, and company research."
DESC_EN["notion-to-markdown"]="Directly convert Notion pages to Obsidian-friendly Markdown."
DESC_EN["obsidian-auto-classifier"]="Intelligently organize and categorize Markdown notes within an Obsidian vault."
DESC_EN["obsidian-markdown"]="Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, etc."
DESC_EN["paper-analyzer"]="Analyze literature in Zotero, generate Markdown reports with LaTeX, and upload as Zotero Notes."
DESC_EN["paper-finder"]="Discover recent arXiv papers matching a research profile and generate Obsidian-compatible notes."
DESC_EN["web-research"]="Provides a structured approach to conducting comprehensive web research."
DESC_EN["continuous-agent-loop"]="Patterns for continuous autonomous agent loops with quality gates and recovery."
DESC_EN["continuous-learning"]="Automatically extract reusable patterns from sessions and save them as learned skills."
DESC_EN["continuous-learning-v2"]="Instinct-based learning system that observes sessions to create and evolve skills."
DESC_EN["cpp-coding-standards"]="C++ coding standards based on the C++ Core Guidelines for modern, safe code."
DESC_EN["docker-patterns"]="Docker and Docker Compose patterns for local development and container orchestration."
DESC_EN["iterative-retrieval"]="Pattern for progressively refining context retrieval to solve subagent context problems."
DESC_EN["python-patterns"]="Pythonic idioms, PEP 8 standards, and best practices for robust Python apps."
DESC_EN["skill-creator"]="Create new skills, modify existing skills, and measure their performance."
DESC_EN["verification-loop"]="A comprehensive verification system for Claude Code sessions."
DESC_EN["videodb"]="See, Understand, and Act on video and audio content from various sources."
DESC_EN["autonomous-loops"]="Patterns and architectures for autonomous Claude Code loops."
DESC_EN["brainstorming"]="A skill for brainstorming and generating ideas."
DESC_EN["executing-plans"]="A skill for executing pre-defined plans."
DESC_EN["tech-doc-writing"]="Write technical documentation, guides, and tutorials with a consistent voice."
DESC_EN["writing-plans"]="A skill for creating detailed plans for complex tasks."
DESC_EN["pptx"]="Create, read, and edit .pptx presentations, from content extraction to generation."
DESC_EN["weekly-report-generator"]="Automatically generates a 1-page weekly progress report PPTX from Obsidian notes."
DESC_EN["knowledge-distillation-from-discussion"]="Distills raw discussions and meeting notes into structured, permanent knowledge notes following Zettelkasten methodology."

# Chinese Descriptions
declare -A DESC_CN
DESC_CN["arxiv-search"]="在 arXiv 预印本库中搜索各领域的论文。"
DESC_CN["deep-research"]="使用 firecrawl 和 exa MCPs 进行多源深度研究。"
DESC_CN["exa-search"]="通过 Exa MCP 进行神经网络搜索，用于网络、代码和公司研究。"
DESC_CN["notion-to-markdown"]="将 Notion 页面直接转换为 Obsidian 友好的 Markdown。"
DESC_CN["obsidian-auto-classifier"]="在 Obsidian 保险库中智能地组织和分类 Markdown 笔记。"
DESC_CN["obsidian-markdown"]="创建和编辑带有 wikilinks、嵌入、callouts 等功能的 Obsidian 风格 Markdown。"
DESC_CN["paper-analyzer"]="分析 Zotero 中的文献，生成带 LaTeX 的 Markdown 报告，并上传为 Zotero 笔记。"
DESC_CN["paper-finder"]="发现符合研究兴趣的最新 arXiv 论文，并生成 Obsidian 兼容的笔记。"
DESC_CN["web-research"]="提供一种进行全面网络研究的结构化方法。"
DESC_CN["continuous-agent-loop"]="具有质量门和恢复控制的连续自主智能体循环模式。"
DESC_CN["continuous-learning"]="从会话中自动提取可重用模式并将其保存为学习到的技能。"
DESC_CN["continuous-learning-v2"]="基于本能的学习系统，通过观察会话来创建和演进技能。"
DESC_CN["cpp-coding-standards"]="基于 C++ 核心指南的 C++ 编码标准，用于现代、安全的代码。"
DESC_CN["docker-patterns"]="用于本地开发和容器编排的 Docker 和 Docker Compose 模式。"
DESC_CN["iterative-retrieval"]="用于逐步优化上下文检索以解决子智能体上下文问题的模式。"
DESC_CN["python-patterns"]="用于构建健壮 Python 应用程序的 Pythonic 惯用法、PEP 8 标准和最佳实践。"
DESC_CN["skill-creator"]="创建新技能、修改现有技能并衡量其性能。"
DESC_CN["verification-loop"]="一个用于 Claude Code 会话的综合验证系统。"
DESC_CN["videodb"]="观察、理解和操作来自各种来源的视频和音频内容。"
DESC_CN["autonomous-loops"]="用于自主 Claude Code 循环的模式和架构。"
DESC_CN["brainstorming"]="一个用于头脑风暴和产生想法的技能。"
DESC_CN["executing-plans"]="一个用于执行预定义计划的技能。"
DESC_CN["tech-doc-writing"]="以一致的风格编写技术文档、指南和教程。"
DESC_CN["writing-plans"]="一个为复杂任务创建详细计划的技能。"
DESC_CN["pptx"]="创建、读取和编辑 .pptx 演示文稿，从内容提取到生成。"
DESC_CN["weekly-report-generator"]="根据 Obsidian 笔记自动生成一页的每周进展报告 PPTX。"
DESC_CN["knowledge-distillation-from-discussion"]="将原始讨论和会议记录提炼为结构化的永久知识笔记，遵循 Zettelkasten 方法论。"

# --- Asset Categorization ---
RESEARCH_SKILLS=("arxiv-search" "exa-search" "notion-to-markdown" "obsidian-auto-classifier" "obsidian-markdown" "paper-analyzer" "paper-finder" "web-research")
RESEARCH_AGENTS=("doc-updater.md")
RESEARCH_COMMANDS=("paper/analyze.toml")
CODING_SKILLS=("continuous-agent-loop" "continuous-learning" "continuous-learning-v2" "cpp-coding-standards" "docker-patterns" "iterative-retrieval" "python-patterns" "verification-loop" "videodb" "writing-plans")
CODING_AGENTS=("architect.md" "build-error-resolver.md" "code-reviewer.md" "python-reviewer.md" "security-reviewer.md")
DAILY_SKILLS=("autonomous-loops" "brainstorming" "executing-plans" "tech-doc-writing" "skill-creator" "deep-research" "knowledge-distillation-from-discussion")
DAILY_AGENTS=("loop-operator.md" "planner.md")
DAILY_COMMANDS=("daily/plan.toml")
LAB_SKILLS=( "pptx" "weekly-report-generator" )

# --- Helper Functions ---

display_categories() {
    echo -e "${C_WHITE_BOLD}----------------------------------${C_RESET}"
    echo -e "${C_WHITE_BOLD}Available Asset Categories (可用资产类别)${C_RESET}"
    echo -e "${C_WHITE_BOLD}----------------------------------${C_RESET}"

    local category_names=("RESEARCH" "CODING" "DAILY" "LAB_SKILLS")
    local category_cns=("科研" "编程" "日常" "实验室专用")
    local skill_arrays=("RESEARCH_SKILLS" "CODING_SKILLS" "DAILY_SKILLS" "LAB_SKILLS")

    for i in "${!category_names[@]}"; do
        local cat_name="${category_names[$i]}"
        local cat_cn="${category_cns[$i]}"
        local skills_ref="${skill_arrays[$i]}[@]"
        local skills=("${!skills_ref}")

        echo -e "\n${C_BOLD}${C_BLUE}[$cat_name] ($cat_cn)${C_RESET}"
        for skill in "${skills[@]}"; do
            echo -e "  - ${C_BOLD}$skill${C_RESET}"
            echo -e "    - ${C_CYAN}EN:${C_RESET} ${DESC_EN[$skill]}"
            echo -e "    - ${C_CYAN}CN:${C_RESET} ${DESC_CN[$skill]}"
        done
    done
}

link_items() {
    local dest_dir="$1"; shift
    local items=("$@")
    
    mkdir -p "$dest_dir"
    for item in "${items[@]}"; do
        local source_path="$(pwd)/$item"
        local dest_path="$dest_dir/$(basename "$item")"
        if [ -e "$dest_path" ]; then
            echo -e "    - ${C_YELLOW_BOLD}WARNING:${C_RESET} '${C_MAGENTA}$dest_path${C_RESET}' already exists. Skipping. (警告: 已存在，跳过。)"
        else
            ln -s "$source_path" "$dest_path"
            echo -e "    - ${C_GREEN}Linked${C_RESET} '${C_MAGENTA}$(basename "$item")${C_RESET}'."
        fi
    done
}

install_assets() {
    local client_name="$1"; local base_dir="$2"; local workspace_dir="$3"; local agent_dir_name="$4"

    echo -e "
--- ${C_GREEN_BOLD}Installing for $client_name (正在为 $client_name 安装)${C_RESET} ---"

    if [ "$INSTALL_RESEARCH_GLOBAL" = true ] || [ "$INSTALL_CODING_GLOBAL" = true ] || [ "$INSTALL_DAILY_GLOBAL" = true ] || [ "$INSTALL_LAB_GLOBAL" = true ]; then
        echo -e "${C_BOLD}Linking global assets to '${C_MAGENTA}$base_dir${C_RESET}'...${C_RESET}"
        [ "$INSTALL_RESEARCH_GLOBAL" = true ] && link_items "$base_dir/skills" "${RESEARCH_SKILLS[@]/#/skills/}" && link_items "$base_dir/$agent_dir_name" "${RESEARCH_AGENTS[@]/#/agents/}"
        [ "$INSTALL_CODING_GLOBAL" = true ] && link_items "$base_dir/skills" "${CODING_SKILLS[@]/#/skills/}" && link_items "$base_dir/$agent_dir_name" "${CODING_AGENTS[@]/#/agents/}"
        [ "$INSTALL_DAILY_GLOBAL" = true ] && link_items "$base_dir/skills" "${DAILY_SKILLS[@]/#/skills/}" && link_items "$base_dir/$agent_dir_name" "${DAILY_AGENTS[@]/#/agents/}"
        [ "$INSTALL_LAB_GLOBAL" = true ] && link_items "$base_dir/skills" "${LAB_SKILLS[@]/#/skills/}"
    fi

    if [ "$INSTALL_RESEARCH_LOCAL" = true ] || [ "$INSTALL_CODING_LOCAL" = true ] || [ "$INSTALL_DAILY_LOCAL" = true ] || [ "$INSTALL_LAB_LOCAL" = true ]; then
        echo -e "${C_BOLD}Linking local assets to '${C_MAGENTA}$workspace_dir${C_RESET}'...${C_RESET}"
        [ "$INSTALL_RESEARCH_LOCAL" = true ] && link_items "$workspace_dir/skills" "${RESEARCH_SKILLS[@]/#/skills/}" && link_items "$workspace_dir/$agent_dir_name" "${RESEARCH_AGENTS[@]/#/agents/}"
        [ "$INSTALL_CODING_LOCAL" = true ] && link_items "$workspace_dir/skills" "${CODING_SKILLS[@]/#/skills/}" && link_items "$workspace_dir/$agent_dir_name" "${CODING_AGENTS[@]/#/agents/}"
        [ "$INSTALL_DAILY_LOCAL" = true ] && link_items "$workspace_dir/skills" "${DAILY_SKILLS[@]/#/skills/}" && link_items "$workspace_dir/$agent_dir_name" "${DAILY_AGENTS[@]/#/agents/}"
        [ "$INSTALL_LAB_LOCAL" = true ] && link_items "$workspace_dir/skills" "${LAB_SKILLS[@]/#/skills/}"
    fi
    
    if [ "$client_name" = "Gemini CLI" ]; then
        if [ "$INSTALL_RESEARCH_GLOBAL" = true ]; then mkdir -p "$base_dir/commands/paper"; ln -sf "$(pwd)/commands/paper/analyze.toml" "$base_dir/commands/paper:analyze.toml"; fi
        if [ "$INSTALL_DAILY_GLOBAL" = true ]; then mkdir -p "$base_dir/commands/daily"; ln -sf "$(pwd)/commands/daily/plan.toml" "$base_dir/commands/daily:plan.toml"; fi
        if [ "$INSTALL_RESEARCH_LOCAL" = true ]; then mkdir -p "$workspace_dir/commands/paper"; ln -sf "$(pwd)/commands/paper/analyze.toml" "$workspace_dir/commands/paper:analyze.toml"; fi
        if [ "$INSTALL_DAILY_LOCAL" = true ]; then mkdir -p "$workspace_dir/commands/daily"; ln -sf "$(pwd)/commands/daily/plan.toml" "$workspace_dir/commands/daily:plan.toml"; fi
    fi
}

# --- Main Script ---

echo -e "${C_GREEN_BOLD}=======================================${C_RESET}"
echo -e "${C_GREEN_BOLD} Stable-JARVIS Asset Installer (智能资产安装程序)${C_RESET}"
echo -e "${C_GREEN_BOLD}=======================================${C_RESET}"
echo "This script will create symbolic links for skills, agents, and commands."
echo "(本脚本将为技能、智能体和命令创建符号链接。)"

display_categories

echo -e "
${C_YELLOW_BOLD}Step 1: Choose your AI client (第一步: 选择您的 AI 客户端)${C_RESET}"
echo -e "${C_WHITE_BOLD}--------------------------------${C_RESET}"
echo "  1) Gemini CLI"
echo "  2) Claude Code"
echo "  3) Codex / GitHub Copilot"
read -p "Enter the number of your client (请输入客户端对应的数字): " client_choice

INSTALL_RESEARCH_GLOBAL=false; INSTALL_CODING_GLOBAL=false; INSTALL_DAILY_GLOBAL=false; INSTALL_LAB_GLOBAL=false
INSTALL_RESEARCH_LOCAL=false; INSTALL_CODING_LOCAL=false; INSTALL_DAILY_LOCAL=false; INSTALL_LAB_LOCAL=false

echo -e "
${C_YELLOW_BOLD}Step 2: Select GLOBAL asset categories to install (第二步: 选择要安装的 全局 资产类别)${C_RESET}"
echo -e "${C_WHITE_BOLD}----------------------------------------------------${C_RESET}"
read -p "  -> Install RESEARCH assets (科研)? [y/N]: " research_choice_g
read -p "  -> Install CODING assets (编程)? [y/N]: " coding_choice_g
read -p "  -> Install DAILY assets (日常)? [y/N]: " daily_choice_g
read -p "  -> Install LAB_SKILLS assets (实验室专用)? [y/N]: " lab_choice_g
[[ "$research_choice_g" =~ ^[Yy]$ ]] && INSTALL_RESEARCH_GLOBAL=true
[[ "$coding_choice_g" =~ ^[Yy]$ ]] && INSTALL_CODING_GLOBAL=true
[[ "$daily_choice_g" =~ ^[Yy]$ ]] && INSTALL_DAILY_GLOBAL=true
[[ "$lab_choice_g" =~ ^[Yy]$ ]] && INSTALL_LAB_GLOBAL=true

echo -e "
${C_YELLOW_BOLD}Step 3: Select LOCAL asset categories to install (第三步: 选择要安装的 本地 资产类别)${C_RESET}"
echo -e "${C_WHITE_BOLD}--------------------------------------------------${C_RESET}"
echo "Only categories not installed globally will be shown. (仅显示未全局安装的类别。)"

ANY_LOCAL_PROMPTS=false
if ! $INSTALL_RESEARCH_GLOBAL || ! $INSTALL_CODING_GLOBAL || ! $INSTALL_DAILY_GLOBAL || ! $INSTALL_LAB_GLOBAL; then ANY_LOCAL_PROMPTS=true; fi

if $ANY_LOCAL_PROMPTS; then
    ! $INSTALL_RESEARCH_GLOBAL && read -p "  -> Install RESEARCH assets (科研)? [y/N]: " rcl && [[ "$rcl" =~ ^[Yy]$ ]] && INSTALL_RESEARCH_LOCAL=true
    ! $INSTALL_CODING_GLOBAL && read -p "  -> Install CODING assets (编程)? [y/N]: " ccl && [[ "$ccl" =~ ^[Yy]$ ]] && INSTALL_CODING_LOCAL=true
    ! $INSTALL_DAILY_GLOBAL && read -p "  -> Install DAILY assets (日常)? [y/N]: " dcl && [[ "$dcl" =~ ^[Yy]$ ]] && INSTALL_DAILY_LOCAL=true
    ! $INSTALL_LAB_GLOBAL && read -p "  -> Install LAB_SKILLS assets (实验室专用)? [y/N]: " lcl && [[ "$lcl" =~ ^[Yy]$ ]] && INSTALL_LAB_LOCAL=true
else
    echo "All categories selected for global installation. Nothing to install locally. (所有类别均已选择全局安装，无需本地安装。)"
fi

echo -e "
${C_YELLOW_BOLD}Step 4: Performing installation (第四步: 执行安装)${C_RESET}"
echo -e "${C_WHITE_BOLD}---------------------------------${C_RESET}"

case $client_choice in
    1) install_assets "Gemini CLI" "$HOME/.gemini" ".gemini" "agents";;
    2) install_assets "Claude Code" "$HOME/.claude" ".claude" "agents";;
    3) install_assets "Codex / GitHub Copilot" "$HOME/.copilot" ".github" "instructions";;
    *) echo -e "${C_YELLOW_BOLD}Invalid choice. Exiting. (无效选择，正在退出。)${C_RESET}"; exit 1;;
esac

echo -e "
${C_GREEN_BOLD}=======================================${C_RESET}"
echo -e "${C_GREEN_BOLD} Installation Complete! (安装完成！)${C_RESET}"
echo -e "${C_GREEN_BOLD}=======================================${C_RESET}"
if [ "$client_choice" -eq 1 ]; then
    echo "-> Remember to run '/commands reload' in Gemini CLI if you installed new commands."
    echo "   (如果在 Gemini CLI 中安装了新命令，请记得运行 '/commands reload'。)"
fi
