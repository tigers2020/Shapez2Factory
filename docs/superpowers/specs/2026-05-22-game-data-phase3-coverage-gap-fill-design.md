# game_data Phase 3 — Domain Coverage Gap Fill

**Date:** 2026-05-22  
**Status:** Draft — awaiting implementation plan  
**Scope:** 구현 변경 + 계약 변경  
**Predecessor:** Phase 2 simulation path audit (2026-05-22)  
**Coverage doc:** [`docs/domain/game_data_coverage.md`](../../domain/game_data_coverage.md)  
**JSON structure:** [`docs/domain/game_data_json_deep/`](../../domain/game_data_json_deep/)

---

## 1. 목표

Phase 2까지 `ignore_audit` 처리된 경로 중 **플래너 기능에 실질적으로 필요한** 경로를 
`promoted`로 승격하여 ORM으로 저장한다.

### 분석 기준

- "기능적 completeness" 기준 — solver/planner에 필요한 데이터 우선  
- JSONField 금지 — 모든 값은 scalar 정규화 컬럼으로  
- Phase 방식 유지 — 추가 경로는 반드시 manifest 등록 후 import

### 분석 결과 요약 (발견된 갭)

| 분류 | 파일 | 경로 | 판정 |
|---|---|---|---|
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IConveyorConfiguration.ConveyorSpeed` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IFluidPort*Configuration.*.Rate.Value` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration.*.Rate.Value` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IFluidStorageConfiguration.*.Rate.Value` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IPipeGateConfiguration.*.Rate.Value` | **PROMOTE** |
| 🟡 MED | `buildings.json` | `<RequiredStoreContentId>k__BackingField.Id` / `RequiredStoreContentId.Id` | **PROMOTE** |
| 🟡 MED | `buildings.json` | `<ShowAsResearchReward>k__BackingField` / `ShowAsResearchReward` | **PROMOTE** |
| 🟡 MED | `fluids.json` | `display_name_key` (row-level) | **PROMOTE** |
| 🟢 IGNORE | `building_variants.json` | `ConnectorData.TileBounds.Min/Max` | `ignore_audit:LAYOUT_METADATA` |
| 🟢 IGNORE | `building_variants.json` | `ConnectorData.AllBuildingConnectors[]._IOType` | `ignore_audit:LEGACY_FIELD` |
| 🟢 IGNORE | `building_variants.json` | `IEntityDefinition.CustomData.All[].CustomDrawData.*` | `ignore_audit:RENDER_METADATA` |

---

## 2. 아키텍처

### 2-A. `BuildingVariantRateConfig` (신규 모델)

`building_variants.json`의 `IEntityDefinition.CustomData.All[]`은 polymorphic 인터페이스 목록이다.
각 항목이 가진 인터페이스 키(예: `IConveyorConfiguration`)와 파라미터를 정규화 행으로 저장한다.

```python
class BuildingVariantRateConfig(models.Model):
    """Per-interface physics/rate parameter extracted from CustomData.All[]."""

    variant = models.ForeignKey(
        BuildingVariant,
        on_delete=models.CASCADE,
        related_name="rate_configs",
    )
    interface_key = models.CharField(max_length=255)   # e.g. "IConveyorConfiguration"
    param_key = models.CharField(max_length=128)        # e.g. "steps_per_tick"
    int_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    text_value = models.CharField(max_length=255, blank=True, default="")
    research_scale_id = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "interface_key", "param_key"],
                name="uq_variant_rate_config_key",
            )
        ]
        verbose_name = "building variant rate config"
        verbose_name_plural = "④ Buildings · Variant rate configs"
