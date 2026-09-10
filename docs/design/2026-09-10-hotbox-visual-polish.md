# Hotbox visual polish and intermittent manipulator follow-up

User approved the bounded visual direction on 2026-09-10: overall horizontal oval arrangement inspired by Maya; individual menu buttons, typography and icons follow Blender's current theme. This extends Phase2B presentation, not command semantics or a new UI subsystem.

## Visual contract

- Make the overall main hotbox composition oval: wider near its center, narrower toward its top/bottom. Keep recognizable Common / Current Pane / central functions / Modeling grouping and sibling order. Use wrapped Modeling rows if necessary to avoid a longest bottom row; do not invent or remove commands to fit a silhouette.
- Individual controls remain compact Blender-style rounded menu buttons, not individual ovals. Read current Blender UI font/style/theme colors, normal/hover/disabled colors, roundness and UI scaling; remove fixed green hover and fixed-font assumptions. Reuse Blender icons where a real semantic equivalent exists; do not copy Autodesk assets or add purely decorative icons.
- Preserve Space tap/hold, central three-button mappings, seven view directions and their actual press origin, center-style blank fallback, menu hierarchy and single authoritative layout/hit rectangles. Changes to positions must change hit geometry together.
- Standard viewport presentation prioritizes the approved oval grouping. Edges and small viewports prioritize legibility and reachability over exact silhouette; retain bounded scrolling, no clipped text, no overlap, no cursor warp, no new input capture outside supported 3D WINDOW.
- Keep Python off mouse-motion paths. No global theme modification, preference resets, UV algorithms, new-window commands or global scale changes.

## Intermittent B12-11

User reports W/E/R all appearing to activate Move and inability to select an axis; restarting Blender restores operation. Status: intermittent, root cause not yet confirmed, NOT fixed by restarting.
Latest manual isolation: triggered after hotbox use, specifically while remaining in quad view; W/E/R act like a grab tool. A quad-to-single round trip is not sufficient coverage. Test all four live regions, actual gizmo hits and resulting location/rotation/scale separately before changing production code.
Reproduced in protected old Phase2B with real events: pane 0 transforms pass; pane 1 real highlighted Move axis does not arm. Handler trace shows editor keymaps before gizmo/tool handlers only in newly created panes. `refresh_quad_clipping(layout_changed)` calls the resize-only initializer before normal area initialization, installing editor handlers early; later initialization appends defaults without reordering. Minimal correction: use full `ED_area_init` at this topology-change boundary to obtain both fresh rectangles and normal default-before-editor handler order. No changes to transform mathematics, keymaps or global WM dispatch. Verify the same RED test plus four-pane direct and armed drags and existing view/clipping regressions on the new stage.
Factory-startup GUI regression passes; saved preference copy has the correct preset and distinct W/E/R semantic mappings. Follow up repeated tool changes, hotbox tool dispatch, profile reload, mode/area changes and real short click timing. Compare tool identity, displayed gizmo and retained-axis state. Only implement a bug fix after actual evidence; report unsuccessful reproduction honestly.

Final result: the quad initialization fix passes all four panes' W/E/R real axis selection, constrained MMB and direct LMB transforms, plus existing hotbox/view/clipping, navigation and same-window release suites. Earlier uncertainty above records the investigation chronology; the reproduced quad handler-order defect is now corrected, while physical acceptance and unrelated long-session symptoms remain unconfirmed. Evidence: `../compatibility/2026-09-10-b12-11-quad-report.md`.

## Verification and delivery

Use test-first layout/behavior coverage and real installed GUI screenshots. Verify normal and high-DPI/theme presentation, main menu and mapped-menu hit targets, seven views, corners/small viewports, cancellation, native input/transform regressions. Retain any reproducible intermittent sequence as regression.
Worktree: D:/source/AxisMeld-phase0, branch axismeld/phase-2a, BASE36f4bc483ed. Build D:/source/AxisMeld-build; explicitly install ONLY to D:/source/AxisMeld-build/phase2b-ui-test-install. Current phase2b-test-install (exe SHA0A119F484EFAAC09156470810795BEC9A6EC7DBE34AF4CFA06529D464789A6E9), Phase2A and normal install remain untouched. No merge/push/publish. Physical visual preference and long-session behavior remain user acceptance.
