from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShapeCode:
    raw: str

    def normalized(self) -> str:
        return self.raw.strip()
