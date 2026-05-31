import pytest

from shapez2_factory.adapters.asteroid_lab.gene_catalog_snapshot import (
    GeneCatalogInvalid,
    GeneCatalogSnapshot,
)


def _valid_payload():
    return {
        "schema_version": "gene_catalog_v1",
        "generated_at": "2026-05-31T00:00:00Z",
        "provenance_hash": "abc123",
        "source_batch_id": "exhaustive_sample_gene_v1",
        "deterministic_sort_key": "by_gene_id_then_throughput_desc",
        "entries": [
            {
                "gene_id": "m3e_01",
                "resource_kind": "both",
                "canonical_output_dir": "E",
                "occupied_offsets": [[0, 0], [-1, 0], [-2, 0], [-3, 0]],
                "extractor_offset": [0, 0],
                "extension_offsets": [[-1, 0], [-2, 0], [-3, 0]],
                "output_stub_offset": [1, 0],
                "route_probe_start_offset": [2, 0],
                "throughput_factor": 16,
                "topology_signature_base": "m3e_01_base",
            }
        ],
    }


def test_from_payload_roundtrip():
    snap = GeneCatalogSnapshot.from_payload(_valid_payload())
    assert snap.schema_version == "gene_catalog_v1"
    assert len(snap.entries) == 1
    assert snap.entries[0].gene_id == "m3e_01"
    assert snap.entries[0].canonical_output_dir == "E"
    assert snap.entries[0].throughput_factor == 16


def test_unsupported_schema_rejected():
    payload = _valid_payload()
    payload["schema_version"] = "gene_catalog_v999"
    with pytest.raises(GeneCatalogInvalid):
        GeneCatalogSnapshot.from_payload(payload)


def test_missing_canonical_output_dir_rejected():
    payload = _valid_payload()
    del payload["entries"][0]["canonical_output_dir"]
    with pytest.raises(GeneCatalogInvalid):
        GeneCatalogSnapshot.from_payload(payload)


def test_bad_throughput_factor_rejected():
    payload = _valid_payload()
    payload["entries"][0]["throughput_factor"] = 5
    with pytest.raises(GeneCatalogInvalid):
        GeneCatalogSnapshot.from_payload(payload)


def test_empty_entries_is_valid_but_has_no_usable_genes():
    payload = _valid_payload()
    payload["entries"] = []
    snap = GeneCatalogSnapshot.from_payload(payload)
    assert snap.entries == ()
