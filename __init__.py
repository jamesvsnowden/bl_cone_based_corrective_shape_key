# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Cone-Based Corrective Shape Key",
    "description": "Cone-based drivers for corrective shape keys.",
    "author": "James Snowden",
    "version": (1, 0, 0),
    "blender": (2, 90, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "https://cone_based_corrective_shape_key.github.io",
    "tracker_url": "https://github.com/jamesvsnowden/bl_cone_based_corrective_shape_key/issues",
    "category": "Animation",
}

import math
import typing
import uuid
import bpy
import mathutils
from .lib import curve_mapping
from .lib.curve_mapping import draw_curve_manager_ui, to_bezier, keyframe_points_assign
from .lib.driver_utils import driver_ensure, driver_find, driver_remove, driver_variables_empty
from .lib.transform_utils import ROTATION_MODE_ITEMS, transform_matrix, transform_matrix_element

def direction_of(q: mathutils.Quaternion) -> mathutils.Vector:
    w, x, y, z = q
    return mathutils.Vector((2.0*(x*y-w*z), 1.0-2.0*(x*x+z*z), 2.0*(y*z+w*x)))

curve_mapping.BLCMAP_OT_curve_copy.bl_idname = "cone_corr_sk.curve_copy"
curve_mapping.BLCMAP_OT_curve_paste.bl_idname = "cone_corr_sk.curve_paste"
curve_mapping.BLCMAP_OT_curve_edit.bl_idname = "cone_corr_sk.curve_edit"

COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
COMPAT_OBJECTS = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}

class ConeBasedDriverCurveMap(curve_mapping.BCLMAP_CurveManager, bpy.types.PropertyGroup):

    def update(self, context: typing.Optional[bpy.types.Context] = None) -> None:
        super().update(context)
        self.id_data.path_resolve(self.path_from_id().rpartition(".")[0]).update()

class ConeBasedDriver(bpy.types.PropertyGroup):
    """Manages and stores settings for a cone based corrective shape key"""

    def get_bone_target(self) -> str:
        fcurve = driver_find(self.id_data, self.data_path)
        if fcurve is not None:
            variables = fcurve.driver.variables
            if len(variables) > 1:
                return variables[1].targets[0].bone_target
        return ""

    def update(self, context: typing.Optional[bpy.types.Context]=None) -> None:

        if isinstance(context, str):
            bone_target = context
        else:
            bone_target = self.get_bone_target()

        fcurve = driver_ensure(self.id_data, self.data_path)
        points = to_bezier(self.falloff.curve.points,
                            x_range=(1.0-self.radius, 1.0),
                            y_range=(0.0, self.value),
                            extrapolate=False)

        keyframe_points_assign(fcurve.keyframe_points, points)

        driver = fcurve.driver
        variables = driver_variables_empty(driver)

        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = self.identifier

        target = variable.targets[0]
        target.id_type = 'KEY'
        target.id = self.id_data
        target.data_path = "reference_key.value"

        for axis in 'WXYZ':

            variable = variables.new()
            variable.type = 'TRANSFORMS'
            variable.name = axis.lower()

            target = variable.targets[0]
            target.id = self.object
            target.bone_target = bone_target
            target.transform_type = f'ROT_{axis}'
            target.transform_space = 'LOCAL_SPACE'
            target.rotation_mode = 'QUATERNION'

        x, y, z = direction_of(self.rotation_quaternion)
        driver.type = 'SCRIPTED'
        # The function runs through the following steps:
        # - Convert the target bone's (local space) rotation quaternion to a direction vector
        # - Calculate the dot product between the pose's direction vector and the target bone's rotation vector
        # - Range the result and apply a inverse sine function to negate the effect of the dot product calculation so that the fcurve operates in the 0-1 range
        driver.expression = f'(asin(2.0*(x*y-w*z)*{x}+(1.0-2.0*(x*x+z*z))*{y}+2.0*(y*z+w*x)*{z})--(pi/2.0))/pi'

    bone_target: bpy.props.StringProperty(
        name="Bone",
        description="The bone to read rotations from",
        get=get_bone_target,
        set=update,
        options=set()
        )

    @property
    def data_path(self) -> str:
        return f'key_blocks["{self.name}"].value'

    falloff: bpy.props.PointerProperty(
        name="Falloff",
        description="The falloff curve for the driver",
        type=ConeBasedDriverCurveMap,
        options=set()
        )

    identifier: bpy.props.StringProperty(
        name="Shape",
        description="Unique identifier used to hold a reference to the driven shape key.",
        get=lambda self: self.get("identifier", ""),
        options={'HIDDEN'}
        )

    mute: bpy.props.BoolProperty(
        name="Mute",
        description=("Whether or not the driven shape key's driver is enabled. Disabling "
                     "the driver allows (temporary) editing of the shape key's value in the UI"),
        default=False,
        options=set(),
        update=update
        )

    object: bpy.props.PointerProperty(
        name="Object",
        description="The armature object",
        type=bpy.types.Object,
        poll=lambda _, ob: ob.type == 'ARMATURE',
        update=update,
        options=set()
        )

    radius: bpy.props.FloatProperty(
        name="Radius",
        description=("The cone driver's radius. Controls how close to the center "
                     "the target's rotation is before the shape key is activated."),
        min=0.0,
        max=1.0,
        default=0.2,
        precision=3,
        update=update,
        options=set()
        )

    def get_rotation_angle(self) -> float:
        return self.rotation_quaternion.to_axis_angle()[1]

    def set_rotation_angle(self, value: float) -> None:
        self.rotation_quaternion = mathutils.Quaternion(self.get_rotation_axis(), value)

    def get_rotation_axis(self) -> mathutils.Vector:
        return self.rotation_quaternion.to_axis_angle()[0]

    def set_rotation_axis(self, value: typing.Tuple[float, float, float]) -> None:
        self.rotation_quaternion = mathutils.Quaternion(value, self.get_rotation_angle())

    rotation_angle: bpy.props.FloatProperty(
        name="Rotation",
        description="Rotation value for the driver",
        subtype='ANGLE',
        get=get_rotation_angle,
        set=set_rotation_angle,
        precision=3,
        options=set()
        )

    rotation_axis: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Rotation value for the driver",
        size=3,
        subtype='XYZ',
        get=get_rotation_axis,
        set=set_rotation_axis,
        precision=3,
        options=set()
        )

    rotation_quaternion: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Rotation value for the driver",
        size=4,
        default=(1.0, 0.0, 0.0, 0.0),
        precision=3,
        subtype='QUATERNION',
        update=update,
        options=set()
        )

    def get_rotation_euler(self) -> mathutils.Euler:
        return self.rotation_quaternion.to_euler()

    def set_rotation_euler(self, value: typing.Tuple[float, float, float]) -> None:
        self.rotation_quaternion = mathutils.Euler(value).to_quaternion()

    rotation_euler: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Rotation value for the driver",
        size=3,
        subtype='EULER',
        precision=3,
        get=get_rotation_euler,
        set=set_rotation_euler,
        options=set()
        )

    rotation_mode: bpy.props.EnumProperty(
        name="Mode",
        description="The rotation value. Editing purposes only, the actual mode does not affect the driver results.",
        items=[
            ('EULER'     , "Euler"     , "Euler angles"       , 'NONE', 0),
            ('QUATERNION', "Quaternion", "Quaternion rotation", 'NONE', 1),
            ('AXIS_ANGLE', "Axis/Angle", "Axis/Angle rotation", 'NONE', 2),
            ],
        default='QUATERNION',
        options=set()
        )

    value: bpy.props.FloatProperty(
        name="Goal",
        description="The value of the shape key when fully activated by the driver",
        default=1.0,
        options=set(),
        update=update
        )

