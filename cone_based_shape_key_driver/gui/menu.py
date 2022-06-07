
from typing import TYPE_CHECKING
from ..lib.driver_utils import driver_find
from ..ops.add import CONEBASEDSHAPEKEYDRIVER_OT_add
from ..ops.remove import CONEBASEDSHAPEKEYDRIVER_OT_remove
if TYPE_CHECKING:
    from bpy.types import Context, Menu


def draw_menu_items(menu: 'Menu', context: 'Context') -> None:
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
                    layout.operator(CONEBASEDSHAPEKEYDRIVER_OT_add.bl_idname,
                                    icon='DECORATE_DRIVER',
                                    text="Add Cone-Based Driver")
                else:
                    variables = fcurve.driver.variables
                    if len(variables) == 5 and variables[0].name.startswith("conedriver_"):
                        layout = menu.layout
                        layout.separator()
                        layout.operator(CONEBASEDSHAPEKEYDRIVER_OT_remove.bl_idname,
                                        icon='REMOVE',
                                        text="Remove Cone-Based Driver")
