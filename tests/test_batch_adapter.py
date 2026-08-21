import math

import pytest

import batch_adapter
from batch_adapter import calculate_row
from engine.corrosion_defects import (
    ACTUAL_DEFECT_LENGTH,
    ENTER_MANUALLY,
    INDEPENDENT_DEFECTS,
    IndividualCorrosionDefect,
)
from batch_schema import ValidatedRow
from tests.helpers import batch_info, validated_row


def test_adapter_applies_common_info_and_matches_baseline():
    outcome = calculate_row(batch_info(), validated_row())

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Installed Plies'] == 3
    assert outcome.outputs['Installed Thickness [mm]'] == 2.49
    assert outcome.outputs['Total Repair Length [mm]'] == pytest.approx(388.934, rel=1e-3)


def test_actual_adapter_returns_the_single_b31g_candidate():
    """Catches dropping the canonical actual-defect assessment trace."""
    outcome = calculate_row(batch_info(), validated_row(**{
        'Defect Length Basis': ACTUAL_DEFECT_LENGTH,
    }))

    assert outcome.outputs['Repair Zone Length [mm]'] == 100.0
    assert outcome.outputs['3t Interaction Threshold [mm]'] == pytest.approx(28.59)
    assert outcome.outputs['B31G Candidate Count'] == 1
    assert outcome.outputs['Governing Defect ID'] == 'Actual/combined defect'
    assert len(outcome.candidate_calculations) == 1
    candidate = outcome.candidate_calculations[0]
    assert candidate.defect_id == 'Actual/combined defect'
    assert candidate.governing is True
    assert candidate.credited_safe_pressure_bar > 0


@pytest.mark.parametrize(('basis', 'defect_id', 'length_mm'), (
    (ACTUAL_DEFECT_LENGTH, 'Actual/combined defect', 100.0),
    (INDEPENDENT_DEFECTS, 'Independent 10x10 mm defects', 10.0),
))
def test_single_candidate_modes_inline_the_complete_scalar_audit(
    basis, defect_id, length_mm,
):
    """Catches Actual/Independent losing trace fields when no detail row exists."""
    outcome = calculate_row(batch_info(), validated_row(**{
        'Defect Length Basis': basis,
    }))
    candidate = outcome.candidate_calculations[0]
    reference = outcome.outputs['B31G Detail']

    assert reference == {
        'candidate_count': 1,
        'detail_excel_row_range': None,
        'detail_schema': 'Individual Defects',
        'detail_schema_version': '2',
        'governing_defect_id': defect_id,
        'inline_candidate': {
            'defect_id': candidate.defect_id,
            'length_mm': length_mm,
            'remaining_wall_mm': 4.5,
            'method': candidate.method,
            'd_over_t': candidate.d_over_t,
            'length_parameter_z': candidate.length_parameter_z,
            'folias_factor': candidate.folias_factor,
            'flow_stress_mpa': candidate.flow_stress_mpa,
            'failure_stress_mpa': candidate.failure_stress_mpa,
            'failure_pressure_bar': candidate.failure_pressure_bar,
            'safe_pressure_bar': candidate.safe_pressure_bar,
            'safety_factor': candidate.safety_factor,
            'operating_hoop_stress_mpa': candidate.operating_hoop_stress_mpa,
            'applicable': candidate.applicable,
            'acceptable': candidate.acceptable,
            'credited_safe_pressure_bar': candidate.credited_safe_pressure_bar,
            'governing': candidate.governing,
            'warning_codes': ', '.join(candidate.warning_codes),
        },
    }


@pytest.mark.parametrize(('value', 'expected'), (
    (float('inf'), 'Infinity'),
    (float('-inf'), '-Infinity'),
    (float('nan'), 'NaN'),
    (12.5, 12.5),
))
def test_audit_scalar_normalization_is_explicit_and_preserves_finite_values(
    value, expected,
):
    """Catches non-standard JSON tokens or lost finite audit precision."""
    normalizer = getattr(batch_adapter, 'normalize_audit_scalar', None)

    assert normalizer is not None
    assert normalizer(value) == expected


