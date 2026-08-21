# Pinned CalcBatch v1.3 calculation-engine source

## Accepted single-case v1.3 source

CalcBatch v1.3 pins the reviewed standalone `Iso24817Calcv1.3` release commit
`da83373d648694f50b8a974ff6071a73ceec2089`. The accepted source-module
SHA-256 values are:

- `band_procurement.py`: `ba5d67eba3be6502e4d3ddbf475ca0189b7a9660ba9508429d77498de240e0bc`
- `prowrap_calculations.py`: `ea191add86766cd79fc5ec9f6e9deed8b950b1d66bd3318d89406c2846be9eca`
- `prowrap_materials.py`: `213064ff8d1a7d06646b3172b90caa79704f11742cef0ad58dbfc3ecd101320e`

The optimizer and material module are copied exactly. The calculation module
is integrated into the `engine` package with relative imports and retains the
documented CalcBatch-only high-temperature screening, zero-pressure Type B,
and strict axial-load validation paths. Both active procurement call sites use
the accepted `optimize_band_procurement` implementation; CalcBatch does not
contain a second optimizer. The resulting package-adapted
`engine/prowrap_calculations.py` SHA-256 is
`1ffbbd7397aab134aad6461a042b18342d5b46c1e86d658215e05a616d23bcfe`.

## Historical CalcBatch v1.2 provenance

**CalcBatch release version:** `1.2.0`
**Verified linked-corrosion source revision:** `91b68d64508a4786934f0e17f2aea0dbebf745a7` (`91b68d6` recorded in processed workbooks)

## Current CalcBatch v1.3 emitted provenance

CalcBatch v1.3 emits Batch Engine Version `1.3.0` and accepted single-case
Source Engine Revision `da83373` on every processed workbook Summary. The
complete accepted revision and current batch-module hashes are recorded in
`PROVENANCE.json`.

## Historical batch baseline (not the emitted source revision)

The original batch baseline was copied from
[`Prowrap110/Iso24817Calcv1.1`](https://github.com/Prowrap110/Iso24817Calcv1.1)
at released merge commit `746f3b3d65d73a2836962126e76f880919c51d0d`
on 2026-08-15. That release commit contains the reviewed dent-split feature
head `7ca0e66ab4f8334fe07fda54b64599f54b1a1256`; it remains the historical
origin for the non-corrosion batch behavior. It is not the source revision
emitted by CalcBatch v1.2 workbooks.

The copied modules are:

- `b31g.py`
- `iso24817_typea_class3.py`
- `prowrap_calculations.py`
- `prowrap_materials.py`
- `prowrap_mechanisms.py`

## Verified v1.2 corrosion-engine port

The external-corrosion assessment route was ported from the verified source revision
`91b68d64508a4786934f0e17f2aea0dbebf745a7` in the separate
`Iso24817Calcv1.2` checkout. The source files were `corrosion_defects.py` and
`prowrap_calculations.py`.

The batch engine retains the verified v1.2 defect-length bases: `Actual defect
length`, `Independent defects`, and `Enter manually`. It assesses every
candidate B31G length/remaining-wall pair independently, uses the least
creditable candidate as governing, and preserves the full entered repair-zone
length for ISO axial extent.

The following batch-only behaviors are intentionally retained rather than
replaced by the source module:

- `allow_unqualified_temperature=False` remains the engine default, with the
  batch adapter's high-temperature review-warning path unchanged.
- Zero-pressure Type B handling retains the batch three-ply review warning and
  the two-year service-life warning without dereferencing Formula 12 details.
- The 300 mm and 500 mm cloth-width configurations retain the batch 50 mm
  stitching-overlap procurement behavior.
- Existing dent mechanism routing and strict unsupported axial-load validation
  remain batch behavior; the v1.2 corrosion basis applies only to external
  corrosion.

Historical CalcBatch v1.2 workbooks emitted Batch Engine Version `1.2.0` and
Source Engine Revision `91b68d6`. Those identifiers are retained here only for
traceability and are not emitted by the current v1.3 product.

## Approved dent mechanism split

The former generic `Dent` engine route is split into two canonical mechanisms:

- `Dent w/crack` retains the conservative full-pressure laminate design and
  receives zero substrate pressure credit.
- Eligible external `Dent no-crack` repairs with at least 1 mm remaining wall
  use component-pipe load sharing:

  ```text
  S_allow = SMYS * Design Factor
  p_s = 2 * S_allow * t_remaining / OD
  p_composite = max(0, p_design - p_s)
  ```

Internal dents and external dents below 1 mm remaining wall retain the Type B
full-replacement route and zero substrate credit. B31G remains corrosion-only.
Legacy `Dent` aliasing is deliberately not an engine formula: the batch upload
boundary maps that exact legacy value conservatively to `Dent w/crack` before
the canonical mechanism reaches the engine.

## Approved batch material-basis change

The user-approved PRW110 material basis in this batch release is Tg = 110 degC.
It derives the general qualified design limit as Tg - 20 = 90 degC and the
Class 3 Type B limit for service longer than two years as Tg - 30 = 80 degC.
This batch release does not change or redeploy the separate v1.1 calculator.

## Intentional batch-only corrections

The following corrections were made only in this separate batch repository.
They do not modify the source repository or the existing v1.1 deployment.

- Strictly reject unsupported defect mechanisms, defect locations, and axial
  load cases before calculation.
- Safely handle a zero-design-pressure Type B case without dereferencing absent
  Formula 12 detail; retain the impact-qualified three-ply minimum and require
  engineering review.
- Use the configured PRW110 Type B two-year service-life limit consistently,
  including zero-pressure Type B warnings.
- Keep the copied engine strict by default for design temperatures above the
  qualified Prowrap limit.  The batch adapter alone opts into numeric
  screening outputs through `allow_unqualified_temperature=True`, adds an
  explicit qualification warning, and returns `REVIEW REQUIRED`; non-batch
  callers retain the strict input rejection.
- Treat both 300 mm and 500 mm Prowrap CF cloth widths as approved batch
  configurations while retaining the fixed 50 mm stitching overlap.
- Keep unexpected row failures isolated as `SYSTEM ERROR` results while
  recording bounded exception type and traceback-frame diagnostics in server
  logs without exposing those internals in the processed workbook.

All batch orchestration, workbook validation, warning-register handling,
status handling, and batch user-interface code is batch-repository-only. The
existing v1.1 repository, application, URL, and deployment remain outside this
release scope.
