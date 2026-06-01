from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason


def test_genetic_sample_seed_skip_reasons_exist():
    assert Layer03SkipReason.MISSING_GENETIC_SAMPLE_SEEDS.value == "missing_genetic_sample_seeds"
    assert (
        Layer03SkipReason.INVALID_GENETIC_SAMPLE_SEED_SNAPSHOT.value
        == "invalid_genetic_sample_seed_snapshot"
    )
