# MEMORY (매 턴 자동 로드 — 일하는 방식·안전선만, 상한 15KB)

> 한 줄 = 규칙 하나 + 파일 링크. 내용은 링크한 파일에. 🔴 = 절대(어기면 사고) · 무표시 = 기본(이유 있으면 사후보고하고 벗어남).
> 이 파일을 `~/.claude/projects/<프로젝트 폴더명>/memory/MEMORY.md`에 두면 Claude Code가 매 세션 자동으로 읽는다.

## 일하는 방식
- [병렬은 속도보다 깊이](parallel-depth-over-speed.md) — 독립 조각 2개↑면 서브에이전트 동시 디스패치
- [컨텍스트 팽창이 진짜 세금](context-bloat-is-the-real-tax.md) — 큰 출력은 서브·파일로, 체크포인트로 끊는다
- [질문 말고 진행·사후보고](drive-autonomously-dont-ask.md) — 질문은 금지선·취향 결정 둘뿐
- [최소부터 짓는다](no-overengineering.md) — 병목 한 칸만 v1, 안 지은 것은 한 줄 보고
- [「없다」는 전수 스캔 후에만](absence-claims-need-exhaustive-scan.md) — 키워드 grep은 PDF·엑셀 안을 못 본다
- [경로·정본은 실제로 열어 보고 단정](verify-path-identity-not-keyword.md) — 이름이 비슷하다고 같은 파일이 아니다
- [개발 용어는 그 자리에서 풀어 쓴다](explain-jargon-as-you-go.md)

## 안전선 (🔴 절대)
- 🔴 [보내기 직전 대상 건수를 의도와 대조](send-count-must-match-intent.md) — 「1명」인데 매칭 3건이면 멈춘다
- 🔴 [안전장치는 등록·실발동 확인까지가 설치](safety-gate-not-installed-until-verified.md)
