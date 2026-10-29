# Custom Property Options Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix existing custom-property dialog draft synchronization and prevent first confirmation from writing to a changed source.
**Architecture:** Keep the existing Blender operator and menus. Add localized draft-loading and transient source validation inside the custom-property section; preserve explicit EXEC and native repeat behavior.
**Tech Stack:** Python, Blender 5.4 RNA/operator UI, existing bilingual dictionaries and isolated event harnesses.
**Spec:** `docs/development/2026-10-29-custom-property-options.md`

## Global Constraints

- UI/interaction only; no new algorithms, menus, default shortcuts or Apply/Reset persistence.
- Preserve global bars, Modeling seven roots, Rigging two roots, grey placeholders, Views geometry and 18px companion lists.
- Open/change/cancel must not write scene properties. Explicit EXEC_DEFAULT arguments and F9 edits must not be overwritten by a dialog callback.
- First confirm requires original window/scene/View Layer/object/mode identity. Successful first confirm releases transient guard for native redo.
- New reasons are bilingual; names and values are user data, not translation sources.
- Old manual IDs/content/status stay unchanged; automated checks do not mark manual acceptance complete.

## Review Focus

- Boolean is an int subclass; untouched bool must remain bool, integer remains integer, Unicode string exact.
- RNA update callback during operator parameter initialization must not replace explicitly supplied EXEC arguments.
- Object removed/recreated under the same name, different scene/layer/window, or property removed: reject without writes.
- F9 Undo restores new pointers; draft synchronization must not overwrite requested redo values.
- Cancel and failed parsing/collision leave all objects' properties unchanged.

### Task 1: Repair parameter dialog and add regression evidence

**Files:**
- Modify `scripts/modules/axismeld/modeling_common_ops.py` custom-property section only.
- Modify the appropriate `translations_*.py` dictionary for new reasons.
- Add `tests/python/axismeld_custom_property_test.py` and `tests/python/axismeld_custom_property_gui.py`.
- Existing reference: `tests/python/axismeld_m3_common_check.py`.

**Interfaces:**
- Consume existing `_custom_keys(context)`, `_object_mode(context)`, operator `axismeld.m3_custom_property(action, property, name, value, kind)`.
- Preserve ADD/EDIT/DELETE and FLOAT/INTEGER/BOOLEAN/STRING public RNA arguments.
- Produce focused tests and isolated GUI script that writes a JSON receipt with evidence boundaries. New private helper names are implementer decisions.

- [x] Write failing tests for untouched integer/bool/string and selector draft refresh; source swap must cancel and preserve both objects. Verify RED against baseline.
- [x] Implement minimal load/update callbacks and transient source guard, preserving supplied EXEC arguments and F9. Cover removal/same-name replacement, no-property/unsupported value, invalid conversion/collision, cancel and deliberate rename/type changes.
- [x] Run focused tests with actual Blender RNA where callbacks matter. Avoid tests merely asserting stub behavior.
- [x] Add GUI harness compatible with disposable factory process (`AXISMELD_TEST_ROOT` and `AXISMELD_TEST_ARTIFACTS`); suppress splash explicitly. Exercise real RNA dialog selection and simulated confirm/cancel, native Undo/Redo and F9, and English/Chinese. Do not operate existing user sessions. Controller launches GUI sequentially after fresh install.
- [x] Run existing M3 common/translation/catalog tests appropriate to changed code; document exact test boundaries, self-review and commit only task files.

### Task 2: Verify and deliver one reviewed batch

**Files:** dated acceptance/snapshot, CHANGELOG/current handoff, manual ledger/index, curated testing-site catalog/config; existing release audit tools.
**Interfaces:** consumes reviewed Task 1 source SHA, actual native build/install and GUI receipts; produces versioned package, public download proof and Pages proof.

- [x] Add four to six manual cases for Modify → Edit Attribute... and Delete Attribute...; preserve old 400 entries except moving isNew flags.
- [x] Fresh incremental build/install, relevant regressions, installed GUI verification, independent archive extraction/factory checks.
- [x] Push source and publish versioned preview with frozen source identity. Verify anonymous download and factory startup.
- [x] Update current docs and website; validate state/browser, push Pages, verify six public resources against committed bytes; push final docs and metadata-only integration README.
- [x] Record manual limitations and final remote identities. Do not merge feature code into integration.

## Completed delivery evidence

- Runtime/distribution source: `1183c5ef866f4b2cc11b7c4dc301dbc23a6564dc`; final review approved.
- Final build/install, 5 focused suites/63 tests, installed and independent extracted GUI each 21 records, and local browser 14 checks passed. GUI records include instrumentation/completion; physical acceptance remains pending. Legacy M3 checker fails unchanged on baseline/current and was not counted passing.
- Public release: `axismeld-2026.10.29-custom-property-preview`; full anonymous ZIP checksum, 6533-file/154-resource extraction audit and a new factory process passed. Incomplete network attempts were preserved; recovery used validated public byte ranges and an exact whole-ZIP SHA256.
- Pages: `bbc80edf43d61be08bcde38ddf130bfdd740bb2a`, six public resources byte-matched. Catalog 405/current 391/current-pending 344; CP-01–CP-05 pending, old 400 records preserved except recency flags.
- Verified delivery docs: `5fb39898a14651a1a34da3585262fb3f7260fc39`. Integration README-only metadata: `f826282cc7fabecfd6024d6caced193237345b33`; feature code was not merged into integration.
- This plan-close commit follows the packaged runtime source and does not change the preview's identity.
