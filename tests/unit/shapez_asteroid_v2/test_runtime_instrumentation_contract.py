"""Runtime instrumentation: TraceCollector + instrumented step (Slice 1–3 staging)."""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime import (
    step_instrumentation as step_inst_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.event_builders import (
    runtime_phase_boundary_event,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V2_PKG = _REPO_ROOT / "django_apps" / "shapez_asteroid" / "services" / "asteroid_mining_layout_v2"
_RUNTIME_PKG = _V2_PKG / "runtime"


def _valid_decision_event() -> TraceEvent:
    return TraceEvent(
        run_id="r1",
        phase="step4",
        step_index=1,
        event_type="route_try",
        committed=True,
        commit_reason=CommitReason.NORMAL_GAIN,
        rejected_reason=None,
        rollback_reason=None,
    )


def test_trace_collector_stores_valid_trace_event() -> None:
    c = TraceCollector("run-a")
    ev = _valid_decision_event()
    c.emit(ev)
    assert c.events == (ev,)
    assert c.has_event("route_try")
    assert c.count("route_try") == 1
    assert c.events_for_phase("step4") == (ev,)


def test_trace_collector_events_is_tuple_copy() -> None:
    c = TraceCollector("run-b")
    c.emit(_valid_decision_event())
    t1 = c.events
    c.emit(
        TraceEvent(
            run_id="r1",
            phase="step4",
            step_index=2,
            event_type="other",
            committed=True,
            commit_reason=CommitReason.NORMAL_GAIN,
            rejected_reason=None,
            rollback_reason=None,
        )
    )
    assert len(t1) == 1
    assert len(c.events) == 2


def test_trace_collector_emit_rejects_invalid_via_trace_event_constructor() -> None:
    with pytest.raises(ValueError, match="committed=true requires commit_reason"):
        TraceEvent(
            run_id="r1",
            phase="step4",
            step_index=0,
            event_type="x",
            committed=True,
            commit_reason=None,
            rejected_reason=None,
            rollback_reason=None,
        )


def test_trace_collector_source_has_no_disk_io_helpers() -> None:
    src = (_RUNTIME_PKG / "trace_collector.py").read_text(encoding="utf-8")
    assert "open(" not in src
    assert "Path(" not in src
    assert "validate_trace" not in src


def test_runtime_phase_boundary_event_semantics() -> None:
    ev = runtime_phase_boundary_event(
        run_id="rid",
        phase="step_1_reconstruction",
        step_index=0,
        event_type="phase_started",
    )
    assert ev.committed is False
    assert ev.commit_reason is None
    assert ev.rejected_reason is None
    assert ev.rollback_reason is None
    assert ev.event_type == "phase_started"


def test_run_instrumented_step_success_emits_start_and_finish() -> None:
    trace = TraceCollector("rid")

    def work() -> int:
        return 7

    assert (
        step_inst_mod.run_instrumented_step(phase="step_x", trace=trace, step_index=0, fn=work) == 7
    )
    types = [e.event_type for e in trace.events]
    assert types == ["phase_started", "phase_finished"]
    assert all(e.phase == "step_x" for e in trace.events)


def test_run_instrumented_step_exception_emits_failed_and_reraises() -> None:
    trace = TraceCollector("rid")

    def boom() -> None:
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError, match="fail"):
        step_inst_mod.run_instrumented_step(phase="step_y", trace=trace, step_index=3, fn=boom)
    assert [e.event_type for e in trace.events] == ["phase_started", "phase_failed"]


def test_run_instrumented_step_logger_extra_contains_run_id_and_phase() -> None:
    trace = TraceCollector("my-run")

    with patch.object(step_inst_mod.logger, "info") as mock_info:
        step_inst_mod.run_instrumented_step(
            phase="step_z", trace=trace, step_index=0, fn=lambda: None
        )

    extras = [call.kwargs.get("extra") for call in mock_info.call_args_list]
    assert {"run_id": "my-run", "phase": "step_z"} in extras


def test_run_instrumented_step_logs_exception() -> None:
    trace = TraceCollector("rid")

    with patch.object(step_inst_mod.logger, "exception") as mock_exc:

        def boom() -> None:
            raise ValueError("nope")

        with pytest.raises(ValueError, match="nope"):
            step_inst_mod.run_instrumented_step(phase="bad", trace=trace, step_index=0, fn=boom)
    mock_exc.assert_called_once()
    assert mock_exc.call_args.kwargs["extra"] == {"run_id": "rid", "phase": "bad"}


def test_run_instrumented_step_does_not_add_root_handlers() -> None:
    before_n = len(logging.root.handlers)
    trace = TraceCollector("rid")
    step_inst_mod.run_instrumented_step(phase="p", trace=trace, step_index=0, fn=lambda: 1)
    assert len(logging.root.handlers) == before_n


def test_instrumentation_modules_have_no_forbidden_disk_reads_in_ast() -> None:
    """Slice 3A: new runtime helpers must not open trace files."""

    for name in (
        "trace_collector.py",
        "step_instrumentation.py",
        "event_builders.py",
        "logging_helpers.py",
    ):
        tree = ast.parse((_RUNTIME_PKG / name).read_text(encoding="utf-8"), filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "open", f"{name}: forbidden open()"


# --- Slice 3B: staged migration allowlists ---

_PUBLIC_PHASE_FUNCS_ALLOWLIST_NO_TRACE_YET: frozenset[tuple[str, str]] = frozenset(
    {
        ("placement.pass1_outer", "run_pass1_outer_placement"),
        ("placement.pass2_internal", "run_pass2_internal_fill"),
    }
)

_ORCHESTRATION_ALLOWLIST_NO_INSTRUMENTED_STEP_YET: frozenset[str] = frozenset(
    {
        "solver.py",
    }
)


def _top_level_functions(path: Path) -> list[ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [n for n in tree.body if isinstance(n, ast.FunctionDef)]


def test_public_run_phase_functions_trace_kwonly_or_allowlisted() -> None:
    """3B: until migration, only known entrypoints may omit ``trace``."""

    for rel in ("placement/pass1_outer.py", "placement/pass2_internal.py"):
        path = _V2_PKG / rel
        mod_key = rel.replace(".py", "").replace("/", ".")
        for fn in _top_level_functions(path):
            if not fn.name.startswith("run_"):
                continue
            key = (mod_key, fn.name)
            if key in _PUBLIC_PHASE_FUNCS_ALLOWLIST_NO_TRACE_YET:
                continue
            kwonly = {a.arg for a in fn.args.kwonlyargs}
            assert "trace" in kwonly, f"{path}:{fn.name} must accept keyword-only trace"


def test_solver_orchestration_uses_instrumented_step_or_allowlisted() -> None:
    path = _V2_PKG / "solver.py"
    src = path.read_text(encoding="utf-8")
    uses_step = "run_instrumented_step" in src
    allowlisted = path.name in _ORCHESTRATION_ALLOWLIST_NO_INSTRUMENTED_STEP_YET
    assert uses_step or allowlisted


def test_runtime_instrumentation_does_not_vendor_trace_semantics() -> None:
    """No duplicate committed/commit_reason rules outside domain.trace_semantics / TraceEvent."""

    combined = ""
    for name in ("trace_collector.py", "step_instrumentation.py", "logging_helpers.py"):
        combined += (_RUNTIME_PKG / name).read_text(encoding="utf-8")
    assert "committed=false must not" not in combined
    assert "FORBIDDEN_COMMIT" not in combined


def test_trace_collector_module_docstring_mentions_no_disk() -> None:
    doc = (_RUNTIME_PKG / "trace_collector.py").read_text(encoding="utf-8")
    assert "disk" in doc.lower()
