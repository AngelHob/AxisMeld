import os,sys,traceback
from pathlib import Path
import bpy
from mathutils import Vector
root=Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
bpy.context.preferences.use_preferences_save=False
bpy.context.preferences.view.show_splash=False

def steps():
    win=bpy.context.window
    bpy.ops.wm.window_fullscreen_toggle()
    for _ in range(8):yield
    print("NORMAL_CAPTURE_WINDOW", win.width, win.height, flush=True)
    preset=next(Path(p)/'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig') if (Path(p)/'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    for _ in range(8):yield
    area=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    with bpy.context.temp_override(window=win,area=area,region=region):
        bpy.ops.screen.screen_full_area()
    for _ in range(8):yield
    area=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    area.spaces.active.show_region_ui=False
    area.spaces.active.show_region_toolbar=False
    for obj in tuple(bpy.context.scene.objects):
        if obj.type!='MESH':bpy.data.objects.remove(obj,do_unlink=True)
    region.data.view_location=Vector((0,0,0))
    region.data.view_distance=8
    for _ in range(8):yield
    from axismeld import hotbox_runtime
    out=Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
    x,y=int(region.x+region.width*.5),int(region.y+region.height-200)
    def event(kind,value='PRESS',**kw):win.event_simulate(type=kind,value=value,x=x,y=y,**kw)
    initial_windows={w.as_pointer() for w in bpy.context.window_manager.windows}
    with bpy.context.temp_override(window=win,area=area,region=region):
        bpy.ops.wm.window_new()
    for _ in range(12):yield
    child=next(w for w in bpy.context.window_manager.windows if w.as_pointer() not in initial_windows)
    ca=next(a for a in child.screen.areas if a.type=='VIEW_3D')
    cr=next(r for r in ca.regions if r.type=='WINDOW')
    cx,cy=int(cr.x+cr.width/2),int(cr.y+100)
    def child_event(kind,value='PRESS',**kw):
        child.event_simulate(type=kind,value=value,x=cx,y=cy,**kw)
    child_event('MOUSEMOVE','NOTHING');child_event('LEFT_SHIFT',shift=True)
    child_event('RIGHTMOUSE',shift=True)
    for _ in range(12):yield
    assert any(op.bl_idname=='VIEW3D_OT_axismeld_hotbox' for op in child.modal_operators)
    with bpy.context.temp_override(window=child,area=ca,region=cr):
        bpy.ops.wm.window_close()
    for _ in range(14):yield
    assert {w.as_pointer() for w in bpy.context.window_manager.windows}==initial_windows
    print('PASS held child-window close; surviving main window intact',flush=True)
    x,y=int(region.x+region.width/2),int(region.y+100)
    for cycle in ('after_child_close','scale_change','after_scale_change'):
        event('MOUSEMOVE','NOTHING');event('LEFT_SHIFT',shift=True);event('RIGHTMOUSE',shift=True)
        for _ in range(10):yield
        assert sum(op.bl_idname=='VIEW3D_OT_axismeld_hotbox' for op in win.modal_operators)==1
        if cycle=='scale_change':
            bpy.context.preferences.view.ui_scale=1.5
            for _ in range(12):yield
            event('MOUSEMOVE','NOTHING',shift=True)
            for _ in range(8):yield
            print('SCALE_AFTER_HANDLERS',[op.bl_idname for op in win.modal_operators],flush=True)
            assert not any(op.bl_idname=='VIEW3D_OT_axismeld_hotbox' for op in win.modal_operators)
        else:
            event('ESC',shift=True);event('ESC','RELEASE',shift=True)
        event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
        for _ in range(10):yield
        assert not win.modal_operators
        if cycle=='scale_change':
            bpy.context.preferences.view.ui_scale=1
            for _ in range(10):yield
        print('PASS lifecycle',cycle,flush=True)
    print('AXISMELD_FULL_MENU_LIFECYCLE_PASS',flush=True)

generator=steps()
def tick():
    try:next(generator);return .05
    except StopIteration:bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)
