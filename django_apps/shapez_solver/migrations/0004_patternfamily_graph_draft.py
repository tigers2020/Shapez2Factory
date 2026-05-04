"""Placeholder PatternFamily for graph-first macro drafts (solver catalog 비매칭)."""

from django.db import migrations

GRAPH_DRAFT_CODE = "graph-draft"
GRAPH_DRAFT_SIGNATURE = "________"


def forwards(apps, schema_editor):
    PatternFamily = apps.get_model("shapez_solver", "PatternFamily")
    if PatternFamily.objects.filter(code=GRAPH_DRAFT_CODE).exists():
        return
    PatternFamily.objects.create(
        code=GRAPH_DRAFT_CODE,
        name="Graph draft (unset signature)",
        signature=GRAPH_DRAFT_SIGNATURE,
        description=(
            "Staff에서 그래프만 먼저 만들 때 쓰는 자리 패밀리. "
            "시그니처가 실제 패턴과 맞지 않아 솔버 매크로 후보 조회에는 걸리지 않는다. "
            "레시피가 준비되면 메타 편집에서 실제 PatternFamily로 바꾼다."
        ),
        allow_rotation=True,
        allow_reflection=False,
        priority=99999,
        is_active=True,
        schema_version=1,
    )


def backwards(apps, schema_editor):
    PatternFamily = apps.get_model("shapez_solver", "PatternFamily")
    PatternFamily.objects.filter(code=GRAPH_DRAFT_CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("shapez_solver", "0003_macrorecipe_graph_document"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
