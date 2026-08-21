"""Pure validation for common batch data and human-readable row inputs."""

import math
from collections.abc import Mapping
from typing import Any

from batch_schema import (
    APPROVED_CLOTH_WIDTHS_MM,
    DETAIL_INPUT_HEADERS,
    INPUT_HEADERS,
    BatchInfo,
    ValidatedIndividualDefectRow,
    ValidatedRow,
    ValidationIssue,
)
from batch_mechanisms import (
    ACCEPTED_UPLOAD_MECHANISMS,
    normalize_upload_mechanism,
)
from engine.corrosion_defects import (
    DEFECT_LENGTH_BASES,
    ENTER_MANUALLY,
)


_COMMON_HEADERS = ('Customer', 'Project Location', 'Report No')
_SELECTIONS = {
    'Defect Location': ('External', 'Internal'),
    'Run Type A / Class 3 Check': ('Yes', 'No'),
    'Component Type': ('Straight', 'Bend', 'Tee', 'Flange', 'Reducer'),
}
_POSITIVE_HEADERS = {
    'Pipe OD [mm]',
    'Nominal Wall [mm]',
    'Pipe Yield [MPa]',
    'Defect Length [mm]',
}
_NONNEGATIVE_HEADERS = {
    'Design Pressure [bar]',
    'Remaining Wall [mm]',
    'Internal Corrosion Rate [mm/year]',
}
_REQUIRED_NUMERIC_HEADERS = {
    'Pipe OD [mm]',
    'Nominal Wall [mm]',
    'Pipe Yield [MPa]',
    'Design Pressure [bar]',
    'Operating Temperature [degC]',
    'Defect Length [mm]',
    'Design Life [years]',
    'Design Factor',
    'Installation Temperature [degC]',
    'Cyclic Derating Factor',
}
_CLOTH_WIDTH_HEADERS = {
    'Prowrap CF Cloth Width 1 [mm]',
    'Prowrap CF Cloth Width 2 [mm]',
}


def validate_batch_info(
    values: Mapping[str, Any],
) -> tuple[BatchInfo | None, tuple[ValidationIssue, ...]]:
    """Normalize and require the three worksheet-level batch values."""
    normalized: dict[str, str] = {}
    issues: list[ValidationIssue] = []
    for header in _COMMON_HEADERS:
        value = values.get(header)
        text = '' if value is None else str(value).strip()
        if not text:
            issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
        else:
            normalized[header] = text

    if issues:
        return None, tuple(issues)
    return (
        BatchInfo(
            customer=normalized['Customer'],
            project_location=normalized['Project Location'],
            report_no=normalized['Report No'],
        ),
        (),
    )


def validate_row(
    excel_row: int,
    values: Mapping[str, Any],
) -> tuple[ValidatedRow | None, tuple[ValidationIssue, ...]]:
    """Validate one populated input row without modifying its source cells."""
    normalized: dict[str, Any] = {}
    issues: list[ValidationIssue] = []

    for header in INPUT_HEADERS:
        raw_value = values.get(header)
        if _is_formula(raw_value):
            issues.append(_issue('FORMULA_NOT_ALLOWED', header, 'formulas are not allowed'))
            continue

        if header == 'Mechanism':
            text = '' if raw_value is None else str(raw_value).strip()
            if not text:
                issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
            elif text not in ACCEPTED_UPLOAD_MECHANISMS:
                issues.append(_issue('INVALID_SELECTION', header, 'is not an allowed selection'))
            else:
                normalized[header] = normalize_upload_mechanism(text)
            continue

        if header == 'Defect Length Basis':
            _validate_defect_length_basis(raw_value, header, normalized, issues)
            continue

        if header == 'Repair Group ID':
            _validate_repair_group_id(raw_value, header, normalized, issues)
            continue

        if header == 'Remaining Wall [mm]':
            _validate_remaining_wall(raw_value, header, normalized, issues)
            continue

        if header in _SELECTIONS:
            if _is_blank(raw_value):
                issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
            elif raw_value not in _SELECTIONS[header]:
                issues.append(_issue('INVALID_SELECTION', header, 'is not an allowed selection'))
            else:
                normalized[header] = raw_value
            continue

        if header == 'Axial Load Case':
            _validate_axial_load_case(raw_value, header, normalized, issues)
            continue

        if header in _CLOTH_WIDTH_HEADERS:
            _validate_cloth_width(raw_value, header, normalized, issues)
            continue

        if header == 'Internal Corrosion Rate [mm/year]':
            _validate_internal_corrosion_rate(raw_value, header, normalized, issues)
            continue

        _validate_numeric_header(raw_value, header, normalized, issues)

    if issues:
        return None, tuple(issues)
    return ValidatedRow(source_excel_row=excel_row, values=normalized), ()


