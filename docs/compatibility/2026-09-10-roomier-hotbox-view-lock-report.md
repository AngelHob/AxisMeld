# Roomier hotbox and fixed-view locking

Status: implementation and automated combined verification complete; physical acceptance and release approval remain pending.

The user accepted B12-11's quad manipulator repair, approved roomier elliptical menus, and requested fixed front/top/side views that cannot tumble with Alt. Scope is recorded in [the approved design](../design/2026-09-10-roomier-hotbox-and-view-lock.md).

## Fixed-view diagnosis and evidence

The previous maximize path removed native rotation locking together with quad-only linking/clipping. Explicit AxisMeld axis actions also did not establish a lock. Fixed-axis actions now establish the native rotation bit; maximizing retains it; explicit Perspective clears it. Quad cache restores the current rotation policy independently of suspended BOXVIEW/BOXCLIP. First entry from a native/loaded named orthographic axis also establishes the fixed-view policy. Arbitrary USER orthographic views are not newly locked.

- `view-lock-red.log`: old protected stage, real Alt+LMB leaves quad fixed pane 0 unchanged but rotates its maximized view (exit 1).
- `view-lock-green.log`: initial implementation, 25 actual navigation cases pass, including all six axes, three fixed quad panes and maximization, pan/dolly positive controls, explicit Perspective restoration, arbitrary USER ortho, Industry native axis navigation and unchanged scene Camera.
- `view-lock-native-top-red.log`: additional initial native TOP -> quad case reproduces a missing initial lock (exit 1). Narrow initialization fix added after this RED.
- `roomy-final-view-lock.log`: final combined build passes all 27 real navigation cases, including the added initial native TOP/maximum case; 42.515 seconds, exit 0 and success marker present.
- `view-lock-clipping-green.log`: existing hotbox/quad clipping suite passes after adapting fixture setup to explicitly choose Perspective. Manually writing a projection no longer represents releasing a fixed view's native lock. Its intentional maximize/axis-action expectations now distinguish rotation policy from quad-only linking/clipping.

No global input dispatch change, custom per-mousemove lock handler, user preference rewrite, or scene Camera transform change is used. A preset switch alone does not erase an explicitly selected native view lock. The existing native controls remain responsible for their own view state.

## Isolated delivery and final checks

The roomier UI keeps 38-pixel logical targets and 10-pixel gaps, with only the active elliptical secondary ring visible and a center return button. Long menus page without shrinking targets. Validation reproduced center-only blank-ring re-entry (`roomy-gap-red.log`), stationary title/latch failures (`roomy-title-red.log`, `roomy-latch-red.log`), and a visible inward-clamped view label disagreeing with its original-origin sector (`roomy-corner-red.log`). Their final real-event suites pass. Direction labels highlight and execute the same target; free-space gestures retain their actual press origin. A proposed Style-on-neutral-release defect was disproved by catalog type checks and the actual deadzone suite; no speculative fix was applied for it.

The early Next-page failure logs also contained a test-coordinate error: custom Entry/Parent/Child fixtures omitted the native icon's 20-pixel measurement. Those logs are not clean standalone attribution evidence. Corrected `roomy-next-coordinates-green.log`, the full nested-menu suite and actual 2x quad suite verify that clicking Next until it becomes disabled leaves the last page usable and its leaf executes. The corresponding press/re-layout/release ownership fix was also independently reviewed.

Final root regression exposed a genuine additional interaction defect: a 2x 30-physical-pixel marking move was blocked by the center Style rectangle. Continuous 1/3/6/10/15/30/50/70/90-logical-pixel samples then independently reproduced a stolen Perspective gesture (`roomy-segmented-isolated-red.log`). During the original marking gesture only, Style now neither opens on hover nor highlights nor obstructs direction inference. A neutral release followed by a fresh Style click/held drag still works. `roomy-menus-segmented-final.log` passes the full suite including both 1x/2x segmented seven-direction cases and 15-logical-pixel Side, 63.813 seconds. Earlier single-jump direction tests alone were insufficient evidence of continuous movement.

The native-quad exit fixture was also corrected without changing product code: native quad duplicates the source into its User pane, including explicit locks. The fixture now uses the real Perspective action before testing native free-User exit behavior, and explicitly asserts that the User pane is unlocked. `roomy-native-quad-fixture-red.log` confirms the former invalid precondition. The full revised hotbox suite (`roomy-final-hotbox.log`) passes in 30.187 seconds, including saved fixed-view rotation locking and arbitrary USER ortho freedom.

Build directory: `D:/source/AxisMeld-build`. New explicit install prefix: `D:/source/AxisMeld-build/phase2b-roomy-test-install`. The user-running `phase2b-ui-test-install` and prior installs are protected. All GUI automation uses new hidden factory-startup processes with temporary configuration and scene files; it never attaches to the user's session.

Final binary SHA-256: `F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`, identical in build and new install directories. Product source/tests/design commit: `b6099b382f4e88f21f1e7f36c06a8c88df9f3e35`. Build info remains disabled, so runtime Unknown is not an identity check. Detailed UI results and earlier checkpoint boundaries are in [the visual report](../design/2026-09-10-roomier-hotbox-verification.md). Physical target size, menu pointing comfort and navigation feel require the [manual acceptance table](phase-2b-manual-test.md).

| Final check | Result | Log below D:/source/AxisMeld-build |
| --- | --- | --- |
| Complete menus, segmented movement and fresh Style entry | PASS, 63.813s | roomy-menus-segmented-final.log |
| All four panes W/E/R, click-axis/MMB/direct drag, cancel/undo/edit/preset | PASS, 44.453s | roomy-final-manipulator.log |
| Quad cache/clipping, contexts, save/reopen including lock | PASS, 30.187s | roomy-final-hotbox.log |
| Fixed views / Perspective / pan / dolly | 27 cases PASS, 42.515s | roomy-final-view-lock.log |
| Navigation direction, scaling, clipping and Industry isolation | PASS, 15.297s | roomy-final-navigation.log |
| Same-window release and settings/Recent ownership | PASS, 5.500s | roomy-final-release.log |
| Installed profile persistence and invalid-file protection | PASS | roomy-final-profiles.log |
| Native suites, including 21 menu layout tests | 5/5 CTest PASS | roomy-native-segmented-final.log |
| Python configuration and input unit tests | 26 + 14 PASS | roomy-final-pure.log / roomy-final-input.log |

Separate view-lock and UI reviews found no remaining blocking code issue; the old 24px test comment was corrected. The new geometry fixture is included in the product commit. No user session was terminated or modified. The prior UI, Phase2B, Phase2A and normal installs retain their respective SHA prefixes `7344BB88`, `0A119F48`, `7A606A5B`, `72DB65ED`.

Deferred Global object scaling, UV functionality and cross-new-window release isolation remain outside this change. No push, merge or publication is authorized by this task.
