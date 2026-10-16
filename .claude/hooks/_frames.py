# -*- coding: utf-8 -*-
"""사람 발화 vs 시스템 프레임 판별 — 훅 공용.

UserPromptSubmit·Stop 훅은 「사용자가 한 말」에만 반응해야 한다. 그런데 서브에이전트 완료 알림·
Stop 훅 피드백·로컬 명령 출력도 user 항목으로 들어온다. 그 본문의 낱말(예: 「기억해둬」)에
훅이 반응하는 오탐이 실제로 났다. 이 모듈로 걸러낸다.
"""
import re

_FRAME = re.compile(
    r"^\s*(?:<(?:task-notification|teammate-message|agent-message|cross-session-message"
    r"|channel|system-reminder|local-command-stdout|local-command-stderr|local-command-caveat)\b"
    r"|\[SYSTEM NOTIFICATION|Stop hook feedback|\[Request interrupted"
    r"|Another Claude session sent a message)",
    re.I)


def is_system_frame(text):
    """True = 사람 말이 아님(알림·시스템 통지). 빈 문자열도 True."""
    if not text or not text.strip():
        return True
    if _FRAME.match(text):
        return True
    # 여러 알림이 한 프롬프트로 합쳐져 앞부분에 태그가 박힌 경우
    return "<task-notification>" in text[:2000]


def entry_is_system(entry, text):
    """전사록(transcript) user 항목용 — origin 메타가 있으면 그걸 우선(사람=human).
    압축 요약문은 사람 말이 아니다."""
    if entry.get("isCompactSummary") or entry.get("isVisibleInTranscriptOnly"):
        return True
    origin = entry.get("origin") or {}
    kind = origin.get("kind") if isinstance(origin, dict) else None
    if kind:
        return kind != "human"
    return is_system_frame(text)
