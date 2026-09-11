# SDD ledger — plan: docs/superpowers/plans/2026-09-11-m1-tool-hotboxes.md

Spec: docs/superpowers/specs/2026-09-11-modeling-interaction-alignment-design.md, user approved execution.
Worktree: D:/source/AxisMeld-phase0, axismeld/phase-2a, no pre-existing changes; 47 baseline Python tests pass.

## Preflight interface / self-consistency scan

| Tasks | Shared interface | Check |
|---|---|---|
| Task 1 internal Python/native | optional tool_menu, direction/presentation, schema-1 old snapshots | one end-to-end task owns producers and consumers; strict validation and old-file tests required |
| Task 1 / controller delivery | candidate exe, changed Python modules, GUI suite tools | implementer builds candidate only; controller owns primary install and config/fallback hashes |
| Task 1 self | tests vs implementation | tests assert immediate tool, fixed directions, selection/orientation result, canceled state and no residual modal; no UV implementation |

Task 1: in progress; implementer /root/m1_tool_implementation; BASE 5a9477433e6a1ffe8963de8e784f47ed32eb49d8. Controller owns source mapping/report documentation outside Task 1 file list; no concurrent code edits or builds.

Task 1: Ruling: Add tool_hotbox.py to the generated native menu fixture CMake DEPENDS — the catalog now imports it, and stale generated fixtures would test obsolete data — if unnecessary it costs only extra fixture regeneration.

Task 1: implementation DONE at 0b27a59ba1a; report task-1-report.md; task review package review-5a9477433e6..0b27a59ba1a.diff. Review not yet complete.

Task 1: Ruling: Reuse the completed reference_hotbox_review agent for an independent M1 task review after spawning failed with agent thread limit reached — this agent did not implement or inspect M1 and receives only the new review package as authority — prior unrelated review context could bias attention, so explicitly exclude it and preserve a separate final review seat.

Task 1: review needs fixes; Important: radial children without direction pass Python/native validation but cannot be laid out. Fix round 1/5 dispatched to original implementer; prior review HEAD 0b27a59ba1a. Current controller-only documentation HEAD 3de4926.
Task 1: minor (deferred): source-resource GUI logs contain Cycles missing and libpng ICC warnings; controller will verify installed-resource behavior and record provenance.
Task 1: cannot-verify items: controller must verify per-tool orientation consumption by gizmo/MMB, installed resources, personal config and fallback preservation before completion.
Task 1: orientation consumption check resolved by controller source audit: DNA slots 1/2/3; RNA use maps SELECT; scene getter maps native tool flags; gizmo setup picks each builtin tool; invoke_prepare uses tool slot and axismeld_gizmo_drag_axis calls the same function. Runtime independent-slot assertions and separate manipulator regression passed. Full per-orientation physical drag matrix is explicitly manual M1-05, not claimed automated.
Task 1: fix round 1/5 (1 Important addressed, 0 open; commit 89b6bba7273). Same reviewer confirmed Python/native contract, atomic rejection and legacy acceptance; no new breakage.
Task 1: complete (commits 5a9477433e6..89b6bba7273, task review clean). Controller delivery and final whole-M1-slice review remain pending. Final review seat: cascade_feedback_review, separate from implementer and task reviewer; reuse under the same thread-cap ruling above.

Final review: With fixes at c4945d0ed37. Two Important findings: overlapping W-down/E-down/W-up blocks the new tool session behind an old release guard; clamped edge layout allows no-motion release/return-to-origin to submit a displaced target. One final fix wave dispatched to original implementer, both findings together. Re-review will be scoped to the fix diff; no new features authorized.
Final review: fix wave c7909d81507; both findings ADDRESSED, no new breakage, scoped review clean. Candidate 97AEE90EF85872F9AF38EFD8C03576CB2DC44B5F3A8956553B8E5116C7876645. No parked code findings.
Controller delivery: fresh no-Blender-process check; validated candidate and old-primary hashes; copied six changed Python files with per-file hash verification and candidate exe into the existing installation. Primary now matches candidate; fallback and all six portable hashes match baseline. Installed tools GUI passed without Cycles warning; remaining serial installed regressions in progress. Implementation report archived to docs/superpowers/reviews/2026-09-11-m1-implementation-report.md before scratch cleanup.
Controller final delivery: all eight installed GUI suites exited 0 with explicit PASS markers: tools, hotbox, menus, native-style, release, selection, appearance, manipulator. No source-resource overrides; no Cycles-missing warning in any installed log. Known libpng ICC warning predates M1 (old logs and Phase 2B report); retained as a documented environment limitation, not new code breakage. Negative test fixture warnings remain intentional.
Controller final preservation: automated comparison against captured baseline reports PERSONAL_FILES_UNCHANGED 6/6 after all GUI suites; fallback hash unchanged F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F; installed hash 97AEE90EF85872F9AF38EFD8C03576CB2DC44B5F3A8956553B8E5116C7876645; no remaining Blender processes. Manual hand-feel checklist remains pending; M2/M3 and UV are not completed. No merge or remote push.
All implementation and review work for this bounded M1 plan is complete. Archive this ledger and implementation report in docs/superpowers/reviews before cleaning only this plan's scratch workspace. Keep the linked source worktree, existing test installation, fallback and candidate intact.

Initial delivery baseline: primary exe 87C6A0989066AEF83E6047DD0CBFCE650DDF7C3BA970058AC6F81BA99F62A59B; fallback exe F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F. Six portable-file hashes captured by controller. No Blender processes at initial check; must recheck before delivery.

## Portable hash baseline
+- `D:\source\AxisMeld-build\phase2b-ui-test-install\portable\.gitignore`: `04BE9483C8141ECE8ADFCDF849A1286B4B814F8C2C59DA691CB17724208A3685`
- `D:\source\AxisMeld-build\phase2b-ui-test-install\portable\README.txt`: `DB6D7AA840044CEFE01A2B9BDFDB5393A963A172C04F4BE9E560241F52670F1B`
- `D:\source\AxisMeld-build\phase2b-ui-test-install\portable\config\platform_support.txt`: `EF38D94CC30BC9B8F86716CC00588473FCC06A61F9C0336A40B1768FC7B6D29C`
- `D:\source\AxisMeld-build\phase2b-ui-test-install\portable\config\recents.toml`: `C9FDA8893A4FA2AD61FCD127B2DB1A22798D0C7774EE26A3E349EFDA9EB969EC`
- `D:\source\AxisMeld-build\phase2b-ui-test-install\portable\config\userpref.blend`: `FBE58AD15F583FF8E216343E6295CC8471BBB6AE39B75BC280D4AC6DB70CB065`
- `D:\source\AxisMeld-build\phase2b-ui-test-install\portable\config\axismeld\hotbox_user.json`: `C8DB55C18BA05349EB9589B56E6BB7C323FAB33D969320418773FE5191CB2EFA`
