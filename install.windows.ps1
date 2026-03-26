#
# Stable-JARVIS Asset Installer for Windows
# This script automates the installation of skills, agents, and commands
# by creating symbolic links for the selected client and scope.
#
# USAGE:
# 1. Open PowerShell AS ADMINISTRATOR.
# 2. Navigate to the stable-jarvis directory.
# 3. Run the script: .\install.windows.ps1
#
# NOTE: If you get an error about script execution being disabled, run this command first:
# > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#

# --- Administrator Check ---
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script must be run as Administrator to create symbolic links. Please re-open PowerShell as an Administrator and try again."
    exit 1
}

# --- Asset & Description Definitions ---

$Descriptions = @{
    "arxiv-search"              = @{ EN="Search arXiv preprint repository for papers in various fields."; CN="在 arXiv 预印本库中搜索各领域的论文。" };
    "deep-research"             = @{ EN="Multi-source deep research using firecrawl and exa MCPs."; CN="使用 firecrawl 和 exa MCPs 进行多源深度研究。" };
    "exa-search"                = @{ EN="Neural search via Exa MCP for web, code, and company research."; CN="通过 Exa MCP 进行神经网络搜索，用于网络、代码和公司研究。" };
    "notion-to-markdown"        = @{ EN="Directly convert Notion pages to Obsidian-friendly Markdown."; CN="将 Notion 页面直接转换为 Obsidian 友好的 Markdown。" };
    "obsidian-auto-classifier"  = @{ EN="Intelligently organize and categorize Markdown notes within an Obsidian vault."; CN="在 Obsidian 保险库中智能地组织和分类 Markdown 笔记。" };
    "obsidian-markdown"         = @{ EN="Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, etc."; CN="创建和编辑带有 wikilinks、嵌入、callouts 等功能的 Obsidian 风格 Markdown。" };
    "paper-analyzer"            = @{ EN="Analyze literature in Zotero, generate Markdown reports with LaTeX, and upload as Zotero Notes."; CN="分析 Zotero 中的文献，生成带 LaTeX 的 Markdown 报告，并上传为 Zotero 笔记。" };
    "paper-finder"              = @{ EN="Discover recent arXiv papers matching a research profile and generate Obsidian-compatible notes."; CN="发现符合研究兴趣的最新 arXiv 论文，并生成 Obsidian 兼容的笔记。" };
    "web-research"              = @{ EN="Provides a structured approach to conducting comprehensive web research."; CN="提供一种进行全面网络研究的结构化方法。" };
    "continuous-agent-loop"     = @{ EN="Patterns for continuous autonomous agent loops with quality gates and recovery."; CN="具有质量门和恢复控制的连续自主智能体循环模式。" };
    "continuous-learning"       = @{ EN="Automatically extract reusable patterns from sessions and save them as learned skills."; CN="从会话中自动提取可重用模式并将其保存为学习到的技能。" };
    "continuous-learning-v2"    = @{ EN="Instinct-based learning system that observes sessions to create and evolve skills."; CN="基于本能的学习系统，通过观察会话来创建和演进技能。" };
    "cpp-coding-standards"      = @{ EN="C++ coding standards based on the C++ Core Guidelines for modern, safe code."; CN="基于 C++ 核心指南的 C++ 编码标准，用于现代、安全的代码。" };
    "docker-patterns"           = @{ EN="Docker and Docker Compose patterns for local development and container orchestration."; CN="用于本地开发和容器编排的 Docker 和 Docker Compose 模式。" };
    "iterative-retrieval"       = @{ EN="Pattern for progressively refining context retrieval to solve subagent context problems."; CN="用于逐步优化上下文检索以解决子智能体上下文问题的模式。" };
    "python-patterns"           = @{ EN="Pythonic idioms, PEP 8 standards, and best practices for robust Python apps."; CN="用于构建健壮 Python 应用程序的 Pythonic 惯用法、PEP 8 标准和最佳实践。" };
    "skill-creator"             = @{ EN="Create new skills, modify existing skills, and measure their performance."; CN="创建新技能、修改现有技能并衡量其性能。" };
    "verification-loop"         = @{ EN="A comprehensive verification system for Claude Code sessions."; CN="一个用于 Claude Code 会话的综合验证系统。" };
    "videodb"                   = @{ EN="See, Understand, and Act on video and audio content from various sources."; CN="观察、理解和操作来自各种来源的视频和音频内容。" };
    "autonomous-loops"          = @{ EN="Patterns and architectures for autonomous Claude Code loops."; CN="用于自主 Claude Code 循环的模式和架构。" };
    "brainstorming"             = @{ EN="A skill for brainstorming and generating ideas."; CN="一个用于头脑风暴和产生想法的技能。" };
    "executing-plans"           = @{ EN="A skill for executing pre-defined plans."; CN="一个用于执行预定义计划的技能。" };
    "tech-doc-writing"          = @{ EN="Write technical documentation, guides, and tutorials with a consistent voice."; CN="以一致的风格编写技术文档、指南和教程。" };
    "writing-plans"             = @{ EN="A skill for creating detailed plans for complex tasks."; CN="一个为复杂任务创建详细计划的技能。" };
    "pptx"                      = @{ EN="Create, read, and edit .pptx presentations, from content extraction to generation."; CN="创建、读取和编辑 .pptx 演示文稿，从内容提取到生成。" };
    "weekly-report-generator"   = @{ EN="Automatically generates a 1-page weekly progress report PPTX from Obsidian notes."; CN="根据 Obsidian 笔记自动生成一页的每周进展报告 PPTX。" };
}

