# ruff: noqa: E501
"""One-off: split game_data/models.py into models/ package. Run from repo root."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "django_apps" / "game_data" / "models.py"
OUT = REPO / "django_apps" / "game_data" / "models"

HEADER = '''"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

from __future__ import annotations

from django.db import models

'''

# 1-based inclusive line ranges from original models.py (class ImportBatch .. LocalizedMessage)
RANGES: dict[str, tuple[int, int]] = {
    "import_meta": (10, 177),
    "assets": (180, 222),
    "shapes": (225, 327),
    "buildings": (330, 533),
    "research": (536, 740),
    "simulation": (743, 1178),
    "toolbar": (1181, 1297),
    "reflection": (1300, 1320),
    "l10n": (1323, 1341),
}

# LocalizationExportStatus is 101-116 — stays in import_meta per plan
# LazyLocalized is in research block but belongs in l10n — handled by moving classes manually

lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)

OUT.mkdir(parents=True, exist_ok=True)

for name, (start, end) in RANGES.items():
    chunk = "".join(lines[start - 1 : end])
    body = chunk.replace("class ImportBatch", "class ImportBatch")  # noqa
    if name != "import_meta":
        body = (
            "from django_apps.game_data.models.import_meta import ImportBatch, SourceObject\n\n"
            + body
        )
    else:
        body = (
            HEADER.strip() + "\n\n" + body.split("\n", 1)[1]
            if body.startswith('"""')
            else HEADER + body
        )
    if name == "import_meta":
        content = HEADER + "".join(lines[9:177])  # lines 10-177
    elif name == "shapes":
        content = (
            HEADER
            + "from django_apps.game_data.models.import_meta import ImportBatch, SourceObject\n\n"
            + "".join(lines[224:327])
        )
    elif name == "research":
        content = (
            HEADER
            + "from django_apps.game_data.models.import_meta import ImportBatch\n"
            + "from django_apps.game_data.models.l10n import LazyLocalizedPlaceholderReplacement, LazyLocalizedTextRef\n"
            + "from django_apps.game_data.models.shapes import ShapeRecipe\n\n"
            + "".join(lines[535:740])
        )
    elif name == "simulation":
        content = (
            HEADER
            + "from django_apps.game_data.models.buildings import BuildingVariant\n"
            + "from django_apps.game_data.models.import_meta import ImportBatch\n"
            + "from django_apps.game_data.models.research import ResearchUpgrade\n\n"
            + "".join(lines[742:1178])
        )
    elif name == "toolbar":
        content = (
            HEADER
            + "from django_apps.game_data.models.buildings import BuildingVariant\n"
            + "from django_apps.game_data.models.import_meta import ImportBatch\n\n"
            + "".join(lines[1180:1297])
        )
    elif name == "buildings":
        content = (
            HEADER
            + "from django_apps.game_data.models.import_meta import ImportBatch\n\n"
            + "".join(lines[329:533])
        )
    elif name == "assets":
        content = (
            HEADER
            + "from django_apps.game_data.models.import_meta import ImportBatch\n\n"
            + "".join(lines[179:222])
        )
    elif name == "reflection":
        content = (
            HEADER
            + "from django_apps.game_data.models.import_meta import ImportBatch\n\n"
            + "".join(lines[1299:1320])
        )
    elif name == "l10n":
        # LazyLocalized 564-610 from research + LocalizedMessage at end
        content = (
            HEADER
            + "from django_apps.game_data.models.import_meta import ImportBatch\n\n"
            + "".join(lines[563:610])
            + "\n"
            + "".join(lines[1322:1341])
        )
    else:
        content = HEADER + body

    (OUT / f"{name}.py").write_text(content, encoding="utf-8")
    print("wrote", name)

print("done")