def test_high_smys_actual_inline_audit_normalizes_limiting_folias_only():
    """Catches adapter traces leaking a non-finite float into workbook JSON."""
    outcome = calculate_row(batch_info(), validated_row(**{
        'Pipe OD [mm]': 1016.0,
        'Nominal Wall [mm]': 12.0,
        'Pipe Yield [MPa]': 550.0,
        'Defect Length [mm]': 1000.0,
    }))
    candidate = outcome.candidate_calculations[0]
    inline = outcome.outputs['B31G Detail']['inline_candidate']

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert candidate.method == 'original'
    assert candidate.length_parameter_z == pytest.approx(82.02099737532808)
    assert math.isinf(candidate.folias_factor)
    assert inline['method'] == 'original'
    assert inline['length_parameter_z'] == pytest.approx(82.02099737532808)
    assert inline['folias_factor'] == 'Infinity'
    assert isinstance(inline['safe_pressure_bar'], float)


def test_independent_adapter_returns_the_conservative_pit_candidate():
    """Catches using the repair-zone span as the independent B31G length."""
    outcome = calculate_row(batch_info(), validated_row(**{
        'Defect Length Basis': INDEPENDENT_DEFECTS,
    }))

    assert outcome.outputs['Repair Zone Length [mm]'] == 100.0
    assert outcome.outputs['B31G Candidate Count'] == 1
    assert outcome.outputs['Governing Defect ID'] == 'Independent 10x10 mm defects'
    assert outcome.outputs['Governing B31G Length [mm]'] == 10.0
    assert [item.defect_id for item in outcome.candidate_calculations] == [
        'Independent 10x10 mm defects',
    ]


def test_manual_adapter_returns_main_and_candidate_outputs():
    """Catches losing manual candidates or using the blank main-row wall."""
    outcome = calculate_row(
        batch_info(),
        validated_row(**{
            'Pipe OD [mm]': 1016.0,
            'Nominal Wall [mm]': 12.0,
            'Pipe Yield [MPa]': 450.0,
            'Design Pressure [bar]': 104.9,
            'Defect Length [mm]': 1000.0,
            'Defect Length Basis': ENTER_MANUALLY,
            'Repair Group ID': 'R-001',
            'Remaining Wall [mm]': None,
            'Prowrap CF Cloth Width 1 [mm]': 500.0,
            'Prowrap CF Cloth Width 2 [mm]': 500.0,
            'Run Type A / Class 3 Check': 'Yes',
        }),
        individual_defects=(
            IndividualCorrosionDefect('D-01', 10.0, 9.652, True),
            IndividualCorrosionDefect('D-02', 35.0, 10.0, True),
        ),
    )

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.outputs['Repair Zone Length [mm]'] == 1000.0
    assert outcome.outputs['B31G Candidate Count'] == 2
    assert outcome.outputs['Governing Defect ID'] == 'D-02'
    assert outcome.outputs['Governing B31G Length [mm]'] == 35.0
    assert [item.defect_id for item in outcome.candidate_calculations] == ['D-01', 'D-02']
    first_candidate = outcome.candidate_calculations[0]
    assert first_candidate.d_over_t == pytest.approx(0.19566666666666674)
    assert first_candidate.length_parameter_z == pytest.approx(0.008202099737532808)
    assert first_candidate.folias_factor == pytest.approx(1.0025699928354461)
    assert first_candidate.flow_stress_mpa == pytest.approx(519.0)
    assert first_candidate.failure_stress_mpa == pytest.approx(518.7347244738818)
    assert first_candidate.failure_pressure_bar == pytest.approx(122.53576168674373)
    assert first_candidate.safe_pressure_bar == pytest.approx(88.2257484144555)
    assert first_candidate.safety_factor == pytest.approx(1.3888888888888888)
    assert first_candidate.operating_hoop_stress_mpa == pytest.approx(
        444.07666666666677
    )
    assert outcome.outputs['B31G Detail'] == {
        'candidate_count': 2,
        'detail_excel_row_range': None,
        'detail_schema': 'Individual Defects',
        'detail_schema_version': '2',
        'governing_defect_id': 'D-02',
        'inline_candidate': None,
    }
    assert outcome.outputs['Type A / Class 3 Check Run'] is True
    class3 = outcome.outputs['Type A Detail']['optional_class3_check']
    assert class3['input_summary']['substrate_allowable_pressure_bar'] == (
        outcome.outputs['Effective Pipe Capacity [bar]']
    )