def validate_individual_defect_row(
    excel_row: int,
    values: Mapping[str, Any],
) -> tuple[ValidatedIndividualDefectRow | None, tuple[ValidationIssue, ...]]:
    """Validate one populated individual-defect row before group linkage."""
    raw_values = {header: values.get(header) for header in DETAIL_INPUT_HEADERS}
    if all(_is_blank(value) for value in raw_values.values()):
        return None, ()

    normalized: dict[str, Any] = {}
    issues: list[ValidationIssue] = []
    for header in DETAIL_INPUT_HEADERS:
        raw_value = raw_values[header]
        if _is_formula(raw_value):
            issues.append(_issue('FORMULA_NOT_ALLOWED', header, 'formulas are not allowed'))
            continue

        if header in ('Repair Group ID', 'Defect ID'):
            text = '' if raw_value is None else str(raw_value).strip()
            if not text:
                issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
            elif header == 'Defect ID' and len(text) > 255:
                issues.append(_issue(
                    'OUT_OF_RANGE', header,
                    'must contain at most 255 characters',
                ))
            else:
                normalized[header] = text
            continue

        if header == 'Separation exceeds 3t':
            if _is_blank(raw_value):
                issues.append(_issue('REQUIRED_VALUE', header, 'a Yes confirmation is required'))
            elif raw_value != 'Yes':
                issues.append(_issue('INVALID_SELECTION', header, 'must be exactly Yes'))
            else:
                normalized[header] = True
            continue

        _validate_detail_number(raw_value, header, normalized, issues)

    if issues:
        return None, tuple(issues)
    return (
        ValidatedIndividualDefectRow(
            source_excel_row=excel_row,
            repair_group_id=normalized['Repair Group ID'],
            defect_id=normalized['Defect ID'],
            longitudinal_length_mm=normalized['Individual longitudinal length [mm]'],
            remaining_wall_mm=normalized['Remaining wall [mm]'],
            separation_exceeds_3t=True,
        ),
        (),
    )


