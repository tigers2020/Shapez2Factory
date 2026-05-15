"""Topology rule catalog + modal payloads (help UI only)."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from django_apps.asteroid_lab.models import TopologyRule
from django_apps.asteroid_lab.services.dto import (
    TopologyModalBodyDTO,
    TopologyModalPayloadDTO,
    TopologyModalResultDTO,
    TopologyRuleSummaryDTO,
)


def get_topology_modal_payload(rule_key: str) -> TopologyModalResultDTO:
    """Load ``TopologyRule`` joined with ``TopologyRuleModalContent``.

    Returns a structured not-found style result when the rule or modal row is missing
    (callers may map ``error_code`` to HTTP 404).
    """

    try:
        rule = TopologyRule.objects.get(rule_key=rule_key)
    except TopologyRule.DoesNotExist:
        return TopologyModalResultDTO(
            found=False,
            error_code="rule_not_found",
            message=f"No topology rule for key={rule_key!r}",
        )

    try:
        modal = rule.modal_content
    except ObjectDoesNotExist:
        return TopologyModalResultDTO(
            found=False,
            error_code="modal_content_not_found",
            message=f"Topology rule {rule_key!r} has no modal content row",
        )

    summary = TopologyRuleSummaryDTO(
        rule_key=rule.rule_key,
        title=rule.title,
        short_label=rule.short_label,
        rule_group=rule.rule_group,
        severity=rule.severity,
        description=rule.description,
        examples_json=list(rule.examples_json or []),
        diagram_json=dict(rule.diagram_json or {}),
        is_active=rule.is_active,
        sort_order=rule.sort_order,
    )
    body = TopologyModalBodyDTO(
        modal_title=modal.modal_title,
        lead_html=modal.lead_html,
        sections_json=list(modal.sections_json or []),
        footer_json=dict(modal.footer_json or {}),
    )
    payload = TopologyModalPayloadDTO(rule=summary, modal=body)
    return TopologyModalResultDTO(found=True, error_code="", message="", payload=payload)
