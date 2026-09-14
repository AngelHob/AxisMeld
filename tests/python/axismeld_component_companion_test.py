# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))
from axismeld import context_hotbox


def node(identifier, kind, label, **kwargs):
    result = dict(id=identifier, kind=kind, label=label, children=())
    result.update(kwargs)
    return result


def walk(item):
    yield item
    for child in item['children']:
        yield from walk(child)


class ComponentCompanionTest(unittest.TestCase):
    def test_screenshot_full_order_and_separators(self):
        root = context_hotbox.component_companion(node)
        self.assertEqual(root['id'], 'context.component_menu')
        self.assertEqual([n['label'] for n in root['children']], [
            'Object...', '', 'Select', 'Select All', 'Deselect All', 'Select Hierarchy',
            'Invert Selection', '', 'Select Similar', '', 'Make Live', '',
            'DG Traversal', 'Inputs', 'Outputs', 'Paint', 'Metadata', 'Actions',
            'UV Sets', 'Color Sets', 'Time Editor', '', 'Scene Assembly', '',
            'Material Attributes...', '', 'Assign New Material',
            'Assign Favorite Material', 'Assign Existing Material'])
        self.assertEqual(sum(n['kind'] != 'separator' for n in root['children']), 22)

    def test_fixed_children_and_readonly_metadata_options(self):
        items = {n['id']: n for n in walk(context_hotbox.component_companion(node))}
        prefix = 'context.component_menu.'
        self.assertEqual([n['label'] for n in items[prefix+'actions']['children']],
                         ['Template', 'Untemplate', 'Unparent', 'Bounding Box'])
        self.assertEqual([n['label'] for n in items[prefix+'metadata']['children']],
                         ['Edit Metadata...', 'Visualize Metadata', 'Select Stream'])
        state = items[prefix+'metadata.visualize']
        self.assertEqual((state['kind'], state['indicator'], state['checked']),
                         ('disabled', 'checkbox', False))
        self.assertEqual(state['children'][0]['id'], state['id']+'.options')
        self.assertEqual([n['label'] for n in items[prefix+'time_editor.select_clip.include_parent']['children']],
                         ['Match Exact', 'Match All', 'Match Any', 'Match None'])
        self.assertEqual(context_hotbox.UNAVAILABLE_INDICATORS,
                         {prefix+'metadata.visualize': 'checkbox'})
        for suffix, labels in {
            'inputs': ['Select All Inputs', 'Enable All Inputs', 'Disable All Inputs', '',
                       'History nodes unavailable', 'All Inputs...'],
            'outputs': ['Select All Outputs', 'Enable All Outputs', 'Disable All Outputs', '',
                        'History nodes unavailable', 'All Outputs...'],
            'paint': ['Paint Select', '3D Paint', 'Paintable attributes unavailable'],
            'uv_sets': ['UV Linking...', 'UV Set Editor', '', 'UV sets unavailable'],
            'color_sets': ['Color Set Editor', '', 'Color sets unavailable'],
            'assign_new_material': ['New Material...', 'Material provider entries unavailable'],
            'assign_favorite_material': ['Material favorites unavailable'],
            'assign_existing_material': ['Scene materials unavailable'],
        }.items():
            self.assertEqual([n['label'] for n in items[prefix+suffix]['children']], labels)

    def test_commands_exact_and_dynamic_data_never_fabricated(self):
        items = list(walk(context_hotbox.component_companion(node)))
        commands = {n['id']: n['command'] for n in items if n['kind']=='command'}
        prefix = 'context.component_menu.'
        self.assertEqual(commands, {prefix+k:v for k,v in (
            ('select_all', 'selection.select_all'), ('deselect_all', 'selection.clear'),
            ('select_hierarchy', 'selection.hierarchy'), ('invert_selection', 'selection.invert'),
            ('actions.template', 'display.template'), ('actions.untemplate', 'display.untemplate'),
            ('actions.unparent', 'edit.unparent'))})
        self.assertEqual(commands, context_hotbox.COMPONENT_MENU_COMMANDS)
        self.assertEqual(len(items), len({n['id'] for n in items}))
        for item in items:
            if item['id'].endswith('.options'):
                self.assertEqual(item['kind'], 'disabled')
                self.assertFalse(item.get('command'))
            if item['kind']=='disabled':
                self.assertFalse(item['enabled'])
                self.assertTrue(item['reason'])
        self.assertFalse(any('pCube' in n['label'] or 'Lambert' in n['label'] for n in items))

    def test_radial_directions_unchanged_and_uv_has_real_children(self):
        ring = context_hotbox.component_menu(node)
        self.assertEqual({n['id'].rsplit('.',1)[1]:n['direction'] for n in ring['children']},
                         dict(edge='N',vertex='W',face='S',object='NE',uv='E',vertex_face='SW',multi='SE'))
        uv = next(n for n in ring['children'] if n['label']=='UV')
        self.assertEqual(uv['kind'], 'menu')
        self.assertEqual([n['label'] for n in uv['children']], ['UV', 'UV Shell'])
        self.assertEqual(next(n for n in ring['children'] if n['direction']=='SE')['label'], 'Multi')


if __name__ == '__main__':
    unittest.main()
