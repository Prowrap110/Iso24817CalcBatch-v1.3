"""Create the controlled six-row CalcBatch v1.3 acceptance source workbook."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import sys

from openpyxl import load_workbook


if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from batch_schema import DETAIL_INPUT_HEADERS, INPUT_HEADERS
from workbook_template import create_template_workbook


_COMMON_VALUES = {
    'Customer': 'Acceptance Customer',
    'Project Location': 'Acceptance Location',
    'Report No': 'ACCEPT-V13-001',
}

_BASE_ROW = {
    'Pipe OD [mm]': 457.2,
    'Nominal Wall [mm]': 9.53,
    'Pipe Yield [MPa]': 359.0,
    'Design Pressure [bar]': 50.0,
    'Operating Temperature [degC]': 40.0,
    'Mechanism': 'Corrosion',
    'Defect Location': 'External',
    'Defect Length [mm]': 300.0,
    'Defect Length Basis': 'Actual defect length',
    'Repair Group ID': None,
    'Remaining Wall [mm]': 4.5,
    'Internal Corrosion Rate [mm/year]': None,
    'Design Life [years]': 20,
    'Design Factor': 0.72,
    'Run Type A / Class 3 Check': 'No',
    'Installation Temperature [degC]': 20.0,
    'Component Type': 'Straight',
    'Cyclic Derating Factor': 1.0,
    'Axial Load Case': 0,
    'Prowrap CF Cloth Width 1 [mm]': 300.0,
    'Prowrap CF Cloth Width 2 [mm]': 300.0,
}


def create_acceptance_workbook(destination: str | Path) -> Path:
    """Write the fixed acceptance input workbook to the requested destination only."""
    path = Path(destination)
    workbook = load_workbook(BytesIO(create_template_workbook()))
    try:
        info = workbook['Batch Information']
        for row, label in enumerate(_COMMON_VALUES, start=3):
            info.cell(row, 2).value = _COMMON_VALUES[label]

        data = workbook['Batch Input & Results']
        for excel_row, values in enumerate(_acceptance_rows(), start=2):
            for column, header in enumerate(INPUT_HEADERS, start=1):
                data.cell(excel_row, column).value = values[header]

        detail = workbook['Individual Defects']
        for excel_row, values in enumerate(_acceptance_details(), start=2):
            for column, header in enumerate(DETAIL_INPUT_HEADERS, start=1):
                detail.cell(excel_row, column).value = values[header]
        workbook.save(path)
    finally:
        workbook.close()
    return path


def _acceptance_rows() -> tuple[dict[str, object], ...]:
    """Freeze width availability, row-error, and no-solution release cases."""
    return (
        {
            **_BASE_ROW,
        },
        {
            **_BASE_ROW,
            'Prowrap CF Cloth Width 1 [mm]': 500.0,
            'Prowrap CF Cloth Width 2 [mm]': 500.0,
        },
        {
            **_BASE_ROW,
            'Prowrap CF Cloth Width 2 [mm]': 500.0,
        },
        {
            **_BASE_ROW,
            'Prowrap CF Cloth Width 1 [mm]': 500.0,
        },
        {
            **_BASE_ROW,
            'Pipe OD [mm]': None,
            'Prowrap CF Cloth Width 2 [mm]': 500.0,
        },
        {
            **_BASE_ROW,
            'Mechanism': 'Leak',
            'Defect Length Basis': None,
            'Design Pressure [bar]': 150.0,
            'Prowrap CF Cloth Width 2 [mm]': 500.0,
        },
    )


def _acceptance_details() -> tuple[dict[str, object], ...]:
    return ()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Create the six-row PROWRAP CalcBatch v1.3 acceptance workbook.',
    )
    parser.add_argument('destination', type=Path, help='Path for the generated .xlsx workbook.')
    args = parser.parse_args()
    create_acceptance_workbook(args.destination)


if __name__ == '__main__':
    main()