class SHAPEKEYCONEDRIVER_OT_add(bpy.types.Operator):

    bl_idname = 'shape_key_cone_driver.add'
    bl_label = "Add Cone-Based Driver"
    bl_description = "Add a cone-based driver to the shape key"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shape = object.active_shape_key
                if shape is not None:
                    key = shape.id_data
                    return (key.use_relative
                            and shape != key.reference_key
                            and (not key.is_property_set("cone_based_drivers")
                                 or shape.name not in key.cone_based_drivers))
        return False

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        object = context.object
        shape = object.active_shape_key
        key = shape.id_data
        settings = key.cone_based_drivers.add()
        settings["name"] = shape.name
        settings["identifier"] = f'conedriver_{uuid.uuid4()}'
        settings["value"] = shape.value if shape.value > 0.01 else 1.0
        settings.falloff.__init__(interpolation='QUAD', easing='EASE_IN_OUT')
        settings.update()
        return {'FINISHED'}

class SHAPEKEYCONEDRIVER_OT_remove(bpy.types.Operator):

    bl_idname = 'shape_key_cone_driver.remove'
    bl_label = "Remove Cone-Based Driver"
    bl_description = "Remove the shape key's cone-based driver"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shape = object.active_shape_key
                if shape is not None:
                    key = shape.id_data
                    return (key.use_relative
                            and shape != key.reference_key
                            and key.is_property_set("cone_based_drivers")
                            and shape.name in key.cone_based_drivers)
        return False

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        object = context.object
        shape = object.active_shape_key
        key = shape.id_data
        driver_remove(key, f'key_blocks["{shape.name}"].value')
        key.cone_based_drivers.remove(key.cone_based_drivers.find(shape.name))
        return {'FINISHED'}

