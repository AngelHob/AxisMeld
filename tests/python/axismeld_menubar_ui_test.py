import importlib.util
from copy import deepcopy
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'scripts/startup/bl_ui/space_axismeld_menubar.py'

class Layout:
    def __init__(self, log=None):
        self.log = [] if log is None else log
        self.enabled = True
    def row(self, **kw): return Layout(self.log)
    def column(self, **kw):
        child=Layout(self.log)
        self.log.append(('column',child))
        return child
    def menu(self, name, **kw): self.log.append(('menu', name, kw, self.enabled))
    def operator(self, name, **kw):
        props = types.SimpleNamespace()
        self.log.append(('operator', name, kw, props, self.enabled))
        return props
    def label(self, **kw): self.log.append(('label', kw, self.enabled))
    def separator(self, **kw): self.log.append(('separator', kw))
    def prop(self, *args, **kw): self.log.append(('prop', args, kw))
    def context_pointer_set(self, name, value): self.log.append(('context_pointer', name, value))

def load_ui():
    bpy = types.ModuleType('bpy')
    bpy.types = types.SimpleNamespace(Menu=type('Menu', (), {}), Operator=type('Operator', (), {}), WindowManager=type('WindowManager', (), {}))
    props = types.ModuleType('bpy.props')
    props.StringProperty = props.EnumProperty = lambda **kw: kw
    nodes = [{'id':'common.file','kind':'menu','label':'File','children':[
        {'id':'new','kind':'command','label':'New','command':'new'},
        {'id':'missing','kind':'disabled','label':'Unavailable','reason':'No adapter', 'options':{'id':'missing.options','kind':'disabled','label':'Options'}},
        {'id':'native','kind':'native','label':'Recent','native_key':'file.recent'},
    ]}]
    cat = types.ModuleType('axismeld.menubar_catalog')
    cat.build_menubar = lambda: {'sets':{key:('common.file',) for key in ('MODELING','RIGGING','ANIMATION','FX','RENDERING')},'menus':nodes}
    projection = types.ModuleType('axismeld.workspace_menu_catalog')
    projection.build_workspace_menubar = cat.build_menubar
    runtime = types.ModuleType('axismeld.menubar_runtime')
    runtime.source_token = lambda context: 'captured'
    runtime.available = lambda *args: (True, '')
    runtime.state = lambda *args: None
    runtime.run = lambda *args: args
    runtime.shortcut_source = lambda *args: None
    native = types.ModuleType('axismeld.menubar_native')
    native.draw_native = lambda layout, context, key, **kw: layout.log.append(('native', context, key, kw))
    blf = types.ModuleType('blf'); blf.size = lambda *args: None
    blf.dimensions = lambda font, text: (len(text)*10, 12)
    commands = types.ModuleType('axismeld.commands'); commands.PRESET_NAME = 'AxisMeld_Maya_2026'
    translations = types.ModuleType('axismeld.translations')
    translations.iface = translations.tip = lambda text, context='*': text
    package = types.ModuleType('axismeld'); package.__path__ = []
    modules = {'blf':blf,'bpy':bpy,'bpy.types':bpy.types,'bpy.props':props,'axismeld':package,'axismeld.commands':commands,'axismeld.menubar_catalog':cat,'axismeld.workspace_menu_catalog':projection,'axismeld.menubar_runtime':runtime,'axismeld.menubar_native':native,'axismeld.translations':translations}
    with patch.dict(sys.modules, modules):
        spec=importlib.util.spec_from_file_location('tested_menubar_ui', UI)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