def test_candidate_warning_codes_follow_the_ordered_candidate_trace():
    """Catches prefixed B31G warnings becoming unmapped or row-global only."""
    outcome = calculate_row(
        batch_info(),
        validated_row(**{
            'Pipe OD [mm]': 1016.0,
            'Nominal Wall [mm]': 12.0,
            'Pipe Yield [MPa]': 555.0,
            'Design Pressure [bar]': 104.9,
            'Defect Length [mm]': 1000.0,
            'Defect Length Basis': ENTER_MANUALLY,
            'Repair Group ID': 'R-001',
            'Remaining Wall [mm]': None,
            'Prowrap CF Cloth Width 1 [mm]': 500.0,
            'Prowrap CF Cloth Width 2 [mm]': 500.0,
        }),
        individual_defects=(
            IndividualCorrosionDefect('D-01', 10.0, 9.652, True),
            IndividualCorrosionDefect('D-02', 35.0, 10.0, True),
        ),
    )

    assert outcome.outputs['Compliance Warnings'] == ('W011', 'W013')
    assert [item.defect_id for item in outcome.candidate_calculations] == ['D-01', 'D-02']
    assert [item.warning_codes for item in outcome.candidate_calculations] == [
        ('W011', 'W013'),
        ('W011', 'W013'),
    ]


def test_cracked_dent_reaches_engine_as_full_pressure_type_a():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Dent w/crack',
        'Remaining Wall [mm]': 9.53,
    }))

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Effective Pipe Capacity [bar]'] == 0.0
    assert outcome.outputs['Composite Pressure Deficit [bar]'] == 50.0
    assert outcome.outputs['Installed Plies'] == 9
    detail = outcome.outputs['Type A Detail']
    assert set(detail) == {
        'calculation_basis',
        'allowable_pipe_stress_mpa',
        'substrate_allowable_pressure_mpa',
        'composite_pressure_deficit_mpa',
        'baseline_typea_design',
        'optional_class3_check',
    }
    assert detail['calculation_basis'] == (
        'Dent w/crack - full-pressure laminate'
    )
    assert detail['allowable_pipe_stress_mpa'] is None
    assert detail['substrate_allowable_pressure_mpa'] == 0.0
    assert detail['composite_pressure_deficit_mpa'] == 5.0
    assert detail['baseline_typea_design']['substrate_pressure_mpa'] == 0.0
    assert detail['optional_class3_check'] is None


def test_uncracked_dent_reaches_engine_with_approved_substrate_credit():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Dent no-crack',
        'Remaining Wall [mm]': 9.53,
    }))

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Effective Pipe Capacity [bar]'] == pytest.approx(
        107.75653543307088
    )
    assert outcome.outputs['Composite Pressure Deficit [bar]'] == 0.0
    assert outcome.outputs['Installed Plies'] == 3
    detail = outcome.outputs['Type A Detail']
    assert detail['calculation_basis'] == (
        'Dent no-crack - substrate load sharing'
    )
    assert detail['allowable_pipe_stress_mpa'] == pytest.approx(258.48)
    assert detail['substrate_allowable_pressure_mpa'] == pytest.approx(
        10.775653543307088
    )
    assert detail['composite_pressure_deficit_mpa'] == 0.0
    assert detail['baseline_typea_design']['substrate_pressure_mpa'] == (
        detail['substrate_allowable_pressure_mpa']
    )
    assert detail['optional_class3_check'] is None


def test_optional_class3_check_is_nested_without_replacing_baseline_audit():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Dent w/crack',
        'Remaining Wall [mm]': 9.53,
        'Run Type A / Class 3 Check': 'Yes',
    }))

    detail = outcome.outputs['Type A Detail']
    assert outcome.outputs['Type A / Class 3 Check Run'] is True
    assert detail['calculation_basis'] == (
        'Dent w/crack - full-pressure laminate'
    )
    assert detail['substrate_allowable_pressure_mpa'] == 0.0
    assert detail['composite_pressure_deficit_mpa'] == 5.0
    assert detail['baseline_typea_design']['substrate_pressure_mpa'] == 0.0
    assert detail['optional_class3_check'] is not None
    assert detail['optional_class3_check']['input_summary'][
        'substrate_allowable_pressure_bar'
    ] == 0.0


