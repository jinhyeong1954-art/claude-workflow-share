# -*- coding: utf-8 -*-
"""korean_reply_gate.py — Stop 훅: 최종 답변 한국어 강제.

왜 — CLAUDE.md에 「한국어로 답한다」만 써 두었더니, 긴 검토 결과를 통째로 영어로 답한 적이 있다.
동작 — 마지막 사람 프롬프트 이후 assistant 글 중 **사용자가 읽는 부분만** 본다:
       「📨 답장」 표식이 있으면 마지막 표식부터 끝까지, 없으면 마지막 text 블록(최종 답변)만.
       (표식 앞 작업 중 한 줄 상태문은 영어여도 통과 — 답변이 두 번 나오는 부작용 방지)
       코드·경로·URL·파일명을 걷어낸 뒤 한글 비율이 MIN_RATIO 미만이고 글자가 MIN_LETTERS 이상이면
       decision=block → 한국어로 다시 답하게 한다.
       stop_hook_active(이미 한 번 되돌림)면 통과(무한루프 방지). 어떤 예외도 통과(exit 0).
"""
import io
import json
import re
import sys

MIN_RATIO = 0.5
MIN_LETTERS = 30
MARKER = re.compile(r"📨\s*\**\s*답장")
STRIP = [
    re.compile(r"```.*?```", re.S),            # 코드 블록
    re.compile(r"`[^`\n]*`"),                  # 인라인 코드
    re.compile(r"https?://\S+"),               # URL
    re.compile(r"[A-Za-z]:[\\/][^\s]*"),       # 윈도 경로
    re.compile(r"\S+\.(?:py|md|json|xlsx|pdf|png|bat|ps1|txt|zip)\b", re.I),   # 파일명
]


def ratio(text):
    for p in STRIP:
        text = p.sub(" ", text)
    ko = len(re.findall(r"[가-힣]", text))
    en = len(re.findall(r"[A-Za-z]", text))
    return ko, en


def english_blocks(path):
    texts = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            content = (d.get("message") or {}).get("content")
            if d.get("type") == "user":
                if isinstance(content, str) or (isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "text" for b in content)):
                    texts = []   # 사람 프롬프트 = 새 턴
            elif d.get("type") == "assistant" and isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        texts.append(b.get("text") or "")
    scope = texts[-1:]
    for i in range(len(texts) - 1, -1, -1):
        ms = list(MARKER.finditer(texts[i]))
        if ms:
            scope = [texts[i][ms[-1].start():]] + texts[i + 1:]
            break
    blocks = []
    for t in scope:
        ko, en = ratio(t)
        if ko + en >= MIN_LETTERS and ko / (ko + en) < MIN_RATIO:
            blocks.append(t.strip()[:80])
    return blocks


def main():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    if d.get("stop_hook_active") or not d.get("transcript_path"):
        return
    bad = english_blocks(d["transcript_path"])
    if bad:
        json.dump({"decision": "block", "reason": (
            "🇰🇷 한국어 아닌 답변 %d덩어리 감지 — 예: %r\n"
            "「📨 답장」 표식 뒤(없으면 최종 답변)를 **한국어로 다시** 써라 — 표식부터 시작, 코드·경로만 원문. "
            "영어 문장을 되풀이하지 말 것." % (len(bad), bad[0]))}, out, ensure_ascii=False)
        out.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
