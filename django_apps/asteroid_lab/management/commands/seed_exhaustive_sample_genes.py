"""Idempotent DB seed for exhaustive sample-gene layouts (GeneticSample by ``gene_key``)."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    TransportKind,
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.models import GeneticSample


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Generate all valid exhaustive sample-gene topologies and upsert GeneticSample rows "
        "by gene_key (metadata_json.generator scoped)."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print counts only; do not write to the database.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Legacy no-op; matching gene_key rows are always upsert-overwritten.",
        )
        parser.add_argument(
            "--transport-kind",
            choices=("belt", "pipe", "all"),
            default="all",
            help="Which transport variants to emit.",
        )
        parser.add_argument(
            "--max-extensions",
            type=int,
            default=3,
            help="Maximum extension count (0..3).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="After dedupe, process at most N samples (upsert order stable).",
        )
        parser.add_argument(
            "--delete-stale-generated",
            action="store_true",
            help=(
                "Delete GeneticSample rows with matching metadata_json.generator whose "
                "gene_key is not in this run's output. Skipped when --limit is set."
            ),
        )
        parser.add_argument(
            "--generator-version",
            default="exhaustive_sample_gene_v1",
            help="metadata_json['generator'] value and stale-delete filter.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        max_ext = int(options["max_extensions"])
        if max_ext < 0 or max_ext > 3:
            raise CommandError("--max-extensions must be between 0 and 3.")

        tk = str(options["transport_kind"])
        if tk == "all":
            tks: tuple[TransportKind, ...] = ("belt", "pipe")
        elif tk == "belt":
            tks = ("belt",)
        else:
            tks = ("pipe",)

        gen_ver = str(options["generator_version"])
        genes, stats = generate_exhaustive_sample_genes(
            max_extensions=max_ext,
            transport_kinds=tks,
            generator_version=gen_ver,
        )
        limit = options["limit"]
        if limit is not None:
            if int(limit) < 0:
                raise CommandError("--limit must be non-negative.")
            genes = genes[: int(limit)]

        self._print_stats(stats, len(genes))
        for g in genes[:10]:
            self.stdout.write(f"  example: {g.name}")
        if len(genes) > 10:
            self.stdout.write(f"  ... +{len(genes) - 10} more")

        if options["dry_run"]:
            self.stdout.write(self.style.NOTICE("dry-run: no database writes."))
            return

        saved = 0
        for g in genes:
            obj, created = GeneticSample.objects.update_or_create(
                gene_key=g.key,
                defaults={
                    "name": g.name,
                    "code": g.encoded_copy_string,
                    "metadata_json": dict(g.metadata),
                    "project": None,
                },
            )
            # ``update_or_create`` updates with ``save(update_fields=…)`` only; ``decoded_json``
            # is filled in ``full_clean()`` and must be persisted on existing rows.
            if not created:
                obj.save()
            saved += 1
        self.stdout.write(self.style.SUCCESS(f"upserted GeneticSample rows: {saved}"))

        if options["delete_stale_generated"]:
            if limit is not None:
                self.stdout.write(
                    self.style.WARNING("Skipping --delete-stale-generated because --limit is set.")
                )
            else:
                keep = {g.key for g in genes}
                deleted, _ = (
                    GeneticSample.objects.filter(
                        metadata_json__generator=gen_ver,
                    )
                    .exclude(gene_key__in=keep)
                    .exclude(gene_key__isnull=True)
                    .delete()
                )
                self.stdout.write(self.style.WARNING(f"deleted stale rows (objects): {deleted}"))

    def _print_stats(self, stats: ExhaustiveGenerationStats, to_save: int) -> None:
        self.stdout.write("--- exhaustive sample gene stats ---")
        self.stdout.write(f"complete_trees_attempted: {stats.complete_trees_attempted}")
        self.stdout.write(f"duplicate_keys_skipped: {stats.duplicate_keys_skipped}")
        self.stdout.write(f"invalid_rejected: {stats.invalid_rejected}")
        self.stdout.write(f"unique_topologies (pre-limit): {stats.unique_topologies}")
        self.stdout.write(f"to_save (after limit): {to_save}")
        for ec in sorted(stats.by_extension_count):
            self.stdout.write(f"  extension_count={ec}: {stats.by_extension_count[ec]}")
        for tk in sorted(stats.by_transport_kind):
            self.stdout.write(f"  transport_kind={tk}: {stats.by_transport_kind[tk]}")
