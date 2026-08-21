from datetime import UTC, datetime
from io import BytesIO

from openpyxl import load_workbook

from tests.helpers import valid_row_values, workbook_bytes_with_rows
from workbook_processor import process_workbook


def test_pinned_engine_revision_is_emitted_in_processed_workbook():
    from engine.prowrap_calculations import calculate_repair

    assert callable(calculate_repair)
    processed = process_workbook(
        workbook_bytes_with_rows([valid_row_values()]),
        datetime(2026, 8, 15, tzinfo=UTC),
        'engine-revision.xlsx',
    )
    workbook = load_workbook(BytesIO(processed.workbook_bytes), data_only=False)

    assert workbook['Summary']['B24'].value == '1.3.0'
    assert workbook['Summary']['B25'].value == 'da83373'


def test_pinned_engine_exposes_v12_corrosion_assessment_contract():
    from engine import (
        ACTUAL_DEFECT_LENGTH,
        DEFECT_LENGTH_BASES,
        IndividualCorrosionDefect,
        build_corrosion_assessment_plan,
    )

    plan = build_corrosion_assessment_plan(
        basis=ACTUAL_DEFECT_LENGTH,
        repair_zone_length_mm=100.0,
        nominal_wall_mm=12.0,
        default_remaining_wall_mm=9.0,
    )

    assert DEFECT_LENGTH_BASES[0] == ACTUAL_DEFECT_LENGTH
    assert plan.candidates == (
        IndividualCorrosionDefect("Actual/combined defect", 100.0, 9.0, True),
    )
