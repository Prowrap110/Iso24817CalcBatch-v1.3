import math

import pytest

from batch_schema import BatchInfo
from batch_validation import (
    validate_batch_info,
    validate_individual_defect_row,
    validate_row,
)
from engine.corrosion_defects import ACTUAL_DEFECT_LENGTH, ENTER_MANUALLY, INDEPENDENT_DEFECTS
from tests.helpers import valid_row_values


def test_batch_info_normalizes_all_common_values():
    info, issues = validate_batch_info({
        'Customer': '  ACME  ',
        'Project Location': ' Station 4 ',
        'Report No': ' R-100 ',
    })

    assert info == BatchInfo('ACME', 'Station 4', 'R-100')
    assert issues == ()


def test_batch_info_requires_each_common_value_in_order():
    info, issues = validate_batch_info({
        'Customer': '  ',
        'Project Location': None,
        'Report No': '',
    })

    assert info is None
    assert [issue.code for issue in issues] == [
        'REQUIRED_VALUE',
        'REQUIRED_VALUE',
        'REQUIRED_VALUE',
    ]


def test_valid_row_normalizes_numeric_inputs_and_keeps_source_row():
    row, issues = validate_row(12, valid_row_values(**{
        'Pipe OD [mm]': '457.2',
        'Design Life [years]': '20',
    }))

    assert issues == ()
    assert row is not None
    assert row.source_excel_row == 12
    assert row.values['Pipe OD [mm]'] == 457.2
    assert row.values['Design Life [years]'] == 20


@pytest.mark.parametrize('mechanism', ['Dent w/crack', 'Dent no-crack'])
def test_accepts_canonical_dent_mechanisms(mechanism):
    row, issues = validate_row(2, valid_row_values(Mechanism=mechanism))

    assert issues == ()
    assert row is not None
    assert row.values['Mechanism'] == mechanism


def test_legacy_dent_is_conservatively_normalized():
    row, issues = validate_row(2, valid_row_values(Mechanism=' Dent '))

    assert issues == ()
    assert row is not None
    assert row.values['Mechanism'] == 'Dent w/crack'


@pytest.mark.parametrize('mechanism', ['dent', 'Dent no crack', 'Dent/crack'])
def test_ambiguous_dent_spellings_are_rejected(mechanism):
    row, issues = validate_row(2, valid_row_values(Mechanism=mechanism))

    assert row is None
    assert [issue.code for issue in issues] == ['INVALID_SELECTION']


def test_remaining_wall_cannot_exceed_nominal_wall():
    row, issues = validate_row(2, valid_row_values(**{
        'Remaining Wall [mm]': 10.0,
    }))

    assert row is None
    assert [issue.code for issue in issues] == ['OUT_OF_RANGE']


@pytest.mark.parametrize(('header', 'value'), [
    ('Mechanism', 'Erosion'),
    ('Defect Location', 'Outside'),
    ('Run Type A / Class 3 Check', 'Maybe'),
    ('Component Type', 'Elbow'),
    ('Axial Load Case', 2),
])
def test_rejects_selection_outside_the_allowed_set(header, value):
    row, issues = validate_row(2, valid_row_values(**{header: value}))

    assert row is None
    assert [issue.code for issue in issues] == ['INVALID_SELECTION']


def test_formula_marker_is_rejected_before_other_validation():
    row, issues = validate_row(2, valid_row_values(**{
        'Pipe OD [mm]': '=A1',
    }))

    assert row is None
    assert [issue.code for issue in issues] == ['FORMULA_NOT_ALLOWED']


def test_internal_corrosion_requires_rate():
    values = valid_row_values(**{
        'Mechanism': 'Corrosion',
        'Defect Location': 'Internal',
        'Internal Corrosion Rate [mm/year]': None,
    })

    row, issues = validate_row(2, values)

    assert row is None
    assert [issue.code for issue in issues] == ['INTERNAL_CORROSION_RATE_REQUIRED']


@pytest.mark.parametrize(('width_1', 'width_2'), [
    (300, 300),
    (500, 500),
    (300, 500),
    (500, 300),
])
def test_dual_cloth_widths_accept_every_approved_availability_pair(
    width_1, width_2,
):
    row, issues = validate_row(2, valid_row_values(**{
        'Prowrap CF Cloth Width 1 [mm]': width_1,
        'Prowrap CF Cloth Width 2 [mm]': width_2,
    }))

    assert issues == ()
    assert row is not None
    assert row.values['Prowrap CF Cloth Width 1 [mm]'] == float(width_1)
    assert row.values['Prowrap CF Cloth Width 2 [mm]'] == float(width_2)


