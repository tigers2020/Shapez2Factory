"""MVP color-channel mix rules for ``color_mixer`` (recipe graph / inventory path).

가정: 한 글자 색 채널은 ``shape_catalog.COLOR_KINDS``의 키(r,g,b,c,m,y,w,u,-)와 동일하다.
무채색 ``u``는 상대 색을 그대로 통과시키고, ``r+g=y`` 등은 가산 혼합으로 처리한다.
지원하지 않는 쌍은 ``ValueError``다.
"""

from __future__ import annotations

_MIX_SECONDARY: dict[frozenset[str], str] = {
    frozenset({"r", "g"}): "y",
    frozenset({"r", "b"}): "m",
    frozenset({"g", "b"}): "c",
}


def mix_color_pair(left: str, right: str) -> str:
    """두 색 채널 문자를 혼합한 한 글자 색을 반환한다."""

    a = (left or "").strip()
    b = (right or "").strip()
    if a == "-" and b == "-":
        return "-"
    if a == "-":
        return b
    if b == "-":
        return a
    if a == "u" and b == "u":
        return "u"
    if a == "u":
        return b
    if b == "u":
        return a
    if a == b:
        return a
    key = frozenset({a, b})
    if key in _MIX_SECONDARY:
        return _MIX_SECONDARY[key]
    raise ValueError(f"unsupported color mix: {left!r} + {right!r}")


__all__ = ["mix_color_pair"]
