# Phase 1: Maya 2026 input foundation

Status: implementation under the approved AxisMeld roadmap and continuation request.

## Deliverable

Ship a selectable `AxisMeld_Maya_2026` key configuration with the normal Blender build.
No add-on installation is required. The first slice covers Object Mode and mesh Edit Mode:
Q/W/E/R select/move/rotate/scale, F8 object/component toggle, F9/F10/F11 vertex/edge/face,
A/F framing, Alt mouse navigation, and 4/5 wireframe/solid display.
All mappings are `adapted`: Blender selection, framing, camera and manipulator semantics
remain visible differences. Q/W/E/R/A hold menus are not implemented in this slice.
Space hotbox/quad view, D/X/C/V/J temporary tools, F12 UV and 1/2/3 smoothing remain
unsupported and reserved in the modeling keymaps instead of invoking unrelated tools.

## Evidence and boundaries

Bindings checked against Autodesk's Maya 2026 All Maya Hotkeys:
https://help.autodesk.com/cloudhelp/2026/ENU/Maya-KeyboardShortcuts/files/GUID-30CACC9D-8FBE-4B85-8A8F-C5ADF32DDD4E.htm
Also checked the installed Maya2026 `scripts/startup/hotkeySetup.mel` for F8-F11 and
framing. Do not distribute Autodesk scripts or personal Maya preference files.

## Integration

Use the upstream Industry Compatible generator for the rest of Blender's editors.
The preset transforms a fresh generated table; the upstream generator stays unchanged.
Existing Blender preferences select and save the preset. Keep Blender's initial preset
until explicit selection, as promised by architecture success criterion 1.
Register a built-in semantic dispatcher via `scripts/startup/bl_operators/__init__.py`.
Its implementation lives in `scripts/modules/axismeld/`; no new C++ patch is necessary.
Commands are identified by stable strings. Registry metadata documents Maya input,
adapter entry, context and differences. UV commands can later use the same interface.

## Configuration

The immutable Python baseline contains command-to-event bindings. Adapter definitions
separately map commands to Blender operations. Optional `studio.json` and `user.json`
under `bpy.utils.user_resource('CONFIG')/axismeld` carry schema 1 deltas only.
Session overrides are an explicit API parameter and never written to disk. Each higher
layer replaces a complete event or disables a command with null. Unknown commands,
invalid types/events, duplicate input and schema mismatches reject that entire layer;
the last valid lower layer remains active, with a readable diagnostic and original
file intact. Input is JSON data, never evaluated as code. File size limit: 64 KiB.
Native Blender user keymap edits remain the final interactive customization surface.
No maintainer-specific profile is bundled. Preset preferences can ignore both file
overrides to restore the baseline; native Restore handles Blender's own edits.

## Keymap safety

Apply replacements only to non-modal modeling keymaps. Reserve both original and
overridden inputs so rebinding W does not silently leave a second inherited Move key.
Remove overlapping PRESS/CLICK/DOUBLE_CLICK/CLICK_DRAG/ANY actions and wildcard modifiers
on owned inputs. Never edit addon keymaps. Report conflicts with addon maps separately.
Reject profile layers whose inputs overlap shared Window/Screen/Frames shortcuts, such
as binding Move to Ctrl+Q where Blender would quit, keeping the prior valid layer.
Operator polling must reject Text Editor, UV Editor, non-window regions and unrelated
modes. Component switching must reject missing/non-mesh/read-only objects before mutation.
Use Blender's native undo and selection conversion, with explicit adapted semantics.

## Acceptance

Pure Python tests: layering, disable, invalid layers, non-mutating baseline, schema,
conflicts and generator inheritance. Installed Blender tests: preset discovery/loading,
registered operators, Object/Edit mode transitions, component mode, repeated tool selection,
wrong context, reload, unchanged addon maps, original preset switch-back and serialized deltas.
Build INSTALL through the existing VS2026 tree; run Phase 0 and new CTests.
Automated context tests do not establish physical mouse/keyboard or hold-menu parity.

## Alternatives considered

Replacing Blender's full default keymap would increase upstream merge work; adding an
ordinary addon would violate out-of-box build integration. A built-in preset plus a small
startup registration seam fits both requirements and keeps future native hotbox/UV work separate.
