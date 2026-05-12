"""MVP color-channel mix rules for ``color_mixer`` (recipe graph / inventory path).

가정: 한 글자 색 채널은 ``shape_catalog.COLOR_KINDS``의 키(r,g,b,c,m,y,w,u,-)와 동일하다.
무채색 ``u``는 상대 색을 그대로 통과시키고, RGB 가산 근사로:

- 2차(secondary): ``r+g=y``, ``r+b=m``, ``g+b=c``
- 3차(white): ``y+b=w``, ``m+g=w``, ``c+r=w`` (2차색 + 남은 원색)

지원하지 않는 쌍은 ``ValueError``다.
"""

from __future__ import annotations

_MIX_PAIR: dict[frozenset[str], str] = {
    frozenset({"r", "g"}): "y",
    frozenset({"r", "b"}): "m",
    frozenset({"g", "b"}): "c",
    frozenset({"y", "b"}): "w",
    frozenset({"m", "g"}): "w",
    frozenset({"c", "r"}): "w",
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
    if key in _MIX_PAIR:
        return _MIX_PAIR[key]
    raise ValueError(f"unsupported color mix: {left!r} + {right!r}")


__all__ = ["mix_color_pair"]
