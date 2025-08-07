bl_info = {
    "name": "Attack of Modifier",
    "author": "Abdulrahman Baggash",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Press Shift+Q",
    "description": "Add-on for Attack of Modifier fast",
    "warning": "",
    "doc_url": "https://github.com/woow3d/attack-of-modifier",
    "category": "Object",
}

import bpy
from bpy.types import Menu

# === أدوات CURVE ===
def sep_curve(obj):
    if obj is None or obj.type != 'CURVE':
        print("يجب أن يكون الكائن النشط منحنى (Curve)")
        return
    connected_points = []
    for spline in obj.data.splines:
        points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
        connected_group = [point.co[:3] for point in points]
        connected_points.append(connected_group)
    return connected_points

def separate_curve():
    obj = bpy.context.active_object
    name = obj.name
    sd = sep_curve(obj)
    for i, group in enumerate(sd):
        tolerance = 1e-5
        def is_close(v1, v2, tol):
            return all(abs(a - b) < tol for a, b in zip(v1, v2))

        if obj and obj.type == 'CURVE':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.select_all(action='DESELECT')
            for spline in obj.data.splines:
                if spline.type == 'BEZIER':
                    for point in spline.bezier_points:
                        for target_coords in group:
                            if is_close(point.co, target_coords, tolerance):
                                point.select_control_point = True
                else:
                    for point in spline.points:
                        for target_coords in group:
                            if is_close(point.co.xyz, target_coords, tolerance):
                                point.select = True
            bpy.ops.curve.separate()
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='DESELECT')
    if name in bpy.data.objects:
        bpy.context.view_layer.objects.active = bpy.data.objects[name]
        bpy.ops.object.delete()

def separate_by_loose_parts():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')

