"""Map one validated worksheet row to the isolated PROWRAP engine."""

from dataclasses import dataclass
import math
from typing import Any

from batch_schema import (
    B31G_DETAIL_SCHEMA,
    B31G_DETAIL_SCHEMA_VERSION,
    BatchInfo,
    ValidatedRow,
)
from batch_mechanisms import normalize_upload_mechanism
from batch_status import CalculationStatus, classify_result
from engine.corrosion_defects import (
    ACTUAL_DEFECT_LENGTH,
    ENTER_MANUALLY,
    INDEPENDENT_DEFECTS,
    IndividualCorrosionDefect,
)
from engine.prowrap_calculations import (
    apply_type_a_class3_result_to_repair,
    calculate_repair,
    calculate_type_a_class3_prowrap_check,
    substrate_credit_bar_for_iso_check,
)
from engine.prowrap_materials import PROWRAP
from warning_catalog import warning_codes


@dataclass(frozen=True)
class CandidateCalculation:
    defect_id: str
    length_mm: float
    remaining_wall_mm: float
    method: str
    d_over_t: float
    length_parameter_z: float
    folias_factor: float
    flow_stress_mpa: float
    failure_stress_mpa: float
    failure_pressure_bar: float
    safe_pressure_bar: float
    safety_factor: float
    operating_hoop_stress_mpa: float
    applicable: bool
    acceptable: bool
    credited_safe_pressure_bar: float
    governing: bool
    warning_codes: tuple[str, ...]


@dataclass(frozen=True)
class RowCalculation:
    source_excel_row: int
    status: CalculationStatus
    outputs: dict[str, object]
    error_code: str = ''
    error_message: str = ''
    candidate_calculations: tuple[CandidateCalculation, ...] = ()


_INSTALLABLE_OUTPUTS = (
    'Required Structural Thickness [mm]',
    'Installed Plies',
    'Installed Thickness [mm]',
    'Thin-Wall Thickness Check OK',
    'Required Overlap [mm]',
    'Taper Length [mm]',
    'Total Repair Length [mm]',
    '500 mm Cloth Band Count',
    '300 mm Cloth Band Count',
    'Procurement Axial Length [mm]',
    'Fabric Area [m2]',
    'Epoxy Mass [kg]',
)


def normalize_audit_scalar(value: object) -> object:
    """Represent non-finite audit floats explicitly without altering finite values."""
    if not isinstance(value, float) or math.isfinite(value):
        return value
    if math.isnan(value):
        return 'NaN'
    return 'Infinity' if value > 0 else '-Infinity'


def calculate_row(
    batch_info: BatchInfo,
    row: ValidatedRow,
    individual_defects: tuple[IndividualCorrosionDefect, ...] = (),
) -> RowCalculation:
    """Calculate a validated row without translating unexpected failures."""
    values = row.values
    try:
        mechanism = normalize_upload_mechanism(values['Mechanism'])
        defect_length_basis = (
            values.get('Defect Length Basis') or ACTUAL_DEFECT_LENGTH
        )
        assessment_remaining_wall = _assessment_remaining_wall(
            values,
            individual_defects,
        )
        result = calculate_repair(
            customer=batch_info.customer,
            location=batch_info.project_location,
            report_no=batch_info.report_no,
            od=values['Pipe OD [mm]'],
            wall=values['Nominal Wall [mm]'],
            yield_strength=values['Pipe Yield [MPa]'],
            pressure=values['Design Pressure [bar]'],
            temp=values['Operating Temperature [degC]'],
            defect_type=mechanism,
            defect_loc=values['Defect Location'],
            length=values['Defect Length [mm]'],
            rem_wall=assessment_remaining_wall,
            internal_corrosion_rate=values['Internal Corrosion Rate [mm/year]'] or 0.0,
            design_life=values['Design Life [years]'],
            design_factor=values['Design Factor'],
            installation_temp=values['Installation Temperature [degC]'],
            component_type=values['Component Type'],
            cyclic_derating_factor=values['Cyclic Derating Factor'],
            axial_load_case=values['Axial Load Case'],
            cloth_widths_mm=(
                values['Prowrap CF Cloth Width 1 [mm]'],
                values['Prowrap CF Cloth Width 2 [mm]'],
            ),
            allow_unqualified_temperature=True,
            defect_length_basis=defect_length_basis,
            individual_defects=individual_defects,
        )
        if _should_run_type_a_check(values, result):
            type_a = calculate_type_a_class3_prowrap_check(
                od=values['Pipe OD [mm]'],
                pressure_bar=values['Design Pressure [bar]'],
                temp=values['Operating Temperature [degC]'],
                rem_wall=result['rem_wall_eol'],
                design_life=values['Design Life [years]'],
                substrate_allowable_pressure_bar=substrate_credit_bar_for_iso_check(result),
                installation_temp=values['Installation Temperature [degC]'],
                component_type=values['Component Type'],
                cyclic_derating_factor=values['Cyclic Derating Factor'],
                nominal_wall_mm=values['Nominal Wall [mm]'],
                axial_load_case=values['Axial Load Case'],
            )
            result = apply_type_a_class3_result_to_repair(
                result,
                type_a,
                cloth_widths_mm=(
                    values['Prowrap CF Cloth Width 1 [mm]'],
                    values['Prowrap CF Cloth Width 2 [mm]'],
                ),
            )
    except ValueError as error:
        return RowCalculation(
            source_excel_row=row.source_excel_row,
            status=CalculationStatus.INPUT_ERROR,
            outputs={},
            error_code='ENGINE_INPUT_ERROR',
            error_message=str(error),
        )

    extra_warnings = _type_a_check_warnings(values, result)
    warnings = tuple(result['compliance_warnings']) + extra_warnings
    status = classify_result(result, extra_warnings)
    candidate_calculations = _candidate_calculations(result)
    outputs = _map_outputs(
        result,
        warning_codes(warnings),
        _should_run_type_a_check(values, result),
        candidate_calculations,
    )
    if status is CalculationStatus.NOT_REPAIRABLE:
        for heading in _INSTALLABLE_OUTPUTS:
            outputs[heading] = None

    return RowCalculation(
        source_excel_row=row.source_excel_row,
        status=status,
        outputs=outputs,
        candidate_calculations=candidate_calculations,
    )


