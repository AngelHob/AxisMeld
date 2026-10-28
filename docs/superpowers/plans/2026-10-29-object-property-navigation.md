# Object Property Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide safe native Object Transform and Modifier property navigation from the approved Maya-style UI and Blender search.

**Architecture:** A bounded property-navigation module selects a compatible Properties editor in the originating window and switches its native context. Existing menubar action dispatch retains source tokens. Dedicated searchable operators share that navigation logic; no geometry or new Maya algorithm is introduced.

**Tech Stack:** Existing Blender 5.4 Python UI/RNA, AxisMeld action catalogs, unittest and native GUI checks.

**Spec:** `docs/development/2026-10-29-object-property-navigation.md`

## Global Constraints

- Preserve Blender global bars, seven Modeling roots, two Rigging roots, Views spacing and 18px companion lists.
- Keep Maya Attribute Editor / Channel Box grey placeholders; use explicit Blender property labels.
- Never change selection, mode, geometry, transforms, modifiers, workspace, another window or pin state to navigate.
- Only same-window visible unpinned or same-object-pinned Properties areas qualify; unavailable cases explain and cancel.
- Navigation creates no scene Undo / Recent; native field edits retain native Undo.
- English stable IDs and English / Simplified Chinese display remain separate.
- Current user authorization covers this bounded implementation, verification and GitHub / Pages delivery; no repeated approval required.

## Review Focus

- Properties pinned to an unrelated object or datablock must not be silently redirected.
- Multiple windows with different scenes / view layers must retain their own active targets.
- A closed source or changed editor must cancel without choosing another source.
- Camera / Light / Empty and empty selection must not accidentally open a Modifier context for a previous mesh.
- A failed navigation must not leave changed UI state or scene data; read-only objects remain viewable.

### Task 1: Native navigation, routes, translations and focused tests

**Files:** Create `scripts/modules/axismeld/property_navigation.py`, `tests/python/axismeld_property_navigation_test.py`, and a native runtime / GUI test under `tests/python/`. Modify `menubar_actions.py`, `menubar_catalog.py`, `scripts/startup/bl_operators/axismeld.py`, existing translation dictionaries and affected focused catalog tests.

**Interfaces:** `property_navigation.available(context, target)` returns `(bool, reason)`; `property_navigation.run(context, target)` returns a Blender operator status set. Targets are `OBJECT` and `MODIFIER`. Reuse existing menubar source validation; expose separate `properties.object_transform` / `properties.modifier` action IDs under Windows → General Editors → Blender Object Properties and named F3 operators. Keep metadata importable without bpy. Native object eligibility must match the checked-in Blender context implementation.

- [ ] Write and run failing behavioral tests for target selection, pins, no selection, types, source invalidation, rollback and no scene mutation.
- [ ] Implement the module and two searchable operators; wire action rows through existing dispatch without editing original Maya reference identities.
- [ ] Add translated labels and reasons, and assert catalog/translation completeness plus original AE/CB disabled state.
- [ ] Run new tests and existing menubar actions/catalog/runtime/integration/workspace/translation tests. Record exact counts and failures; fix only relevant regressions.
- [ ] Prepare a deterministic native test that exercises real Properties RNA in the GUI, then checks native edit/Undo on the source object and unaffected pin / other window data. Controller runs against a fresh install.
- [ ] Self-review and commit only task-owned source/test files; report commit, commands, results and remaining GUI evidence to controller.

### Task 2: Verification and delivery

**Files:** Update `docs/CHANGELOG.md`, current roadmap/issue/handoff entry points, manual ledger, generated catalog/index and `tools/testing_site/config.json` only after a real package exists. Create a dated acceptance record and release snapshot.

**Interfaces:** Consume the Task 1 source commit, targeted test results and GUI test. Preserve old manual IDs/results; new `PN-*` items start pending.

- [ ] Incrementally build the existing configured native checkout and install into a new dated candidate directory; do not overwrite the prior public candidate.
- [ ] Run real runtime / GUI navigation evidence and proportional existing regressions; record source, executable identity and actual results separately from manual acceptance.
- [ ] Add focused pending manual cases and regenerate/validate the public catalog and website.
- [ ] Obtain independent code review, fix confirmed defects, and record scoped re-review results.
- [ ] Package/audit/independently launch the verified build, publish the tagged GitHub preview and verify download identity.
- [ ] Commit/push source and documentation, deploy Pages from its clean worktree and verify remote content. Do not merge the integration branch.
