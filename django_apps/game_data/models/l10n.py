"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.import_meta import ImportBatch


class LazyLocalizedTextRef(models.Model):
    """Normalized Core.Localization.LazyLocalizedText from export snapshots."""

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="lazy_localized_text_refs"
    )
    message_key = models.CharField(max_length=512, blank=True, default="", db_index=True)
    lazy_text_type = models.CharField(max_length=128, blank=True, default="")
    placeholder_resolver_type = models.CharField(max_length=128, blank=True, default="")
    is_cycle_reference = models.BooleanField(default=False)
    cycle_reference = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "lazy localized text"
        verbose_name_plural = "⑧ L10n · Lazy text refs"

    def __str__(self) -> str:
        if self.message_key:
            return self.message_key
        return self.cycle_reference or self.canonical_id


class LazyLocalizedPlaceholderReplacement(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    lazy_text = models.ForeignKey(
        LazyLocalizedTextRef, on_delete=models.CASCADE, related_name="placeholder_replacements"
    )
    replacement_key = models.CharField(max_length=255)
    value_kind = models.CharField(max_length=64, blank=True, default="")
    nested_message_key = models.CharField(max_length=512, blank=True, default="")
    value_preview = models.TextField(blank=True, default="")
    order_index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "lazy localized placeholder"
        verbose_name_plural = "⑧ L10n · Placeholder replacements"
        ordering = ["order_index", "replacement_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["lazy_text", "replacement_key"],
                name="uq_lazy_placeholder_key",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.replacement_key} → {self.nested_message_key or self.value_kind}"

class LocalizedMessage(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="localized_messages")
    message_key = models.CharField(max_length=512)
    locale_code = models.CharField(max_length=16, default="en")
    message_text = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message_key", "locale_code"],
                name="uq_localized_message",
            ),
        ]
        verbose_name = "localized message"
        verbose_name_plural = "⑧ L10n · Messages"

    def __str__(self) -> str:
        return f"{self.message_key} [{self.locale_code}]"