def test_direct_legacy_dent_caller_is_normalized_before_engine_invocation():
    canonical = validated_row(**{
        'Mechanism': 'Dent w/crack',
        'Remaining Wall [mm]': 9.53,
    })
    legacy = ValidatedRow(
        source_excel_row=canonical.source_excel_row,
        values={**canonical.values, 'Mechanism': ' Dent '},
    )

    outcome = calculate_row(batch_info(), legacy)

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Installed Plies'] == 9
    assert outcome.outputs['Type A Detail']['calculation_basis'] == (
        'Dent w/crack - full-pressure laminate'
    )


def test_not_repairable_blanks_installable_quantities():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Mechanism': 'Leak',
        'Design Pressure [bar]': 150.0,
    }))

    assert outcome.status.value == 'NOT REPAIRABLE'
    for heading in (
        'Required Structural Thickness [mm]',
        'Installed Plies',
        'Installed Thickness [mm]',
        'Total Repair Length [mm]',
        '500 mm Cloth Band Count',
        '300 mm Cloth Band Count',
        'Procurement Axial Length [mm]',
        'Fabric Area [m2]',
        'Epoxy Mass [kg]',
    ):
        assert outcome.outputs[heading] is None


@pytest.mark.parametrize(('width_1', 'width_2', 'expected_counts', 'expected_length'), [
    (300.0, 300.0, (0, 2), 600.0),
    (500.0, 500.0, (1, 0), 500.0),
    (300.0, 500.0, (1, 0), 500.0),
    (500.0, 300.0, (1, 0), 500.0),
])
def test_adapter_maps_separate_band_counts_for_each_width_pair(
    width_1, width_2, expected_counts, expected_length,
):
    outcome = calculate_row(batch_info(), validated_row(**{
        'Prowrap CF Cloth Width 1 [mm]': width_1,
        'Prowrap CF Cloth Width 2 [mm]': width_2,
    }))

    assert outcome.status.value == 'OK'
    assert outcome.outputs['Compliance Warnings'] == ()
    assert (
        outcome.outputs['500 mm Cloth Band Count'],
        outcome.outputs['300 mm Cloth Band Count'],
    ) == expected_counts
    assert outcome.outputs['Procurement Axial Length [mm]'] == expected_length


def test_width_availability_does_not_change_structural_or_classification_results():
    structural_headings = (
        'Wall Loss [%]',
        'Required Structural Thickness [mm]',
        'Installed Plies',
        'Installed Thickness [mm]',
        'Required Overlap [mm]',
        'Taper Length [mm]',
        'Total Repair Length [mm]',
        'Repair Zone Length [mm]',
        'B31G Detail',
        'Type A Detail',
        'Type B Detail',
        'Compliance Warnings',
    )
    outcomes = tuple(
        calculate_row(batch_info(), validated_row(**{
            'Prowrap CF Cloth Width 1 [mm]': width_1,
            'Prowrap CF Cloth Width 2 [mm]': width_2,
        }))
        for width_1, width_2 in (
            (300.0, 300.0),
            (500.0, 500.0),
            (300.0, 500.0),
            (500.0, 300.0),
        )
    )
    expected = (
        outcomes[0].status,
        tuple(outcomes[0].outputs[heading] for heading in structural_headings),
    )

    for outcome in outcomes[1:]:
        assert (
            outcome.status,
            tuple(outcome.outputs[heading] for heading in structural_headings),
        ) == expected


def test_temperature_above_qualification_limit_becomes_review_required():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Operating Temperature [degC]': 150.0,
    }))

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.error_message == ''
    assert 'W001' in outcome.outputs['Compliance Warnings']


def test_zero_pressure_type_a_check_is_skipped_and_requires_review():
    outcome = calculate_row(batch_info(), validated_row(**{
        'Design Pressure [bar]': 0.0,
        'Run Type A / Class 3 Check': 'Yes',
    }))

    assert outcome.status.value == 'REVIEW REQUIRED'
    assert outcome.outputs['Type A / Class 3 Check Run'] is False
    assert outcome.outputs['Compliance Warnings'] == ('W019',)
