"""Import ``rttp-cert-candidate-recon-l0`` for B1 Phase C slug guards."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.rttp_recovery_evidence import (
    GATE_A_PRIMARY_SLUGS,
)

CERT_SLUG = "rttp-cert-candidate-recon-l0"

assert CERT_SLUG in GATE_A_PRIMARY_SLUGS


def import_cert_candidate_recon_l0(*, replace: bool = False) -> int:
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.reconstruction import load_reconstruction_fixture_line_pairs
    from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input

    required_copy, _ = load_reconstruction_fixture_line_pairs()[0]
    proj, created = m.AsteroidProject.objects.get_or_create(
        slug=CERT_SLUG,
        defaults={"name": "RTTP cert candidate (recon fixture L0)"},
    )
    if not created and replace:
        m.AsteroidMapInput.objects.filter(project_id=proj.pk).delete()
    elif not created and proj.map_inputs.exists():
        return int(proj.pk)

    create_copy_code_map_input(proj, required_copy)
    return int(proj.pk)


__all__ = ["CERT_SLUG", "import_cert_candidate_recon_l0"]
