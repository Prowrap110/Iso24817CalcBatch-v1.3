# PROWRAP CalcBatch v1.3

PROWRAP CalcBatch v1.3 is a separate Excel batch calculator for preliminary PROWRAP repair screening. It accepts up to 150 continuous-repair rows and 150 linked individual-defect rows, then returns a controlled results workbook beside the preserved inputs.

This repository, workbook contract, deployment, and future public URL are isolated from CalcBatch v1.2 and the single-case PROWRAP calculators. They must never replace, redirect, modify, or deploy over an earlier application.

## Run locally

Use Python 3.11, install the application dependencies, and start Streamlit:

```bash
python3 -m pip install -r requirements-dev.txt
streamlit run app.py
```

## Current v1.3 workbook contract

1. Download `PROWRAP_CalcBatch_v1.3_Template.xlsx` from the v1.3 app.
2. Enter Customer, Project Location, and Report No once on **Batch Information**.
3. Enter one continuous repair zone per row on **Batch Input & Results**. Do not add, remove, rename, or reorder columns.
4. Select both required width inputs: **Prowrap CF Cloth Width 1 [mm]** and **Prowrap CF Cloth Width 2 [mm]**. Each accepts exactly 300 or 500. Duplicate choices restrict procurement to one width; different choices make both widths available to the accepted optimizer.
5. For external corrosion, use **Actual defect length**, **Independent defects**, or **Enter manually**. Manual groups use one unique Repair Group ID on the main row and matching rows on **Individual Defects**; leave the main Remaining Wall blank in that mode.
6. Upload the `.xlsx`, review the validation preview, calculate, and download a file whose name starts with `PROWRAP_CalcBatch_v1.3_Results_`.
7. On **Cost Calculation**, the highlighted assumptions are `B3` for CF Cost / m2, `E3` for Epoxy Cost / kg, and `H3` for Price Multiplier. **Quantity** is editable in `Y6:Y155` as blank or a non-negative number.

Only the current v1.3 template and current v1.3 processed workbooks are supported. Historical templates and workbook upgrades are outside this release contract; start again from the current template.

The main table has exactly 21 controlled inputs and 10 controlled outputs in `A1:AE151`. The outputs, in order, are **Wall Loss [%]**, **Required Structural Thickness [mm]**, **Installed Plies**, **Total Repair Length [mm]**, **500 mm Cloth Band Count**, **300 mm Cloth Band Count**, **Procurement Axial Length [mm]**, **Fabric Area [m2]**, **Epoxy Mass [kg]**, and **Repair Zone Length [mm]**. The **Individual Defects** table remains `A1:X151`.

Procurement is optimized only after the structural repair length is fixed. `Procurement Axial Length [mm]` equals `500 x 500 mm count + 300 x 300 mm count`; effective covered length subtracts 50 mm for every joint between adjacent bands. Width availability must not change wall loss, required structural thickness, installed plies, ISO repair length, repair-zone length, status, or warnings. `NOT REPAIRABLE` rows have both band counts and all other installable quantities blank.

The **Cost Calculation** projection has 22 engineering fields in `A:V`, followed by controlled **Cost** in `W`, **Price** in `X`, editable **Quantity** in `Y`, and controlled **Total Amount** in `Z`. Cost is `Fabric Area x CF Cost / m2 + Epoxy Mass x Epoxy Cost / kg`; Price is `Cost x Price Multiplier`; Total Amount is `Price x Quantity`. Processed-workbook re-upload retains valid commercial assumptions and Quantity while rebuilding engineering results, warnings, protections, and the exact controlled formulas.

The **Warnings** worksheet consolidates permanent warning codes, meanings, actions, and affected source rows. The **Summary** sheet records Batch Engine Version `1.3.0` and accepted source revision `da83373`.

## Engineering boundaries

**Dent w/crack** uses the conservative full-pressure laminate basis with no substrate pressure credit. An eligible external **Dent no-crack** with at least 1 mm remaining wall may use component-pipe substrate load sharing. Internal dents and external dents below 1 mm remaining wall remain on the Type B full-replacement route. Dent depth, local strain, ovalization, fatigue, gouge, and weld interaction are outside this calculator and require competent engineering review.

The approved material basis is Tg = 110 degC, giving a general qualified design-temperature limit of 90 degC and a long-life Class 3 Type B limit of 80 degC. These outputs are preliminary screening results, not installation approval or certification.

## Statuses

- `OK` — a valid screening result with no review warning.
- `REVIEW REQUIRED` — a result exists, but engineering or product approval is needed.
- `NOT REPAIRABLE` — the Type B Formula 12 route has no repair solution; installable quantities are blank.
- `INPUT ERROR` — correct the main or linked Individual Defects row and recalculate.
- `SYSTEM ERROR` — retain the workbook and contact PROTAP.

## Privacy and file handling

The app processes one controlled `.xlsx` workbook at a time, up to 10 MB, in the active Streamlit session or temporary processing memory. It does not create a calculation database or retain customer workbooks. Macros, password-protected files, uncontrolled formulas, and altered controlled formulas are rejected.

## Verify

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 scripts/create_acceptance_workbook.py /tmp/PROWRAP_CalcBatch_v1.3_Acceptance_Input.xlsx
```

The six-row acceptance workbook covers 300-only, 500-only, mixed, and reversed mixed width availability with identical engineering inputs, followed by one localized input error and one not-repairable case. It reconciles structural invariance, literal 500/300 band counts, procurement, effective coverage, fabric area, epoxy mass, W/X/Z formulas, Quantity Y, warnings, Summary identity, protection, table limits, and processed-workbook re-upload parity.

Batch release version is `1.3.0`; the accepted single-case source is `da83373d648694f50b8a974ff6071a73ceec2089`. Full source and module hashes are recorded in `PROVENANCE.json`.
