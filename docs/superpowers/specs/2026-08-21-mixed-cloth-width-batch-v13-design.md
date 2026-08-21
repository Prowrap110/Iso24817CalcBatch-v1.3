# PROWRAP CalcBatch v1.3 Mixed Cloth Width Design

## Purpose and source

Create a new CalcBatch v1.3 repository and Streamlit app from reviewed CalcBatch v1.2 commit `5b916df79c6e24462c4cd9194ce8938fafcb70e3`. CalcBatch v1.3 pins the exact accepted ISO24817Calc v1.3 engine revision and never implements a second optimizer.

CalcBatch v1.2 remains unchanged. Only current v1.3 templates and processed workbooks are supported.

## Workbook contract

Replace `Prowrap CF Cloth Width [mm]` with required inputs:

- `Prowrap CF Cloth Width 1 [mm]`
- `Prowrap CF Cloth Width 2 [mm]`

Each uses list validation containing exactly 300 and 500. Duplicate values restrict procurement to that width.

Replace `Cloth Band Count` with outputs:

- `500 mm Cloth Band Count`
- `300 mm Cloth Band Count`

Keep `Procurement Axial Length [mm]` unchanged. The output is `500*n500 + 300*n300` and covered length is that total minus 50 mm for every inter-band joint.

The main sheet has 21 inputs and 10 outputs in `A1:AE151`. `Individual Defects` remains `A1:X151` and all 150-row limits remain.

## Output order

1. Wall Loss [%]
2. Required Structural Thickness [mm]
3. Installed Plies
4. Total Repair Length [mm]
5. 500 mm Cloth Band Count
6. 300 mm Cloth Band Count
7. Procurement Axial Length [mm]
8. Fabric Area [m2]
9. Epoxy Mass [kg]
10. Repair Zone Length [mm]

## Cost Calculation

The Cost source mapping has 22 fields and the table spans `A:Z`:

- `L/M`: width inputs
- `R/S`: 500/300 band counts
- `T`: Procurement Axial Length
- `U`: Fabric Area
- `V`: Epoxy Mass
- `W`: Cost
- `X`: Price
- `Y`: Quantity
- `Z`: Total Amount

Controlled formulas are:

```excel
W6 =IF(OR($B$3="",$E$3="",U6="",V6=""),"",U6*$B$3+V6*$E$3)
X6 =IF(OR(W6="",$H$3=""),"",W6*$H$3)
Z6 =IF(OR(X6="",Y6=""),"",X6*Y6)
```

Quantity is editable in `Y6:Y155`. Formulas, column indexes, validation, protection, and table ranges must be derived from semantic headers wherever practical.

## Invariants and release

Width availability must not change structural calculations, ISO repair length, status, or warning classification. `NOT REPAIRABLE` rows have both count fields and installable quantities blank. Processed-workbook re-upload preserves commercial assumptions and Quantity while regenerating engineering results and controlled formulas.

The repository is `Prowrap110/Iso24817CalcBatch-v1.3` and deploys to a new Streamlit app. It does not alter the v1.2 repo, branch, template, results, or app.
