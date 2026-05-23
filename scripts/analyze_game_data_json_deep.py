"""Exhaustive JSON path + merged schema for documents/game_data/*.json."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "documents" / "game_data"
OUT_DIR = REPO / "docs" / "domain" / "game_data_json_deep"
MAX_DEPTH = 48
MAX_ARRAY_DEPTH = 6  # max consecutive [] in norm_path
LIST_ELEM_SAMPLE = 32
SKIP_DESCEND_KEYS = frozenset({"$cycle"})
CLR_PRUNE_SEGMENTS = frozenset(
    {
        "DeclaredMembers",
        "DeclaredFields",
        "DeclaredConstructors",
        "DeclaredMethods",
        "DeclaredProperties",
        "DeclaredEvents",
        "CustomAttributes",
        "DefinedTypes",
        "Evidence",
        "ReturnParameter",
        "ReturnTypeCustomAttributes",
        "Module",
        "_minimum",
    }
)
DYNAMIC_KEY_RE = re.compile(r"^\(.*\)$|TileVector|LocalTilePivot")


def _norm_key(key: str) -> str:
    if DYNAMIC_KEY_RE.search(key):
        return "{dynamic_key}"
    return key


def _norm_path(path: str) -> str:
    p = re.sub(r"\[\d+\]", "[]", path)
    # collapse repeated [] from bugs / deep lists
    while "[][]" in p:
        p = p.replace("[][]", "[]")
    return p


def _array_depth(path: str) -> int:
    return path.count("[]")


@dataclass
class PathStat:
    row_hits: int = 0
    value_types: Counter[str] = field(default_factory=Counter)
    dollar_types: Counter[str] = field(default_factory=Counter)
    unity_types: Counter[str] = field(default_factory=Counter)
    max_list_len: int = 0

    def observe(self, value: Any) -> None:
        if value is None:
            self.value_types["null"] += 1
        elif isinstance(value, bool):
            self.value_types["boolean"] += 1
        elif isinstance(value, int):
            self.value_types["integer"] += 1
        elif isinstance(value, float):
            self.value_types["number"] += 1
        elif isinstance(value, str):
            self.value_types["string"] += 1
        elif isinstance(value, list):
            self.value_types["array"] += 1
            self.max_list_len = max(self.max_list_len, len(value))
        elif isinstance(value, dict):
            self.value_types["object"] += 1
            if isinstance(value.get("$type"), str):
                self.dollar_types[value["$type"]] += 1
            unity = value.get("$unity")
            if isinstance(unity, str):
                self.unity_types[unity] += 1


@dataclass
class SchemaNode:
    scalars: set[str] = field(default_factory=set)
    props: dict[str, SchemaNode] = field(default_factory=dict)
    items: SchemaNode | None = None
    dollar_type: Counter[str] = field(default_factory=Counter)
    pruned: bool = False

    def merge_value(self, value: Any, depth: int) -> None:
        if depth > MAX_DEPTH or self.pruned:
            self.scalars.add("…")
            return
        if value is None:
            self.scalars.add("null")
        elif isinstance(value, bool):
            self.scalars.add("boolean")
        elif isinstance(value, int):
            self.scalars.add("integer")
        elif isinstance(value, float):
            self.scalars.add("number")
        elif isinstance(value, str):
            self.scalars.add("string")
        elif isinstance(value, list):
            self.scalars.add("array")
            if self.items is None:
                self.items = SchemaNode()
            sample = value if len(value) <= LIST_ELEM_SAMPLE else value[:LIST_ELEM_SAMPLE]
            for item in sample:
                self.items.merge_value(item, depth + 1)
        elif isinstance(value, dict):
            self.scalars.add("object")
            if isinstance(value.get("$type"), str):
                self.dollar_type[value["$type"]] += 1
            for key, child in value.items():
                nk = _norm_key(key)
                node = self.props.setdefault(nk, SchemaNode())
                if key in SKIP_DESCEND_KEYS:
                    node.scalars.add("string")
                    continue
                if nk in CLR_PRUNE_SEGMENTS or key in CLR_PRUNE_SEGMENTS:
                    node.scalars.add("object")
                    node.pruned = True
                    if isinstance(child, dict) and isinstance(child.get("$type"), str):
                        node.dollar_type[child["$type"]] += 1
                    continue
                node.merge_value(child, depth + 1)
        else:
            self.scalars.add(type(value).__name__)


def _should_prune_segment(segment: str) -> bool:
    return segment in CLR_PRUNE_SEGMENTS


def _walk_paths(value: Any, prefix: str, stats: dict[str, PathStat], depth: int) -> None:
    if depth > MAX_DEPTH:
        return
    norm = _norm_path(prefix) if prefix else "<root>"
    if _array_depth(norm) > MAX_ARRAY_DEPTH:
        return
    stats.setdefault(norm, PathStat()).observe(value)

    if isinstance(value, dict):
        for key, child in value.items():
            if key in SKIP_DESCEND_KEYS:
                child_prefix = f"{prefix}.{'$cycle'}" if prefix else "$cycle"
                stats.setdefault(_norm_path(child_prefix), PathStat()).observe(child)
                continue
            nk = _norm_key(key)
            child_prefix = f"{prefix}.{nk}" if prefix else nk
            if _should_prune_segment(nk) or _should_prune_segment(key):
                stats.setdefault(_norm_path(child_prefix), PathStat()).observe(child)
                continue
            _walk_paths(child, child_prefix, stats, depth + 1)
    elif isinstance(value, list):
        list_prefix = f"{prefix}[]" if prefix else "[]"
        if _array_depth(_norm_path(list_prefix)) <= MAX_ARRAY_DEPTH:
            stats.setdefault(_norm_path(list_prefix), PathStat()).observe(value)
            sample = value if len(value) <= LIST_ELEM_SAMPLE else value[:LIST_ELEM_SAMPLE]
            for item in sample:
                _walk_paths(item, list_prefix, stats, depth + 1)


def _render_schema(node: SchemaNode, indent: int = 0) -> list[str]:
    pad = "  " * indent
    lines: list[str] = []
    if node.pruned:
        lines.append(f"{pad}object /* CLR reflection pruned */")
        if node.dollar_type:
            top = ", ".join(f"{n}×{c}" for n, c in node.dollar_type.most_common(5))
            lines.append(f"{pad}// $type: {top}")
        return lines
    if node.dollar_type:
        top = ", ".join(f"{n}×{c}" for n, c in node.dollar_type.most_common(10))
        extra = len(node.dollar_type) - 10
        suffix = f" (+{extra} more)" if extra > 0 else ""
        lines.append(f"{pad}// $type: {top}{suffix}")
    if "object" in node.scalars and node.props:
        lines.append(f"{pad}object {{")
        for key in sorted(node.props):
            lines.append(f'{pad}  "{key}":')
            lines.extend(_render_schema(node.props[key], indent + 2))
        lines.append(f"{pad}}}")
    elif "array" in node.scalars:
        lines.append(f"{pad}array<")
        if node.items:
            lines.extend(_render_schema(node.items, indent + 1))
        else:
            lines.append(f"{pad}  empty")
        lines.append(f"{pad}>")
    else:
        scalar = " | ".join(sorted(node.scalars)) if node.scalars else "unknown"
        if scalar:
            lines.append(f"{pad}{scalar}")
    return lines


def _envelope_stats(rows: list[dict[str, Any]]) -> list[str]:
    key_counts: Counter[str] = Counter()
    for row in rows:
        key_counts.update(row.keys())
    total = len(rows) or 1
    lines = ["| key | rows | rate |", "| --- | ---: | ---: |"]
    for key, count in key_counts.most_common():
        lines.append(f"| `{key}` | {count} | {count / total:.4f} |")
    return lines


def _write_paths_tsv(path: Path, stats: dict[str, PathStat], row_total: int) -> None:
    lines = ["norm_path\trow_hits\tvalue_types\tmax_list_len\t$type_top\t$unity_top"]
    for norm_path in sorted(stats.keys()):
        st = stats[norm_path]
        vtypes = ",".join(f"{k}:{v}" for k, v in st.value_types.most_common())
        dtypes = ";".join(f"{k}×{v}" for k, v in st.dollar_types.most_common(5))
        utypes = ";".join(f"{k}×{v}" for k, v in st.unity_types.most_common(5))
        hits = st.row_hits if st.row_hits else (row_total if norm_path == "<root>" else 0)
        lines.append(f"{norm_path}\t{hits}\t{vtypes}\t{st.max_list_len}\t{dtypes}\t{utypes}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_detail_md(stem: str, meta: dict[str, Any], stats: dict[str, PathStat]) -> None:
    lines = [
        f"# `{meta['name']}` — deep structure",
        "",
        f"- **Bytes:** {meta['bytes']:,}",
        f"- **Root:** `{meta['root_kind']}`",
        f"- **Rows:** {meta['row_count']}",
        f"- **Unique norm paths:** {meta['path_count']}",
        "",
        "## Row envelope (all rows)",
        "",
        *meta["envelope"],
        "",
    ]
    if meta.get("source_type_name_top15"):
        lines.extend(["## `source_type_name` distribution", ""])
        for name, count in meta["source_type_name_top15"]:
            lines.append(f"- `{name}` — {count}")
        lines.append("")
    lines.extend(
        [
            "## Artifacts",
            "",
            f"- [Merged schema]({stem}.schema.txt)",
            f"- [Path catalog]({stem}.paths.tsv)",
            "",
            "## Longest paths (sample)",
            "",
            "| depth | path |",
            "| ----: | ---- |",
        ]
    )
    by_len = sorted(stats.keys(), key=lambda p: (-p.count("."), -len(p)))[:40]
    for p in by_len:
        lines.append(f"| {p.count('.')} | `{p}` |")
    lines.append("")
    (OUT_DIR / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_file(json_path: Path) -> dict[str, Any]:
    data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    path_stats: dict[str, PathStat] = {}
    root_schema = SchemaNode()

    if isinstance(data, list):
        dict_rows = [r for r in data if isinstance(r, dict)]
        for row in dict_rows:
            path_stats.setdefault("<root>", PathStat()).row_hits += 1
            _walk_paths(row, "", path_stats, 0)
            root_schema.merge_value(row, 0)
        envelope = _envelope_stats(dict_rows)
        root_kind = f"array[{len(data)}]"
        row_count = len(data)
    elif isinstance(data, dict):
        path_stats.setdefault("<root>", PathStat()).row_hits = 1
        _walk_paths(data, "", path_stats, 0)
        root_schema.merge_value(data, 0)
        envelope = ["| key | present |", "| --- |:---:|"] + [
            f"| `{k}` | yes |" for k in sorted(data.keys())
        ]
        root_kind = f"object[{len(data)} keys]"
        dict_rows = []
        row_count = 0
    else:
        envelope = [f"primitive `{type(data).__name__}`"]
        root_kind = type(data).__name__
        dict_rows = []
        row_count = 0

    stem = json_path.stem
    _write_paths_tsv(OUT_DIR / f"{stem}.paths.tsv", path_stats, row_count or 1)
    schema_text = "\n".join(_render_schema(root_schema)) + "\n"
    (OUT_DIR / f"{stem}.schema.txt").write_text(schema_text, encoding="utf-8")

    stype_dist = Counter(str(r.get("source_type_name", "")) for r in dict_rows)
    meta = {
        "name": json_path.name,
        "bytes": json_path.stat().st_size,
        "root_kind": root_kind,
        "row_count": row_count,
        "path_count": len(path_stats),
        "envelope": envelope,
        "source_type_name_top15": stype_dist.most_common(15),
    }
    _write_detail_md(stem, meta, path_stats)
    return meta


def _write_readme(summaries: list[dict[str, Any]]) -> None:
    lines = [
        "# game_data JSON — deep structure appendix",
        "",
        (
            "**목표:** 데이터 구조 분석. **중복 파일도 각각 전량 기록** "
            "(`buildings` ≠ `building_groups` 부록 분리)."
        ),
        "",
        "생성: `python scripts/analyze_game_data_json_deep.py`",
        "",
        "규칙:",
        "- 모든 행 병합 스키마 (`*.schema.txt`)",
        "- 정규화 경로 카탈로그 (`*.paths.tsv`) — `[]` 인덱스, `{dynamic_key}` pivot 맵",
        "- `$cycle`·CLR reflection(`DeclaredMembers` 등) 하위는 **pruned** (경로 노드는 유지)",
        "",
        "| file | rows | paths | detail | schema | paths TSV |",
        "| ---- | ---: | ----: | ------ | ------ | --------- |",
    ]
    for s in summaries:
        stem = Path(s["name"]).stem
        lines.append(
            f"| `{s['name']}` | {s['row_count']} | {s['path_count']} | "
            f"[{stem}.md]({stem}.md) | [{stem}.schema.txt]({stem}.schema.txt) | "
            f"[{stem}.paths.tsv]({stem}.paths.tsv) |"
        )
    lines.extend(
        [
            "",
            "`simulation_systems` 추가 감사: "
            "`documents/game_data_analysis/simulation_systems/_nested_path_audit_agg.tsv`.",
            "",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _patch_main_structure_doc(summaries: list[dict[str, Any]]) -> None:
    main = REPO / "docs" / "domain" / "game_data_json_structure.md"
    if not main.is_file():
        return
    text = main.read_text(encoding="utf-8")
    appendix = [
        "",
        "---",
        "",
        "## 부록 A — 전량 경로·병합 스키마 (필수)",
        "",
        "**원칙:** 구조 분석 목적 — **중복·동형 파일도 각각 별도 부록**.",
        "17개 JSON 전부: [`game_data_json_deep/README.md`](game_data_json_deep/README.md).",
        "",
        "| file | rows | paths | detail |",
        "| ---- | ---: | ----: | ------ |",
    ]
    for s in summaries:
        stem = Path(s["name"]).stem
        appendix.append(
            f"| `{s['name']}` | {s['row_count']} | {s['path_count']} | "
            f"[{stem}.md](game_data_json_deep/{stem}.md) |"
        )
    appendix.append("")
    if "## 부록 A — 전량 경로" in text:
        start = text.index("## 부록 A — 전량 경로")
        end = text.find("\n## 3. 파일 카탈로그")
        if end == -1:
            end = text.find("\n---\n\n## 3.")
        if end == -1:
            text = text[:start].rstrip() + "\n" + "\n".join(appendix)
        else:
            text = text[:start].rstrip() + "\n" + "\n".join(appendix) + text[end:]
    intro = (
        "**구조 분석 목표:** 값 제외 타입 기록；**중복 여부 무관 17파일 전부**；"
        "깊이 우선 → §1–12 개요 + **부록 A 전 경로**.\n\n"
    )
    if "구조 분석 목표" not in text:
        text = text.replace(
            "이 문서는 **값(example) 없이 JSON 필드의 타입·역할**만 기술한다.",
            intro + "이 문서는 **값(example) 없이 JSON 필드의 타입·역할**을 기술한다.",
            1,
        )
    main.write_text(text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for path in sorted(SOURCE.glob("*.json")):
        print(f"analyze {path.name}...", flush=True)
        summaries.append(analyze_file(path))
    _write_readme(summaries)
    _patch_main_structure_doc(summaries)
    print(f"done -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