def _validate_defect_length_basis(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    eligible = (
        normalized.get('Mechanism') == 'Corrosion'
        and normalized.get('Defect Location') == 'External'
    )
    if _is_blank(raw_value):
        if eligible:
            issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
        else:
            normalized[header] = None
        return
    if not eligible:
        issues.append(_issue('DEFECT_LENGTH_BASIS_NOT_ALLOWED', header, 'is only allowed for external corrosion'))
        return
    if raw_value not in DEFECT_LENGTH_BASES:
        issues.append(_issue('INVALID_SELECTION', header, 'is not an allowed selection'))
        return
    normalized[header] = raw_value


def _validate_repair_group_id(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    basis = normalized.get('Defect Length Basis')
    if basis == ENTER_MANUALLY:
        text = '' if raw_value is None else str(raw_value).strip()
        if not text:
            issues.append(_issue('REPAIR_GROUP_REQUIRED', header, 'a value is required for Enter manually'))
        else:
            normalized[header] = text
        return
    if _is_blank(raw_value):
        normalized[header] = None
    else:
        issues.append(_issue('REPAIR_GROUP_NOT_ALLOWED', header, 'is only allowed for Enter manually'))


def _validate_remaining_wall(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    if normalized.get('Defect Length Basis') == ENTER_MANUALLY:
        if _is_blank(raw_value):
            normalized[header] = None
        else:
            issues.append(_issue('REMAINING_WALL_NOT_ALLOWED', header, 'must be blank for Enter manually'))
        return
    if _is_blank(raw_value):
        issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
        return
    _validate_numeric_header(raw_value, header, normalized, issues)


def _validate_detail_number(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    if _is_blank(raw_value):
        issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
        return
    number = _finite_number(raw_value)
    if number is None:
        issues.append(_issue('INVALID_NUMBER', header, 'must be a finite number'))
        return
    if header == 'Individual longitudinal length [mm]' and number <= 0:
        issues.append(_issue('OUT_OF_RANGE', header, 'must be greater than zero'))
        return
    if header == 'Remaining wall [mm]' and number < 0:
        issues.append(_issue('OUT_OF_RANGE', header, 'must be zero or greater'))
        return
    normalized[header] = number


def _validate_numeric_header(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    if _is_blank(raw_value):
        if header in _REQUIRED_NUMERIC_HEADERS:
            issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
        return

    number = _finite_number(raw_value)
    if number is None:
        issues.append(_issue('INVALID_NUMBER', header, 'must be a finite number'))
        return

    if header in _POSITIVE_HEADERS and number <= 0:
        issues.append(_issue('OUT_OF_RANGE', header, 'must be greater than zero'))
        return
    if header in _NONNEGATIVE_HEADERS and number < 0:
        issues.append(_issue('OUT_OF_RANGE', header, 'must be zero or greater'))
        return
    if header == 'Design Life [years]':
        if number < 1 or not number.is_integer():
            issues.append(_issue('OUT_OF_RANGE', header, 'must be a whole number of at least one'))
            return
        normalized[header] = int(number)
        return
    if header == 'Design Factor' and not 0.10 <= number <= 1.00:
        issues.append(_issue('OUT_OF_RANGE', header, 'must be between 0.10 and 1.00'))
        return
    if header == 'Cyclic Derating Factor' and not 0 < number <= 1:
        issues.append(_issue('OUT_OF_RANGE', header, 'must be greater than zero and no more than one'))
        return
    if header == 'Remaining Wall [mm]':
        nominal_wall = normalized.get('Nominal Wall [mm]')
        if nominal_wall is not None and number > nominal_wall:
            issues.append(_issue('OUT_OF_RANGE', header, 'cannot exceed nominal wall'))
            return

    normalized[header] = number


def _validate_cloth_width(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    if _is_blank(raw_value):
        issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
        return
    number = _finite_number(raw_value)
    if number is None:
        issues.append(_issue('INVALID_NUMBER', header, 'must be a finite number'))
        return
    if number not in APPROVED_CLOTH_WIDTHS_MM:
        issues.append(_issue(
            'INVALID_SELECTION', header,
            'must be an approved 300 mm or 500 mm PROWRAP width',
        ))
        return
    normalized[header] = number


def _validate_internal_corrosion_rate(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    required = (
        normalized.get('Mechanism') == 'Corrosion'
        and normalized.get('Defect Location') == 'Internal'
    )
    if _is_blank(raw_value):
        if required:
            issues.append(_issue(
                'INTERNAL_CORROSION_RATE_REQUIRED', header,
                'is required for internal corrosion',
            ))
        else:
            normalized[header] = None
        return

    number = _finite_number(raw_value)
    if number is None:
        issues.append(_issue('INVALID_NUMBER', header, 'must be a finite number'))
    elif number < 0:
        issues.append(_issue('OUT_OF_RANGE', header, 'must be zero or greater'))
    else:
        normalized[header] = number


def _validate_axial_load_case(
    raw_value: Any,
    header: str,
    normalized: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    if _is_blank(raw_value):
        issues.append(_issue('REQUIRED_VALUE', header, 'a value is required'))
        return

    number = _finite_number(raw_value)
    if number is None or not number.is_integer() or int(number) not in (0, 1):
        issues.append(_issue('INVALID_SELECTION', header, 'is not an allowed selection'))
        return
    normalized[header] = int(number)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _is_formula(value: Any) -> bool:
    return isinstance(value, str) and value.lstrip().startswith('=')


def _issue(code: str, header: str, detail: str) -> ValidationIssue:
    return ValidationIssue(code=code, message=f'{header}: {detail}.')
