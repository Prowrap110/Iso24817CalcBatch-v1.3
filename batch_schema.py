"""Canonical workbook contract for the PROWRAP batch calculator."""

from dataclasses import dataclass
from typing import Any


MAX_ROWS = 150
MAX_DETAIL_ROWS = 150
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
STITCH_OVERLAP_MM = 50.0
APPROVED_CLOTH_WIDTHS_MM = (300.0, 500.0)


LEGACY_INPUT_HEADERS = (
    'Pipe OD [mm]',
    'Nominal Wall [mm]',
    'Pipe Yield [MPa]',
    'Design Pressure [bar]',
    'Operating Temperature [degC]',
    'Mechanism',
    'Defect Location',
    'Defect Length [mm]',
    'Remaining Wall [mm]',
    'Internal Corrosion Rate [mm/year]',
    'Design Life [years]',
    'Design Factor',
    'Run Type A / Class 3 Check',
    'Installation Temperature [degC]',
    'Component Type',
    'Cyclic Derating Factor',
    'Axial Load Case',
    'Prowrap CF Cloth Width [mm]',
)


LEGACY_OUTPUT_HEADERS = (
    'Source Excel Row',
    'Calculation Status',
    'Error Code',
    'Error Message',
    'Compliance Warnings',
    'Batch Engine Version',
    'Source Engine Revision',
    'Processed At [UTC]',
    'Thickness Calculation Method',
    'Overlap Calculation Method',
    'Wall Loss [%]',
    'End-of-Life Remaining Wall [mm]',
    'No Substrate Capacity',
    'B31G Applicable',
    'B31G Acceptable',
    'Effective Pipe Capacity [bar]',
    'Composite Pressure Deficit [bar]',
    'Required Structural Thickness [mm]',
    'Installed Plies',
    'Installed Thickness [mm]',
    'Thin-Wall Thickness Check OK',
    'Type A / Class 3 Check Run',
    'Type A / Class 3 Controls',
    'Required Overlap [mm]',
    'Taper Length [mm]',
    'Total Repair Length [mm]',
    'Cloth Band Count',
    'Procurement Axial Length [mm]',
    'Fabric Area [m2]',
    'Epoxy Mass [kg]',
    'B31G Detail',
    'Type A Detail',
    'Type B Detail',
)


def _insert_after(
    headers: tuple[str, ...],
    existing_header: str,
    inserted_headers: tuple[str, ...],
) -> tuple[str, ...]:
    index = headers.index(existing_header) + 1
    return headers[:index] + inserted_headers + headers[index:]


INPUT_HEADERS = _insert_after(
    LEGACY_INPUT_HEADERS[:-1] + (
        'Prowrap CF Cloth Width 1 [mm]',
        'Prowrap CF Cloth Width 2 [mm]',
    ),
    'Defect Length [mm]',
    ('Defect Length Basis', 'Repair Group ID'),
)


HISTORICAL_V12_OUTPUT_HEADERS = LEGACY_OUTPUT_HEADERS + (
    'Repair Zone Length [mm]',
    '3t Interaction Threshold [mm]',
    'B31G Candidate Count',
    'Governing Defect ID',
    'Governing B31G Length [mm]',
    'Governing B31G Remaining Wall [mm]',
)


OUTPUT_HEADERS = (
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


DETAIL_INPUT_HEADERS = (
    'Repair Group ID',
    'Defect ID',
    'Individual longitudinal length [mm]',
    'Remaining wall [mm]',
    'Separation exceeds 3t',
)


DETAIL_OUTPUT_HEADERS = (
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

B31G_DETAIL_SCHEMA = 'Individual Defects'
B31G_DETAIL_SCHEMA_VERSION = '2'


@dataclass(frozen=True)
class BatchInfo:
    customer: str
    project_location: str
    report_no: str


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ValidatedRow:
    source_excel_row: int
    values: dict[str, Any]


@dataclass(frozen=True)
class ValidatedIndividualDefectRow:
    source_excel_row: int
    repair_group_id: str
    defect_id: str
    longitudinal_length_mm: float
    remaining_wall_mm: float
    separation_exceeds_3t: bool