class SHAPEKEYCONEDRIVER_OT_center_update(bpy.types.Operator):

    bl_idname = 'shape_key_cone_driver.center_update'
    bl_label = "Update Center"
    bl_description = "Update the rotation center from the target's current rotation value"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shape = object.active_shape_key
                if shape is not None:
                    key = shape.id_data
                    if (key.use_relative
                        and shape != key.reference_key
                        and key.is_property_set("cone_based_drivers")):
                        settings = key.cone_based_drivers.get(shape.name)
                        if settings:
                            object = settings.object
                            return (object is not None
                                    and object.type == 'ARMATURE'
                                    and settings.bone_target in object.pose.bones)
        return False

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        shape = context.object.active_shape_key
        settings = shape.id_data.cone_based_drivers[shape.name]
        object = settings.object
        target = settings.bone_target
        matrix = transform_matrix(object.pose.bones[target], 'LOCAL_SPACE')
        settings.rotation_quaternion = matrix.to_quaternion()
        return {'FINISHED'}

class SHAPEKEYCONEDRIVER_OT_radius_calculate(bpy.types.Operator):

    bl_idname = 'shape_key_cone_driver.radius_calculate'
    bl_label = "Calculate Radius"
    bl_description = "Calculate the radius based on the distance to the nearest neighboring target pose"
    bl_options = {'INTERNAL', 'UNDO'}

    method: bpy.props.EnumProperty(
        name="Calculate Radius",
        items=[
            ('CENT', "Nearest Neighbor", ""),
            ('EDGE', "Nearest Neighbor (No Intersection)", ""),
            ],
            default='CENT',
            options=set()
        )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shape = object.active_shape_key
                if shape is not None:
                    key = shape.id_data
                    if (key.use_relative
                        and shape != key.reference_key
                        and key.is_property_set("cone_based_drivers")):
                        settings = key.cone_based_drivers.get(shape.name)
                        if settings:
                            object = settings.object
                            return (object is not None
                                    and object.type == 'ARMATURE'
                                    and bool(settings.bone_target))
        return False

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        shape = context.object.active_shape_key
        key = shape.id_data
        data = key.cone_based_drivers
        item = data[shape.name]
        object = item.object
        bone = item.bone_target
        neighbors = [x for x in data if x != item and x.object == object and x.bone_target == bone]
        if neighbors:
            value = direction_of(item.rotation_quaternion)
            radii = []
            outer = self.method == 'EDGE'
            for other in neighbors:
                radius = (math.asin(value.dot(direction_of(other.rotation_quaternion))) - -(math.pi/2.0))/math.pi
                radii.append(max(0.0, radius - other.radius if outer else radius))
            radius = min(radii)
            if radius > 0.001:
                item.radius = radius
        return {'FINISHED'}

UI_SPLIT = 0.385

def layout_split(layout: bpy.types.UILayout,
                 label: typing.Optional[str]="",
                 align: typing.Optional[bool]=False,
                 factor: typing.Optional[float]=0.385,
                 decorate: typing.Optional[bool]=True,
                 decorate_fill: typing.Optional[bool]=True
                 ) -> typing.Union[bpy.types.UILayout, typing.Tuple[bpy.types.UILayout, ...]]:
    split = layout.row().split(factor=factor)
    col_a = split.column(align=align)
    col_a.alignment = 'RIGHT'
    if label:
        col_a.label(text=label)
    row = split.row()
    col_b = row.column(align=align)
    if decorate:
        col_c = row.column(align=align)
        if decorate_fill:
            col_c.label(icon='BLANK1')
        else:
            return (col_b, col_c) if label else (col_a, col_b, col_c)
    return col_b if label else (col_a, col_b)

