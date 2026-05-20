---
name: git-workflow
description: >-
  안전한 git 스테이징·커밋·push 워크플로. /git-workflow 또는 @git-workflow 로 호출한다.
  빠른 단일 세션 commit+push와 전체 검토(diff·시크릿 확인) 모드를 모두 지원한다.
disable-model-invocation: true
---

# git-workflow

모든 커밋 메시지는 **한국어**. Conventional Commits 형식 (`feat:` / `fix:` / `docs:` / `chore:` 등).

## 절차

### 1. 저장소 상태 확인

```bash
git status
git branch --show-current
git diff --stat
```

아래 상태면 중단:
- merge conflict 존재
- rebase 진행 중
- detached HEAD

### 2. 변경 검토

```bash
git diff
```

- 민감값(`.env`, API 키, 토큰) 포함 여부 확인 — 있으면 **커밋 금지**
- 관계 없는 파일이 포함되면 사용자에게 확인

### 3. 스테이징

이번 작업과 연관된 경로만 add한다:
```bash
git add <path> …
```

또는 전체:
```bash
git add .
```

### 4. 커밋

사용자가 메시지를 주면 그것을 사용; 없으면 변경 요약으로 한 줄 생성.

```bash
git commit -m "$(cat <<'EOF'
type(scope): 요약
EOF
)"
```

실패 시: 이유 설명 후 단순 이슈면 수정 후 1회 재시도.

### 5. Push

```bash
git push
```

upstream 없으면:
```bash
git push -u origin <current-branch>
```

`git push --force`는 사용자 명시 요청 시에만.

## 보고

- 실행한 명령·성공·실패 요약
- 커밋 생략(변경 없음) 시 이유 한 줄
- 원격 오류(거절·충돌·권한) 있으면 그대로 전달
