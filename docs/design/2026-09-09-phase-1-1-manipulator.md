# Phase 1.1: persistent transform axis

Status: user approved priority, scope and implementation on 2026-09-09.

Follow-up decision (2026-09-09): the user deferred the Object Mode Global scaling
geometry mismatch (AXM-COMPAT-001). Retain native transform mathematics and continue
the hotbox/view roadmap; do not adopt the experimental geometry or parent-matrix routes.
See `../compatibility/global-object-scale.md`. Deferral is not a fix or a review approval.

## Interaction contract

In the AxisMeld Maya 2026 preset, Object Mode and mesh Edit Mode:

- Click and release a visible X/Y/Z handle of Move, Rotate or Scale without dragging:
  select the axis, retain a yellow visual cue, and do not transform data or push undo.
- Middle-drag in empty viewport space uses that axis and the current tool's orientation.
  Releasing MMB confirms; Escape or RMB cancels; one native undo reverses a confirmed drag.
- Repeated drags keep the axis. Clicking another single axis replaces it.
- Direct LMB handle dragging continues to use the native gizmo path without extra thresholds.
- Tool, active object, Object/Edit mode, or preset change clears stale state. State is
  transient and region-local, never a saved scene property. Explicit Escape while idle clears it.
- No selected axis means the existing Industry Compatible free-transform behavior remains.
- Alt+MMB remains navigation. Non-transform gizmos, non-mesh modes and other presets are unchanged.
- Plane, center, trackball, temporary pivot, snapping, hotbox and UV parity are not added here.
  Their inherited behavior remains adapted. Orientation, pivot, numeric input and transform
  math remain Blender behavior; this slice does not claim complete Maya equivalence.

## Architecture and alternatives

Use native gizmo hit-testing and its existing CLICK / CLICK_DRAG distinction. Add a
profile-only click command before generic gizmo fallback, and a profile-only MMB command
before transform tool fallback. Keep axis state in each native transform gizmo group.
Expose narrow access helpers in `transform_gizmo.hh`; implement operators separately in
`transform_axismeld.cc`. Reuse native translate/rotate/resize operators, copied gizmo
properties and orientation preparation. Do not route every mouse move through Python.

A pure Python replacement gizmo would duplicate orientation and drawing behavior; a full
transform rewrite would duplicate geometry, cancellation and undo. Both increase maintenance
and correctness risk. The selected design changes only the transform editor seams and built-in
profile generation, leaving window-manager dispatch and upstream keymap generators untouched.

## Verification and performance

Add pure native state tests for selection retention, invalid axes, context invalidation and
independent regions. Add generated keymap tests for click/MMB priority, Alt isolation and
preservation of other editors. Real simulated input must exercise click-release, empty-space
MMB, axis-constrained geometry, repeated drags, cancel, undo, direct drag and original preset.
Run a separate factory-startup GUI process; never inject events into the user's session.

Measure first and repeated tool activation via the semantic dispatcher and direct native
calls in the same test process. Report timings as command dispatch measurements, not physical
latency or GPU frame-time proof. Do not claim the reported stutter fixed without evidence.

Rebuild INSTALL, run existing and new tests, review the diff, then deliver a new manual
acceptance table. Preserve user preferences and any existing running Blender process.
