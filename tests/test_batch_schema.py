from batch_schema import (
    B31G_DETAIL_SCHEMA_VERSION,
    BatchInfo,
    DETAIL_OUTPUT_HEADERS,
    INPUT_HEADERS,
    MAX_ROWS,
    OUTPUT_HEADERS,
)


def test_row_inputs_begin_with_pipe_od_and_exclude_common_fields():
    assert INPUT_HEADERS[0] == 'Pipe OD [mm]'
    assert 'Customer' not in INPUT_HEADERS
    assert 'Project Location' not in INPUT_HEADERS
    assert 'Report No' not in INPUT_HEADERS
    assert MAX_ROWS == 150


def test_batch_info_holds_three_common_values():
    info = BatchInfo('ACME', 'Station 4', 'R-100')

    assert info.customer == 'ACME'
    assert info.project_location == 'Station 4'
    assert info.report_no == 'R-100'


def test_v13_inputs_have_exact_dual_width_contract():
    from batch_schema import MAX_DETAIL_ROWS

    assert INPUT_HEADERS == (
        'Pipe OD [mm]',
        'Nominal Wall [mm]',
        'Pipe Yield [MPa]',
        'Design Pressure [bar]',
        'Operating Temperature [degC]',
        'Mechanism',
        'Defect Location',
        'Defect Length [mm]',
        'Defect Length Basis',
        'Repair Group ID',
        'Remaining Wall [mm]',
        'Internal Corrosion Rate [mm/year]',
        'Design Life [years]',
        'Design Factor',
        'Run Type A / Class 3 Check',
        'Installation Temperature [degC]',
        'Component Type',
        'Cyclic Derating Factor',
        'Axial Load Case',
        'Prowrap CF Cloth Width 1 [mm]',
        'Prowrap CF Cloth Width 2 [mm]',
    )
    assert len(INPUT_HEADERS) == 21
    assert MAX_ROWS == 150
    assert MAX_DETAIL_ROWS == 150


def test_v13_outputs_have_exact_separate_band_count_contract():
    """Catches diagnostic workbook columns escaping the compact public contract."""
    assert OUTPUT_HEADERS == (
        'Wall Loss [%]',
        'Required Structural Thickness [mm]',
        'Installed Plies',
        'Total Repair Length [mm]',
        '500 mm Cloth Band Count',
        '300 mm Cloth Band Count',
        'Procurement Axial Length [mm]',
        'Fabric Area [m2]',
        'Epoxy Mass [kg]',
        'Repair Zone Length [mm]',
    )
    assert len(OUTPUT_HEADERS) == 10


def test_detail_outputs_hold_the_complete_scalar_b31g_candidate_audit():
    """Catches candidate intermediates being kept only in opaque main-row JSON."""
    assert DETAIL_OUTPUT_HEADERS == (
        'Source Excel Row',
        'Calculation Status',
        'Error Code',
        'Error Message',
        'B31G Method',
        'B31G d/t',
        'B31G Length Parameter z',
        'B31G Folias Factor M',
        'B31G Flow Stress [MPa]',
        'B31G Estimated Failure Stress [MPa]',
        'B31G Failure Pressure [bar]',
        'B31G Safe Pressure [bar]',
        'B31G Safety Factor',
        'B31G Operating Hoop Stress [MPa]',
        'B31G Applicable',
        'B31G Acceptable',
        'Credited Safe Pressure [bar]',
        'Governing Defect',
        'Assessment Warning Codes',
    )
    assert B31G_DETAIL_SCHEMA_VERSION == '2'
