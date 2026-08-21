# PROWRAP CalcBatch v1.3 Mixed Cloth Width Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build isolated CalcBatch v1.3 with two cloth-width inputs, separate 500/300 band counts, optimized procurement, and unchanged structural calculations.

**Architecture:** Pin and copy the accepted single-case v1.3 engine, then expose its result through one controlled workbook schema. Workbook generation, processing, cost formulas, re-upload, and Streamlit all use semantic headers rather than a parallel optimization implementation.

**Tech Stack:** Python 3.11, Streamlit, openpyxl controlled workbook generation/processing, pytest, artifact-tool for final workbook inspection.

**Spec:** `docs/superpowers/specs/2026-08-21-mixed-cloth-width-batch-v13-design.md`

## Global Constraints

- Source baseline is exactly `5b916df79c6e24462c4cd9194ce8938fafcb70e3`.
- Never modify or push to CalcBatch v1.2 or its Streamlit app.
- Pin the exact accepted single-case v1.3 engine; do not duplicate the optimizer in batch code.
- Accept only v1.3 template/result contracts; historical workbook upgrades are out of scope.
- Main and Individual Defects permit exactly 150 populated rows.
- Procurement heading stays `Procurement Axial Length [mm]`.
- Width choices must not change structural results, ISO repair length, statuses, or warnings.
- Use TDD for every production change.

---

### Task 1: Pin the accepted v1.3 engine and expose dual-width row results

**Files:**
- Create: `engine/band_procurement.py`
- Modify: `engine/prowrap_calculations.py`
- Modify: `engine/prowrap_materials.py`
- Modify: `batch_schema.py`
- Modify: `batch_validation.py`
- Modify: `batch_adapter.py`
- Modify: `ENGINE_SOURCE.md`
- Modify: `tests/test_batch_schema.py`
- Modify: `tests/test_batch_validation.py`
- Modify: `tests/test_batch_adapter.py`
- Create: `tests/test_engine_snapshot_v13.py`

**Interfaces:**
- Consumes: exact accepted single-case v1.3 engine files and provenance SHA.
- Produces: 21 input headers, 10 output headers, and mapped `num_bands_500`/`num_bands_300` results.

- [ ] **Step 1: Copy the accepted engine snapshot and write failing contract tests**

Tests assert byte/hash provenance, exact two width inputs, exact two count outputs, accepted combinations `300/300`, `500/500`, `300/500`, `500/300`, rejected blank/250/bool/nonnumeric inputs, structural invariance, and blank installable outputs for `NOT REPAIRABLE`.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/test_batch_schema.py tests/test_batch_validation.py tests/test_batch_adapter.py tests/test_engine_snapshot_v13.py`

- [ ] **Step 3: Implement schema, validation, adapter, and provenance**

Replace the singular width/count fields, pass both widths to the engine, map separate counts, and remove the obsolete unapproved-width warning path.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command and engine tests; expect zero failures.

- [ ] **Step 5: Commit**

Commit message: `feat: pin mixed-width v1.3 calculation engine`

### Task 2: Generate the 21-input/10-output controlled workbook

**Files:**
- Modify: `workbook_template.py`
- Modify: `workbook_processor.py`
- Modify: `tests/test_workbook_template.py`
- Modify: `tests/test_workbook_processor.py`

**Interfaces:**
- Consumes: Task 1 semantic input/output headers.
- Produces: main table `A1:AE151`, two validated width cells per row, protected outputs, and safe processed re-upload.

- [ ] **Step 1: Write failing template and processor tests**

Assert exact headers/order, `A1:AE151`, dropdown validation through row 151, protected two-count outputs, exactly 150 valid rows, row 152 rejection, width-order invariance, structural-output invariance, and re-upload equality.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/test_workbook_template.py tests/test_workbook_processor.py`

- [ ] **Step 3: Update template and processor semantically**

Use header lookup for copying and output writing. Accept only current v1.3 contracts. Preserve formulas only where explicitly allowed on Cost Calculation.

- [ ] **Step 4: Run focused workbook tests**

Run the Step 2 command; expect zero failures.

- [ ] **Step 5: Commit**

Commit message: `feat: add mixed-width batch workbook contract`

### Task 3: Shift Cost Calculation to A:Z safely

**Files:**
- Modify: `cost_calculation.py`
- Modify: `workbook_template.py`
- Modify: `workbook_processor.py`
- Modify: `tests/test_cost_calculation.py`
- Modify: `tests/test_workbook_processor.py`

**Interfaces:**
- Consumes: Task 1 22-field semantic Cost source mapping.
- Produces: formulas in W/X/Z and editable Quantity in Y.

- [ ] **Step 1: Write failing cost and formula-trust tests**

Assert exact 22 source fields, A:Z table range, the literal W/X/Z formulas, `Y6:Y155` input validation/unlocked cells, assumptions preservation, altered-formula rejection, and re-upload restoration.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/test_cost_calculation.py tests/test_workbook_processor.py -k 'cost or quantity or formula'`

- [ ] **Step 3: Implement semantic Cost positions**

Move Cost/Price/Quantity/Total Amount to W/X/Y/Z, update the formula allow-list and protection, and remove stale U/V/W/X numeric assumptions.

- [ ] **Step 4: Run focused Cost and processor tests**

Run the Step 2 command; expect zero failures.

- [ ] **Step 5: Commit**

Commit message: `feat: price optimized mixed-width repairs`

### Task 4: v1.3 app, acceptance workbook, documentation, and release evidence

**Files:**
- Modify: `app.py`
- Modify: `scripts/create_acceptance_workbook.py`
- Modify: `README.md`
- Modify: `DEPLOYMENT.md`
- Modify: `tests/test_app_smoke.py`
- Modify: `tests/test_full_batch_acceptance.py`
- Create: `docs/superpowers/reports/2026-08-21-calcbatch-v13-verification.md`
- Create: `PROVENANCE.json`

**Interfaces:**
- Consumes: Tasks 1-3 finalized workbook and engine contracts.
- Produces: v1.3 template/result filenames, six-row acceptance, documentation, and deployable app.

- [ ] **Step 1: Write failing app and acceptance tests**

Assert v1.3 title, template/result names, 21/10 header summaries, six scenarios including 300-only, 500-only, mixed, reversed mixed, input error, and not-repairable; reconcile counts, procurement, area, epoxy, Cost formulas, warnings, protections, 150-row limits, and re-upload parity.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/test_app_smoke.py tests/test_full_batch_acceptance.py`

- [ ] **Step 3: Implement identity, generator, docs, and provenance**

Use `PROWRAP_CalcBatch_v1.3_Template.xlsx`, result prefix `PROWRAP_CalcBatch_v1.3_Results_`, Batch Engine `1.3.0`, and new isolated deployment instructions.

- [ ] **Step 4: Verify the full release candidate**

Run: `python3 -m pytest -q`.

Generate a controlled template and processed six-row result through production paths. Inspect formulas, values, protections, table ranges, all eight rendered sheets, and processed-workbook re-upload.

- [ ] **Step 5: Commit**

Commit message: `chore: prepare CalcBatch v1.3 release`
