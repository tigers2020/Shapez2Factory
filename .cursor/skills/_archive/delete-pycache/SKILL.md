---
name: delete-pycache
description: >-
  __pycache__ 디렉터리를 프로젝트 전역에서 삭제합니다. Use when the user invokes
  /delete-pycache or @delete-pycache, or asks to remove Python __pycache__ folders
  across the repo.
disable-model-invocation: true
---

# delete-pycache

__pycache__ 디렉터리를 프로젝트 전역에서 삭제합니다.

호출: 채팅에서 `@delete-pycache` 또는 사용자가 `/delete-pycache`라고 부를 때 이 스킬을 연다.

## 절차

1. 작업 루트는 현재 워크스페이스(저장소 루트)로 둔다.
2. 아래 중 하나를 실행한다 (에이전트가 직접 실행).

**Python (OS 공통, 이 레포 기준 권장)** — 워크스페이스 루트에서:

```bash
python -c "import pathlib, shutil; root = pathlib.Path('.'); paths = [p for p in root.rglob('__pycache__') if p.is_dir()]; [shutil.rmtree(p) for p in paths]"
```

**PowerShell (Windows)** — 워크스페이스 루트에서:

```powershell
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
```

3. 선택: `**/__pycache__/**` Glob 등으로 남은 `__pycache__`가 없는지 확인한다.

## 보고

- 삭제 실행 여부, 사용한 명령 한 줄.
- 가상환경이 레포 안에 있으면 그 안의 `__pycache__`도 함께 지워질 수 있음을 짧게 안내한다.
