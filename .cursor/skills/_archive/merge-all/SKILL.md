---
name: merge-all
description: >-
  Git 통합 전략: 통합 브랜치를 만들고 브랜치를 순서대로 merge, 충돌 처리, merge·rebase·cherry-pick 선택,
  검증(pytest·ruff·mypy·black). 사용자가 /merge-all 을 쓰거나, 여러 브랜치를 한 번에 main/master에
  합치지 않고 안전하게 합치는 흐름을 원할 때 사용한다.
disable-model-invocation: true
---

Role: Git 통합 전략 컨설턴트

## 결론

여러 명이 다양한 브랜치에서 작업했다면, **무작정 한 브랜치에 몰아 merge하지 말고 통합용 브랜치 하나를 만들어 순서대로 합치는 방식**이 가장 안전합니다.

## 사전 확인 (빠짐없이)

1. **기본 브랜치 이름**은 저장소마다 다르다(`main`, `master` 등). 아래 예시의 `<기본브랜치>`는 모두 이 이름으로 바꾼다.
   - 확인: `git branch -a`에서 `remotes/origin/HEAD -> origin/???`를 본다.
   - 또는 Bash: `basename "$(git symbolic-ref refs/remotes/origin/HEAD)"` / PowerShell: `Split-Path (git symbolic-ref refs/remotes/origin/HEAD) -Leaf`
2. **작업 트리가 깨끗한지** 확인한다. 수정이 있으면 먼저 커밋하거나 `git stash push`로 치운 뒤 통합을 시작한다.
3. **병합할 브랜치 목록**을 정한다. `git fetch --all --prune` 후 `git branch -a`로 원격 브랜치를 확인한다.
4. **이미 기본 브랜치에 포함된 브랜치**는 `git merge origin/…` 시 `Already up to date`로 끝난다. 그대로 두고 다음 브랜치로 넘어가면 된다.

## 추천 방식

`<기본브랜치>`를 실제 이름으로 치환한다.

```bash
git fetch --all --prune
git checkout <기본브랜치>
git pull origin <기본브랜치>

git checkout -b integration/merge-all-work
```

이제 합칠 **각 작업 브랜치**를 하나씩 merge한다.

```bash
git merge origin/feature-a
git merge origin/feature-b
git merge origin/feature-c
```

충돌 나면 그때마다 해결하고:

```bash
git status
# 충돌 파일 수정

git add .
git commit
```

모든 브랜치가 합쳐지면 검증(범위는 저장소 루트 `AGENTS.md`의 **검증 단계**에 따름):

```bash
python -m pytest
ruff check .
mypy .
black --check .
```

문제 없으면 기본 브랜치로 되돌아 합친다:

```bash
git checkout <기본브랜치>
git merge integration/merge-all-work
git push origin <기본브랜치>
```

**PR로만 합치는 경우**에는 위 `merge`/`push` 대신 `git push -u origin integration/merge-all-work` 후 호스팅에서 `integration/merge-all-work` → `<기본브랜치>` PR을 연다.

## 더 안전한 절차

### 1. 현재 브랜치 백업

```bash
git branch backup/before-integration
```

### 2. 원격 최신화

```bash
git fetch --all --prune
```

### 3. 브랜치 목록 확인

```bash
git branch -a
```

### 4. 통합 브랜치 생성

`<기본브랜치>`를 치환한다.

```bash
git checkout <기본브랜치>
git pull origin <기본브랜치>
git checkout -b integration/2026-05-11
```

### 5. 작은 브랜치부터 병합

추천 순서:

```text
1. 문서 변경 브랜치
2. 테스트 추가 브랜치
3. 독립 유틸/상수 브랜치
4. 서비스 로직 브랜치
5. UI 변경 브랜치
6. 큰 구조 변경 브랜치
```

## merge vs rebase

| 방식             | 사용 상황                         | 추천도 |
| ---------------- | --------------------------------- | ------ |
| `merge`          | 여러 사람 작업 합치기             | 높음   |
| `rebase`         | 개인 브랜치를 최신 기본 브랜치 위로 정리 | 중간   |
| `cherry-pick`    | 특정 커밋만 가져오기              | 높음   |
| `squash merge`   | PR 단위로 깔끔하게 합치기         | 높음   |

팀 작업 통합이면 기본은:

```bash
git merge origin/branch-name
```

## 충돌이 심하면

특정 브랜치 전체가 위험하면 merge 취소:

```bash
git merge --abort
```

특정 커밋만 가져오기:

```bash
git cherry-pick <commit-hash>
```

커밋 로그 확인:

```bash
git log --oneline --graph --all --decorate
```

## 실전 추천 플로우

`<기본브랜치>`를 치환한다.

```bash
git fetch --all --prune

git checkout <기본브랜치>
git pull origin <기본브랜치>

git checkout -b integration/merge-all

git merge origin/branch-1
# fix conflicts, test

git merge origin/branch-2
# fix conflicts, test

git merge origin/branch-3
# fix conflicts, test

python -m pytest
ruff check .
mypy .
black --check .

git push -u origin integration/merge-all
```

그다음 호스팅에서 `integration/merge-all` → `<기본브랜치>` PR을 연다.

## 셸 메모

Windows PowerShell 구버전에서는 `a && b`가 동작하지 않을 수 있다. 명령은 줄 단위로 실행하거나 `;`로 이어 쓴다.

## 핵심

**한 번에 다 합치지 말고, 통합 브랜치에서 하나씩 merge → 충돌 해결 → 테스트 → 다음 브랜치** 순서로 가세요.
