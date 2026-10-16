# -*- coding: utf-8 -*-
"""memory_keyword_reminder.py — UserPromptSubmit 훅: 기록 트리거 감지기.

사용자 프롬프트에 「기억해둬/참고해둬/기록해둬/적어둬」 류 워딩이 있으면
Claude 컨텍스트에 「파일에 영구 기록하라」는 리마인더를 주입한다.
왜 — 「네, 기억하겠습니다」라고 말로만 답하고 파일엔 안 적어서 다음 세션에 다 잊은 일이 반복됐다.
매칭 없으면 아무것도 출력하지 않는다(무해).
"""
import io
import json
import os
import re
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

prompt = data.get("prompt") or ""

# 서브에이전트 보고·알림 본문의 「기억해둬」는 사용자 말이 아니다
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _frames import is_system_frame
    if is_system_frame(prompt):
        sys.exit(0)
except ImportError:
    pass

PAT = re.compile(
    r"기억해\s*[둬줘놔두]"
    r"|참고해\s*[둬줘놔두]"
    r"|기록해\s*[둬줘놔두]"
    r"|적어\s*[둬놔]"
    r"|박아\s*[둬줘놔]"
    r"|외워\s*[둬줘]"
)

if PAT.search(prompt):
    reminder = (
        "🧷 기록 트리거 감지(기억해둬/참고해둬/기록해둬 … 워딩). "
        "이 턴이 끝나기 전에 반드시 해당 내용을 파일에 영구 기록할 것 — 말로만 답하고 끝내기 금지. "
        "라우팅: ①업무 지식·절차 → 해당 업무 문서(md) ②Claude 행동방식·사용자 취향 → memory/<규칙>.md + MEMORY.md 색인 1줄 "
        "③끝나면 어느 파일 어느 자리에 기록했는지 답변에 보고."
    )
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": reminder}},
        sys.stdout,
        ensure_ascii=False,
    )

sys.exit(0)