def _assessment_remaining_wall(
    values: dict[str, Any],
    individual_defects: tuple[IndividualCorrosionDefect, ...],
) -> float | None:
    """Use the conservative linked wall when manual-mode main cells are blank."""
    if values.get('Defect Length Basis') != ENTER_MANUALLY:
        return values['Remaining Wall [mm]']
    if not individual_defects:
        return 0.0
    return min(defect.remaining_wall_mm for defect in individual_defects)


def _candidate_calculations(result: dict[str, Any]) -> tuple[CandidateCalculation, ...]:
    """Expose ordered B31G traces for linked individual-defect rows."""
    calculations = []
    for item in result['b31g_assessments']:
        assessment = item['assessment']
        prefix = f"Defect ID {item['defect_id']}: "
        messages = tuple(
            warning
            for warning in result['compliance_warnings']
            if str(warning).startswith(prefix)
        )
        calculations.append(CandidateCalculation(
            defect_id=item['defect_id'],
            length_mm=item['length_mm'],
            remaining_wall_mm=item['remaining_wall_mm'],
            method=assessment['method'],
            d_over_t=assessment['d_over_t'],
            length_parameter_z=assessment['z'],
            folias_factor=assessment['folias_m'],
            flow_stress_mpa=assessment['s_flow_mpa'],
            failure_stress_mpa=assessment['s_f_mpa'],
            failure_pressure_bar=assessment['p_f_mpa'] * 10.0,
            safe_pressure_bar=assessment['p_s_mpa'] * 10.0,
            safety_factor=assessment['safety_factor'],
            operating_hoop_stress_mpa=assessment['s_o_mpa'],
            applicable=assessment['applicable'],
            acceptable=assessment['acceptable'],
            credited_safe_pressure_bar=item['credited_pressure_mpa'] * 10.0,
            governing=item['defect_id'] == result['governing_defect_id'],
            warning_codes=warning_codes(messages),
        ))
    return tuple(calculations)


def _should_run_type_a_check(values: dict[str, Any], result: dict[str, Any]) -> bool:
    return (
        values['Run Type A / Class 3 Check'] == 'Yes'
        and 'Type A' in result['calc_method_thick']
        and values['Design Pressure [bar]'] > 0
        and values['Operating Temperature [degC]'] <= PROWRAP['max_temp']
    )


