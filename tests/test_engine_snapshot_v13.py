import hashlib
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_SOURCE_REVISION = 'da83373d648694f50b8a974ff6071a73ceec2089'
ACCEPTED_ENGINE_HASHES = {
    'band_procurement.py': 'ba5d67eba3be6502e4d3ddbf475ca0189b7a9660ba9508429d77498de240e0bc',
    'prowrap_calculations.py': 'ea191add86766cd79fc5ec9f6e9deed8b950b1d66bd3318d89406c2846be9eca',
    'prowrap_materials.py': '213064ff8d1a7d06646b3172b90caa79704f11742cef0ad58dbfc3ecd101320e',
}
ACTIVE_BATCH_CALCULATIONS_HASH = (
    '1ffbbd7397aab134aad6461a042b18342d5b46c1e86d658215e05a616d23bcfe'
)


def test_exact_accepted_optimizer_snapshot_is_pinned():
    optimizer = (REPOSITORY_ROOT / 'engine' / 'band_procurement.py').read_bytes()

    assert hashlib.sha256(optimizer).hexdigest() == ACCEPTED_ENGINE_HASHES[
        'band_procurement.py'
    ]


def test_engine_source_records_full_revision_and_all_accepted_module_hashes():
    provenance = (REPOSITORY_ROOT / 'ENGINE_SOURCE.md').read_text(encoding='utf-8')

    assert ACCEPTED_SOURCE_REVISION in provenance
    for module_name, digest in ACCEPTED_ENGINE_HASHES.items():
        assert module_name in provenance
        assert digest in provenance
    active_calculations = (
        REPOSITORY_ROOT / 'engine' / 'prowrap_calculations.py'
    ).read_bytes()
    assert hashlib.sha256(active_calculations).hexdigest() == (
        ACTIVE_BATCH_CALCULATIONS_HASH
    )
    assert ACTIVE_BATCH_CALCULATIONS_HASH in provenance
