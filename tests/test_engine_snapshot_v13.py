import hashlib
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_SOURCE_REVISION = 'da83373d648694f50b8a974ff6071a73ceec2089'
ACCEPTED_ENGINE_HASHES = {
    'band_procurement.py': 'ba5d67eba3be6502e4d3ddbf475ca0189b7a9660ba9508429d77498de240e0bc',
    'prowrap_calculations.py': 'ea191add86766cd79fc5ec9f6e9deed8b950b1d66bd3318d89406c2846be9eca',
    'prowrap_materials.py': '213064ff8d1a7d06646b3172b90caa79704f11742cef0ad58dbfc3ecd101320e',
}
BYTE_EXACT_ENGINE_HASHES = {
    module_name: ACCEPTED_ENGINE_HASHES[module_name]
    for module_name in ('band_procurement.py', 'prowrap_materials.py')
}
ACTIVE_BATCH_CALCULATIONS_HASH = (
    '1ffbbd7397aab134aad6461a042b18342d5b46c1e86d658215e05a616d23bcfe'
)


@pytest.mark.parametrize(
    ('module_name', 'expected_hash'),
    BYTE_EXACT_ENGINE_HASHES.items(),
)
def test_exact_accepted_engine_file_snapshot_is_pinned(
    module_name, expected_hash,
):
    module_bytes = (REPOSITORY_ROOT / 'engine' / module_name).read_bytes()

    assert hashlib.sha256(module_bytes).hexdigest() == expected_hash


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