@pytest.mark.parametrize('header', [
    'Prowrap CF Cloth Width 1 [mm]',
    'Prowrap CF Cloth Width 2 [mm]',
])
@pytest.mark.parametrize(('value', 'expected_code'), [
    (None, 'REQUIRED_VALUE'),
    ('', 'REQUIRED_VALUE'),
    (250, 'INVALID_SELECTION'),
    (True, 'INVALID_NUMBER'),
    ('wide', 'INVALID_NUMBER'),
])
def test_dual_cloth_widths_reject_blank_unapproved_boolean_and_nonnumeric_values(
    header, value, expected_code,
):
    row, issues = validate_row(2, valid_row_values(**{header: value}))

    assert row is None
    assert [issue.code for issue in issues] == [expected_code]


@pytest.mark.parametrize('value', [math.nan, math.inf, -math.inf, True])
def test_rejects_non_finite_or_boolean_numbers(value):
    row, issues = validate_row(2, valid_row_values(**{'Pipe OD [mm]': value}))

    assert row is None
    assert [issue.code for issue in issues] == ['INVALID_NUMBER']


def test_design_life_requires_a_whole_number_of_at_least_one_year():
    row, issues = validate_row(2, valid_row_values(**{
        'Design Life [years]': 1.5,
    }))

    assert row is None
    assert [issue.code for issue in issues] == ['OUT_OF_RANGE']


def test_issues_follow_input_column_order():
    row, issues = validate_row(2, valid_row_values(**{
        'Pipe OD [mm]': None,
        'Mechanism': 'Erosion',
        'Remaining Wall [mm]': 10.0,
    }))

    assert row is None
    assert [issue.code for issue in issues] == [
        'REQUIRED_VALUE',
        'INVALID_SELECTION',
        'OUT_OF_RANGE',
    ]


@pytest.mark.parametrize('basis', [ACTUAL_DEFECT_LENGTH, INDEPENDENT_DEFECTS])
def test_nonmanual_external_requires_wall_and_rejects_group_id(basis):
    row, issues = validate_row(2, valid_row_values(**{
        'Defect Length Basis': basis,
        'Repair Group ID': 'R-001',
        'Remaining Wall [mm]': None,
    }))

    assert row is None
    assert [issue.code for issue in issues] == [
        'REPAIR_GROUP_NOT_ALLOWED',
        'REQUIRED_VALUE',
    ]


def test_manual_external_requires_group_and_blank_main_wall():
    row, issues = validate_row(2, valid_row_values(**{
        'Defect Length Basis': ENTER_MANUALLY,
        'Repair Group ID': 'R-001',
        'Remaining Wall [mm]': None,
    }))

    assert issues == ()
    assert row is not None
    assert row.values['Repair Group ID'] == 'R-001'


def test_individual_defect_requires_exact_yes_and_normalizes_linking_values():
    row, issues = validate_individual_defect_row(12, {
        'Repair Group ID': ' R-001 ',
        'Defect ID': ' D-02 ',
        'Individual longitudinal length [mm]': '35',
        'Remaining wall [mm]': '9.652',
        'Separation exceeds 3t': 'Yes',
    })

    assert issues == ()
    assert row is not None
    assert row.source_excel_row == 12
    assert row.repair_group_id == 'R-001'
    assert row.defect_id == 'D-02'
    assert row.longitudinal_length_mm == 35.0
    assert row.remaining_wall_mm == 9.652
    assert row.separation_exceeds_3t is True


def test_individual_defect_rejects_defect_id_too_long_for_bounded_audit_reference():
    row, issues = validate_individual_defect_row(2, {
        'Repair Group ID': 'R-001',
        'Defect ID': 'D' * 256,
        'Individual longitudinal length [mm]': 10.0,
        'Remaining wall [mm]': 4.5,
        'Separation exceeds 3t': 'Yes',
    })

    assert row is None
    assert [issue.code for issue in issues] == ['OUT_OF_RANGE']
    assert issues[0].message == 'Defect ID: must contain at most 255 characters.'


def test_individual_defect_rejects_nonexact_separation_confirmation():
    row, issues = validate_individual_defect_row(2, {
        'Repair Group ID': 'R-001',
        'Defect ID': 'D-01',
        'Individual longitudinal length [mm]': 10.0,
        'Remaining wall [mm]': 4.5,
        'Separation exceeds 3t': ' yes ',
    })

    assert row is None
    assert [issue.code for issue in issues] == ['INVALID_SELECTION']
