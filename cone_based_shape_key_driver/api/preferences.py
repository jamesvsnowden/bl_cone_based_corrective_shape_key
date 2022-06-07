

from bpy.types import AddonPreferences
from ..lib.update import AddonUpdatePreferences

class ConeBasedShapeKeyDriverPreferences(AddonUpdatePreferences, AddonPreferences):
    bl_idname = "cone_based_shape_key_driver"
