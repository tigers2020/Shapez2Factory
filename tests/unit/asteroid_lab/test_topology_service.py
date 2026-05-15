"""``topology_service`` — modal payload + structured misses."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services import topology_service


@pytest.mark.django_db
def test_get_topology_modal_payload_found() -> None:
    rule = m.TopologyRule.objects.create(
        rule_key="rule-a",
        title="Title",
        short_label="A",
        rule_group="g",
        description="d",
    )
    m.TopologyRuleModalContent.objects.create(
        rule=rule,
        modal_title="Modal",
        lead_html="<p>x</p>",
        sections_json=[{"k": 1}],
    )
    res = topology_service.get_topology_modal_payload("rule-a")
    assert res.found is True
    assert res.payload is not None
    assert res.payload.rule.rule_key == "rule-a"
    assert res.payload.modal.modal_title == "Modal"


@pytest.mark.django_db
def test_get_topology_modal_payload_rule_missing() -> None:
    res = topology_service.get_topology_modal_payload("nope")
    assert res.found is False
    assert res.error_code == "rule_not_found"


@pytest.mark.django_db
def test_get_topology_modal_payload_modal_missing() -> None:
    m.TopologyRule.objects.create(
        rule_key="rule-b",
        title="Title",
        short_label="B",
        rule_group="g",
        description="d",
    )
    res = topology_service.get_topology_modal_payload("rule-b")
    assert res.found is False
    assert res.error_code == "modal_content_not_found"
