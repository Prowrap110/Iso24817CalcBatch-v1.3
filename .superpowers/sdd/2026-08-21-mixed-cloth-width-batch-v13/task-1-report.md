# Task 1 Report: Accepted v1.3 engine and dual-width row contract

## Scope delivered

- Pinned accepted standalone source revision
  `da83373d648694f50b8a974ff6071a73ceec2089` in `ENGINE_SOURCE.md`.
- Copied `band_procurement.py` and `prowrap_materials.py` byte-for-byte from
  that revision. The accepted SHA-256 values are
  `ba5d67eba3be6502e4d3ddbf475ca0189b7a9660ba9508429d77498de240e0bc`
  and `213064ff8d1a7d06646b3172b90caa79704f11742cef0ad58dbfc3ecd101320e`.
- Integrated the accepted optimizer into both active procurement call sites
  in the package-adapted calculation engine, retaining the documented
  CalcBatch-only high-temperature, zero-pressure Type B, and strict axial-load
  safety paths. No second optimizer was implemented.
- Replaced the singular public row fields with exactly 21 inputs and 10
  outputs, including two width selections and separate 500/300 band counts.
- Required each width input to be exactly 300 or 500 mm. Duplicate pairs
  restrict procurement to one width; mixed and reversed pairs are accepted.
- Passed both widths through baseline and controlling Class 3 adapter paths,
  removed the obsolete unapproved-width review-warning route, and mapped
  `num_bands_500` / `num_bands_300` to the public outputs.
- Kept all structural results and classification independent of width
  availability and blanked both count outputs with the other installable
  quantities for `NOT REPAIRABLE` rows.
- Preserved the 150 main-row and 150 detail-row limits.

## TDD evidence

Required focused RED command, before production edits:

```text
python3 -m pytest -q tests/test_batch_schema.py tests/test_batch_validation.py tests/test_batch_adapter.py tests/test_engine_snapshot_v13.py
```

RED result: `58 failed, 16 passed`. Failures named the missing 21/10 schema,
missing dual-width validation and adapter mapping, missing accepted optimizer
snapshot, and absent v1.3 provenance.

The same focused command after implementation returned:

```text
74 passed in 0.45s
```

## Engine and broader verification

Batch engine regression command:

```text
python3 -m pytest -q tests/engine tests/test_engine_batch_hardening.py tests/test_engine_corrosion_v12.py tests/test_engine_snapshot_v13.py
```

Result: `78 passed in 0.46s`.

The accepted standalone source repository was also verified read-only at exact
commit `da83373`:

```text
python3 -m pytest -q
202 passed in 4.22s
```

The current CalcBatch repository-wide command returned `188 passed, 145
failed`. The failures are confined to intentionally unimplemented Tasks 2-4
surfaces that still consume the singular v1.2 workbook/app/cost contract. The
first root failure is `workbook_template.py` lacking header metadata for
`Prowrap CF Cloth Width 1 [mm]`; those surfaces were left untouched as
required by this Task 1 boundary.

`git diff --check` completed cleanly.

## Self-review

- The accepted optimizer file is byte-identical and its hash is asserted.
- The material file is byte-identical; accepted source hashes for all three
  named modules and the active package-adapted calculation hash are recorded.
- Both engine procurement call sites use `optimize_band_procurement` only
  after continuous ISO repair length is fixed.
- Width order is normalized only inside procurement; structural inputs and
  structural outputs are unchanged.
- Validation rejects blank, 250, boolean, and nonnumeric width values before
  engine invocation.
- Public output order and installable-output blanking cover both new count
  fields.
- No v1.2 repository, remote, deployment, app, workbook template, processor,
  cost sheet, or final XLSX artifact was modified.

## Concern for subsequent tasks

The repository is deliberately between contracts after Task 1: workbook,
Cost, app, and acceptance tests remain red until Tasks 2-4 migrate those
consumers. Task 2 should begin with the current schema rather than attempting
historical workbook compatibility.
