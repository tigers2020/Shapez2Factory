# Plan: Auto LCM target batch (2026-05-02)

## Goal

Remove manual `target_count` from API, DTOs, and solver UI. Always derive batch size from `minimal_balanced_target_count`. JSON response: keep `target.count`; remove top-level `target_count`.

## Status

Approved for implementation (aligns with workspace plan Auto LCM target batch).
