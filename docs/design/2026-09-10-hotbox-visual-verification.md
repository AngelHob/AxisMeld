# Hotbox visual polish verification

This presentation change follows `2026-09-10-hotbox-visual-polish.md`. It does not modify
command dispatch, input lifecycle, transform operators or persistent user preferences.

## Implemented presentation

The normal main composition has five centered rows: Common, Current Pane, the central
three controls, and two consecutive Modeling rows. Measured label widths determine its
size. The central row is widest; the adjacent rows use 92% of that span and the outer
rows taper to 72% and 64%. All original siblings remain present in their original
reading order. The existing central hit target remains at the invocation point.

If this envelope cannot fit around the actual invocation point, the existing bounded
row scrolling and inward placement take over. Hidden-row and center/zones styles retain
their established composition. Drawing and hit testing consume the same native rectangles.

Menu typography comes from Blender's current widget font style, including point size,
weight and UI scale. Background, outline, foreground, selected and disabled colors use
the current native menu theme. Round boxes use Blender's UI drawing API and theme
roundness. Icons reuse native semantic equivalents for Views, Recent, Controls, view
projection, shading and component selection; their reserved width participates in layout.

## Automated and rendered verification

- The new pure layout test first failed against the previous four-row arrangement and
  then passed with five rows, tapered widths, centered spans, preserved Modeling order
  and distinct reachable rectangles. Existing full-tree, corner, scrolling, mapping and
  disabled-occlusion tests also pass.
- A disposable GUI theme probe changes native menu colors to a distinctive red. The old
  fixed-color renderer fails the actual screenshot-pixel assertion; the theme renderer
  passes. This probe never saves preferences.
- High-DPI screenshot review found an unscaled icon call; a pixel regression first failed
  with no icon foreground in the upper half of the 2x slot. A separate black-background
  probe caught double attenuation of disabled icons compared with adjacent disabled text.
  The native icon call now uses inverse DPI aspect and applies the theme alpha once.
- The complete installed GUI suite covers main/menu/center mappings, all seven directions
  through all three default buttons, actual command results, cancellation, mode handoff,
  live Controls/Recent, 1/1.25/1.5/2x scaling, actual content corners, a 534x375 viewport,
  independent nested scrolling and unsupported dimensions.

Run the native five tests only, not the broad configured CTest suite (which still points
some installed tests at an older installation):

```powershell
ctest --test-dir D:/source/AxisMeld-build -C Release --output-on-failure -R '^(axismeld_hotbox_menu|axismeld_hotbox_state|axismeld_identity|axismeld_transform_axis|editor_hotbox_hotbox_model)$'
C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe --suite menus --artifacts D:/source/AxisMeld-build/visual-polish-gui
```

Set `AXISMELD_TEST_THEME_PROBE=1` for the bounded theme pixel regression. Set
`AXISMELD_TEST_FONT_POINTS=15` and `AXISMELD_TEST_VISUAL_ONLY=1` for a disposable native
font-size screenshot check. `AXISMELD_TEST_ICON_SCALE_PROBE=1` and
`AXISMELD_TEST_ICON_ALPHA_PROBE=1` select the bounded icon pixel regressions (run separately).
Detailed local execution evidence and screenshots are in
`D:/source/AxisMeld-build/visual-polish-20260910-report.md`.

## Physical acceptance

Review the main silhouette, text legibility, density and hover/disabled distinction using
the user's real theme and display scale. Exercise all three central buttons, both click
and drag browsing, and the four actual viewport corners. Check that the wrapped Modeling
row is comfortable to scan. The separate intermittent manipulator problem requires its
own four-view investigation; this visual change does not claim to fix it.
