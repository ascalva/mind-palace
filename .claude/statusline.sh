#!/usr/bin/env bash
# mind-palace statusLine — plane-aware telemetry.
#
# Reads Claude Code's statusLine JSON on stdin and prints ONE line:
#   principal · dir · branch · model[ effort][ ⚡] · ctx N% · $cost · +A/-D · rl 5h% 7d%
#
# `principal` (whoami) leads deliberately: in the four-plane setup, knowing whether a
# pane runs as ouroboros-work vs ascalva matters at a glance. All fields come from the
# documented statusLine payload (schema verified via claude-code-guide, 2026-07-20);
# optional fields (effort, rate_limits, fast_mode) are omitted when the payload lacks them.
# Runs on every render, so it makes exactly ONE jq call.
set -u
input=$(cat)

# One jq pass → fields joined by ASCII Unit Separator (0x1F). NOT tab: `read` treats tab as
# IFS-whitespace and collapses consecutive ones, which would drop empty optional fields and
# shift every field after them. A non-whitespace separator preserves empty fields positionally.
IFS=$'\037' read -r dir model effort ctx cost add del r5 r7 fast < <(
  printf '%s' "$input" | jq -r '[
    (.workspace.current_dir // .cwd // ""),
    (.model.display_name // ""),
    (.effort.level // ""),
    (.context_window.used_percentage // ""),
    (.cost.total_cost_usd // 0),
    (.cost.total_lines_added // 0),
    (.cost.total_lines_removed // 0),
    (.rate_limits.five_hour.used_percentage // ""),
    (.rate_limits.seven_day.used_percentage // ""),
    (.fast_mode // false)
  ] | map(tostring) | join("")'
)

who=$(whoami)
base=$(basename "${dir:-$PWD}")
branch=$(git --no-optional-locks -C "${dir:-$PWD}" branch --show-current 2>/dev/null)

# ANSI: dim for chrome, threshold colors for context pressure.
D=$'\033[2m'; R=$'\033[0m'; GRN=$'\033[32m'; YEL=$'\033[33m'; RED=$'\033[31m'
SEP="${D}·${R}"

# Context %: green < 50, yellow < 80, red >= 80.
ctx_col="$GRN"
if [ -n "$ctx" ]; then
  ci=${ctx%.*}
  if [ "$ci" -ge 80 ] 2>/dev/null; then ctx_col="$RED"
  elif [ "$ci" -ge 50 ] 2>/dev/null; then ctx_col="$YEL"; fi
fi

# model + effort (+ fast-mode bolt).
mseg="$model"
[ -n "$effort" ] && mseg="$mseg ${D}${effort}${R}"
[ "$fast" = "true" ] && mseg="$mseg ${D}⚡${R}"

out="${D}${who}${R} ${SEP} ${D}${base}${R}"
[ -n "$branch" ] && out="$out ${SEP} ${D}${branch}${R}"
out="$out ${SEP} ${mseg}"
[ -n "$ctx" ] && out="$out ${SEP} ${ctx_col}ctx ${ctx}%${R}"

costf=$(printf '%.2f' "$cost" 2>/dev/null || printf '%s' "$cost")
out="$out ${SEP} ${D}\$${costf}${R}"

if [ "${add:-0}" != "0" ] || [ "${del:-0}" != "0" ]; then
  out="$out ${SEP} ${GRN}+${add}${R}${D}/${R}${RED}-${del}${R}"
fi

if [ -n "$r5" ] || [ -n "$r7" ]; then
  rl="rl"
  [ -n "$r5" ] && rl="$rl 5h ${r5%.*}%"
  [ -n "$r7" ] && rl="$rl 7d ${r7%.*}%"
  out="$out ${SEP} ${D}${rl}${R}"
fi

printf '%s' "$out"
