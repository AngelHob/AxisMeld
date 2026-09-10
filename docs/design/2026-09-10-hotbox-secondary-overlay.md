# Secondary view hotbox: retained parent and owned release

Approved by the user after the second Maya screenshot and their release-behavior
clarification. This supersedes the hidden-parent, central Style button and neutral
release latching rules for the central view marking menu.

## Interaction

- Space owns the first-level hotbox lifetime. Its original position stays fixed.
- Press a center button mapped to Views: overlay the view ring while that button
  is held. The visible AxisMeld center belongs exclusively to the first level.
- Do not create a second-level center button. A neutral release returns to the
  first level; a valid command release executes once and returns to the first
  level. Space release closes every layer. Non-owning releases do nothing.
- Keep first-level rectangles for drawing, but exclude them from hit testing
  while a secondary menu owns input. Empty secondary space cannot activate a
  background first-level title. Direction gestures retain their real press origin.
- Style is a tail below Front View, not a radial direction or center target.
  Holding the same button over it opens an ordinary rightward vertical submenu;
  releasing over its setting applies that setting. Releasing without a setting
  does not latch this transient view menu. At the right edge the list opens left.
  Moving back to the actual press-origin dead zone while still held closes the
  Style list and restores direction sectors for a subsequent outward stroke.
- Full view labels and the eight screenshot positions are preferred. NE New
  Camera is explicitly disabled until a camera-creation adapter exists. Existing
  `view.side` command identity remains unchanged (visible name: Right View).
- Keep native theme transparency. Suppress a parent label only when its actual
  text/icon bounds intersect a higher-level button, not when merely its padding
  overlaps. This preserves unobscured labels without text bleeding through the
  translucent foreground and obscuring the selected view name.

## Bounded layouts and existing menus

Do not shrink the existing 38-pixel targets or reintroduce overlap in small panes.
If full labels plus the Style tail cannot fit, retain the compact seven-direction
view ring with short labels and no center button. Style remains available through
the existing Hotbox Controls entry. This is an explicit small-viewport fallback,
not pixel-for-pixel Maya parity. The full screenshot layout is used where it fits.

Other catalog directories keep their existing paging/Back navigation in this
change; those controls are not the incorrectly introduced center of the Views
marking menu. Parent display is retained for them as well, without click-through.

## Verification

Add failing native tests for retained background, inactive background hits, empty
view center and Style tail/list placement. Add real event/pixel tests for held
overlay, owner/non-owner release, repeated open, valid selection, Style and Space
cleanup. Update obsolete tests that required latching the central Style button.
Run native/pure tests and isolated GUI suites; inspect captured UI. Reuse an
existing non-running test stage and preserve its portable configuration.
