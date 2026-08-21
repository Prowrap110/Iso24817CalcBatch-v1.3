import cost_calculation

from cost_calculation import (
    COST_FIRST_DATA_ROW,
    COST_LAST_DATA_ROW,
    COST_SOURCE_HEADERS,
    COST_TABLE_HEADERS,
    cost_formula,
    is_allowed_cost_formula,
    price_formula,
)


def test_cost_source_headers_survive_inserted_v12_columns():
    assert COST_SOURCE_HEADERS == (
        'Pipe OD [mm]', 'Nominal Wall [mm]', 'Pipe Yield [MPa]',
        'Design Pressure [bar]', 'Operating Temperature [degC]',
        'Mechanism', 'Defect Location', 'Defect Length [mm]',
        'Remaining Wall [mm]', 'Design Life [years]', 'Design Factor',
        'Prowrap CF Cloth Width 1 [mm]',
        'Prowrap CF Cloth Width 2 [mm]', 'Wall Loss [%]',
        'Required Structural Thickness [mm]', 'Installed Plies',
        'Total Repair Length [mm]', '500 mm Cloth Band Count',
        '300 mm Cloth Band Count',
        'Procurement Axial Length [mm]', 'Fabric Area [m2]',
        'Epoxy Mass [kg]',
    )
    assert len(COST_SOURCE_HEADERS) == 22
    assert COST_TABLE_HEADERS == COST_SOURCE_HEADERS + (
        'Cost', 'Price', 'Quantity', 'Total Amount',
    )


def test_cost_formulas_use_absolute_inputs_and_relative_rows():
    assert cost_formula(COST_FIRST_DATA_ROW) == (
        '=IF(OR($B$3="",$E$3="",U6="",V6=""),"",'
        'U6*$B$3+V6*$E$3)'
    )
    assert price_formula(COST_FIRST_DATA_ROW) == (
        '=IF(OR(W6="",$H$3=""),"",W6*$H$3)'
    )
    assert hasattr(cost_calculation, 'total_amount_formula')
    assert cost_calculation.total_amount_formula(COST_FIRST_DATA_ROW) == (
        '=IF(OR(X6="",Y6=""),"",X6*Y6)'
    )
    assert cost_formula(COST_LAST_DATA_ROW) == (
        '=IF(OR($B$3="",$E$3="",U155="",V155=""),"",'
        'U155*$B$3+V155*$E$3)'
    )
    assert price_formula(COST_LAST_DATA_ROW) == (
        '=IF(OR(W155="",$H$3=""),"",W155*$H$3)'
    )
    assert cost_calculation.total_amount_formula(COST_LAST_DATA_ROW) == (
        '=IF(OR(X155="",Y155=""),"",X155*Y155)'
    )


class _FormulaCell:
    def __init__(self, row, column, value):
        self.row = row
        self.column = column
        self.value = value


def test_only_exact_controlled_cost_formulas_are_allowed():
    assert is_allowed_cost_formula(_FormulaCell(6, 23, cost_formula(6))) is True
    assert is_allowed_cost_formula(_FormulaCell(6, 24, price_formula(6))) is True
    assert is_allowed_cost_formula(
        _FormulaCell(6, 26, cost_calculation.total_amount_formula(6)),
    ) is True
    assert is_allowed_cost_formula(_FormulaCell(6, 25, '=1+1')) is False
    assert is_allowed_cost_formula(_FormulaCell(6, 23, '=1+1')) is False
    assert is_allowed_cost_formula(_FormulaCell(5, 23, cost_formula(5))) is False
    assert is_allowed_cost_formula(
        _FormulaCell(COST_LAST_DATA_ROW + 1, 24, price_formula(COST_LAST_DATA_ROW + 1)),
    ) is False
