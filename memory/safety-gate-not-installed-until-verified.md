---
name: safety-gate-not-installed-until-verified
description: 🔴 훅·안전장치는 파일을 만든 걸로 끝이 아니다 — settings 등록 확인 + 실제로 한 번 발동하는 걸 봐야 설치 완료
metadata:
  type: feedback
---

안전장치를 「만들었다」와 「설치됐다」를 구분한다.

**Why:** 훅 스크립트만 만들고 `settings.json`에 배선을 빠뜨려서, 몇 주 동안 막아 준다고 믿었던 것이 한 번도 돌지 않았다.

**How to apply:**
- 만든 뒤 `settings.json`에 실제로 등록됐는지 열어 본다.
- 걸려야 할 입력을 직접 넣어 훅이 반응하는지 시험한다(예: 가짜 JSON을 표준입력으로 넣어 실행).
- 실제 세션에서 한 번 발동하는 걸 확인한 뒤에야 「설치 완료」라고 말한다.
