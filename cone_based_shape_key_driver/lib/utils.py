
from typing import TYPE_CHECKING
from mathutils import Vector
if TYPE_CHECKING:
    from mathutils import Quaternion

def direction_of(q: 'Quaternion') -> Vector:
    w, x, y, z = q
    return Vector((2.0*(x*y-w*z), 1.0-2.0*(x*x+z*z), 2.0*(y*z+w*x)))