# === BOOLEAN ===
def boolean(object_a_name, object_b_name):
    object_a = bpy.data.objects.get(object_a_name)
    object_b = bpy.data.objects.get(object_b_name)
    if object_a and object_b:
        mod = object_a.modifiers.new(name="Boolean", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = object_b
        mod.solver = 'FAST'
    else:
        print(f"Object '{object_a_name}' or '{object_b_name}' not found.")

def boolean_all(context):
    selected = bpy.context.active_object
    name = selected.name
    others = [obj for obj in bpy.context.selected_objects if obj != selected]
    for obj in others:
        obj.hide_viewport = True
        boolean(name, obj.name)

# === MIRROR ===
def mirror(target_name, context):
    if target_name in bpy.data.objects:
        obj = bpy.data.objects[target_name]
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = bpy.context.active_object
        empty.name = "Em." + target_name
        empty.location = obj.location
        mod = obj.modifiers.new(name="Mirror", type='MIRROR')
        mod.mirror_object = empty
        bpy.context.view_layer.objects.active = empty
        empty.select_set(True)
        bpy.ops.transform.translate('INVOKE_DEFAULT')
    else:
        print(f"Object '{target_name}' not found.")

# === COPY & SNAP ===
def copy_snap(original_name, target_name, context):
    if original_name in bpy.data.objects and target_name in bpy.data.objects:
        original = bpy.data.objects[original_name]
        target = bpy.data.objects[target_name]
        new_obj = original.copy()
        new_obj.data = original.data.copy()
        bpy.context.collection.objects.link(new_obj)
        new_obj.location = target.location
        return new_obj.name
    else:
        print(f"One or both objects not found.")
        return 0

# === ARRAY + CURVE ===
def array(obj_name, curve_name):
    obj = bpy.data.objects.get(obj_name)
    curve = bpy.data.objects.get(curve_name)
    if obj and curve:
        mod = obj.modifiers.new(name="Array", type='ARRAY')
        mod.fit_type = 'FIT_CURVE'
        mod.curve = curve

def curve(obj_name, curve_name):
    obj = bpy.data.objects.get(obj_name)
    curve_obj = bpy.data.objects.get(curve_name)
    if obj and curve_obj:
        mod = obj.modifiers.new(name="Curve", type='CURVE')
        mod.object = curve_obj

def array_fit(context):
    selected = bpy.context.active_object
    name = selected.name
    others = [obj for obj in bpy.context.selected_objects if obj != selected]
    for obj in others:
        dup = copy_snap(obj.name, name, context)
        if dup != 0:
            apply_scale(dup)
            array(dup, name)
            curve(dup, name)

def apply_scale(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# === BEVEL / CONVERT ===
def bevel_depth(number, context):
    for obj in bpy.context.selected_objects:
        if obj.type == 'CURVE':
            obj.data.bevel_depth = number
            obj.data.bevel_resolution = 12

def convert(context):
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target='CURVE')

# === SOLIDIFY ===
def solidify_gold(thickness, context):
    for obj in bpy.context.selected_objects:
        apply_scale(obj.name)
        mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
        mod.thickness = thickness
        mod.offset = 0.0
        mod.use_rim = True
        mod.use_even_offset = True
        mod.use_quality_normals = True
        mod.thickness_clamp = 0.0
        if obj.type == "MESH":
            for name in ["Shell", "Rim", "Pin"]:
                obj.vertex_groups.new(name=name)
            mod.shell_vertex_group = "Shell"
            mod.rim_vertex_group = "Rim"

# === CURVE OBJ ===
def curve_obj(context):
    selected = bpy.context.active_object
    name = selected.name
    others = [obj for obj in bpy.context.selected_objects if obj != selected]
    for obj in others:
        curve(obj.name, name)

# === SHRINKWRAP ===
def shrinkwrap(context):
    selected = bpy.context.selected_objects
    active = bpy.context.view_layer.objects.active
    if len(selected) > 1 and active:
        target = next((obj for obj in selected if obj != active), None)
        if target:
            mod = target.modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')
            mod.target = active
            mod.wrap_method = 'NEAREST_SURFACEPOINT'
        else:
            print("لم يتم العثور على كائن غير نشط.")
    else:
        print("يجب تحديد كائنين على الأقل.")

# === PIE MENU ===
class VIEW3D_PIE_template(Menu):
    bl_label = "woow3d.com"
    bl_idname = "VIEW3D_PIE_template"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator("wm.print_number", text="Solidify", icon='MOD_SOLIDIFY').number = 1
        pie.operator("wm.print_number", text="Curve", icon='OUTLINER_OB_CURVE').number = 2
        pie.operator("wm.print_number", text="Split", icon='FACE_MAPS').number = 4
        pie.operator("wm.print_number", text="Boolean", icon='MOD_BOOLEAN').number = 5
        pie.operator("wm.print_number", text="To Curve", icon='MOD_CURVE').number = 6
        pie.operator("wm.print_number", text="Mirror", icon='MOD_MIRROR').number = 7
        pie.operator("wm.print_number", text="Curve Array", icon='PARTICLE_POINT').number = 8
        pie.operator("wm.print_number", text="Shrinkwrap", icon='SNAP_FACE_NEAREST').number = 9

class WM_OT_print_number(bpy.types.Operator):
    bl_idname = "wm.print_number"
    bl_label = "Attack"
    number: bpy.props.IntProperty()

    def execute(self, context):
        selected = bpy.context.active_object
        name = selected.name if selected else "None"
        if self.number == 1:
            solidify_gold(0.0, context)
        elif self.number == 2:
            if selected.type == 'CURVE':
                bevel_depth(0.0, context)
            else:
                convert(context)
        elif self.number == 4:
            if selected.type == 'CURVE':
                separate_curve()
            else:
                separate_by_loose_parts()
        elif self.number == 5:
            boolean_all(context)
        elif self.number == 6:
            curve_obj(context)
        elif self.number == 7:
            mirror(name, context)
        elif self.number == 8:
            array_fit(context)
        elif self.number == 9:
            shrinkwrap(context)
        return {'FINISHED'}

class OBJECT_OT_call_pie_menu(bpy.types.Operator):
    bl_idname = "wm.call_pie_menu"
    bl_label = "woow3d.com"

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="VIEW3D_PIE_template")
        return {'FINISHED'}

# === REGISTER ===
addon_keymaps = []

def register():
    bpy.utils.register_class(VIEW3D_PIE_template)
    bpy.utils.register_class(WM_OT_print_number)
    bpy.utils.register_class(OBJECT_OT_call_pie_menu)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_pie_menu", type='Q', value='PRESS', shift=True)
    addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(VIEW3D_PIE_template)
    bpy.utils.unregister_class(WM_OT_print_number)
    bpy.utils.unregister_class(OBJECT_OT_call_pie_menu)

if __name__ == "__main__":
    register()