# --- Asset Categorization ---
$RESEARCH_SKILLS = @("arxiv-search", "deep-research", "exa-search", "notion-to-markdown", "obsidian-auto-classifier", "obsidian-markdown", "paper-analyzer", "paper-finder", "web-research")
$RESEARCH_AGENTS = @("doc-updater.md")
$CODING_SKILLS = @("continuous-agent-loop", "continuous-learning", "continuous-learning-v2", "cpp-coding-standards", "docker-patterns", "iterative-retrieval", "python-patterns", "skill-creator", "verification-loop", "videodb")
$CODING_AGENTS = @("architect.md", "build-error-resolver.md", "code-reviewer.md", "python-reviewer.md", "security-reviewer.md")
$DAILY_SKILLS = @("autonomous-loops", "brainstorming", "executing-plans", "tech-doc-writing", "writing-plans")
$DAILY_AGENTS = @("loop-operator.md", "planner.md")
$LAB_SKILLS = @("pptx", "weekly-report-generator")

# --- Helper Functions ---

function Show-Categories {
    Write-Host "----------------------------------" -ForegroundColor White
    Write-Host "Available Asset Categories (可用资产类别)" -ForegroundColor White
    Write-Host "----------------------------------" -ForegroundColor White

    $categories = @(
        @{ Name="RESEARCH"; CN="科研"; Skills=$RESEARCH_SKILLS },
        @{ Name="CODING"; CN="编程"; Skills=$CODING_SKILLS },
        @{ Name="DAILY"; CN="日常"; Skills=$DAILY_SKILLS },
        @{ Name="LAB_SKILLS"; CN="实验室专用"; Skills=$LAB_SKILLS }
    )

    foreach ($cat in $categories) {
        Write-Host ""
        Write-Host "[$($cat.Name)] ($($cat.CN))" -ForegroundColor Blue
        foreach ($skill in $cat.Skills) {
            Write-Host "  - $($skill)" -ForegroundColor Gray
            Write-Host "    - EN: $($Descriptions[$skill].EN)"
            Write-Host "    - CN: $($Descriptions[$skill].CN)"
        }
    }
}

