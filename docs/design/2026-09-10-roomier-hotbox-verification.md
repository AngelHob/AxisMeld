# Roomier native hotbox verification — 2026-09-10

## Result and scope

Implemented the approved roomier layout in D:/source/AxisMeld-phase0 (base d3331dd0f04e86fb3042a864ec82840fd0ac4145). This report covers hotbox geometry, presentation and menu event behavior only. View locking, navigation and manipulator verification are owned by the root task.

- Main targets are 38 logical pixels high, separated by 10 pixels, with 40 pixels of horizontal text padding. The desktop composition retains the wider middle and tapered outer rows.
- Seven view targets lie on a true horizontal ellipse, with the original seven semantic directions and empty NE sector. Short labels retain the native font size.
- Every ordinary secondary directory uses an ellipse. Long directories page; capacity decreases with available space, not target/font size.
- Only the active ring is rendered and hittable. Its center Back control reconstructs the previous directory and its independent page state.
- At least 340 × 200 logical pixels are required; actual label measurements must also fit. Compact main layouts below 480 × 320 expose paged original root groups, not reduced-size controls. Actual 2× quad verification used 392.5 × 212.5 logical pixels.
- Current native Blender menu font, theme colors, roundness and semantic icons remain in use. No command/schema/global preference expansion, Python pointer-motion call, cursor warp, or release-guard ownership change.

## Event ownership checked

| Input | Result |
| --- | --- |
| Ordinary menu press, no pointer movement | Enter and latch directory; release cannot select a newly exposed rectangle |
| Ordinary menu press, actual held motion | Hover through child directories and release a leaf, as before |
| Latched submenu | Explicit click enters; unpressed hover cannot replace the intended click target with Back |
| Back / page-control press | Perform navigation once; its release remains consumed even if layout moves or the control becomes disabled |
| Active ring gap in center-only style | Does not restart center mapping |
| Central view marking | Real-origin 12px dead zone first; visible view hit selects that label; other empty space uses original directional sectors |
| Original marking crosses central Style | Style is transparent to direction inference, does not hover-open, and does not hover-highlight; release first, then a fresh click enters Style |
| Visual view highlight | Same pending leaf as actual dispatch, including inward-clamped corner buttons |
| Space/Esc/reverse release/second mouse | Existing cancellation and owning-mouse guards preserved |

## Evidence

### RED before geometry implementation

roomy-layout-red.log: all four new behavior tests failed against the previous 28px/4px/column implementation:

1. RoomierMainTargetsKeepTenPixelGaps.
2. SecondaryCommandsOccupyAnEllipseInsteadOfAColumn.
3. SevenViewsLieOnHorizontalEllipseWithTheOriginalDirections.
4. QuadAtTwoTimesScalePagesSecondaryWithoutShrinking.

Additional direct regressions captured before their fixes:

- roomy-occlusion-red.log: root hit rectangles remained behind an active secondary ring.
- roomy-gap-red.log: active-ring gap incorrectly restarted center-only marking.
- roomy-title-red.log: a latched child-directory click immediately bounced through the newly exposed Back control.
- roomy-latch-red.log: stationary corner menu release reclassified the rebuilt ring.
- roomy-corner-red.log: visible inward-clamped Top target dispatched its original-origin sector instead of Top.

Evidence caveat: roomy-next-red.log and the first roomy-next-green.log were initially confounded by the test fixture omitting the native semantic icon width for synthetic Entry/Parent/Child labels. The coordinate fixture was corrected. Do not use those two logs as isolated causal evidence for the terminal-page release bug. The corrected terminal-page test, complete nested test, and actual 2× quad test all pass after the ownership fix.

### Final segmented-motion correction and GREEN

Root's independent near-distance check exposed that single-jump gesture tests missed continuous motion through the new central Style target. `roomy-segmented-isolated-red.log` reproduces this with the old 290620CF binary while no other test GUI runs: 1/3/6/10/15/30/50/70/90 logical-pixel motion steals the Perspective gesture. The initial repeated `roomy-segmented-red.log` has the same failure, but only the isolated repeat is used for causal evidence because a root navigation run briefly overlapped the first attempt.