def _type_a_check_warnings(values: dict[str, Any], result: dict[str, Any]) -> tuple[str, ...]:
    if (
        values['Run Type A / Class 3 Check'] != 'Yes'
        or 'Type A' not in result['calc_method_thick']
    ):
        return ()
    if values['Design Pressure [bar]'] == 0:
        return (
            'Type A / Class 3 check was not run at zero design pressure; '
            'the check is non-controlling and engineering review is required.',
        )
    if values['Operating Temperature [degC]'] > PROWRAP['max_temp']:
        return (
            'Type A / Class 3 check was not run above the qualified Prowrap '
            'temperature limit; engineering review is required.',
        )
    return ()


def _map_outputs(
    result: dict[str, Any],
    warnings: tuple[str, ...],
    type_a_check_run: bool,
    candidate_calculations: tuple[CandidateCalculation, ...],
) -> dict[str, object]:
    b31g = result['b31g_details']
    type_a_detail = None
    if result.get('typea_design') is not None:
        type_a_detail = {
            'calculation_basis': result['calculation_basis'],
            'allowable_pipe_stress_mpa': result['allowable_pipe_stress_mpa'],
            'substrate_allowable_pressure_mpa': result['p_steel_capacity'],
            'composite_pressure_deficit_mpa': result['p_composite_design'],
            'baseline_typea_design': result.get('typea_design'),
            'optional_class3_check': result.get('iso_typea_class3'),
        }
    return {
        'Thickness Calculation Method': result['calc_method_thick'],
        'Overlap Calculation Method': result['calc_method_overlap'],
        'Wall Loss [%]': result['wall_loss_ratio'] * 100.0,
        'End-of-Life Remaining Wall [mm]': result['rem_wall_eol'],
        'No Substrate Capacity': result['has_no_substrate_capacity'],
        'B31G Applicable': None if b31g is None else b31g['applicable'],
        'B31G Acceptable': None if b31g is None else b31g['acceptable'],
        'Effective Pipe Capacity [bar]': result['p_steel_capacity'] * 10.0,
        'Composite Pressure Deficit [bar]': result['p_composite_design'] * 10.0,
        'Required Structural Thickness [mm]': result['t_required'],
        'Installed Plies': result['num_plies'],
        'Installed Thickness [mm]': round(result['final_thickness'], 2),
        'Thin-Wall Thickness Check OK': result['thickness_check_ok'],
        'Type A / Class 3 Check Run': type_a_check_run,
        'Type A / Class 3 Controls': result.get('iso_typea_class3_controls'),
        'Required Overlap [mm]': result['overlap_length'],
        'Taper Length [mm]': result['taper_length'],
        'Total Repair Length [mm]': result['iso_length'],
        '500 mm Cloth Band Count': result['num_bands_500'],
        '300 mm Cloth Band Count': result['num_bands_300'],
        'Procurement Axial Length [mm]': result['proc_length'],
        'Fabric Area [m2]': result['optimized_sqm'],
        'Epoxy Mass [kg]': result['epoxy_kg'],
        'Compliance Warnings': warnings,
        'B31G Detail': {
            'candidate_count': len(result['b31g_assessments']),
            'detail_excel_row_range': None,
            'detail_schema': B31G_DETAIL_SCHEMA,
            'detail_schema_version': B31G_DETAIL_SCHEMA_VERSION,
            'governing_defect_id': result['governing_defect_id'],
            'inline_candidate': _inline_candidate_audit(
                result, candidate_calculations,
            ),
        },
        'Type A Detail': type_a_detail,
        'Type B Detail': result['type_b_details'],
        'Repair Zone Length [mm]': result['repair_zone_length_mm'],
        '3t Interaction Threshold [mm]': result['interaction_distance_mm'],
        'B31G Candidate Count': len(result['b31g_assessments']),
        'Governing Defect ID': result['governing_defect_id'],
        'Governing B31G Length [mm]': result['governing_b31g_length_mm'],
        'Governing B31G Remaining Wall [mm]': (
            result['governing_b31g_remaining_wall_mm']
        ),
    }


def _inline_candidate_audit(
    result: dict[str, Any],
    candidates: tuple[CandidateCalculation, ...],
) -> dict[str, object] | None:
    """Inline the sole non-Manual candidate; Manual audits stay normalized."""
    if (
        result['defect_length_basis']
        not in {ACTUAL_DEFECT_LENGTH, INDEPENDENT_DEFECTS}
        or len(candidates) != 1
    ):
        return None
    candidate = candidates[0]
    audit = {
        'defect_id': candidate.defect_id,
        'length_mm': candidate.length_mm,
        'remaining_wall_mm': candidate.remaining_wall_mm,
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
    }
    return {
        key: normalize_audit_scalar(value)
        for key, value in audit.items()
    }