function New-Symlink {
    param(
        [string]$LinkDirectory,
        [string[]]$SourceItems
    )
    
    if (-not (Test-Path $LinkDirectory)) {
        New-Item -Path $LinkDirectory -ItemType Directory -Force | Out-Null
    }
    
    foreach ($item in $SourceItems) {
        $sourcePath = Join-Path -Path $PSScriptRoot -ChildPath $item
        $linkPath = Join-Path -Path $LinkDirectory -ChildPath (Split-Path $item -Leaf)
        
        if (Test-Path $linkPath) {
            Write-Warning "'$linkPath' already exists. Skipping. (警告: 已存在，跳过。)"
        } else {
            New-Item -ItemType SymbolicLink -Path $linkPath -Target $sourcePath | Out-Null
            Write-Host "    - Linked '$($linkPath)'." -ForegroundColor Green
        }
    }
}

function Invoke-AssetInstallation {
    param(
        [string]$ClientName,
        [string]$BaseDir,
        [string]$WorkspaceDir,
        [string]$AgentDirName
    )

    Write-Host "`n--- Installing for $ClientName (正在为 $ClientName 安装) ---" -ForegroundColor Green

    # Global Installation
    if ($INSTALL_RESEARCH_GLOBAL -or $INSTALL_CODING_GLOBAL -or $INSTALL_DAILY_GLOBAL -or $INSTALL_LAB_GLOBAL) {
        Write-Host "Linking global assets to '$BaseDir'..."
        if ($INSTALL_RESEARCH_GLOBAL) { New-Symlink "$BaseDir\skills" $RESEARCH_SKILLS; New-Symlink "$BaseDir\$AgentDirName" $RESEARCH_AGENTS }
        if ($INSTALL_CODING_GLOBAL)   { New-Symlink "$BaseDir\skills" $CODING_SKILLS;   New-Symlink "$BaseDir\$AgentDirName" $CODING_AGENTS }
        if ($INSTALL_DAILY_GLOBAL)    { New-Symlink "$BaseDir\skills" $DAILY_SKILLS;    New-Symlink "$BaseDir\$AgentDirName" $DAILY_AGENTS }
        if ($INSTALL_LAB_GLOBAL)      { New-Symlink "$BaseDir\skills" $LAB_SKILLS }
    }

    # Local Installation
    if ($INSTALL_RESEARCH_LOCAL -or $INSTALL_CODING_LOCAL -or $INSTALL_DAILY_LOCAL -or $INSTALL_LAB_LOCAL) {
        Write-Host "Linking local assets to '$WorkspaceDir'..."
        if ($INSTALL_RESEARCH_LOCAL) { New-Symlink "$WorkspaceDir\skills" $RESEARCH_SKILLS; New-Symlink "$WorkspaceDir\$AgentDirName" $RESEARCH_AGENTS }
        if ($INSTALL_CODING_LOCAL)   { New-Symlink "$WorkspaceDir\skills" $CODING_SKILLS;   New-Symlink "$WorkspaceDir\$AgentDirName" $CODING_AGENTS }
        if ($INSTALL_DAILY_LOCAL)    { New-Symlink "$WorkspaceDir\skills" $DAILY_SKILLS;    New-Symlink "$WorkspaceDir\$AgentDirName" $DAILY_AGENTS }
        if ($INSTALL_LAB_LOCAL)      { New-Symlink "$WorkspaceDir\skills" $LAB_SKILLS }
    }
}

# --- Main Script ---

Write-Host "=======================================" -ForegroundColor Green
Write-Host " Stable-JARVIS Asset Installer (智能资产安装程序)" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host "This script will create symbolic links for skills, agents, and commands."

Show-Categories

Write-Host "`nStep 1: Choose your AI client (第一步: 选择您的 AI 客户端)" -ForegroundColor Yellow
Write-Host "--------------------------------" -ForegroundColor White
Write-Host "  1) Gemini CLI"
Write-Host "  2) Claude Code"
Write-Host "  3) Codex / GitHub Copilot"
$client_choice = Read-Host "Enter the number of your client (请输入客户端对应的数字)"

