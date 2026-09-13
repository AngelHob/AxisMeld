# Implementer report — Radio Menu Settings

Status: implemented; native and isolated GUI evidence passed; source/tests frozen for main handoff.

## Change

- Added MenuRadioState (None / Unselected / Selected) and menu_radio_state(snapshot, node), deriving from existing Setting command/value and snapshot fields. No JSON/schema, persistence or event-handler changes.
- Native list drawing passes ICON_RADIOBUT_ON/OFF through existing MenuOverlayItem.icon. Non-native hotboxes, ordinary commands, separators, independent row toggles and unsupported settings retain their existing presentation.
- Label measurement reserves one existing 20px icon allowance, including mapping rows already having generic icons (no double padding).
- Existing native_list routing already covers both Style occurrences, Transparency and all three center mapping lists; no catalog change required.
- Native parser represents disabled JSON null center mappings as empty strings; helper translates this representation to the existing setting value `none`.

## Tests and evidence

All evidence paths below are under D:/source/AxisMeld-build/.

- radio-red-state.log: runnable first state test fails with an unimplemented helper.
- radio-null-red.log: revised realistic empty-string mapping test fails before the null fix.
- radio-mappings-null-red.log: actual GUI pixel assertion independently catches Disabled incorrectly showing all OFF before the null fix.
- radio-final-build.log: Release blender and axismeld_hotbox_menu_test build passed.
- radio-final-native.log: five required native ctest targets passed, including independent Style occurrences, all mapping groups, snapshot mutation, unsupported non-radio nodes and defensive non-preset snapshot handling.
- radio-pixels.log / radio-pixels/: enhanced native-style GUI passed at 1x and 2x. Real screenshot pixel tests verify ON/OFF circle centers separately from hover, both Style occurrences, Transparency, and reopened submenu after an actual click while the parent hotbox remains open. Existing native background/label/hover/row-toggle/Space-release checks also passed.
- radio-mappings-final.log / radio-mappings-final/: mapping GUI passed. Pixel tests verify initial Views ON, hover elsewhere without changing ON, then persisted/reloaded LEFT=NULL (Disabled ON), MIDDLE=common, RIGHT=pane.shading independently. Existing all-labels, wheel, mouse-release, Space-release and W/E/R checks passed.
- Manual image inspection: radio-native-style/native-style-style-controls-1.0-normal.png shows correctly aligned circle + full label; radio-mappings-final/radio-mapping-0-reloaded.png shows Disabled filled circle and twelve hollow alternatives.
- git diff --check passed (only line-ending normalization warnings).

## Limits

Current Python profile validator and native parser only accept the five transparency presets. A 37 snapshot is a defensive pure-helper test; it is not a reachable current GUI/profile value. An attempted GUI custom-value test correctly failed because validation rejected the session layer; that invalid case was removed. No schema was expanded.

Only the independent candidate phase2b-ui-test-install/blender-opacity-check.exe was replaced after confirming it was not running. No primary executable, installed Python, user scene, preferences or existing user PID was modified. All GUI runs used the factory/temp isolated runner. GUI ownership returned to main after final mappings PASS; source/tests frozen. Main owns preview packaging, final regressions, documentation/ledger and any commit.
