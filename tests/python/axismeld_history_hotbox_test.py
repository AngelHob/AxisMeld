# SPDX-License-Identifier: GPL-2.0-or-later
"""History Operations content and event-entry boundary; no Maya code execution."""
import ast
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
from axismeld import hotbox_catalog, hotbox_runtime
from axismeld.commands import baseline_bindings
from axismeld.keymap import generate_keymaps


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))


class HistoryHotboxTest(unittest.TestCase):
    def root(self):
        nodes = {n['id']: n for n in walk(hotbox_catalog.default_catalog())}
        self.assertTrue('context.history' in nodes, 'A + LMB History Operations is missing')
        return nodes['context.history']

    def test_all_eight_reference_slots_and_two_independent_gray_options(self):
        root = self.root()
        self.assertEqual(root['presentation'], 'radial')
        rows = {n['direction']: n for n in root['children']}
        self.assertEqual({d: n['label'] for d,n in rows.items()}, {
            'W':'Select All Inputs', 'E':'Select All Outputs', 'N':'Enable All Outputs',
            'S':'Disable All Outputs', 'NW':'Delete History', 'NE':'Delete Non-Deformer History',
            'SE':'Freeze Transformations', 'SW':'Reset Transformations'})
        for direction in ('W','E','N','S'):
            n=rows[direction]
            self.assertEqual((n['kind'],n['command'],n['enabled']), ('disabled','',False))
            self.assertTrue(n['reason'])
        self.assertEqual({d:rows[d]['command'] for d in ('NW','NE','SE','SW')}, {
            'NW':'edit.bake_selected', 'NE':'edit.bake_selected_non_deform',
            'SE':'transform.apply_all', 'SW':'transform.reset_all'})
        for direction in ('SE','SW'):
            node=rows[direction];self.assertEqual(len(node['children']),1)
            option=node['children'][0]
            self.assertEqual((option['id'],option['kind'],option['command'],option['enabled']),
                             (node['id']+'.options','disabled','',False))
        hotbox_runtime.serialize_snapshot(hotbox_runtime.make_snapshot(generation=1))

    def test_existing_frame_command_remains_single_binding_and_user_rebindable(self):
        self.root()
        for key in ('A','F20'):
            bindings=baseline_bindings()
            bindings['view.frame_all']={**bindings['view.frame_all'],'type':key}
            data=generate_keymaps([('3D View',{'space_type':'VIEW_3D','region_type':'WINDOW'},{'items':[]})],bindings)
            rows=[item for _name,_context,content in data for item in content['items']
                  if item[0]=='axismeld.command' and item[2]['properties']==[('command','view.frame_all')]]
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0][1]['type'],key)

    def test_keyboard_only_arms_history_and_menu_frame_all_stays_immediate(self):
        path=ROOT/'scripts/modules/axismeld/adapter.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        file_selectors=next(n for n in tree.body if isinstance(n,ast.Assign)
                            and any(isinstance(t,ast.Name) and t.id=='FILE_SELECTORS' for t in n.targets))
        calls=[]
        def call(name):
            def op(*args,**kwargs):calls.append((name,args,kwargs));return {'RUNNING_MODAL'}
            return op
        namespace=dict(available=lambda *args:(True,''), MODELING_SPECS={},
            FILE_SELECTORS=ast.literal_eval(file_selectors.value),
            HISTORY_ROOT='context.history', HISTORY_TRIGGER='view.frame_all',
            CONVERSION_HOTBOX='context.convert_hotbox',CURRENT_TOOL_HOTBOX='context.tool_hotbox',
            OBJECT_TOOLS={},OBJECT_ACTION_COMMANDS={},CREATE_OPERATORS={}, MODEL_HOTBOX='context.modeling_hotbox',
            CREATE_HOTBOX='context.create_hotbox',TOOLS={},ORIENTATIONS={}, COMPONENT_HOTBOX='context.component_hotbox',
            COMPONENTS={},MODE_COMMANDS={},SELECTION_ACTIONS={},VIEW_ACTIONS={},
            VIEW_OPS={'view.frame_all':('view_all',{'center':False})},
            bpy=NS(ops=NS(view3d=NS(axismeld_hotbox=call('history'),view_all=call('frame')))),
            __name__='axismeld.adapter', __package__='axismeld')
        exec(compile(ast.Module(body=[run],type_ignores=[]),str(path),'exec'),namespace)
        from unittest.mock import patch
        with patch.object(hotbox_runtime,'snapshot',return_value='checked_snapshot'):
            namespace['run'](NS(), 'view.frame_all', keyboard_tool_session=True)
        self.assertEqual([c[0] for c in calls],['history'])
        self.assertEqual(calls[0][2]['tool_menu'],'context.history')
        calls.clear()
        namespace['run'](NS(), 'view.frame_all', invoke=False)
        self.assertEqual([c[0] for c in calls],['frame'])

    def test_real_command_entry_rejects_repeat_and_preserves_rebound_trigger(self):
        path=ROOT/'scripts/startup/bl_operators/axismeld.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AXISMELD_OT_command')
        invoke=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='invoke')
        namespace=dict(CONVERSION_HOTBOX='context.conversion_hotbox', CURRENT_TOOL_HOTBOX='context.tool_hotbox',
                       MODEL_HOTBOX='context.modeling_hotbox', CREATE_HOTBOX='context.create_hotbox',
                       COMPONENT_HOTBOX='context.component_hotbox', TOOL_ROOTS={}, HISTORY_TRIGGER='view.frame_all')
        exec(compile(ast.Module(body=[invoke],type_ignores=[]),str(path),'exec'),namespace)
        calls=[]
        owner=NS(command='view.frame_all',
                 _run=lambda *args,**kwargs:calls.append((args,kwargs)) or {'FINISHED'})
        for key in ('A','F20'):
            event=NS(type=key,value='PRESS',is_repeat=True)
            self.assertEqual(namespace['invoke'](owner,NS(),event),{'CANCELLED'})
            self.assertEqual(calls,[])
            event.is_repeat=False
            self.assertEqual(namespace['invoke'](owner,NS(),event),{'FINISHED'})
            self.assertTrue(calls[0][1]['keyboard_tool_session'])
            calls.clear()


if __name__=='__main__':unittest.main()
