#!/bin/bash
#
# sync-upstream.sh — Replace upstream-sourced skills and agents with symlinks
#                   to git submodules. Run from the repo root.
#
# Usage:
#   bash scripts/sync-upstream.sh          # dry-run (show what would change)
#   bash scripts/sync-upstream.sh --apply  # apply the symlinks
#
# Requires: git, python3

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

C_RESET='\e[0m'
C_BOLD='\e[1m'
C_GREEN='\e[0;32m'
C_YELLOW='\e[0;33m'
C_CYAN='\e[0;36m'

DRY_RUN=true
if [[ "${1:-}" == "--apply" ]]; then
    DRY_RUN=false
fi

echo -e "${C_BOLD}=== Upstream Sync ===${C_RESET}"
if $DRY_RUN; then
    echo -e "${C_YELLOW}DRY RUN — use --apply to actually create symlinks${C_RESET}"
fi
echo ""

# Step 1: update submodules
echo -e "${C_BOLD}Step 1: Updating git submodules...${C_RESET}"
git submodule update --init --recursive
echo ""

# Step 2: parse taxonomy XML to find upstream skills
echo -e "${C_BOLD}Step 2: Reading skill-taxonomy.xml...${C_RESET}"

# Python emits TYPE|REPO|PATH|NAME lines for upstream skills and agents
parsed=$(python3 <<'PYEOF'
import xml.etree.ElementTree as ET
import sys

tree = ET.parse("skill-taxonomy.xml")
root = tree.getroot()

upstream_count = 0

for cat in root.findall("category"):
    for s in cat.findall("skills/skill"):
        name = (s.text or "").strip()
        if not name:
            continue
        upstream = s.get("upstream", "")
        if upstream:
            path = s.get("path", "skills")
            print(f"SKILL|{upstream}|{path}|{name}")
            upstream_count += 1

for cat in root.findall("category"):
    for a in cat.findall("agents/agent"):
        name = (a.text or "").strip()
        if not name:
            continue
        upstream = a.get("upstream", "")
        if upstream:
            path = a.get("path", "agents")
            print(f"AGENT|{upstream}|{path}|{name}")
            upstream_count += 1

if upstream_count == 0:
    print("No upstream skills or agents found in taxonomy.", file=sys.stderr)
PYEOF
)

# Step 3: create symlinks
echo -e "${C_BOLD}Step 3: Processing skills & agents...${C_RESET}"
echo ""

linked=0
skipped=0
while IFS='|' read -r type repo path name; do
    [[ -z "$type" ]] && continue
    src="upstream/${repo}/${path}/${name}"
    dst="${type,,}s/${name}"   # SKILL→skills, AGENT→agents

    if [ ! -d "$src" ] && [ ! -f "$src" ]; then
        echo -e "  ${C_YELLOW}SKIP${C_RESET}  $type $name — $src not found"
        skipped=$((skipped + 1))
        continue
    fi

    current_target=""
    if [ -L "$dst" ]; then
        current_target=$(readlink "$dst")
    fi

    expected_target="../upstream/${repo}/${path}/${name}"

    if [ "$current_target" = "$expected_target" ]; then
        echo -e "  ${C_CYAN}OK${C_RESET}    $name → upstream/${repo}/${path}/${name} (already linked)"
        linked=$((linked + 1))
        continue
    fi

    if $DRY_RUN; then
        if [ -L "$dst" ]; then
            echo -e "  ${C_GREEN}LINK${C_RESET}  $name → upstream/${repo}/${path}/${name} (would replace: $current_target)"
        elif [ -d "$dst" ] || [ -f "$dst" ]; then
            echo -e "  ${C_GREEN}LINK${C_RESET}  $name → upstream/${repo}/${path}/${name} (would replace local)"
        else
            echo -e "  ${C_GREEN}LINK${C_RESET}  $name → upstream/${repo}/${path}/${name} (new)"
        fi
        linked=$((linked + 1))
    else
        rm -rf "$dst"
        ln -s "../upstream/${repo}/${path}/${name}" "$dst"
        echo -e "  ${C_GREEN}LINK${C_RESET}  $name → upstream/${repo}/${path}/${name}"
        linked=$((linked + 1))
    fi
done <<< "$parsed"

echo ""
echo -e "${C_BOLD}=== Summary ===${C_RESET}"
echo -e "  Upstream skills & agents linked: $linked"
echo -e "  Skipped (not found):    $skipped"

if $DRY_RUN; then
    echo ""
    echo -e "${C_YELLOW}This was a dry run. Run with --apply to make changes.${C_RESET}"
else
    echo ""
    echo -e "${C_GREEN}Done. Upstream skills are now symlinked to upstream/ submodules.${C_RESET}"
    echo "  git submodule update --remote   # pull latest from all upstreams"
fi