The minimal correction makes central Style transparent only during the original views-marking gesture. It cannot hover-open or hover-highlight then; the actual origin and 12px dead zone stay unchanged. Original RMB release at rest latches the views ring, after which a **fresh** Style click opens its directory. A fresh Style press can still drag to a setting leaf. The old synthetic same-origin MOVE-to-open-Style test was replaced with those actual fresh-press paths.

- `roomy-menus-segmented-final.log`: complete suite PASS, **63.813s**, including segmented seven-direction motion at 1x/2x, 15-logical-pixel Side at both scales, fresh Style click and held drag, and the entire previously listed menu regression matrix.
- `roomy-native-segmented-final.log`: the same five allowed native CTest tests PASS, **0.33s**.
- `roomy-segmented-build.log` / `roomy-segmented-install.log`: final production build and explicit isolated install succeeded.
- Final near-Side screenshots at 1x/2x were inspected: only Side highlights while the pointer remains over central Style; Style itself stays unhighlighted. Fresh Style drag screenshot shows the actual selected Zones Only setting.

### Earlier layout/paging checkpoint GREEN (290620CF binary)

- roomy-layout-final.log: 21/21 native menu tests PASS.
- roomy-native-final.log: exactly the five allowed CTest tests PASS, 0.32s.
- roomy-menus-final.log: complete installed real-event menu suite PASS, 53.907s. Covers all three mouse buttons × seven actual orientations, dead zone/NE and setting non-dispatch, cancellation, click and held-drag shading, disabled behavior, mode/quad close-before handoff, center remaps, blank center origin, Style, Controls persistence, Recent replay, 1/1.25/1.5/2× true corners, row paging, nested Back/page retention, malformed snapshots, unsupported width/height tap/hold lifecycle.
- roomy-deadzone-verified.log: command and setting spies around real dispatch plus 21 direction positive controls PASS.
- roomy-next-coordinates-green.log: corrected terminal Next press/release retains final page and dispatches Entry17 as Top, 15.704s.
- roomy-gap-final.log: active ring gap cannot restart center-only marking, PASS, 13.547s.
- roomy-title-final.log: latched directory click and actual setting leaf, PASS, 13.703s.
- roomy-corner-final.log: visible clamped Top highlight and actual Top dispatch, PASS, 13.547s.
- roomy-latch-final.log: stationary corner directory entry followed by a fresh actual leaf click, PASS, 13.656s.
- roomy-quad-green.log: actual 2× quad (392.5 × 212.5 logical) all seven visible view targets and an 18-item ellipse's final page, PASS, 20.031s.
- roomy-pixel-THEME.log: native menu theme background pixel probe PASS, 2.922s.
- roomy-pixel-ICON_SCALE.log: 2× native icon occupies scaled slot PASS, 2.907s.
- roomy-pixel-ICON_ALPHA.log: disabled icon and text receive the same single alpha attenuation PASS, 2.906s.

All artifacts above are below D:/source/AxisMeld-build/. PNG iCCP/chromaticity warnings came from image loading in the disposable screenshot fixture. Unsupported-dimension warnings are expected negative controls. No Python traceback occurs in the final passing logs.

## Build and reproducible commands

PowerShell; no configured all-tests CTest was run. All GUI invocations are serial and use the disposable hidden factory-scene runner.

```powershell
$cmake = 'C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$ctest = 'C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
& $cmake --build D:/source/AxisMeld-build --config Release --target blender axismeld_hotbox_menu_test
& $cmake --install D:/source/AxisMeld-build --config Release --prefix D:/source/AxisMeld-build/phase2b-roomy-test-install
& D:/source/AxisMeld-build/bin/tests/Release/axismeld_hotbox_menu_test.exe
& $ctest --test-dir D:/source/AxisMeld-build -C Release --output-on-failure -R '^(axismeld_hotbox_menu|axismeld_hotbox_state|axismeld_identity|axismeld_transform_axis|editor_hotbox_hotbox_model)$'
& C:/Python314/python.exe -m py_compile tests/python/axismeld_hotbox_menu_events.py tests/python/axismeld_hotbox_geometry_fixture.py
& C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-roomy-test-install/blender.exe --suite menus --artifacts D:/source/AxisMeld-build/roomy-menus-segmented-final
# AXISMELD_TEST_SEGMENTED_PROBE=1 runs only the real segmented-motion regression.
# Run separately: AXISMELD_TEST_NAVIGATION_PROBE = 1, gap, title, corner, latch, quad.
# Run separately: AXISMELD_TEST_DEADZONE_PROBE=1, AXISMELD_TEST_THEME_PROBE=1,
# AXISMELD_TEST_ICON_SCALE_PROBE=1, AXISMELD_TEST_ICON_ALPHA_PROBE=1.
# Each flag precedes the identical runner command, using its corresponding artifact directory.
git diff --check
```