class SHAPEKEYCONEDRIVER_PT_settings(bpy.types.Panel):

    bl_parent_id = "DATA_PT_shape_keys"
    bl_label = "Cone-Based Driver"
    bl_description = "Cone-Based driver settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        if object is not None:
            shape = object.active_shape_key
            if shape is not None:
                key = shape.id_data
                return (key.is_property_set("cone_based_drivers")
                        and shape.name in key.cone_based_drivers)
        return False

    def draw(self, context: bpy.types.Context) -> None:
        object = context.object
        target = object.active_shape_key
        layout = self.layout
        key = target.id_data
        settings = key.cone_based_drivers[target.name]
        
        values = layout_split(layout, "Target", align=True)
        object = settings.object

        subrow = values.row(align=True)
        subrow.alert = object is None or object.type != 'ARMATURE'

        values.prop(settings, "object", text="")
        subrow = values.row(align=True)
        if object is None or object.type != 'ARMATURE':
            subrow.prop(settings, "bone_target", icon='BONE_DATA', text="")
        else:
            subrow.alert = settings.bone_target != "" and settings.bone_target not in object.data.bones
            subrow.prop_search(settings, "bone_target", object.data, "bones", icon='BONE_DATA', text="")

        labels, values, decorations = layout_split(layout, align=True, decorate_fill=False)
        labels.label(text="Center")
        
        mode = settings.rotation_mode
        if mode == 'QUATERNION':
            for index, axis in enumerate('WXYZ'):
                values.prop(settings, "rotation_quaternion", text=axis, index=index)
        elif mode == 'AXIS_ANGLE':
            values.prop(settings, "rotation_angle", text="W")
            for index, axis in enumerate('XYZ'):
                values.prop(settings, "rotation_axis", text=axis, index=index)
        else:
            for index, axis in enumerate('XYZ'):
                values.prop(settings, "rotation_euler", text=axis, index=index)

        values.separator(factor=0.5)
        values.prop(settings, "rotation_mode", text="")

        decorations.operator(SHAPEKEYCONEDRIVER_OT_center_update.bl_idname,
                             text="",
                             icon='IMPORT',
                             emboss=False)

        values = layout_split(layout, "Radius").row(align=True)
        values.prop(settings, "radius", text="")
        values.operator_menu_enum(SHAPEKEYCONEDRIVER_OT_radius_calculate.bl_idname, "method",
                                  text="",
                                  icon='DOWNARROW_HLT')

        labels, values = layout_split(layout, decorate=False)
        labels.label(text="Easing")
        draw_curve_manager_ui(values, settings.falloff)
        layout_split(layout, label="Goal").prop(settings, "value", text="")

CLASSES = [
    curve_mapping.BLCMAP_CurvePointProperties,
    curve_mapping.BLCMAP_CurveProperties,
    curve_mapping.BLCMAP_CurvePoint,
    curve_mapping.BLCMAP_CurvePoints,
    curve_mapping.BLCMAP_Curve,
    curve_mapping.BLCMAP_OT_curve_copy,
    curve_mapping.BLCMAP_OT_curve_paste,
    curve_mapping.BLCMAP_OT_curve_edit,
    ConeBasedDriverCurveMap,
    ConeBasedDriver,
    SHAPEKEYCONEDRIVER_OT_add,
    SHAPEKEYCONEDRIVER_OT_remove,
    SHAPEKEYCONEDRIVER_OT_center_update,
    SHAPEKEYCONEDRIVER_OT_radius_calculate,
    SHAPEKEYCONEDRIVER_PT_settings,
    ]

def draw_menu_items(menu: bpy.types.Menu, context: bpy.types.Context) -> None:
    object = context.object
    if object is not None:
        shape = object.active_shape_key
        if shape is not None:
            key = shape.id_data
            if shape != key.reference_key:
                fcurve = driver_find(key, f'key_blocks["{shape.name}"].value')
                if fcurve is None:
                    layout = menu.layout
                    layout.separator()
                    layout.operator(SHAPEKEYCONEDRIVER_OT_add.bl_idname,
                                    icon='DECORATE_DRIVER',
                                    text="Add Cone-Based Driver")
                else:
                    variables = fcurve.driver.variables
                    if len(variables) == 5 and variables[0].name.startswith("conedriver_"):
                        layout = menu.layout
                        layout.separator()
                        layout.operator(SHAPEKEYCONEDRIVER_OT_remove.bl_idname,
                                        icon='REMOVE',
                                        text="Remove Cone-Based Driver")

MESSAGE_BROKER = object()

def shape_key_name_callback():
    for key in bpy.data.shape_keys:
        if key.is_property_set("cone_based_drivers"):
            animdata = key.animation_data
            if animdata:
                data = key.cone_based_drivers
                for fc in animdata.drivers:
                    vars = fc.driver.variables
                    if len(vars) == 2:
                        k = vars[0].name
                        if k.startswith("conedriver_") and k in data:
                            data[k]["name"] = fc.data_path[12:-8]

@bpy.app.handlers.persistent
def enable_message_broker(_=None) -> None:
    bpy.msgbus.clear_by_owner(MESSAGE_BROKER)
    bpy.msgbus.subscribe_rna(key=(bpy.types.ShapeKey, "name"),
                             owner=MESSAGE_BROKER,
                             args=tuple(),
                             notify=shape_key_name_callback)

class register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Key.cone_based_drivers = bpy.props.CollectionProperty(
        name="Cone Based Corrective Shape Keys",
        type=ConeBasedDriver,
        options=set()
        )

    bpy.types.MESH_MT_shape_key_context_menu.append(draw_menu_items)
    bpy.app.handlers.load_post.append(enable_message_broker)
    enable_message_broker() # Ensure messages are subscribed to on first install

def unregister():
    bpy.msgbus.clear_by_owner(MESSAGE_BROKER)
    bpy.app.handlers.load_post.remove(enable_message_broker)
    bpy.types.MESH_MT_shape_key_context_menu.remove(draw_menu_items)

    try:
        del bpy.types.Key.cone_based_drivers
    except: pass

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)