```

**저장 예시:**

| variant | interface_key | param_key | int_value | float_value | text_value |
|---|---|---|---|---|---|
| Belt1x1 | `IConveyorConfiguration` | `steps_per_tick` | 1 | null | |
| Belt1x1 | `IConveyorConfiguration` | `research_scale_id` | null | null | `BeltSpeedUpgrade` |
| FluidPump | `IFluidPortReceiverConfiguration` | `fluid_provide_rate` | null | 0.5 | |
| FluidPump | `IFluidPortSenderConfiguration` | `fluid_consume_rate` | null | 0.5 | |

**추출 인터페이스 → param_key 매핑:**

| CustomData 인터페이스 | 추출 경로 | param_key | 타입 |
|---|---|---|---|
| `IConveyorConfiguration` | `ConveyorSpeed.StepsPerTick.Value` | `steps_per_tick` | int |
| `IConveyorConfiguration` | `ConveyorSpeed.BaseSpeed` | `base_speed` | float |
| `IConveyorConfiguration` | `ConveyorSpeed.ResearchId.Id` | `research_scale_id` | text |
| `IFluidPortReceiverConfiguration` | `ProvidingConfiguration.IProvidingFluidContainerConfiguration.ProvidingRate.Value` | `fluid_provide_rate` | float |
| `IFluidPortSenderConfiguration` | `ConsumingConfiguration.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `fluid_consume_rate` | float |
| `ICrystalGeneratorConfiguration` | `ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `crystal_consume_rate` | float |
| `IFluidStorageConfiguration` | `ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingRate.Value` | `fluid_storage_provide_rate` | float |
| `IFluidStorageConfiguration` | `ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `fluid_storage_consume_rate` | float |
| `IPipeGateConfiguration` | `ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingRate.Value` | `pipe_gate_provide_rate` | float |
| `IPipeGateConfiguration` | `ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `pipe_gate_consume_rate` | float |

추출 로직: `CustomData.All[]` 리스트에서 각 항목이 가진 최상위 key를 인터페이스 키로 사용.
동일 인터페이스가 복수 등장하면 첫 번째 항목만 사용(추후 감사용 warning 추가).

### 2-B. `BuildingGroup` 필드 추가

```python
# buildings.json / building_groups.json definition_snapshot에서 추출
required_store_content_id = models.CharField(max_length=128, blank=True, default="")
show_as_research_reward = models.BooleanField(default=False)
```

추출 경로:
- `RequiredStoreContentId.Id` (non-backing field 우선; fallback `<RequiredStoreContentId>k__BackingField.Id`)
- `ShowAsResearchReward` (boolean; fallback `<ShowAsResearchReward>k__BackingField`)

### 2-C. `FluidColor.display_name_key` 추가

```python
display_name_key = models.CharField(max_length=512, blank=True, default="")
```

Row-level 필드 `display_name_key` 직접 읽기 (이미 importer에서 `row.get("display_name_key")` 가능).

---

## 3. Manifest 등록

**신규 reason_codes** (`django_apps/game_data/coverage/reason_codes.py` 추가):

```python
LAYOUT_METADATA = "LAYOUT_METADATA"       # ConnectorData TileBounds 등 배치 렌더링 전용
LEGACY_FIELD = "LEGACY_FIELD"             # _IOType 등 하위호환 레거시 필드
RENDER_METADATA = "RENDER_METADATA"       # CustomDrawData 등 렌더링 전용
NESTED_ENTITY_DEF = "NESTED_ENTITY_DEF"  # CustomData.All[].Definitions[] 재귀 엔티티
REFLECTION_CACHE = "REFLECTION_CACHE"     # DataPerTypeCache 등 CLR 반영 캐시
```

`django_apps/game_data/coverage/manifest.py` 추가:

```python
# Phase 3 PROMOTED
"building_variants.json:IEntityDefinition.CustomData.All[].IConveyorConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IFluidStorageConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IPipeGateConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"buildings.json:RequiredStoreContentId": (PROMOTED, "BuildingGroup.required_store_content_id"),
"buildings.json:ShowAsResearchReward": (PROMOTED, "BuildingGroup.show_as_research_reward"),

