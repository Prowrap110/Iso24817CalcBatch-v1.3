# Deploy CalcBatch v1.3 as a new isolated public application

## Release hold

**Do not deploy now.** These are exact operator instructions for a later, separately authorized public release. This preparation task must not create a GitHub repository, add or push a remote, or create/reboot a Streamlit application.

## Fixed new targets

- Public GitHub repository: `Prowrap110/Iso24817CalcBatch-v1.3`
- Release branch: `release/v1.3.0`
- Streamlit entry point: `app.py`
- New Streamlit application name: `iso24817calcbatch-prowrapv13`
- Expected new URL: `https://iso24817calcbatch-prowrapv13.streamlit.app`

Create both public resources as new v1.3 resources. Do not select, reboot, reconfigure, or deploy over the existing CalcBatch v1.2 application, any earlier CalcBatch application, or a single-case PROWRAP calculator. Do not reuse an existing repository, Streamlit app, URL, branch, or deployment mapping.

## Authorized future release procedure

1. Confirm the reviewed local source is this isolated CalcBatch v1.3 repository on `release/v1.3.0`, with a clean worktree and the approved release commit.
2. Run `python3 -m pytest -q` and require zero failures.
3. Confirm `PROVENANCE.json` parses and pins accepted source commit `da83373d648694f50b8a974ff6071a73ceec2089`, Batch Engine `1.3.0`, the v1.3 filenames, and current module hashes.
4. Create the new public repository named exactly `Prowrap110/Iso24817CalcBatch-v1.3`. Do not import, rename, redirect, archive, or alter the v1.2 repository.
5. Add that new repository as the only publication target for this local v1.3 checkout, then push only the reviewed `release/v1.3.0` branch. Verify the remote branch SHA equals the reviewed local SHA.
6. In Streamlit Community Cloud, create a **new app** named `iso24817calcbatch-prowrapv13` from repository `Prowrap110/Iso24817CalcBatch-v1.3`, branch `release/v1.3.0`, entry point `app.py`. Do not choose any existing app.
7. Confirm the new deployment resolves only at `https://iso24817calcbatch-prowrapv13.streamlit.app` and displays `PROWRAP CalcBatch v1.3`.
8. Download `PROWRAP_CalcBatch_v1.3_Template.xlsx`. Verify the exact eight-sheet order, hidden Lists sheet, main table/filter `A1:AE151`, Individual Defects table/filter `A1:X151`, and exactly 21 inputs plus 10 outputs.
9. Confirm both width inputs validate exactly 300/500 through row 151, output cells are locked, Quantity `Y6:Y155` is unlocked and non-negative, and the blank template contains no formulas.
10. Upload the production-generated six-row v1.3 acceptance workbook. Require status totals `4 OK`, `1 INPUT ERROR`, `1 NOT REPAIRABLE`, and `0` for the other statuses.
11. Reconcile the four valid rows: 300-only counts `0/3` and procurement `900`; 500-only `2/0` and `1000`; mixed and reversed mixed `1/1` and `800`. Confirm their structural outputs are identical and the not-repairable row has blank installable quantities.
12. Confirm processed Cost Calculation uses `W/X/Z` formulas, editable Quantity in `Y`, warning rows W002/W003/W006 for source row 7, Summary identity `1.3.0` / `da83373`, and protected controlled sheets.
13. Re-upload the processed workbook after entering valid B3/E3/H3 assumptions and Y quantities. Confirm assumptions and Quantity persist while engineering results, formulas, warnings, tables, and protections are regenerated identically.
14. Record the new repository URL, exact deployed commit SHA, new Streamlit URL, public template hash, processed acceptance hash, and live re-upload result in the release record.

## Rollback boundary

If the new v1.3 deployment fails, stop or roll back only `iso24817calcbatch-prowrapv13`. Do not change DNS, repository state, branches, deployment settings, or runtime state for v1.2 or any other calculator. Keep the failed v1.3 commit and workbooks available for diagnosis.
