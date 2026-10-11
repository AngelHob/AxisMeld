# Current GUI completion implementation plan

> **For agentic workers:** Execute with scoped subagents and controller integration; retain the progress ledger across compaction. Steps use checkbox syntax for tracking.

**Goal:** Complete the currently authorized Modeling/general viewport/Rigging GUI, hotbox interaction and Maya-default input layer, with missing algorithms retained as honest disabled entries.

**Architecture:** Extend the existing first-party catalogs, native menu hosts and native hotbox session. Reuse existing operators and explicit context targets; do not add a parallel menu framework or approximate modeling algorithms. Preserve the native Blender global bar and current workspace layout.

**Tech Stack:** Blender Python/RNA, C++ view3d hotbox, Windows CMake/MSVC, pure Python and disposable GUI event tests.

**Spec:** [UI/input scope](../../development/2026-09-29-ui-interaction-shortcuts.md), [geometry contract](../../development/2026-09-14-hotbox-reference-contract.md), user request 2026-10-11 to complete the GUI. The existing requirements are approved; routine implementation choices do not require renewed approval.

## Global constraints

- Keep Modeling's seven roots and Vertex/Edge/Face inside Edit Mesh, Rigging's Skeleton/Skin, native Blender global menus/workspaces.
- Keep unimplemented Maya actions and Options separately disabled; no fabricated functional equivalence.
- Four-view secondary hotbox is the geometry and interaction reference. Preserve actual gaps, outer marking, cancel zones, owned releases and repeated held-QWER/LMB.
- Native companion menus stay fully expanded, bottom aligned when there is insufficient room below. No silent deletion, internal collapsing or scrolling to hide overlong fixed content.
- No scene, mode or selection mutation merely from opening/cancelling a menu. Any explicit preselection action must have transactional cancellation/Undo.
- Personal profiles/addon bindings stay independent. Preserve all historical manual test results; automated GUI checks do not mark manual cases passed.
- No new Skin/Skeleton/modeling/UV algorithms; Global object scale remains explicitly deferred.
- Update CHANGELOG, current handoff, manual catalog and public Pages, commit/push and verify remote. Candidate native builds must match the modified source.

## Review focus

1. Empty/hidden/multi-object Edit Mesh targets, invalidated geometry and cancellation after a modal command starts.
2. Conflicting modifier combinations, trigger key released before/after mouse, active tool restored, another area/window.
3. Empty dynamic menu provider, disabled headings/options, submenu-only entries and real addon menu callbacks.
4. Viewport bottom/right corners, single/quad view, DPI and visible-region clamping; actual hit regions versus visible geometry.
5. Rebind/disable/reload and switching native key presets; holds cannot leave temporary snapping/pivot flags behind.

## Task 1: Context input and preselection GUI

**Owner:** context subagent; controller builds and reviews.
**Files:** command/keymap/profile/adapter/context modules; startup operators; `AXM_context_modeling.hh`; `view3d_axismeld_hotbox.cc`; related pure/runtime/event tests.
**Interfaces:** `context.conversion_hotbox` and current-tool context identities selected from verified Maya reference; native root eligibility and target/selection transaction, described in the task design before implementation.

- [x] Verify Maya reference and write context design.
- [x] Write/observe failing checks for Ctrl+RMB conversion, Ctrl+Shift+RMB current tool and empty Edit preselection.
- [x] Add owned session routing using existing catalogs/operators; leave unsupported content disabled.
- [x] Verify neutral/cancel/release, target validity and Undo; test rejected contexts retain fallback.
- [x] Integrate native build and actual GUI events, then fresh review.

## Task 2: Menu structure, disabled state and layout

**Owner:** menu subagent.
**Files:** menu catalogs/UI hosts and menu tests; `docs/development/2026-10-11-menu-gui-completion.md`.
**Interfaces:** preserve catalog IDs, order, native callback host contexts and option routes.

- [x] Audit all current menu/hotbox nodes against the stored Maya trees, not a visual sample.
- [x] Reproduce the empty dynamic submenu bug and render a disabled identity when there is no actionable/dynamic provider.
- [x] Check native providers, explicit placeholders, independent Options and existing radio/icon behavior.
- [x] Record fixed-tree counts, actual geometry boundaries and GUI evidence; no claim that arbitrary future plugin content fits any viewport.

## Task 3: Complete public input references and hold-state scope

**Owner:** reference subagent; product changes coordinated by controller.
**Files:** current-input audit tool/tests and explicit reference artifact; commands/keymap remain Task 1-owned until handoff.
**Interfaces:** report comparisons are evidence categories, not functional/GUI pass statuses.

- [x] Resolve 18 prose and 2 notation references using Maya2026 default scripts/official references.
- [x] Classify every reserved input and inherited removal: supported interaction, deliberate difference or unavailable capability.
- [x] Examine D/X/V/J holds against actual Maya and existing Blender state/operator semantics; implement existing-capability temporary-state gaps with press/release/cancel tests, or document precise non-UI dependency rather than silently excluding it.
- [x] Regenerate report after final command changes and run drift/isolation tests.

## Task 4: Controller integration and delivery

**Files:** current phase, ROADMAP/CURRENT_ISSUES/HANDOFF, CHANGELOG, unified manual ledger/catalog, build/GUI receipts and fresh candidate.

- [x] Confirm clean starting branch, existing worktree and remote baseline.
- [x] Run proportional pure tests, native hotbox/geometry tests and fresh CMake build/install.
- [x] Verify installed resource hashes and use disposable isolated GUI runs for menus, context inputs, releases/cancel and geometry; fix real failures without deleting checks.
- [x] Close the historical cross-window file-browser release diagnostic using bounded native ownership; preserve true focus-loss and fresh-press recovery. Add a reproducible manual GUI case.
- [x] Fresh review of code and scope matrix; no load-bearing GUI gaps silently marked complete.
- [ ] Add manual cases without altering old results; publish catalog and a usable verified candidate where feasible.
- [ ] Commit/push code/logs and Pages; verify actual remote/public data. Separate implemented, automated evidence and pending manual acceptance in final report.

## Ownership/preflight

| Pair / task | Shared interface or risk | Ruling |
|---|---|---|
| Context / menu | hotbox catalog and runtime | Context owns these; menu reports required changes instead of concurrent edits. |
| Context / input | commands/keymap/profiles | Context owns until explicit handoff; reference agent owns only report tool/data/tests. |
| Input / controller | generated input report | Controller generates once final commands are integrated. |
| All / controller | source versus build snapshot | No build/install during unannounced source mutation; native changes require a new verified candidate. |
| Context | opening versus committing preselection | No selection at open; action transaction must restore on failure/modal cancel, including later Escape. |
| Menu | content completeness versus viewport capacity | Preserve fixed trees and accessible native providers; report physical-size limits, do not delete content. |
| Input | GUI-only scope versus reserved capabilities | Verify semantics first; no approximate algorithm binding to satisfy shortcut count. |
| Delivery | GUI result versus manual status | Automated screenshots/events remain separate from user acceptance. |