# --- Global First ---
Write-Host "`nStep 2: Select GLOBAL asset categories to install (第二步: 选择要安装的 全局 资产类别)" -ForegroundColor Yellow
Write-Host "----------------------------------------------------" -ForegroundColor White
$research_choice_g = Read-Host "  -> Install RESEARCH assets (科研)? [y/N]"
$coding_choice_g = Read-Host "  -> Install CODING assets (编程)? [y/N]"
$daily_choice_g = Read-Host "  -> Install DAILY assets (日常)? [y/N]"
$lab_choice_g = Read-Host "  -> Install LAB_SKILLS assets (实验室专用)? [y/N]"

$INSTALL_RESEARCH_GLOBAL = $research_choice_g -match '^[Yy]'
$INSTALL_CODING_GLOBAL = $coding_choice_g -match '^[Yy]'
$INSTALL_DAILY_GLOBAL = $daily_choice_g -match '^[Yy]'
$INSTALL_LAB_GLOBAL = $lab_choice_g -match '^[Yy]'

# --- Then Local, Conditionally ---
Write-Host "`nStep 3: Select LOCAL asset categories to install (第三步: 选择要安装的 本地 资产类别)" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor White
Write-Host "Only categories not installed globally will be shown. (仅显示未全局安装的类别。)"

$INSTALL_RESEARCH_LOCAL, $INSTALL_CODING_LOCAL, $INSTALL_DAILY_LOCAL, $INSTALL_LAB_LOCAL = $false, $false, $false, $false

if (-not $INSTALL_RESEARCH_GLOBAL -or -not $INSTALL_CODING_GLOBAL -or -not $INSTALL_DAILY_GLOBAL -or -not $INSTALL_LAB_GLOBAL) {
    if (-not $INSTALL_RESEARCH_GLOBAL) { 
        $rcl = Read-Host "  -> Install RESEARCH assets (科研)? [y/N]"
        if ($rcl -match '^[Yy]') { $INSTALL_RESEARCH_LOCAL = $true }
    }
    if (-not $INSTALL_CODING_GLOBAL) {
        $ccl = Read-Host "  -> Install CODING assets (编程)? [y/N]"
        if ($ccl -match '^[Yy]') { $INSTALL_CODING_LOCAL = $true }
    }
    if (-not $INSTALL_DAILY_GLOBAL) {
        $dcl = Read-Host "  -> Install DAILY assets (日常)? [y/N]"
        if ($dcl -match '^[Yy]') { $INSTALL_DAILY_LOCAL = $true }
    }
    if (-not $INSTALL_LAB_GLOBAL) {
        $lcl = Read-Host "  -> Install LAB_SKILLS assets (实验室专用)? [y/N]"
        if ($lcl -match '^[Yy]') { $INSTALL_LAB_LOCAL = $true }
    }
} else {
    Write-Host "All categories selected for global installation. Nothing to install locally. (所有类别均已选择全局安装，无需本地安装。)"
}

# --- Perform Installation ---
Write-Host "`nStep 4: Performing installation (第四步: 执行安装)" -ForegroundColor Yellow
Write-Host "---------------------------------" -ForegroundColor White

switch ($client_choice) {
    "1" { Invoke-AssetInstallation "Gemini CLI" (Join-Path $env:USERPROFILE ".gemini") ".gemini" "agents" }
    "2" { Invoke-AssetInstallation "Claude Code" (Join-Path $env:USERPROFILE ".claude") ".claude" "agents" }
    "3" { Invoke-AssetInstallation "Codex / GitHub Copilot" (Join-Path $env:USERPROFILE ".copilot") ".github" "instructions" }
    default { Write-Warning "Invalid choice. Exiting. (无效选择，正在退出。)"; exit 1 }
}

Write-Host "`n=======================================" -ForegroundColor Green
Write-Host " Installation Complete! (安装完成！)" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
if ($client_choice -eq "1") {
    Write-Host "-> Remember to run '/commands reload' in Gemini CLI if you installed new commands."
    Write-Host "   (如果在 Gemini CLI 中安装了新命令，请记得运行 '/commands reload'。)"
}