class MenuBarUIContract(unittest.TestCase):
    def setUp(self):
        self.ui=load_ui()
        self.context=types.SimpleNamespace(window_manager=types.SimpleNamespace(keyconfigs=types.SimpleNamespace(active=types.SimpleNamespace(name='Blender')), axismeld_menubar_set='MODELING'), window=types.SimpleNamespace(height=300), preferences=types.SimpleNamespace(system=types.SimpleNamespace(ui_scale=2),ui_styles=[types.SimpleNamespace(widget=types.SimpleNamespace(points=11))]))
    def test_opt_in_and_original_header_survives(self):
        layout=Layout(); self.assertFalse(self.ui.draw_bar(layout,self.context)); self.assertEqual(layout.log,[])
        self.context.window_manager.keyconfigs.active.name='AxisMeld_Maya_2026'
        self.assertTrue(self.ui.draw_bar(layout,self.context)); self.assertEqual(len([r for r in layout.log if r[0]=='menu']),1)
        source=(ROOT/'scripts/startup/bl_ui/space_topbar.py').read_text()
        self.assertNotIn('class TOPBAR_HT_menubar',source)
        registration=(ROOT/'scripts/startup/bl_ui/__init__.py').read_text()
        self.assertIn('space_axismeld_menubar.register_props()',registration)
        self.assertIn('space_axismeld_menubar.unregister_props()',registration)
        self.assertIn('TOPBAR_MT_editor_menus.draw_collapsible(context, layout)',source)
        self.assertIn('layout.template_ID_tabs(window, "workspace"',source)
        self.assertIn('screen.back_to_previous',source)
    def test_readonly_draw_native_context_and_options(self):
        layout=Layout(); self.ui.draw_menu(layout,self.context,'common.file')
        native=next(r for r in layout.log if r[0]=='native'); self.assertIs(native[1],self.context)
        ops=[r for r in layout.log if r[0]=='operator']
        self.assertTrue(all(r[2].get('icon') for r in ops))
        option=next(r for r in ops if r[2]['icon']=='PREFERENCES'); self.assertFalse(option[4])
        command=next(r for r in ops if getattr(r[3],'key','')=='new'); self.assertEqual(command[3].token,'captured')
    def test_localized_caption_measurement_uses_the_concrete_ui_context(self):
        rows = [
            {'id':'heading','kind':'separator','label':'Heading'},
            {'id':'submenu','kind':'menu','label':'Submenu','children':[{'kind':'disabled'}]},
            {'id':'empty','kind':'menu','label':'Empty','children':[]},
            {'id':'action','kind':'disabled','label':'Action'},
        ]
        contexts = []
        def translate(text, context='*'):
            contexts.append((text, context))
            return {'Heading':'分组标题','Submenu':'子菜单','Empty':'空菜单','Action':'操作'}[text]
        with patch.object(self.ui, '_NODES', {'test':{'children':rows}}), \
             patch.object(self.ui, 'iface', side_effect=translate), \
             patch.object(self.ui.blf, 'dimensions', return_value=(123,12)) as measured, \
             patch.object(self.ui, '_draw_item'):
            self.ui.draw_menu(Layout(), self.context, 'test')
        self.assertEqual(contexts, [('Heading','*'),('Submenu','*'),('Empty','Operator'),('Action','Operator')])
        self.assertEqual([call.args[1] for call in measured.call_args_list], ['分组标题','子菜单','空菜单','操作'])
    def test_old_saved_chinese_modeling_name_keeps_workspace_menus(self):
        self.context.area = types.SimpleNamespace(type='VIEW_3D')
        self.context.window_manager.keyconfigs.active.name = 'AxisMeld_Maya_2026'
        for name in ('Modeling','Modeling.001','建模','建模.001'):
            self.context.workspace = types.SimpleNamespace(name=name)
            self.assertTrue(self.ui.modeling_workspace(self.context))
        self.context.workspace = types.SimpleNamespace(name='My Custom Workspace')
        self.assertFalse(self.ui.modeling_workspace(self.context))
    def test_semantic_shortcut_context_comes_from_same_execution_token(self):
        source=types.SimpleNamespace(window=object(),screen=object(),scene=object(),
                                     view_layer=object(),area=object(),region=object())
        layout=Layout()
        with patch.object(self.ui.menubar_runtime,'shortcut_source',return_value=source) as resolve:
            self.ui._draw_item(layout,self.context,{'kind':'command','label':'Move Tool',
                                                   'command':'transform.move','options':{}})
        resolve.assert_called_once_with(self.context,'command','transform.move','captured')
        pointers={r[1]:r[2] for r in layout.log if r[0]=='context_pointer'}
        for name in ('window','screen','scene','view_layer','area','region'):
            self.assertIs(pointers['axismeld_shortcut_'+name],getattr(source,name))
        op=next(r[3] for r in layout.log if r[0]=='operator')
        self.assertEqual((op.kind,op.key,op.token),('command','transform.move','captured'))
    def test_empty_dynamic_directory_is_visible_gray_with_reason_and_no_empty_popup(self):
        for children in ([], [{'id':'heading','kind':'separator','label':'Scene items'},
                              {'id':'gap','kind':'separator','label':''}]):
            node={'id':'dynamic','kind':'menu','label':'Assign Existing Material',
                  'children':children,'reason':'Scene material provider is not adapted',
                  'icon':'MATERIAL'}
            layout=Layout()
            with patch.object(self.ui,'_MENU_NAMES',{'dynamic':'AXISMELD_MT_empty'}), \
                 patch.object(self.ui.menubar_runtime,'source_token',side_effect=AssertionError('No capture')):
                self.ui._draw_item(layout,self.context,node)
            self.assertFalse(any(row[0]=='menu' for row in layout.log), 'Empty submenu must not open')
            row=next(row for row in layout.log if row[0]=='operator')
            self.assertEqual((row[2]['text'],row[2]['icon'],row[4]),
                             ('Assign Existing Material','MATERIAL',False))
            self.assertEqual((row[3].kind,row[3].key,row[3].token),('disabled','',''))
            self.assertEqual(row[3].reason,node['reason'])
    def test_directory_with_disabled_body_keeps_its_inspectable_hierarchy(self):
        node={'id':'dynamic','kind':'menu','label':'Unavailable Tools',
              'children':[{'id':'tool','kind':'disabled','label':'Tool'}]}
        layout=Layout()
        with patch.object(self.ui,'_MENU_NAMES',{'dynamic':'AXISMELD_MT_tools'}):
            self.ui._draw_item(layout,self.context,node)
        self.assertEqual([row[1] for row in layout.log if row[0]=='menu'],['AXISMELD_MT_tools'])
        self.assertFalse(any(row[0]=='operator' for row in layout.log))
    def test_all_current_empty_directories_keep_their_labels_icons_and_provenance(self):
        sys.path.insert(0, str(ROOT / 'scripts/modules'))
        from axismeld.workspace_menu_catalog import build_workspace_menubar
        catalog=build_workspace_menubar()
        before=deepcopy(catalog)
        def walk(nodes):
            for node in nodes:
                yield node
                yield from walk(node.get('children',()))
        empty=[node for node in walk(catalog['menus']) if node['kind']=='menu' and
               not any(child['kind']!='separator' for child in node['children'])]
        self.assertEqual(len(empty),9)
        for node in empty:
            with self.subTest(menu=node['id']):
                layout=Layout()
                self.ui._draw_item(layout,self.context,node)
                self.assertFalse(any(row[0]=='menu' for row in layout.log))
                row=next(row for row in layout.log if row[0]=='operator')
                self.assertEqual((row[2]['text'],row[2]['icon']), (node['label'],node['icon']))
                self.assertFalse(row[4])
                self.assertTrue(row[3].reason)
        self.assertEqual(catalog,before)
    def test_hair_curves_header_keeps_actual_native_plugin_host(self):
        for mode, host in [('EDIT_CURVES', 'VIEW3D_MT_edit_curves'), ('EDIT_CURVE', 'VIEW3D_MT_edit_curve')]:
            self.context.mode = mode
            layout = Layout()
            with patch.object(self.ui, 'modeling_workspace', return_value=True), \
                 patch.object(self.ui, '_CATALOG', {'modeling_roots': ('modeling.curves',)}), \
                 patch.object(self.ui, '_NODES', {'modeling.curves': {'label': 'Curves'}}), \
                 patch.object(self.ui, '_MENU_NAMES', {'modeling.curves': 'AXISMELD_MT_test_curves'}):
                self.ui.draw_modeling_menus(layout, self.context)
            self.assertEqual(layout.log[0][1], host)
    def test_component_submenus_keep_native_plugin_hosts_in_modeling(self):
        for label, host in [('Vertex', 'VIEW3D_MT_edit_mesh_vertices'),
                            ('Edge', 'VIEW3D_MT_edit_mesh_edges'),
                            ('Face', 'VIEW3D_MT_edit_mesh_faces')]:
            identifier = 'viewport.modeling.' + label.lower()
            node = {'id': identifier, 'kind': 'menu', 'label': label,
                    'children': [{'id': identifier + '.entry', 'kind': 'disabled', 'label': 'Entry'}]}
            with patch.object(self.ui, '_MENU_NAMES', {identifier: 'AXISMELD_MT_test_component'}):
                for active, expected in [(True, host), (False, 'AXISMELD_MT_test_component')]:
                    with patch.object(self.ui, 'modeling_workspace', return_value=active):
                        layout = Layout()
                        self.ui._draw_item(layout, self.context, node)
                    menu = next(row for row in layout.log if row[0] == 'menu')
                    self.assertEqual(menu[1], expected)
                    self.assertEqual(menu[2]['text'], label)
    def test_dispatch_never_recaptures_or_adds_undo(self):
        op=self.ui.AXISMELD_OT_menubar_execute(); op.kind='command'; op.key='new'; op.token='old'
        self.assertEqual(op.execute(self.context),(self.context,'command','new','old'))
        self.assertNotIn('UNDO',op.bl_options)
    def test_complete_columns_no_pagination(self):
        rows=[{'id':str(i),'label':str(i),'kind':'disabled'} for i in range(70)]
        columns=self.ui.menu_columns(rows,self.context)
        self.assertGreater(len(columns),1)
        self.assertEqual([r['id'] for c in columns for r in c],[str(i) for i in range(70)])
    def test_child_modal_belongs_to_child_and_native_errors_cancel(self):
        op=self.ui.AXISMELD_OT_menubar_execute(); op.kind='command'; op.key='new'; op.token='old'
        reports=[]; op.report=lambda level, message: reports.append((level,message))
        with patch.object(self.ui.menubar_runtime,'run',return_value={'RUNNING_MODAL'}):
            self.assertEqual(op.execute(self.context),{'FINISHED'})
        for error in (RuntimeError('poll failed'),ValueError('source expired')):
            with patch.object(self.ui.menubar_runtime,'run',side_effect=error):
                self.assertEqual(op.execute(self.context),{'CANCELLED'})
        self.assertEqual(len(reports),2)
    def test_unadapted_indicator_is_gray_and_never_uses_capture_checked(self):
        for indicator, icon in [('checkbox','CHECKBOX_DEHLT'),('radio','RADIOBUT_OFF')]:
            layout=Layout()
            self.ui._draw_item(layout,self.context,{'id':'missing','kind':'disabled','label':'Missing','indicator':indicator,'checked':True})
            state=next(r for r in layout.log if r[0]=='label')
            self.assertEqual(state[1]['icon'],icon); self.assertFalse(state[2])
        layout=Layout()
        with patch.object(self.ui.menubar_runtime,'state',return_value=('radio',True)):
            self.ui._draw_item(layout,self.context,{'id':'plain','kind':'command','label':'Plain','command':'new','origin':'maya','indicator':''})
        self.assertFalse(any(r[0]=='label' for r in layout.log))
    def test_group_heading_keeps_next_item_in_same_column(self):
        nodes=[{'id':str(i),'kind':'disabled','label':str(i)} for i in range(2)]
        nodes += [{'id':'title','kind':'separator','label':'Group'}, {'id':'gap','kind':'separator','label':''}, {'id':'child','kind':'disabled','label':'Child'}]
        columns=self.ui.menu_columns(nodes,self.context)
        containing=next(column for column in columns if any(n['id']=='title' for n in column))
        self.assertIn('child',[n['id'] for n in containing])
        self.assertEqual([n['id'] for col in columns for n in col],[n['id'] for n in nodes])
    def test_enum_session_only_and_five_modes(self):
        self.ui.register_props()
        prop=self.ui.bpy.types.WindowManager.axismeld_menubar_set
        self.assertEqual(len(prop['items']),5); self.assertIn('SKIP_SAVE',prop['options'])
        self.ui.unregister_props(); self.assertFalse(hasattr(self.ui.bpy.types.WindowManager,'axismeld_menubar_set'))
    def test_column_uses_measured_glyph_width_and_option_cell(self):
        layout=Layout()
        self.ui._NODES['common.file']['children']=[n for n in self.ui._NODES['common.file']['children'] if n['kind']=='disabled']
        with patch.object(self.ui.blf,'dimensions',return_value=(800,20)):
            self.ui.draw_menu(layout,self.context,'common.file')
        column=next(r[1] for r in layout.log if r[0]=='column')
        self.assertGreaterEqual(column.ui_units_x*20,800/2+48+24)
    def test_native_shortcut_width_is_not_overridden_by_caption_measure(self):
        layout=Layout();self.ui.draw_menu(layout,self.context,'common.file')
        column=next(r[1] for r in layout.log if r[0]=='column')
        self.assertFalse(hasattr(column,'ui_units_x'))
    def test_semantic_shortcut_width_uses_native_estimate(self):
        layout=Layout()
        self.ui._NODES['common.file']['children']=[n for n in self.ui._NODES['common.file']['children'] if n['kind']!='native']
        self.ui.draw_menu(layout,self.context,'common.file')
        column=next(r[1] for r in layout.log if r[0]=='column')
        self.assertFalse(hasattr(column,'ui_units_x'))
    def test_modeling_host_keeps_native_modes_and_avoids_duplicate_roots(self):
        self.context.window_manager.keyconfigs.active.name='AxisMeld_Maya_2026'
        self.context.workspace=types.SimpleNamespace(name='Modeling')
        self.context.area=types.SimpleNamespace(type='VIEW_3D')
        layout=Layout(); hosted=self.ui.viewport_menu_layout(layout,self.context)
        for identifier in ('VIEW3D_MT_view','VIEW3D_MT_edit_mesh','VIEW3D_MT_edit_mesh_vertices','VIEW3D_MT_uv_map','VIEW3D_MT_sculpt'):
            hosted.menu(identifier)
        self.assertEqual([r[1] for r in layout.log],['VIEW3D_MT_view','VIEW3D_MT_sculpt'])
        self.context.workspace.name='Layout'
        self.assertIs(self.ui.viewport_menu_layout(layout,self.context),layout)
    def test_global_supplement_and_other_menu_sets_stay_opt_in(self):
        layout=Layout()
        self.ui.draw_supplement(layout,self.context,'common.file')
        self.ui.draw_menu_sets_entry(layout,self.context)
        self.assertEqual(layout.log,[])
        self.context.window_manager.keyconfigs.active.name='AxisMeld_Maya_2026'
        self.ui.draw_supplement(layout,self.context,'common.file')
        self.ui.draw_menu_sets_entry(layout,self.context)
        menus=[r for r in layout.log if r[0]=='menu']
        self.assertEqual(menus[0][1],self.ui._MENU_NAMES['common.file'])
        self.assertEqual(menus[1][2]['text'],'Maya Menu Sets')
    def test_native_menu_ids_host_new_groups_only_in_modeling(self):
        self.assertNotIn('Blender Tools', UI.read_text())
        self.context.window_manager.keyconfigs.active.name='AxisMeld_Maya_2026'
        self.context.workspace=types.SimpleNamespace(name='Modeling')
        self.context.area=types.SimpleNamespace(type='VIEW_3D')
        with patch.object(self.ui,'draw_menu') as draw:
            self.assertTrue(self.ui.draw_native_modeling_menu(Layout(),self.context,'viewport.modeling.vertex'))
            self.assertEqual(draw.call_args.args[2],'viewport.modeling.vertex')
            self.context.workspace.name='Layout'
            self.assertFalse(self.ui.draw_native_modeling_menu(Layout(),self.context,'viewport.modeling.vertex'))
            self.assertEqual(draw.call_count,1)
    def test_native_groups_keep_runtime_drawing_and_actual_height_budget(self):
        node={'id':'native.vertex.shape','kind':'native_group','label':'Shape Keys','group_key':'vertex.shape','row_count_hint':6}
        renderer=types.ModuleType('bl_ui.space_axismeld_native_modeling')
        drawn=[]
        renderer.draw_group=lambda *args,**kw:drawn.append((args,kw))
        with patch.dict(sys.modules,{'bl_ui':types.SimpleNamespace(space_axismeld_native_modeling=renderer)}):
            layout=Layout(); self.ui._draw_item(layout,self.context,node)
        self.assertEqual(drawn[0][0][1:],(self.context,'vertex.shape'))
        self.context.window.height=390
        self.context.preferences.system.ui_scale=1
        nodes=[dict(node,id='first'),dict(node,id='second'),dict(node,id='third')]
        columns=self.ui.menu_columns(nodes,self.context)
        self.assertEqual([len(c) for c in columns],[2,1])

if __name__=='__main__': unittest.main()
