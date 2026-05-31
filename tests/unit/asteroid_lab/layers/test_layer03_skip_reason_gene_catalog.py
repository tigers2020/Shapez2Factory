from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason


def test_gene_catalog_skip_reasons_exist():
    assert Layer03SkipReason.MISSING_GENE_CATALOG.value == "missing_gene_catalog"
    assert Layer03SkipReason.INVALID_GENE_CATALOG.value == "invalid_gene_catalog"
