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

# --- Asset Categorization ---
# All categories, skills, agents, and commands are defined in skill-taxonomy.xml.
# The parse_taxonomy() function reads this file and populates the arrays below.

CATEGORY_IDS=()
declare -A CATEGORY_CN DESC_EN DESC_CN

parse_taxonomy() {
	    local xml_file
	    xml_file="$(dirname "$0")/skill-taxonomy.xml"
	    if [ ! -f "$xml_file" ]; then
	        echo -e "${C_YELLOW_BOLD}ERROR: skill-taxonomy.xml not found at $xml_file${C_RESET}"
	        exit 1
	    fi
	    eval "$(python3 <<PYEOF
import xml.etree.ElementTree as ET
tree = ET.parse('$xml_file')
root = tree.getroot()
# Category IDs and Chinese names
for cat in root.findall('category'):
    cid = cat.get('id')
    cn = cat.get('cn', '')
    print('CATEGORY_IDS+=("' + cid + '")')
    print('CATEGORY_CN["' + cid + '"]="' + cn + '"')
print()
# Skill lists and descriptions (en/cn attributes on <skill> elements)
for cat in root.findall('category'):
    cid = cat.get('id')
    skills = []
    for s in cat.findall('skills/skill'):
        name = s.text.strip() if s.text else ''
        if not name:
            continue
        skills.append(name)
        desc_en = s.get('en', '')
        desc_cn = s.get('cn', '')
        print('DESC_EN["' + name + '"]="' + desc_en.replace('"', '\\"') + '"')
        print('DESC_CN["' + name + '"]="' + desc_cn.replace('"', '\\"') + '"')
    agents = [a.text.strip() for a in cat.findall('agents/agent') if a.text]
    commands = [c.text.strip() for c in cat.findall('commands/command') if c.text]
    if skills:
        print(cid + '_SKILLS=(' + ' '.join('"' + s + '"' for s in skills) + ')')
    else:
        print(cid + '_SKILLS=()')
    if agents:
        print(cid + '_AGENTS=(' + ' '.join('"' + a + '"' for a in agents) + ')')
    else:
        print(cid + '_AGENTS=()')
    if commands:
        print(cid + '_COMMANDS=(' + ' '.join('"' + c + '"' for c in commands) + ')')
    else:
        print(cid + '_COMMANDS=()')
PYEOF
)"
	}

parse_taxonomy

# --- Helper Functions ---

