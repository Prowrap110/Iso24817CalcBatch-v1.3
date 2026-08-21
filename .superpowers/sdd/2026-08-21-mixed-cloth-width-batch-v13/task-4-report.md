# Task 4 Report: CalcBatch v1.3 release preparation

## Scope delivered

- Replaced active v1.2 app/workbook identity with `PROWRAP CalcBatch v1.3`, template `PROWRAP_CalcBatch_v1.3_Template.xlsx`, result prefix `PROWRAP_CalcBatch_v1.3_Results_`, Batch Engine `1.3.0`, and accepted source revision `da83373`.
- Added current-v1.3-only app, workbook, README, and deployment guidance.
- Replaced the historical acceptance generator with six frozen v1.3 scenarios: 300-only, 500-only, mixed, reversed mixed, input error, and not repairable.
- Reconciled literal structural invariance, 500/300 counts, gross procurement, effective coverage, fabric area, epoxy, W/X/Z formulas, Quantity Y, warnings, Summary, protections, `AE151`/`X151`/`Z11` tables, 150-row validation limits, and processed re-upload.
- Added exact future instructions for new public repository `Prowrap110/Iso24817CalcBatch-v1.3` and new Streamlit app `iso24817calcbatch-prowrapv13`, while explicitly holding deployment.
- Added `PROVENANCE.json` with exact accepted single-case source, batch source identities, and recomputed current module hashes.
- Added `docs/superpowers/reports/2026-08-21-calcbatch-v13-verification.md`.

## TDD and verification evidence

- Required RED: `6 failed, 8 passed`.
- Required focused GREEN: `14 passed in 11.46s`.
- Identity/provenance/warning gate: `31 passed in 1.59s`; JSON parsing, source compilation, and `git diff --check` clean.
- Full suite: `324 passed in 74.43s`.
- Temporary production-path verification: zero template/input formulas; 18 exact processed W/X/Z formulas; exact table/protection/validation/status/output/warning identities; re-upload parity with assumptions and Quantity preserved.
- Temporary rendering: template and result each rendered to exactly eight pages; required content was extractable for every sheet and all eight processed pages were visually inspected.

## Release boundary retained

No final artifact marker was run. No final template, acceptance, or result workbook was created in a release output location. No v1.2 file/repository/app was modified. No remote was added or contacted; no GitHub repository, push, PR, Streamlit app, deployment, reboot, or URL change was performed.

## Concern / controller handoff

The wide main/detail/Cost tables are necessarily compressed in one-page temporary LibreOffice print previews. The controller's dedicated spreadsheet artifact workflow must perform the final authoritative workbook rendering and artifact generation after review. Publication and deployment remain separately authorized future actions.
