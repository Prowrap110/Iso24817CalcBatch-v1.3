# CalcBatch v1.3 release-candidate verification

## Scope and release boundary

This verification covers the isolated CalcBatch v1.3 checkout created from exact Task 4 base `420a40dc84e9f787ff24c0862ec9307729b929d2`. It prepares source, tests, documentation, and provenance for a future release. It does not create or push a GitHub repository, add a remote, create or reboot a Streamlit application, deploy a public service, modify CalcBatch v1.2, run the spreadsheet artifact marker, or create the final release workbooks.

The prepared identity is:

- Product: `PROWRAP CalcBatch v1.3`
- Template: `PROWRAP_CalcBatch_v1.3_Template.xlsx`
- Result prefix: `PROWRAP_CalcBatch_v1.3_Results_`
- Batch Engine: `1.3.0`
- Accepted source: `da83373d648694f50b8a974ff6071a73ceec2089` (`da83373` in processed Summary)
- Future repository: `Prowrap110/Iso24817CalcBatch-v1.3`
- Future branch: `release/v1.3.0`
- Future Streamlit app: `iso24817calcbatch-prowrapv13`
- Future URL: `https://iso24817calcbatch-prowrapv13.streamlit.app`

Only current v1.3 template/result contracts are documented as supported.

## TDD evidence

Task 4 app and acceptance tests were changed before production. The required focused command was observed RED:

```text
python3 -m pytest -q tests/test_app_smoke.py tests/test_full_batch_acceptance.py
6 failed, 8 passed in 11.57s
```

The failures named the stale v1.2 title/template/result prefix, absent 21/10 mixed-procurement guidance, stale documentation/deployment identity, and the singular-width acceptance generator.

After the minimal release implementation, the first GREEN attempt had one meaningful fixture failure: the new generator still retained the old high-pressure comparison baseline, so the first four rows were correctly `REVIEW REQUIRED`. The generator alone was corrected to the independently frozen 457.2 mm / 50 bar case. The literal acceptance expectations were not changed.

The required focused command then passed:

```text
14 passed in 11.46s
```

## Automated verification

The identity, engine snapshot, warning, JSON, source-compilation, and diff gate passed:

```text
python3 -m pytest -q tests/test_engine_snapshot.py tests/test_engine_snapshot_v13.py tests/test_warning_catalog.py
31 passed in 1.59s

python3 -m json.tool PROVENANCE.json
python3 -m py_compile app.py scripts/create_acceptance_workbook.py workbook_template.py workbook_processor.py
git diff --check
```

The fresh full suite passed:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
324 passed in 74.43s
```

## Six-row acceptance reconciliation

The production generator creates six main rows in this order:

1. 300-only (`300/300`)
2. 500-only (`500/500`)
3. Mixed (`300/500`)
4. Reversed mixed (`500/300`)
5. Deliberate localized input error
6. Deliberate Type B Formula 12 not-repairable case

The first four use identical structural inputs. Their shared outputs are wall loss `52.7806925498426 %`, required structural thickness `2.0 mm`, installed plies `3`, total repair length `588.933816016055 mm`, and repair-zone length `300 mm`.

| Width availability | 500 count | 300 count | Procurement (mm) | Effective coverage (mm) | Fabric area (m2) | Epoxy (kg) |
|---|---:|---:|---:|---:|---:|---:|
| 300-only | 0 | 3 | 900 | 800 | 3.878107635297385 | 4.653729162356862 |
| 500-only | 2 | 0 | 1000 | 950 | 4.309008483663760 | 5.170810180396512 |
| Mixed | 1 | 1 | 800 | 750 | 3.447206786931009 | 4.136648144317211 |
| Reversed mixed | 1 | 1 | 800 | 750 | 3.447206786931009 | 4.136648144317211 |

The status totals are exactly `4 OK`, `0 REVIEW REQUIRED`, `1 NOT REPAIRABLE`, `1 INPUT ERROR`, and `0 SYSTEM ERROR`. The not-repairable row has both band counts and every other installable quantity blank. Its warning register entries are W002, W003, and W006, all attributed to main row 7.

## Temporary production-path workbook checks

Temporary files were generated under `/tmp/calcbatch-v13-task4.fY0iYQ` through `create_template_workbook`, `create_acceptance_workbook`, and the public `process_workbook` entry point. They are verification intermediates, not release artifacts.

- Exact eight-sheet order verified; Lists is hidden in production outputs.
- Template and acceptance input contain zero formulas.
- Processed result contains exactly 18 formulas: W/X/Z for Cost/Price/Total Amount across rows 6–11.
- Formula text exactly matches the controlled helpers.
- Main/detail/Cost table and filter ranges are `A1:AE151`, `A1:X151`, and `A5:Z11`.
- Quantity validation is `Y6:Y155`; Quantity is unlocked and W/X/Z are locked.
- Batch Input & Results, Individual Defects, Cost Calculation, Warnings, and Summary are protected.
- Re-upload retained B3/E3/H3 values `25`, `8`, `1.4` and Y quantities `1`, `2`, `0`, `3`, `1.5`, `4`, while regenerating the same statuses, engineering outputs, warnings, formulas, tables, and protections.
- Summary records `1.3.0` and `da83373`.

Temporary template and processed render copies made Lists visible only for inspection, constrained each sheet to its focused used range, and were converted by LibreOffice to one eight-page PDF each. Both PDFs had title `PROWRAP CalcBatch v1.3`, exactly eight pages, and extractable required text for every sheet. All eight processed pages were visually inspected. The inherently wide main, detail, and Cost tables are compressed in one-page print previews, but the focused headers and data remain present; the controller's dedicated final spreadsheet artifact workflow remains the authoritative release-layout check.

## Provenance

`PROVENANCE.json` records the product and filename identity, exact accepted single-case commit, imported CalcBatch v1.2 baseline, Task 4 preparation base, accepted source-module hashes, active package-adapted engine hash, and hashes for the current app/schema/cost/generator/processor/template modules. Tests recompute current local module hashes and compare them with the manifest.

## Remaining release work

The controller must perform the dedicated final spreadsheet artifact marker/generation/render workflow after code review, then separately authorize any GitHub publication or Streamlit deployment. No public or final-artifact claim is made by this Task 4 verification.
