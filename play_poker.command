#!/bin/bash
# Double-click this file to play. (macOS opens .command files in Terminal.)
cd "$(dirname "$0")" 2>/dev/null || cd /Users/jangnamgyu/Desktop/Python/Practice/practice/pokercommunity
clear
python3 -m arena.campaign
echo
echo "게임 종료. 아무 키나 누르면 창이 닫힙니다."
read -n 1 -s
