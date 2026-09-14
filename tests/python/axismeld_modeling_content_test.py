# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent Maya2026 MEL/MayaStrings inventory, not production-derived expectations."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/modules'))
from axismeld import context_modeling_hotbox as model, creation_hotbox as create


def node(identifier,kind,label,**kwargs):
    return dict(id=identifier,kind=kind,label=label,children=kwargs.pop('children',()),**kwargs)


def signature(menu):
    return tuple('|' if item['kind']=='separator' else item['label'] +
                 (' +O' if any(c['id'].endswith('.options') for c in item['children']) else '')
                 for item in menu['children'])


EXPECTED = {
'vertex': ('Crease Tool +O','Connect Components +O','Detach Components','Transform Component +O',
           'Connect Tool +O','|','Circularize Vertices +O','Reorder Vertices','|','Apply Color +O','|','Polygon Display'),
'edge': ('Crease Tool +O','Offset Edge Loop Tool +O','Insert Edge Loop Tool +O','Slide Edge Tool +O',
         'Circularize Components +O','Edit Edge Flow +O','|','Add Divisions To Edge +O','Bridge +O','Fill Hole',
         '|','Connect Components +O','Detach Components','Transform Component +O','Connect Tool +O','|','Polygon Display'),
'face': ('|','Smart Extrude','Smooth Faces +O','Assign Invisible Faces +O','Add Divisions To Faces +O',
         'Circularize Components +O','Connect Components +O','Detach Components','Triangulate Faces',
         'Quadrangulate Faces +O','Reduce Faces +O','Remesh +O','Bridge Faces +O','|','Mirror +O',
         'Extract Faces +O','Duplicate Face +O','Transform Component +O','Connect Tool +O','Target Weld Tool +O',
         '|','Mapping','|','Polygon Display'),
}
DISPLAYS = {
'vertex': ('Toggle Backface Culling','|','Toggle Vertices','Toggle Vertex Normals','Toggle Vertex Numbers','|','Reset Polygon Display'),
'edge': ('Toggle Backface Culling','|','Toggle Border Edges','Toggle Texture Border Edges','|',
         'Toggle Hidden Triangle Edges','Toggle Soft Edge Display','|','Reset Polygon Display'),
'face': ('Toggle Backface Culling','|','Toggle Face Centers','Toggle Face Normals','Toggle Face Numbers',
         'Toggle Hidden Triangles','|','Reset Polygon Display'),
}

def walk(nodes):
    for item in nodes:
        yield item
        yield from walk(item['children'])


class ModelingContentTest(unittest.TestCase):
    def test_component_companions_exact_maya_inventory(self):
        self.assertTrue(hasattr(model,'modeling_companions'),'Vertex/Edge/Face companion declarations missing')
        menus=model.modeling_companions(node)
        self.assertEqual(tuple(m['id'] for m in menus),model.MODEL_COMPANION_ROOTS)
        for domain,menu in zip(EXPECTED,menus):
            self.assertEqual(signature(menu),EXPECTED[domain])
            display=next(c for c in menu['children'] if c['label']=='Polygon Display')
            self.assertEqual(signature(display),DISPLAYS[domain])

    def test_radial_options_labels_and_existing_directions(self):
        expected = (
            {'.extrude','.bevel','.knife','.merge.distance','.merge.target_weld','.normals.average','.normals.from_faces'},
            {'.extrude','.bevel','.knife','.merge.border','.merge.target_weld','.normals.angle'},
            {'.extrude','.bevel','.knife','.wedge','.poke','.normals.reverse'},
        )
        for root, wanted in zip(model.modeling_menus(node), expected):
            options=[n for n in walk((root,)) if n['id'].endswith('.options')]
            self.assertEqual({n['id'][len(root['id']):-8] for n in options},wanted)
            self.assertTrue(all(n['kind']=='disabled' and not n['enabled'] for n in options))
            self.assertEqual({n['direction'] for n in root['children']},{'N','NE','E','SE','S','SW','W','NW'})
        edge=model.modeling_menus(node)[1]
        merge=next(n for n in edge['children'] if n['direction']=='N')
        border=next(n for n in merge['children'] if n['label']=='Merge Border Edges')
        self.assertFalse(border['enabled']);self.assertEqual(border['direction'],'NE')

    def test_face_mapping_inventory_and_isolated_ids(self):
        self.assertTrue(hasattr(model,'modeling_companions'))
        menus=model.modeling_companions(node)
        face=menus[2]
        mapping=next(n for n in face['children'] if n['label']=='Mapping')
        self.assertEqual(signature(mapping),('Planar Map X','Planar Map Y','Planar Map Z','Planar Map +O','|',
             'Cylindrical Map +O','Spherical Map +O','|','Automatic Map +O','Camera-Based Map +O','Normal-Based Map +O'))
        items=list(walk(menus));ids=[n['id'] for n in items]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all(n['id'].startswith(face['id']+'.') for n in walk((mapping,))))
        self.assertFalse(any(n.get('command') for n in walk((mapping,))))

    def test_create_display_preserves_two_actions_and_four_dividers(self):
        display=next(c for c in create.creation_companion(node)['children'] if c['label']=='Polygon Display All')
        self.assertEqual(signature(display),('Backface Culling on for All Polys','Backface Culling off for All Polys','|',
            'Toggle All Geometry Border Edges','Toggle All Texture Border Edges','|','Toggle All Face Normals','Toggle All Vertex Normals',
            '|','Toggle All Face Centers','Toggle All Hidden Triangles','Toggle All Vertices','|','Reset Display for All Polys'))
        self.assertEqual([c.get('command') for c in display['children'][:2]],
                         ['display.backface_culling_on','display.backface_culling_off'])

    def test_new_options_never_execute_main_and_whitelist_is_domain_scoped(self):
        self.assertTrue(hasattr(model,'modeling_companions'))
        for domain,menu in zip(EXPECTED,model.modeling_companions(node)):
            for item in walk((menu,)):
                if item['id'].endswith('.options'):
                    self.assertFalse(item['enabled']);self.assertFalse(item.get('command',''))
                if item.get('command'):
                    self.assertEqual(model.MODEL_MENU_COMMANDS[item['id']],item['command'])
                    self.assertEqual(model.MODEL_MENU_DOMAINS[item['id']],domain)
        nodes={item['id']:item for item in walk(model.modeling_companions(node))}
        self.assertEqual(set(model.MODEL_MENU_COMMANDS),set(model.MODEL_MENU_DOMAINS))
        self.assertEqual(set(model.MODEL_MENU_COMMANDS),{key for key,n in nodes.items() if n.get('command')})
        reorder=next(n for n in nodes.values() if n['label']=='Reorder Vertices')
        self.assertFalse(reorder['enabled']);self.assertIn('meshReorder',reorder['reason'])

if __name__=='__main__':unittest.main()
