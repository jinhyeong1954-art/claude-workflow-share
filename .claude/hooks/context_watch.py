# -*- coding: utf-8 -*-
"""context_watch.py — UserPromptSubmit 훅: 세션 컨텍스트가 얼마나 부었는지 매 프롬프트마다 실측해 경고한다.

왜 — 컨텍스트 크기는 화면에 잘 안 보인다. 실측해 보니 세션이 30만~100만 토큰까지 부풀어 있었고,
그 구간에서 실수가 늘었다. transcript의 마지막 assistant usage(=직전 턴 프롬프트 토큰)를 읽어
  · 30만 이상 → 🟠 큰 출력은 서브에이전트로 + 체크포인트
  · 40만 이상 → 🔴 체크포인트 + /compact
를 컨텍스트에 주입한다. 그 미만이면 아무것도 출력하지 않는다. 어떤 예외도 통과(exit 0).
`python context_watch.py --report 14` = 최근 14일 세션별 컨텍스트 표 + 무엇이 컨텍스트를 키웠나(도구별).
"""
import io
import json
import os
import sys

WARN = 300_000
STOP = 400_000
TAIL_BYTES = 2_000_000  # 마지막 2MB만 읽는다(큰 transcript도 즉시)


def last_context_tokens(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if size > TAIL_BYTES:
            f.seek(size - TAIL_BYTES)
            f.readline()  # 잘린 줄 버림
        chunk = f.read().decode("utf-8", errors="replace")
    ctx = 0
    for line in chunk.splitlines():
        if '"usage"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant" or d.get("isSidechain"):
            continue
        u = (d.get("message") or {}).get("usage") or {}
        c = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        if c:
            ctx = c
    return ctx


def main():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    try:
        ctx = last_context_tokens(path)
    except Exception:
        return
    if ctx < WARN:
        return
    man = ctx / 10_000
    tail = (
        " 답변 끝에 재개어를 준다: memory/_inbox/<날짜>-<주제>.md에 체크포인트"
        "(어디까지·다음 한 수·열린 값·주의점·건드린 파일)를 쓰고 「재개어: 이어서 <주제>」 한 줄 — 사용자가 언제든 세션을 끊을 수 있게."
    )
    if ctx >= STOP:
        msg = (
            f"🔴 컨텍스트 {man:.0f}만 토큰(40만 초과). 이번 프롬프트는 최소로 마무리하고 "
            "체크포인트 후 「/compact <이어갈 작업 초점>」을 안내할 것. 새 조사·큰 출력은 서브에이전트로." + tail
        )
    else:
        msg = (
            f"🟠 컨텍스트 {man:.0f}만 토큰(30만 초과 — 실수가 느는 구간). "
            "큰 출력(디렉터리 목록·긴 로그·파일 통독)은 서브에이전트나 파일로 보내고 요약만 받을 것." + tail
        )
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}},
        sys.stdout,
        ensure_ascii=False,
    )


def report(days=14):
    """`--report [일수]` — 세션별 컨텍스트 실측 표 + 도구별 증가분 귀속."""
    import collections
    import datetime
    import glob
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Claude Code 규칙: 영숫자 외 전부 '-' (예: C:\work\myrepo → C--work-myrepo)
    slug = "".join(c if c.isascii() and c.isalnum() else "-" for c in os.path.abspath(proj).rstrip("\\/"))
    root = os.path.join(os.path.expanduser("~"), ".claude", "projects", slug)
    since = datetime.datetime.now() - datetime.timedelta(days=days)
    rows = []; attr = collections.Counter(); tot_turns = 0; g2 = 0; g4 = 0
    for f in glob.glob(os.path.join(root, "*.jsonl")):
        if datetime.datetime.fromtimestamp(os.path.getmtime(f)) < since:
            continue
        first = None; peak = 0; turns = 0; prev = None; pending = []; idmap = {}
        try:
            fh = open(f, encoding="utf-8", errors="replace")
        except Exception:
            continue
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("isSidechain"):
                continue
            m = d.get("message") or {}; c = m.get("content"); t = d.get("type")
            if t == "assistant":
                if isinstance(c, list):
                    for b in c:
                        if b.get("type") == "tool_use":
                            nm = b["name"]
                            if nm == "Read":
                                nm += ":" + os.path.splitext(str(b["input"].get("file_path", "")))[1].lower()
                            idmap[b["id"]] = nm
                u = m.get("usage") or {}
                ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                if ctx:
                    if prev is not None:
                        attr[pending[0] if pending else "(text/thinking)"] += ctx - prev
                    prev = ctx; pending = []; turns += 1; peak = max(peak, ctx)
                    g2 += ctx > 200_000; g4 += ctx > 400_000
                    if first is None:
                        first = ctx
            elif t == "user" and isinstance(c, list):
                for b in c:
                    if b.get("type") == "tool_result":
                        pending.append(idmap.get(b.get("tool_use_id"), "?"))
        fh.close()
        if turns >= 5:
            rows.append((os.path.getmtime(f), turns, first, peak, os.path.basename(f)[:8])); tot_turns += turns
    rows.sort()
    print(f"최근 {days}일 세션 {len(rows)}개 · 턴 {tot_turns} · 20만 초과 {100*g2/max(tot_turns,1):.1f}% · 40만 초과 {100*g4/max(tot_turns,1):.1f}%")
    print(f"{'날짜':12} {'턴':>5} {'첫턴ctx':>8} {'최대ctx':>8}  세션")
    for mt, turns, first, peak, sid in rows:
        print(f"{datetime.datetime.fromtimestamp(mt).strftime('%m-%d %H:%M'):12} {turns:5d} {first:8d} {peak:8d}  {sid}")
    tot = sum(v for v in attr.values() if v > 0) or 1
    print("증가분 귀속(도구별):")
    for k, v in attr.most_common(10):
        print(f"  {100*v/tot:5.1f}%  {v:9d} tok  {k}")


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--report":
            report(int(sys.argv[2]) if len(sys.argv) > 2 else 14)
        else:
            main()
    except Exception:
        pass
    sys.exit(0)