display_categories() {
    echo -e "${C_WHITE_BOLD}----------------------------------${C_RESET}"
    echo -e "${C_WHITE_BOLD}Available Asset Categories (可用资产类别)${C_RESET}"
    echo -e "${C_WHITE_BOLD}----------------------------------${C_RESET}"

    for cid in "${CATEGORY_IDS[@]}"; do
        local cn="${CATEGORY_CN[$cid]}"
        local skills_ref="${cid}_SKILLS[@]"
        local skills=("${!skills_ref}")

        echo -e "\n${C_BOLD}${C_BLUE}[$cid] ($cn)${C_RESET}"
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
    local client_name="$1"; local global_skills_dir="$2"; local global_agents_dir="$3"; local local_skills_dir="$4"; local local_agents_dir="$5"

    echo -e "
--- ${C_GREEN_BOLD}Installing for $client_name (正在为 $client_name 安装)${C_RESET} ---"

    if [ "$INSTALL_RESEARCH_GLOBAL" = true ] || [ "$INSTALL_CODING_GLOBAL" = true ] || [ "$INSTALL_DAILY_GLOBAL" = true ] || [ "$INSTALL_LAB_GLOBAL" = true ]; then
        echo -e "${C_BOLD}Linking global assets to '${C_MAGENTA}$global_skills_dir${C_RESET}' and '${C_MAGENTA}$global_agents_dir${C_RESET}'...${C_RESET}"
        [ "$INSTALL_RESEARCH_GLOBAL" = true ] && link_items "$global_skills_dir" "${RESEARCH_SKILLS[@]/#/skills/}" && link_items "$global_agents_dir" "${RESEARCH_AGENTS[@]/#/agents/}"
        [ "$INSTALL_CODING_GLOBAL" = true ] && link_items "$global_skills_dir" "${CODING_SKILLS[@]/#/skills/}" && link_items "$global_agents_dir" "${CODING_AGENTS[@]/#/agents/}"
        [ "$INSTALL_DAILY_GLOBAL" = true ] && link_items "$global_skills_dir" "${DAILY_SKILLS[@]/#/skills/}" && link_items "$global_agents_dir" "${DAILY_AGENTS[@]/#/agents/}"
        [ "$INSTALL_LAB_GLOBAL" = true ] && link_items "$global_skills_dir" "${LAB_SKILLS[@]/#/skills/}"
    fi

    if [ "$INSTALL_RESEARCH_LOCAL" = true ] || [ "$INSTALL_CODING_LOCAL" = true ] || [ "$INSTALL_DAILY_LOCAL" = true ] || [ "$INSTALL_LAB_LOCAL" = true ]; then
        echo -e "${C_BOLD}Linking local assets to '${C_MAGENTA}$local_skills_dir${C_RESET}' and '${C_MAGENTA}$local_agents_dir${C_RESET}'...${C_RESET}"
        [ "$INSTALL_RESEARCH_LOCAL" = true ] && link_items "$local_skills_dir" "${RESEARCH_SKILLS[@]/#/skills/}" && link_items "$local_agents_dir" "${RESEARCH_AGENTS[@]/#/agents/}"
        [ "$INSTALL_CODING_LOCAL" = true ] && link_items "$local_skills_dir" "${CODING_SKILLS[@]/#/skills/}" && link_items "$local_agents_dir" "${CODING_AGENTS[@]/#/agents/}"
        [ "$INSTALL_DAILY_LOCAL" = true ] && link_items "$local_skills_dir" "${DAILY_SKILLS[@]/#/skills/}" && link_items "$local_agents_dir" "${DAILY_AGENTS[@]/#/agents/}"
        [ "$INSTALL_LAB_LOCAL" = true ] && link_items "$local_skills_dir" "${LAB_SKILLS[@]/#/skills/}"
    fi
    
    if [ "$client_name" = "Gemini CLI" ]; then
        local global_root
        local local_root
        global_root="$(dirname "$global_skills_dir")"
        local_root="$(dirname "$local_skills_dir")"
        if [ "$INSTALL_RESEARCH_GLOBAL" = true ]; then mkdir -p "$global_root/commands/paper"; ln -sf "$(pwd)/commands/paper/analyze.toml" "$global_root/commands/paper/analyze.toml"; fi
        if [ "$INSTALL_DAILY_GLOBAL" = true ]; then mkdir -p "$global_root/commands/daily"; ln -sf "$(pwd)/commands/daily/plan.toml" "$global_root/commands/daily/plan.toml"; fi
        if [ "$INSTALL_RESEARCH_LOCAL" = true ]; then mkdir -p "$local_root/commands/paper"; ln -sf "$(pwd)/commands/paper/analyze.toml" "$local_root/commands/paper/analyze.toml"; fi
        if [ "$INSTALL_DAILY_LOCAL" = true ]; then mkdir -p "$local_root/commands/daily"; ln -sf "$(pwd)/commands/daily/plan.toml" "$local_root/commands/daily/plan.toml"; fi
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
echo "  3) Codex"
read -p "Enter the number of your client (请输入客户端对应的数字): " client_choice

INSTALL_RESEARCH_GLOBAL=false; INSTALL_CODING_GLOBAL=false; INSTALL_DAILY_GLOBAL=false; INSTALL_LAB_GLOBAL=false
INSTALL_RESEARCH_LOCAL=false; INSTALL_CODING_LOCAL=false; INSTALL_DAILY_LOCAL=false; INSTALL_LAB_LOCAL=false

echo -e "
${C_YELLOW_BOLD}Step 2: Select GLOBAL asset categories to install (第二步: 选择要安装的 全局 资产类别)${C_RESET}"
echo -e "${C_WHITE_BOLD}----------------------------------------------------${C_RESET}"
read -p "  -> Install RESEARCH assets (科研)? [y/N]: " research_choice_g
read -p "  -> Install CODING assets (编程)? [y/N]: " coding_choice_g
read -p "  -> Install DAILY assets (日常)? [y/N]: " daily_choice_g
read -p "  -> Install LAB assets (实验室专用)? [y/N]: " lab_choice_g
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
    1) install_assets "Gemini CLI" "$HOME/.gemini/skills" "$HOME/.gemini/agents" ".gemini/skills" ".gemini/agents";;
    2) install_assets "Claude Code" "$HOME/.claude/skills" "$HOME/.claude/agents" ".claude/skills" ".claude/agents";;
    3) install_assets "Codex" "$HOME/.codex/skills" "$HOME/.codex/agents" ".agents/skills" ".codex/agents";;
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