Actual intermediate build logs: roomy-layout-red-build.log, roomy-layout-build.log, roomy-occlusion-red-build.log, roomy-active-ring-build.log, roomy-navigation-build.log, roomy-final-build.log, roomy-target-build.log, roomy-latched-build.log, roomy-layout-final-build.log. The segmented correction's final build/install logs are listed above.

## Binary identity and preservation

- Final new prefix blender.exe SHA256: F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F.
- Superseded roomier checkpoint before the segmented-motion correction: 290620CFC1E357F2C244FBF7A2B65EE03A72EF5EE33EEA09485B7ABA17787568.
- Protected phase2b-ui-test-install/blender.exe remains 7344BB88D4BC783FC3B7358C8AB832FCCFFB55612D26FDD0073998C46BED8AF2.
- Protected phase2b-test-install/blender.exe remains 0A119F484EFAAC09156470810795BEC9A6EC7DBE34AF4CFA06529D464789A6E9.
- GUI handoff confirmed only user PID50228 remained, running the protected UI stage. No user preference save, normal/older install overwrite, push, merge, reset, or deletion outside disposable runner files was performed.

## Screenshot SHA256

Paths below are relative to D:/source/AxisMeld-build/. All listed screenshots were personally inspected.

| Screenshot | SHA256 |
| --- | --- |
| roomy-menus-segmented-final/menus-segmented-near-side-1.0.png | 497D1637EBE7C2E6BBD3228D389307446304394B5BDC19F5D67526EE09BE364B |
| roomy-menus-segmented-final/menus-segmented-near-side-2.0.png | F9DB077FEC18B754395EB5C976FC5C38E841AC4283A2F9B75E516DB624627CD8 |
| roomy-menus-segmented-final/menus-fresh-style-drag-candidate.png | 00199E02628173FD9BF2067CE349A2B0E00782CA2E866CC8ADAEF79AF4DF7FA4 |
| roomy-menus-final/menus-main.png | 3BA878BF07A0C5E6483947B96803AB07DAB6154BCF0264B91F95D7864B374BFB |
| roomy-menus-final/menus-controls-center-button-open.png | 3AA81EEFB58B5FC0CA07A76117A1D5561ACE66BB66FCC2382945431708D468E1 |
| roomy-menus-final/menus-small-child-scrolled.png | 58C52786A07C21DE871E056BE9A9123D8D4A9AFD72E91D803427D7BC6ECC1337 |
| roomy-quad-green/menus-quad-2x-compact-main.png | 6989872F3B69C1A5DD29E624DEB20FFFCF42365D5627AF69D0004F2CEFF88A08 |
| roomy-quad-green/menus-quad-2x-seven-views.png | 6DDB00B67B09AF2B240F2754823CE760FF05F718AF7581AF5878CCDED5394895 |
| roomy-quad-green/menus-quad-2x-page-last.png | 3642A64120110008DABCE95609C723C7C141C6DC19666E9993ECCA6FC4E00AF3 |
| roomy-corner-final/menus-corner-visible-top.png | FF9FCEBAD17442C294B11C50561CC51043F5244E7D1CCF691B578F69109F90F1 |
| roomy-pixel-THEME/menus-main.png | 71861FFDC534AC8E5F940366BCEB6EF25B1C8549025FE765DD26E15153AB7B67 |
| roomy-pixel-ICON_SCALE/menus-main.png | 46193ED69E613C9A9542550F28A7DB7C6B204AAF9C815DE6BD3582DF4EE38DCC |
| roomy-pixel-ICON_ALPHA/menus-main.png | B1C416512D215C349F6DB35122BC6172A6C150E7F91F2D3F2484BDABAC68DA87 |

## Remaining acceptance boundary

Automated behavior and screenshots are verified, not a claim about physical pointing comfort. Tachikoma still needs to judge the roomier feel and paging trade-off on the new isolated stage. Root task separately supplies final fixed-view locking and all-pane transform regression evidence.
