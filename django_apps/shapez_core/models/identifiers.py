"""Identifier categories (per release) and normalized identifier rows."""

from __future__ import annotations

from django.db import models

from django_apps.shapez_core.models.release import ShapezBasedataRelease


class ShapezIdentifierCategory(models.Model):
    """One key from ``identifiers.json`` (e.g. ``BuildingVariantIds``) for a release."""

    release = models.ForeignKey(
        ShapezBasedataRelease,
        on_delete=models.CASCADE,
        related_name="identifier_categories",
    )
    key = models.CharField(max_length=120, db_index=True)
    sort_order = models.SmallIntegerField(default=0)
    label = models.CharField(max_length=160, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("release", "key"),
                name="shapez_identifier_category_release_key_uniq",
            ),
        ]
        ordering = ("release", "sort_order", "key")

    def __str__(self) -> str:
        if (self.label or "").strip():
            return f"{(self.label or '').strip()} ({self.key})"
        rel = getattr(self, "release", None)
        if rel is not None:
            return f"{self.key} @ v{rel.game_version}"
        return f"{self.key} (release {self.release_id})"


class ShapezGameIdentifier(models.Model):
    """One id string from identifiers.json under a category."""

    release = models.ForeignKey(
        ShapezBasedataRelease,
        on_delete=models.CASCADE,
        related_name="game_identifiers",
    )
    identifier_category = models.ForeignKey(
        ShapezIdentifierCategory,
        on_delete=models.CASCADE,
        related_name="identifiers",
    )
    value = models.CharField(max_length=512, db_index=True)
    normalized_value = models.CharField(max_length=512, blank=True, db_index=True)
    sprite_static_relpath = models.CharField(
        max_length=280,
        blank=True,
        default="",
        db_index=True,
        help_text="Static path under web/assets/sprites/ (posix), if a lab SVG exists.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("release", "identifier_category", "value"),
                name="shapez_game_identifier_release_cat_value_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=("release", "identifier_category")),
            models.Index(fields=("release", "value")),
        ]

    def save(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        if not self.normalized_value:
            self.normalized_value = self.value.strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        cat = getattr(self, "identifier_category", None)
        key = getattr(cat, "key", None) or str(self.identifier_category_id)
        return f"{key}: {self.value}"
