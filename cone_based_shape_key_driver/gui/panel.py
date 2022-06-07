
from typing import TYPE_CHECKING
from bpy.types import Panel
from ..lib.curve_mapping import draw_curve_manager_ui
from ..ops.radius import CONEBASEDSHAPEKEYDRIVER_OT_radius_calculate
from ..ops.recenter import CONEBASEDSHAPEKEYDRIVER_OT_recenter
if TYPE_CHECKING:
    from bpy.types import Context

class CONEBASEDSHAPEKEYDRIVER_PT_settings(Panel):

    bl_parent_id = "DATA_PT_shape_keys"
    bl_label = "Cone-Based Driver"
    bl_description = "Cone-Based driver settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        if object is not None:
            shape = object.active_shape_key
            if shape is not None:
                key = shape.id_data
                return (key.is_property_set("cone_based_drivers")
                        and shape.name in key.cone_based_drivers)
        return False

    def draw(self, context: 'Context') -> None:
        shape = context.object.active_shape_key
        key = shape.id_data
        manager = key.cone_based_drivers[shape.name]
        layout = self.layout

        # Target Object / PoseBone
        split = layout.split(factor=0.385)
        
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Target")

        row = split.row()
        column = row.column(align=True)
        row.separator(factor=2.0)

        object = manager.object
        
        subrow = column.row(align=True)
        subrow.alert = object is None or object.type != 'ARMATURE'
        subrow.prop(manager, "object", text="")

        subrow = column.row(align=True)
        if object is None or object.type != 'ARMATURE':
            subrow.alert = True
            subrow.prop(manager, "bone_target", icon='BONE_DATA', text="")
        else:
            subrow.alert = manager.bone_target not in object.data.bones
            subrow.prop_search(manager, "bone_target", object.data, "bones", icon='BONE_DATA', text="")

        split = layout.split(factor=0.385)

        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Center")

        row = split.row()
        col = row.column()
        row.separator(factor=2.0)

        subrow = col.row()
        subcol = subrow.column(align=True)
        subrow.operator(CONEBASEDSHAPEKEYDRIVER_OT_recenter.bl_idname,
                        text="",
                        icon='ORIENTATION_CURSOR')

        if manager.rotation_mode == 'QUATERNION':
            for index, axis in enumerate('WXYZ'):
                subcol.prop(manager, "center_quaternion", text=axis, index=index)
        elif manager.rotation_mode == 'AXIS_ANGLE':
            subcol.prop(manager, "center_angle", text="W")
            for index, axis in enumerate('XYZ'):
                subcol.prop(manager, "center_axis", text=axis, index=index)
        else:
            for index, axis in enumerate('XYZ'):
                subcol.prop(manager, "center_euler", text=axis, index=index)

        subcol.separator(factor=0.5)
        subcol.prop(manager, "rotation_mode", text="")

        activation = manager.activation

        split = layout.split(factor=0.385)

        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Activation")

        col = split.column()

        row = col.row()
        draw_curve_manager_ui(row, activation)
        row.separator(factor=2.0)

        row = col.row(align=True)
        row.prop(activation, "radius", text="Radius")
        row.operator_menu_hold(CONEBASEDSHAPEKEYDRIVER_OT_radius_calculate.bl_idname,
                               "method",
                               text="",
                               icon='PIVOT_INDIVIDUAL')

        col.prop(activation, "target", text="Target")
