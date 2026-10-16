# -*- coding: utf-8 -*-
"""danger_gate.py — PreToolUse(Bash) 훅: 위험 명령을 사람 승인 없이 못 돌게 막는다.

왜 — 「돈·발송·삭제는 사람 확인」을 규칙으로만 두면 자율 모드에서 언젠가 넘어간다. 그래서 훅으로 강제한다.
동작 — 실행하려는 Bash 명령이 DANGER 패턴에 걸리면:
       · 직전 사용자 발화에 「승인」이 있으면 통과 (그 한 턴만)
       · 아니면 permissionDecision=deny + 이유 → Claude는 멈추고 사용자에게 확인을 받는다.
       어떤 예외도 통과(exit 0) — 훅 버그가 작업 전체를 막지 않게.
고쳐 쓰기 — DANGER 목록에 자기 업무의 위험 명령(메일 발송 스크립트·이체 파일 생성 등)을 추가한다.
"""
import io
import json
import os
import re
import sys

DANGER = [
    (re.compile(r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r", re.I), "재귀 강제 삭제"),
    (re.compile(r"Remove-Item\b.*-Recurse", re.I), "재귀 삭제"),
    (re.compile(r"\bgit\s+push\b.*(--force|-f\b)", re.I), "강제 push(이력 덮어쓰기)"),
    (re.compile(r"\bgit\s+reset\s+--hard", re.I), "작업 내용 버리기"),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*f", re.I), "추적 안 된 파일 삭제"),
    # 예시 — 자기 업무 스크립트로 바꿔 쓴다
    (re.compile(r"send_mail\.py\b.*--send", re.I), "메일 실발송"),
]
APPROVE = re.compile(r"승인")


def last_user_text(path):
    """전사록에서 마지막 '사람' 발화 텍스트."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _frames import entry_is_system
    last = ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") != "user":
                continue
            c = (d.get("message") or {}).get("content")
            if isinstance(c, str):
                t = c
            elif isinstance(c, list):
                t = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
            else:
                continue
            if t and not entry_is_system(d, t):
                last = t
    return last


def main():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    if d.get("tool_name") != "Bash":
        return
    cmd = (d.get("tool_input") or {}).get("command") or ""
    hit = next((why for pat, why in DANGER if pat.search(cmd)), None)
    if not hit:
        return
    path = d.get("transcript_path")
    if path and os.path.exists(path) and APPROVE.search(last_user_text(path)):
        return
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"🔴 위험 명령({hit}) — 사용자 승인 없이 실행 불가. "
            "무엇을·몇 건·왜 하는지 보여 주고, 사용자가 「승인」이라고 답하면 그 턴에 한 번만 다시 실행할 것."),
    }}, out, ensure_ascii=False)
    out.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
