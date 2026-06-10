# Cursor / AGENTS.md Workflow Research Digest

Report-only location for Hermes weekly research loop (cron `49dc6e7733b3`). Findings here are **proposals not applied** — human approval required before any governance file changes.

---

## 2026-06-10 Baseline Research Run

### Sources Checked
- [Stop Building AI Agents. Build Workflows With AI Steps Instead.](https://dev.to/kesimo/stop-building-ai-agents-build-workflows-with-ai_steps-instead-36dc) — blog (Kevin, 2026-06-10)
- [I Spent a Month Pair-Programming with Claude Code — Here's What Actually Worked](https://dev.to/z_z_c01afd7cf4c3764a2c73d/i-spent-a-month-pair-programming-with-claude-code-heres-what-actually-worked-4fne) — blog (z, 2026-06-10)
- [3 Patterns Broke When I Ran Claude Code Unattended for 7 Days](https://dev.to/mjmirza/3-patterns-broke-when-i-ran-claude-code-unattended-for-7-days-5apl) — blog (Mirza Iqbal, 2026-06-10)
- [¿Por qué SDD está fallando y cómo lo reemplaza IDSD?](https://dev.to/jcmexdev/por-que-spec-driven-development-esta-fallando-y-como-lo-reemplaza-intent-driven-software-3njn) — blog (Juan Carlos Garcia, 2026-06-10)
- Dev.to weekly trending: coding, productivity, devops tags — aggregated (2026-06-09 ~ 06-10)
- [How to write a great agents.md: Lessons from over 2,500 repositories](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) — official blog (GitHub)
- [Evaluating AGENTS.md: Are Repository-Level Context Files Helpful?](https://arxiv.org/abs/2602.11988) — paper (arXiv 2026)

### Accepted Findings

| # | Finding | Evidence | Source | Impact Area | Confidence |
|---|---------|----------|--------|-------------|------------|
| 1 | Workflow-with-AI-Steps vs. Agent: 단계가 정해졌으면 state machine + LLM 한 call로 끝, agent loop는 오버헤프만 추가 | Kevin Dev.to 글 — 실제 프로덕션에서 "agent" 절반이 if/else 감싸기일 뿐 | [link](https://dev.to/kesimo/stop-building-ai-agents-build-workflows-with-ai_steps-instead-36dc) | agents.md / workflow | high |
| 2 | Claude Code pair-programming 6주 리포트: goal → first pass → diff review (not chat) → human fix edge cases → commit. 핵심 이득은 flow state 유지 | z Dev.to — 600-line route refactor one-shot, boilerplate 90%, WGSL shader bug find | [link](https://dev.to/...) | workflow / testing | high |
| 3 | Unattended AI run의 silent failure가 진짜 해로움: loud crash는 드물고 조용한 파괴(forward-looking green while destroying work)가 문제 | Mirza — 168h/47 sessions, self-poisoning thinking block catch 불가 | [link](https://dev.to/mjmirza/3-patterns-broke-when-i-ran-claude-code-unattended-for-7-days-5apl) | safety / workflow | high |
| 4 | IDSD (ICE: Intent·Context·Expectations)로 SDD 진화 — 전체 spec 작성 불가, 3층 분할 + acceptance judgment 인간 유지 | Juan Carlos — vibe coding → SDD 실패 → IDSD 등장 | [link](https://dev.to/jcmexdev/por-que-spec-driven-development-esta-fallando-y-como-lo-reemplaza-intent-driven-software-3njn) | workflow / testing | med |
| 5 | AGENTS.md length 연구 갈등: arXiv 논문은 context file이 success rate ↓, cost ↑ 보고; GitHub blog는 2.5k repo 분석에서 "commands/tests/structure/style/git/boundaries" 6영역 핵심 | 논문 vs blog 갈림. 결론: 짧고 검증 가능한 규칙만 유지 | [arxiv](https://arxiv.org/abs/2602.11988), [github.blog](https://github.blog/...) | agents.md | high |

### Recommended Actions (NOT APPLIED)

> ⚠ Never auto-apply. Proposals for human approval only.

1. **AGENTS.md §SDD/Testing:** `(ICE: Intent · Context · Expectations)` 태그를 section header에 추가하고 첫 bullet가 3층 분할 원칙 명시 → IDSD 트렌드 반영
2. **AGENTS.md §Agent Scope:** `Anti-silent-failure` guard 추가 — "every run verify exit code + diff; forward-looking green = red" → unattended failure 패턴 차단
3. **.cursor/rules/:** Claude Code task chunking 규칙 (15분 단위 분할 권장) 새로운 .mdc 라우터로 제안

### Rejected Findings
- Self-host Tabby Server — 이 프로젝트에서 self-host 코드 완성 불필요 (agent는 외부 도구임). → not-applicable
- Container vuln scanner shootout (Trivy vs Grype) — DevOps concern이지만 현재 repo에 관련 layer 없음. → no_action
- R-CLI model harness — 모델 벤치마크 프레임워크, 우리 워크플로우와 직접 관련 X. → no_action
- GLM-5.1 MoE performance — 모델 아키텍처 리뷰, governance 규칙 변경 필요 X. → no_action

### Duplicate Check
- Baseline run; 이전 digest 없음 → overlap N/A

### Risky Trends to Avoid
- **"Agent-everything" hype:** 모든 작업을 agent loop로 감싸려는 경향. 이 repo는 Hermes skill suggestion + Cursor implementer 분리로 명확한 workflow separation 유지 중 — agent loop 도입은 token cost ↑, controllability ↓ 만 초래
- **Broad AGENTS.md expansion:** arXiv 연구에 따르면 context file 지나치게 길면 success rate ↓. 현재 75줄 제한은 합리적

### Next Research Focus
1. Cursor Cloud Agent / Automations 최신 changelog — user-facing workflow 변화 있는지 확인
2. OpenAI Codex `AGENTS.md` global→project→nested 병합 규칙 업데이트 — 이 repo에 nested AGENTS.md 도입 고려시 필요
