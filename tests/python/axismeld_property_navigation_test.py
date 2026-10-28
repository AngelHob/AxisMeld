# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Behavioral navigation contracts; real RNA coverage lives in the GUI test."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace as NS
import importlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))


class Item(NS):
    def as_pointer(self):
        return id(self)


class Space:
    def __init__(self, pin=None, pinned=False):
        self.context = 'MATERIAL'
        self.search_filter = 'old search'
        self.use_pin_id = pinned
        self.pin_id = pin
        self.fail = ''

    def __setattr__(self, key, value):
        if self.__dict__.get('fail') == key:
            object.__setattr__(self, 'fail', '')
            raise RuntimeError('RNA write failed')
        object.__setattr__(self, key, value)


def area(kind='PROPERTIES', width=300, height=600, x=0, y=0, pin=None, pinned=False):
    return Item(type=kind, width=width, height=height, x=x, y=y,
                regions=[Item(type='WINDOW', width=width, height=height, x=x, y=y)],
                spaces=Item(active=Space(pin, pinned)))


class NavigationTest(unittest.TestCase):
    def setUp(self):
        try:
            self.api = importlib.import_module('axismeld.property_navigation')
        except ModuleNotFoundError:
            self.api = None
        self.obj = Item(type='MESH', name='source', location=(1, 2, 3), modifiers=(),
                        selected=True, is_editable=False)
        self.obj.select_get = lambda **kwargs: self.obj.selected
        self.viewport = area('VIEW_3D', width=900)
        self.props = area()
        self.scene = Item()
        self.layer = Item(objects=Item(active=self.obj))
        self.screen = Item(areas=[self.viewport, self.props])
        self.window = Item(screen=self.screen, scene=self.scene, view_layer=self.layer)
        self.ctx = Item(window=self.window, screen=self.screen, scene=self.scene, view_layer=self.layer,
                        area=self.viewport, region=self.viewport.regions[0], mode='OBJECT',
                        window_manager=Item(windows=[self.window]))

        @contextmanager
        def override(**kwargs):
            old = {key: getattr(self.ctx, key) for key in kwargs}
            for key, value in kwargs.items():
                setattr(self.ctx, key, value)
            try:
                yield self.ctx
            finally:
                for key, value in old.items():
                    setattr(self.ctx, key, value)
        self.ctx.temp_override = override
        self.bpy = NS(context=self.ctx, app=NS(background=False))
        self.patch = patch.dict(sys.modules, {'bpy': self.bpy})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.assertIsNotNone(self.api, 'Native property navigation is not implemented')

    def test_changes_only_target_tab_and_search_for_read_only_source(self):
        before = self.obj.__dict__.copy()
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'FINISHED'})
        self.assertEqual((self.props.spaces.active.context, self.props.spaces.active.search_filter), ('OBJECT', ''))
        self.assertEqual(self.obj.__dict__, before)
        self.assertEqual(self.ctx.mode, 'OBJECT')
        self.assertIs(self.ctx.area, self.viewport)

    def test_current_properties_wins_over_larger_editor(self):
        large = area(width=800)
        self.screen.areas.append(large)
        self.ctx.area = self.props
        self.ctx.region = self.props.regions[0]
        self.assertEqual(self.api.run(self.ctx, 'MODIFIER'), {'FINISHED'})
        self.assertEqual(self.props.spaces.active.context, 'MODIFIER')
        self.assertEqual(large.spaces.active.context, 'MATERIAL')

    def test_largest_then_leftmost_bottommost_is_deterministic(self):
        small = self.props
        upper = area(width=500, x=10, y=100)
        right = area(width=500, x=20)
        wanted = area(width=500, x=10)
        self.screen.areas.extend([upper, right, wanted])
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'FINISHED'})
        self.assertEqual(wanted.spaces.active.context, 'OBJECT')
        for other in (small, upper, right):
            self.assertEqual(other.spaces.active.context, 'MATERIAL')

    def test_same_object_pin_is_retained(self):
        space = self.props.spaces.active
        space.use_pin_id, space.pin_id = True, self.obj
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'FINISHED'})
        self.assertTrue(space.use_pin_id)
        self.assertIs(space.pin_id, self.obj)

    def test_other_object_datablock_and_empty_pin_are_untouched(self):
        for pin in (Item(type='MESH'), Item(), None):
            with self.subTest(pin=pin):
                space = self.props.spaces.active
                space.use_pin_id, space.pin_id = True, pin
                before = space.__dict__.copy()
                self.assertFalse(self.api.available(self.ctx, 'OBJECT')[0])
                self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})
                self.assertEqual(space.__dict__, before)

    def test_incompatible_current_pin_uses_compatible_same_window_editor(self):
        self.props.spaces.active.use_pin_id = True
        self.props.spaces.active.pin_id = Item()
        other = area(width=200)
        self.screen.areas.append(other)
        self.ctx.area = self.props
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'FINISHED'})
        self.assertEqual(other.spaces.active.context, 'OBJECT')
        self.assertEqual(self.props.spaces.active.context, 'MATERIAL')

    def test_other_window_is_never_used(self):
        other = area(width=2000)
        self.ctx.window_manager.windows.append(Item(screen=Item(areas=[other]), scene=Item(), view_layer=Item()))
        self.screen.areas.remove(self.props)
        self.assertFalse(self.api.available(self.ctx, 'OBJECT')[0])
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})
        self.assertEqual(other.spaces.active.context, 'MATERIAL')

    def test_hidden_properties_or_window_region_are_not_targets(self):
        for target, field in ((self.props, 'width'), (self.props.regions[0], 'height')):
            old = getattr(target, field)
            setattr(target, field, 1)
            self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})
            setattr(target, field, old)

    def test_active_object_must_exist_and_be_selected(self):
        self.obj.selected = False
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})
        self.layer.objects.active = None
        self.assertFalse(self.api.available(self.ctx, 'OBJECT')[0])
        self.assertEqual(self.props.spaces.active.context, 'MATERIAL')

    def test_native_modifier_types_include_empty_and_exclude_armature(self):
        # Hand-checked against buttons_context_path_modifier in buttons_context.cc.
        supported = ('EMPTY', 'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE',
                     'GREASEPENCIL', 'CURVES', 'POINTCLOUD', 'VOLUME')
        for kind in supported + ('ARMATURE', 'CAMERA', 'LIGHT', 'SPEAKER', 'META', 'LIGHT_PROBE'):
            self.obj.type = kind
            self.assertEqual(self.api.available(self.ctx, 'MODIFIER')[0], kind in supported, kind)
            self.assertTrue(self.api.available(self.ctx, 'OBJECT')[0], kind)

    def test_edit_and_pose_modes_are_not_changed(self):
        for mode in ('EDIT_MESH', 'POSE'):
            self.ctx.mode = mode
            self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'FINISHED'})
            self.assertEqual(self.ctx.mode, mode)

    def test_stale_window_scene_layer_and_viewport_reject(self):
        self.ctx.window_manager.windows = []
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})
        self.ctx.window_manager.windows = [self.window]
        for field in ('scene', 'view_layer'):
            old = getattr(self.ctx, field)
            setattr(self.ctx, field, Item())
            self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})
            setattr(self.ctx, field, old)
        self.viewport.type = 'TEXT_EDITOR'
        self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})

    def test_invalid_target_and_background_are_unavailable(self):
        self.assertEqual(self.api.run(self.ctx, 'MATERIAL'), {'CANCELLED'})
        self.bpy.app.background = True
        self.assertFalse(self.api.available(self.ctx, 'OBJECT')[0])

    def test_failed_search_or_tab_write_rolls_back_editor(self):
        space = self.props.spaces.active
        for field in ('context', 'search_filter'):
            space.fail = field
            self.assertEqual(self.api.run(self.ctx, 'OBJECT'), {'CANCELLED'})
            self.assertEqual((space.context, space.search_filter, space.use_pin_id, space.pin_id),
                             ('MATERIAL', 'old search', False, None))

    def test_real_action_dispatch_requires_captured_live_viewport(self):
        from axismeld import menubar_runtime
        token = menubar_runtime.source_token(self.ctx)
        self.assertTrue(menubar_runtime.available(self.ctx, 'action', 'properties.modifier', token)[0])
        self.assertEqual(menubar_runtime.run(self.ctx, 'action', 'properties.modifier', token), {'FINISHED'})
        self.assertEqual(self.props.spaces.active.context, 'MODIFIER')
        self.viewport.type = 'TEXT_EDITOR'
        replacement = area('VIEW_3D')
        self.screen.areas.append(replacement)
        self.assertEqual(menubar_runtime.run(self.ctx, 'action', 'properties.object_transform', token), {'CANCELLED'})
        self.assertEqual(self.props.spaces.active.context, 'MODIFIER')


if __name__ == '__main__':
    unittest.main()
