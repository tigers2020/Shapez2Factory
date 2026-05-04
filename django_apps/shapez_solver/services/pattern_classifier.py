from __future__ import annotations


def pattern_signature(shape_code: str) -> str:
    """단일 레이어 4사분면의 kind 등장 순서를 A/B/C… 시그니처로 표현한다."""

    if ":" in shape_code:
        raise ValueError("pattern_signature supports single-layer codes only")
    if len(shape_code) % 2 != 0:
        raise ValueError("shape_code length must be even")
    tokens = tuple(shape_code[index : index + 2] for index in range(0, len(shape_code), 2))
    mapping: dict[str, str] = {}
    letters: list[str] = []
    for token in tokens:
        if token not in mapping:
            mapping[token] = chr(ord("A") + len(mapping))
        letters.append(mapping[token])
    return "".join(letters)


def is_full_source_signature(shape_code: str) -> bool:
    """풀 소스(AAAA) 여부 — 인벤토리 매크로 후보 판별에 사용한다."""

    return pattern_signature(shape_code) == "AAAA"
