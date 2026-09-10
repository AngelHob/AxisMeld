# Compact secondary hotboxes and native Style menus

Approved by the user on 2026-09-10. Follows [composition convention](hotbox-menu-composition.md).

Secondary rings use 24 logical pixel targets and 16 pixels of horizontal padding,
separate from unchanged 38-pixel primary rows and 83.6-pixel central side gaps.
Keep readable native fonts, the ellipse, true gesture origins and non-overlapping
targets. Existing ordinary directory paging and return semantics remain supported.

Style option lists use Blender native menu drawing/components with continuous
rows and a shared menu background. Both the Views tail and Controls Style use the
same implementation. Preserve the existing hotbox-owned event dispatch: do not
create competing modal ownership or allow Space/RMB releases to leak to the scene.
The native menu rendering is separate from the ring renderer, suitable for reuse
by future option lists; no unnecessary change to upstream menu event handling.
Native ordinary menus reserve 40 logical pixels beyond the measured text width:
their built-in text clipping and item padding need more room than the ring's 16.
The first rendered prototype with ring padding visibly truncated the longest label.

Restore this test installation's persisted style from zones to rows with backup;
do not remove the user's ability to select Zones Only later, or globally ignore
saved settings. Restore all existing Common/Pane/Modeling placeholders as disabled
entries. Do not overwrite configuration while the user's process can save it back.

Tests cover compact secondary hit areas, unchanged primary geometry, native Style
theme rendering and contiguous rows, selection/cancel/backtracking, complete main
rows, 1x/2x and quad panes, W/E/R and owned-release cleanup. Reuse existing stages
and preserve a rollback executable. No push or publication.
