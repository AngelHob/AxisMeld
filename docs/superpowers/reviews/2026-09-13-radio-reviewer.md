# Independent radio menu review

Scope: uncommitted source/tests versus af3f5d86428; read-only review, no test/build/GUI execution. Reviewed plan and existing snapshot parser, Python profiles/runtime/catalog, native MenuOverlay drawing and layout. Implementation may still change.

## Confirmed issues in first reviewed diff

- **P1 — Disabled loses its selected circle.** `source/blender/axismeld/intern/hotbox_menu.cc:23-33` compares mapping snapshot strings directly with catalog value `none`. The production parser (`source/blender/editors/space_view3d/view3d_axismeld_hotbox_model.cc:327-336`) leaves JSON null as an empty string. Consequently selecting Disabled and reopening shows no selected option. The added unit test assigns `none`, which is not the parser output. Normalize the empty current mapping for comparison and exercise empty strings for all three independent groups. No schema change is needed.
- **P2 — New custom-transparency GUI case cannot establish its claimed input.** `tests/python/axismeld_hotbox_native_style_events.py:1161-1195` supplies transparency 37 and expects every circle empty. Existing `hotbox_profiles.py:108-110` rejects non-preset transparency; `hotbox_runtime.py:197-216` reports invalid session diagnostics and keeps the previous valid session. Native parser also rejects nonmultiples of 25 (`view3d_axismeld_hotbox_model.cc:295-299`). Therefore the screenshot retains an actual preset and the all-empty assertion fails. Remove this unreachable GUI case, retain helper-only defensive coverage, and describe profile rejection accurately. Do not expand supported settings merely to enable the test.

## Satisfied contracts visible in source

- Display state derives only from existing MenuSnapshot fields; no new stored state or schema fields.
- Five independent setting commands are classified; Rows toggles and all non-Setting nodes return None.
- Both Style occurrences derive from the same current style; the three mouse mappings read separate array indices.
- Radio icon derives from snapshot, while row hover is passed independently as UI_HOVER. Hover does not alter radio selection.
- Existing native list layout already covers Style, Transparency and mapping directories; the new icon reaches native uiDefIconTextBut.
- Measurement reserves one logical 20px column when either an existing icon or radio icon exists. The OR avoids double counting mappings that already had an icon.
- No mouse handler, release/cancel path or QWER direction definition is changed.

## Nonblocking test observation

The helper unit test initially mirrored the string comparison, which hid the real null encoding. Prefer explicit expected outcomes for parser-representative disabled values. GUI screenshots provide useful independent visual checks, but their actual results remain outside this review until the implementation owner runs them.

Assessment at first review: changes requested for the two confirmed issues. Both findings sent directly to coordinator and implementer. No tests were executed by reviewer.

## Follow-up source review

Re-read the updated diff after implementer notification:

- P1 is resolved in source: only recognized center commands normalize an empty snapshot value to `none`; the unit test now supplies parser-realistic empty mapping. Left/middle/right indexing remains independent.
- P2 is resolved in source: the impossible 37 GUI case is removed, while the helper retains defensive nonpreset coverage. Existing schemas were not expanded.

Final static assessment: no remaining confirmed blocking issue found in the reviewed radio changes. Runtime/build/screenshot verification is still the implementation owner's responsibility; this reviewer did not run tests or GUI and does not certify those results.