# Phase 3 IGNORE_AUDIT
"building_variants.json:ConnectorData.TileBounds": (IGNORE_AUDIT, "LAYOUT_METADATA"),
"building_variants.json:ConnectorData.AllBuildingConnectors[]._IOType": (IGNORE_AUDIT, "LEGACY_FIELD"),
"building_variants.json:IEntityDefinition.CustomData.All[].CustomDrawData": (IGNORE_AUDIT, "RENDER_METADATA"),
"building_variants.json:IEntityDefinition.CustomData.All[].Definitions[]": (IGNORE_AUDIT, "NESTED_ENTITY_DEF"),
"building_variants.json:IEntityDefinition.CustomData.DataPerTypeCache": (IGNORE_AUDIT, "REFLECTION_CACHE"),
```

---

## 4. 불변식 (Invariants)

```text
1. BuildingVariantRateConfig에 JSONField 없음.
2. 동일 (variant, interface_key, param_key) 조합은 유일.
3. CustomData.All[] 파싱 실패 시 해당 variant rate config를 건너뛰고 ctx.record_unknown으로 기록.
4. BuildingGroup.required_store_content_id == "" 이면 DLC 제한 없음.
5. FluidColor.display_name_key 추가는 기존 FK/UK 변경 없음.
6. 모든 새 경로는 manifest에 등록 후에만 import 가능.
```

---

## 5. 데이터 흐름

```
building_variants.json
  └── _import_building_variants()  (importer.py)
        ├── BuildingVariant (기존)
        ├── BuildingConnector (기존)
        ├── BuildingFootprintTile (기존)
        └── BuildingVariantRateConfig (NEW) ← CustomData.All[] 파싱

buildings.json / building_groups.json
  └── _upsert_building_group()  (importer.py)
        └── BuildingGroup (required_store_content_id, show_as_research_reward 추가)

fluids.json
  └── _import_fluids()  (importer.py)
        └── FluidColor (display_name_key 추가)
```

---

## 6. 테스트 계획

| 테스트 파일 | 검증 내용 |
|---|---|
| `tests/unit/game_data/test_building_variant_rate_config.py` | ConveyorSpeed 추출, fluid rate 추출, interface_key 정확성, 복수 인터페이스 처리 |
| `tests/unit/game_data/test_building_group_flags.py` | required_store_content_id, show_as_research_reward 올바른 추출 |
| `tests/unit/game_data/test_fluid_color_display_name.py` | display_name_key 저장 확인 |
| `tests/unit/game_data/test_domain_coverage_manifest.py` | 신규 manifest 경로 등록 확인 (기존 파일 확장) |
| 기존 regression | `test_simulation_path_coverage.py` — 변경 없이 green 확인 |

**테스트 데이터:** 실제 `documents/game_data/` JSON에서 belt/fluid variant 1개씩 fixture 추출.

---

## 7. 마이그레이션 전략

1. `BuildingVariantRateConfig` 신규 테이블 — migration 생성
2. `BuildingGroup.required_store_content_id`, `show_as_research_reward` — migration (nullable 아님, default 있음)
3. `FluidColor.display_name_key` — migration (default `""`)
4. 마이그레이션 후 `import_game_data --source documents/game_data` 재실행
5. `dumpdata game_data` 재생성 → `game_data_backup/game_data_dump.json` 갱신

---

## 8. 리스크

| 리스크 | 수준 | 대응 |
|---|---|---|
| `CustomData.All[]` 구조가 버전에 따라 변화 | MEDIUM | 파싱 실패는 `record_unknown`으로 기록, not crash |
| 동일 interface_key 복수 등장 시 첫 번째만 사용 | LOW | warning 기록, 추후 감사 가능 |
| 새 manifest 경로가 기존 coverage test와 충돌 | LOW | manifest 등록 후 test 갱신 동시 진행 |
| `k__BackingField` vs 비-backing field 양측 값 존재 | LOW | 비-backing 우선 read, backing field fallback |

---

## 9. 범위 외 (Out of Scope)

- `research_unlocks.json` Rewards 모델화 — 별도 Phase
- `building_variants.json ConnectorData.TileBounds` 정규화 — `ignore_audit` 등록만
- `simulation_systems.json` 추가 경로 — Phase 2에서 완료
- 기존 `ignore_audit` 경로(Assembly reflection, Runtime delegate 등) — 변경 없음

---

## 10. 참조

- Phase 1-2 spec: [`docs/superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md`](2026-05-22-game-data-domain-complete-coverage-design.md)
- JSON deep docs: [`docs/domain/game_data_json_deep/`](../../domain/game_data_json_deep/)
- Coverage manifest: [`django_apps/game_data/coverage/manifest.py`](../../../django_apps/game_data/coverage/manifest.py)
- Reason codes: [`django_apps/game_data/coverage/reason_codes.py`](../../../django_apps/game_data/coverage/reason_codes.py)
