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
    "name": "Cone-Based Shape Key Driver",
    "description": "Cone-Based drivers for shape keys.",
    "author": "James Snowden",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "https://jamesvsnowden.xyz/addons/asks/cone-based/docs",
    "tracker_url": "https://github.com/jamesvsnowden/bl_cone_based_corrective_shape_key/issues",
    "category": "Animation",
}

import bpy
from .lib.curve_mapping import (BLCMAP_CurvePointProperties,
                                BLCMAP_CurveProperties,
                                BLCMAP_CurvePoint,
                                BLCMAP_CurvePoints,
                                BLCMAP_Curve,
                                BLCMAP_OT_curve_copy,
                                BLCMAP_OT_curve_paste,
                                BLCMAP_OT_handle_type_set,
                                BLCMAP_OT_node_ensure,
                                BCLMAP_OT_curve_point_remove)
from .api.preferences import ConeBasedShapeKeyDriverPreferences
from .api.activation import ConeBasedShapeKeyDriverActivation
from .api.manager import ConeBasedShapeKeyDriverManager
from .ops.add import CONEBASEDSHAPEKEYDRIVER_OT_add
from .ops.remove import CONEBASEDSHAPEKEYDRIVER_OT_remove
from .ops.recenter import CONEBASEDSHAPEKEYDRIVER_OT_recenter
from .ops.radius import CONEBASEDSHAPEKEYDRIVER_OT_radius_calculate
from .gui.panel import CONEBASEDSHAPEKEYDRIVER_PT_settings
from .gui.menu import draw_menu_items


def classes():
    return [
        BLCMAP_CurvePointProperties,
        BLCMAP_CurveProperties,
        BLCMAP_CurvePoint,
        BLCMAP_CurvePoints,
        BLCMAP_Curve,
        BLCMAP_OT_curve_copy,
        BLCMAP_OT_curve_paste,
        BLCMAP_OT_handle_type_set,
        BLCMAP_OT_node_ensure,
        BCLMAP_OT_curve_point_remove,
        ConeBasedShapeKeyDriverPreferences,
        ConeBasedShapeKeyDriverActivation,
        ConeBasedShapeKeyDriverManager,
        CONEBASEDSHAPEKEYDRIVER_OT_add,
        CONEBASEDSHAPEKEYDRIVER_OT_remove,
        CONEBASEDSHAPEKEYDRIVER_OT_recenter,
        CONEBASEDSHAPEKEYDRIVER_OT_radius_calculate,
        CONEBASEDSHAPEKEYDRIVER_PT_settings
    ]


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
    from bpy.utils import register_class
    from bpy.types import Key
    from bpy.props import CollectionProperty

    BLCMAP_OT_curve_copy.bl_idname = "cone_based_shape_key_driver.curve_copy"
    BLCMAP_OT_curve_paste.bl_idname = "cone_based_shape_key_driver.curve_paste"
    BLCMAP_OT_node_ensure.bl_idname = "cone_based_shape_key_driver.node_ensure"
    BCLMAP_OT_curve_point_remove.bl_idname = "cone_based_shape_key_driver.curve_point_remove"
    BLCMAP_OT_handle_type_set.bl_idname = "cone_based_shape_key_driver.handle_type_set"

    for cls in classes():
        register_class(cls)

    Key.cone_based_drivers = CollectionProperty(
        name="Cone Based Corrective Shape Keys",
        type=ConeBasedShapeKeyDriverManager,
        options=set()
        )

    import bpy
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

    for cls in reversed(classes()):
        bpy.utils.unregister_class(cls)
