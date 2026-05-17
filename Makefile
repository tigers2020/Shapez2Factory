# 로컬 기본: lint/type + 단위 위주·병렬 pytest (전체 스위트는 PR 직전·CI).
# Windows: GNU Make 설치 후 사용하거나, 아래 명령을 PowerShell에서 그대로 실행.

PYTHON ?= python

.PHONY: lint type test-fast test-integration test-slow test-all

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .

type:
	$(PYTHON) -m mypy .

# 무거운 리플레이/영속 테스트 제외 (-m "not slow"). Django+xdist는 loadscope 권장.
test-fast:
	$(PYTHON) -m pytest -n auto --dist loadscope -m "not slow" tests/unit/shapez_asteroid tests/unit/asteroid_lab tests/unit/web

test-integration:
	$(PYTHON) -m pytest -n auto --dist loadscope tests/integration

test-slow:
	$(PYTHON) -m pytest -n auto --dist loadscope -m slow

test-all:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .
	$(PYTHON) -m mypy .
	$(PYTHON) -m pytest -n auto --dist loadscope
