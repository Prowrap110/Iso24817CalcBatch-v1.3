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

## Implementation release boundary retained

The Task 4 implementation itself did not run the final artifact marker or
create final workbooks in a release output location. No v1.2
file/repository/app was modified. No remote was added or contacted; no GitHub
repository, push, PR, Streamlit app, deployment, reboot, or URL change was
performed.

## Pre-artifact controller handoff (completed)

The wide main/detail/Cost tables were necessarily compressed in one-page
temporary LibreOffice print previews. The controller's dedicated spreadsheet
artifact workflow was therefore required for authoritative final workbook
rendering and generation; that workflow is now complete as recorded below.
Publication and deployment remain separately authorized future actions.

## Final artifact-review fix: clipped Cost/Quantity instruction

The controller's artifact-tool render found that Instructions row 11 clipped
the last line of instruction 9 into row 12 in both generated workbooks. The
fix was limited to that row height; no wording, formula, workbook structure,
or other row height changed.

- RED: the new blank-template and production acceptance assertions both failed
  at the observed `32 pt` height (`2 failed`).
- Implementation: Instructions row 11 now uses `64 pt`; row 12 remains `32 pt`.
- Focused GREEN with provenance recomputation: `3 passed in 1.67s`.
- Affected template/acceptance/provenance files: `28 passed in 7.18s`.
- Fresh full suite: `325 passed in 78.29s`.
- Temporary template and processed workbooks were generated through production
  paths. Focused `Instructions!A9:A13` render copies each produced a one-page
  PDF. Visual inspection showed all three lines of instruction 9 with clear
  space before instruction 10 in both renders.

`PROVENANCE.json` now records the refreshed `workbook_template.py` SHA-256
`fd04e0f8d8d77dadca14a38b7af4b0288ee5e2523dd79c50c06ee1f9623ef0b9`.
During this review fix, the final artifact marker was not rerun and final
workbook files were not touched. No remote, deployment, v1.2 source, or public
resource was changed.

## Controller final artifact evidence

The controller subsequently regenerated the authoritative final workbooks from
artifact-review fix commit `c00e02d1c362571a96f7c54221c9fac83193647a` at
fixed UTC `2026-08-21T12:00:00Z`, without rerunning the artifact marker:

- `PROWRAP_CalcBatch_v1.3_Acceptance_Input.xlsx` — 51,305 bytes — SHA-256
  `9f5059d259057257fe401ed9b04bd494e8ced0ad26959d1331efed98702a02bf`.
- `PROWRAP_CalcBatch_v1.3_Acceptance_Processed.xlsx` — 53,876 bytes — SHA-256
  `7144158686cd3e67774df5fb80e79c0a4997c974205f355ed6e158241cbac53c`.

Final read-only inspection confirmed the exact eight sheets and hidden Lists,
zero input formulas, exactly 18 processed W/X/Z formulas in rows 6–11, no
formula-error matches, exact `A1:AE151` / `A1:X151` / `A5:Z11` table-filter
pairs, correct protection and unlocked input/commercial/Quantity cells,
`4 OK` / `1 INPUT ERROR` / `1 NOT REPAIRABLE`, literal mixed-width
procurement/material outputs, Summary `1.3.0` / `da83373`, re-upload parity
with only the designed B7 filename refresh, and Instructions row 11 at
`64 pt`.

Artifact-tool rendered all eight sheets in both final workbooks. All 16 renders
were visually reviewed and found clean. The final full regression suite passed
`325` tests. The workbook artifact workflow is complete; public repository and
Streamlit publication remain outside this task.
