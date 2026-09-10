# User-reference hotbox spacing and drag guide

Approved for implementation by the user on 2026-09-10 with their attached Maya screenshot.

## Reference and scope

The supplied 804 x 507 screenshot shows Recent Commands at approximately x=177..290,
the central Maya button at x=377..442, and Hotbox Controls at x=528..630. Central
height is approximately 40 pixels; the left/right gaps are approximately 87/86 pixels.
Use a 2.2-times-button-height gap (83.6 logical pixels for AxisMeld's 38-pixel target),
not a claim about Maya's internal constants. Keep Blender native fonts/icons/theme.
Side buttons use measured text plus existing icon/padding, without stretching into
the gaps. This supersedes the older requirement that the central row be the widest.
Other main rows and existing elliptical secondary menus retain their current layout.
Apply the same gap to ordinary three-button fallback rows. At viewport edges or
small sizes, keep the existing separate/paged-row fallback rather than squeezing
buttons or moving the invocation target away from the original cursor position.

The screenshot proves visual spacing, not invisible Maya zone or release rules.
Do not add a global inert-zone override or invent new Maya region mappings. Existing
visible-rectangle hits, center-only mapping, seven-view dead zone, and owned marking
gestures remain unchanged. In the standard main row the visual gaps cannot hit a
side entry; an already active marking gesture continues across them as before.

## Drag guide

While the hotbox owns a held mouse button and the pointer has moved, draw a thin,
DPI-scaled native-theme line from the actual press position to the current pointer.
Keep these coordinates separate from inward-clamped menu geometry. Draw beneath
buttons/text, using the region's clipping. No line for ordinary hover or Space alone.
Release, Escape, Space release, context invalidation and window deactivation remove
the line through existing ownership/lifetime cleanup. A non-owning button release
does not remove it. Timer events must not move the endpoint. No Python motion path.

## Verification and delivery

Add native geometry/hit regression tests before layout changes and real rendered
pixel checks before drawing changes. Cover full/hidden-row/edge layouts, 1x/2x,
press origin, non-owning release, release/cancel cleanup, existing menus and W/E/R.
Use factory-startup isolated processes only. Reuse an existing non-running test install;
preserve portable configuration and one rollback install. Do not
overwrite a running executable, add an unbounded permanent stage, push, or publish.

Delivery adjustment: the user still had roomy-test-install running. Reused
phase2b-ui-test-install after backing up and hash-checking all five portable files;
roomy-test-install remains untouched as rollback. The widened center row needed an
extra utility row at 480x320, where neither side alone could hold four rows. The
fallback now distributes those rows over free slots above and below the fixed anchor,
maintaining canonical order. Existing complete-tree reachability tests caught this.
