"""Controlled commercial worksheet contract for PROWRAP batch workbooks."""

from batch_schema import MAX_ROWS
from openpyxl.utils import get_column_letter


COST_INPUTS = (
    ('B3', 'CF Cost / m2'),
    ('E3', 'Epoxy Cost / kg'),
    ('H3', 'Price Multiplier'),
)

# These are semantic source names, deliberately independent of the insertion
# points in the main input and output schemas.
COST_SOURCE_HEADERS = (
    'Pipe OD [mm]',
    'Nominal Wall [mm]',
    'Pipe Yield [MPa]',
    'Design Pressure [bar]',
    'Operating Temperature [degC]',
    'Mechanism',
    'Defect Location',
    'Defect Length [mm]',
    'Remaining Wall [mm]',
    'Design Life [years]',
    'Design Factor',
    'Prowrap CF Cloth Width 1 [mm]',
    'Prowrap CF Cloth Width 2 [mm]',
    'Wall Loss [%]',
    'Required Structural Thickness [mm]',
    'Installed Plies',
    'Total Repair Length [mm]',
    '500 mm Cloth Band Count',
    '300 mm Cloth Band Count',
    'Procurement Axial Length [mm]',
    'Fabric Area [m2]',
    'Epoxy Mass [kg]',
)
COST_TABLE_HEADERS = COST_SOURCE_HEADERS + ('Cost', 'Price', 'Quantity', 'Total Amount')

COST_TABLE_HEADER_ROW = 5
COST_FIRST_DATA_ROW = 6
COST_LAST_DATA_ROW = COST_FIRST_DATA_ROW + MAX_ROWS - 1


def _column_index(header: str) -> int:
    return COST_TABLE_HEADERS.index(header) + 1


def _column_letter(header: str) -> str:
    return get_column_letter(_column_index(header))


def cost_formula(row: int) -> str:
    """Return the exact controlled material-cost formula for ``row``."""
    fabric = _column_letter('Fabric Area [m2]')
    epoxy = _column_letter('Epoxy Mass [kg]')
    return (
        f'=IF(OR($B$3="",$E$3="",{fabric}{row}="",{epoxy}{row}=""),"",'
        f'{fabric}{row}*$B$3+{epoxy}{row}*$E$3)'
    )


def price_formula(row: int) -> str:
    """Return the exact controlled price formula for ``row``."""
    cost = _column_letter('Cost')
    return f'=IF(OR({cost}{row}="",$H$3=""),"",{cost}{row}*$H$3)'


def total_amount_formula(row: int) -> str:
    """Return the exact controlled quantity-based total formula for ``row``."""
    price = _column_letter('Price')
    quantity = _column_letter('Quantity')
    return (
        f'=IF(OR({price}{row}="",{quantity}{row}=""),"",'
        f'{price}{row}*{quantity}{row})'
    )


def is_allowed_cost_formula(cell) -> bool:
    """Return whether ``cell`` contains an exact app-generated cost formula."""
    if not (COST_FIRST_DATA_ROW <= cell.row <= COST_LAST_DATA_ROW):
        return False
    formula_for_column = {
        _column_index('Cost'): cost_formula,
        _column_index('Price'): price_formula,
        _column_index('Total Amount'): total_amount_formula,
    }.get(cell.column)
    return (
        formula_for_column is not None
        and cell.value == formula_for_column(cell.row)
    )
