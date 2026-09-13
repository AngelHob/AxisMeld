# Gesture template independent review

Baseline: 129373b45c6. Scope: uncommitted gesture source/test changes against docs/superpowers/specs/2026-09-13-hotbox-gesture-template-design.md. Read-only source review; reviewer runs no builds, tests or GUI.

## Interim findings

1. **P2 — Space-path radial cancellation initially uses an unrelated origin.** The added `modal()` radial-origin check compares `data.origin`. Normal Space invocation initializes center, and a non-Views mouse press initializes `press_position` but does not initialize origin. Thus Space -> Modify -> Tool Settings -> tool ring uses zero/default origin (or an earlier Views stroke), rather than its actual LMB press. Returning to the true stroke origin can be interpreted as an extended radial choice. Use the current stroke press position for non-marking Space radial cancellation and keep Views gesture-origin semantics intact. Reported to coordinator; awaiting final diff.

## Operator rearm review

- The 18-command allowlist matches existing synchronous adapters: 13 orientation property settings, 3 persistent tool selections via EXEC_DEFAULT, select-all and clear-selection via EXEC_DEFAULT. Component dispatch remains a separate earlier branch.
- Default dangerous command handling still cleans up before dispatch and does not inspect the captured area/region afterwards.
- rearm_tool removes its draw callback and clears tool_shown, mouse ownership, open/return paths, scrolling, hover/pending candidate and per-stroke navigation flags. The next LMB press assigns a new real origin and refreshes capabilities and layout before drawing.
- Reviewed correction removing immediate refresh after rearm: empty open_path is not a displayable tool layout; refresh now occurs at the next stroke as required.
- Trigger-first release, Esc, focus loss, invalid context, modifiers and unrelated tool keys still pass through existing cleanup/guard branches. No new timer or handler is created per stroke.
- Tests include repeated success, empty/disabled cancellation, relocated origins, second-stroke trigger-first/Esc/focus cancellation, key handoff, and unchanged native-list paths. Reading test definitions does not certify their runtime outcomes.

Model helper review pending implementation completion; the temporary forwarding stub is not treated as a final implementation.

## Final source follow-up

The Space origin finding is resolved in the reviewed source: non-marking radial checks use `press_position`, and retraction selects the origin appropriate to tool/Views versus ordinary Space strokes. The added dedicated Space test is still owned by the event-test implementer.

Reviewed the completed model implementation:

- `marking_position` shares the existing five-row geometry with the Views template, changes radial horizontal clearance from 32 to 8 logical pixels, and retains per-label widths and original direction assignments.
- `hit_marking_menu_rect` validates the active owner against the latest return region, rejects open native lists, prioritizes real visible rectangles, and limits fallback candidates to the active radial depth.
- Fallback excludes the current center only; hidden ancestor centers do not take input. Outward row continuation respects shorter labels before a longer neighboring row can win by distance.
- Missing radial directions produce disabled, undrawn gap records only after fitting succeeds. Switching rings clears old gaps. Returned pointers refer to original layout vectors, not temporary filtered copies.
- The existing Views wrapper uses the original no-active-center path; changed gap clearing prevents older ring metadata from leaking into a replacement ring.
- Unit-test definitions cover content widths, short reach, outer extension and disabled values, three origins including edges, missing-direction pointer identity, current-child ownership, ancestor-center overlap and native list exclusion.

**Final static assessment: no remaining confirmed blocking issue found in the reviewed diff.** This is a source review, not a claim that build, native tests, event tests or manual keyboard/mouse feel passed. Runtime verification, especially Space actual-origin cancellation and existing Views/component/radio regressions, remains the coordinator's completion gate.

## Integration follow-up: ancestor return precedence

**P2 confirmed after cross-checking model and operator together:** `retract_at_center` runs before radial hit testing. `menu_return_target` suppresses an ancestor return only when a real child rectangle occupies that point, not when the point belongs to the child's newly extended row. Thus an invisible ancestor center overlapping the current child's extension retracts the path before the correct helper can run. The earlier final static assessment did not cover this precedence interaction and is superseded pending this fix.

Recommended bounded fix: when the last open menu is radial, discard ancestor return targets before applying the existing current-center outward/back mapping. Preserve the current center's one-level return and the later real-stroke-origin cancellation override. Leave native-list ancestor return behavior unchanged. Do not filter the parent ID after it has intentionally been produced by the current-center return transition. Sent to coordinator for implementation and integration verification.

### Ancestor-precedence fix re-reviewed

The latest operator now filters `menu_return_target` using the actual last-open radial owner **before** converting current-center return into a parent target. Its subsequent real-origin override remains intact, and native-list owners bypass the new filter. This resolves the confirmed integration issue in source without changing Views/native-list return semantics. Final static assessment is again no remaining confirmed blocking issue; runtime integration regressions remain required and were not executed by this reviewer.
