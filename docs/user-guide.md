# User-Guide

## Adding Cone-Based Drivers

Once the addon has been installed, select a shape key in the Shape Keys panel. You will now find a extra option in the
Shape Key Specials Menu: **Add Cone-Based Driver**.

Selecting this option will add a cone-based driver for the selected shape key. You can now set up the driver using the
settings in the Cone-Based Driver panel that will appear below the other Shape Key settings in the Shape Keys panel.

## Target

The driver's target is the pose bone that will be used to driver the corrective shape key.
Select an object (which must be an armature) and specify the bone that you want to use. The
target will normally be a bone in the rig you are using to deform the mesh, but could be a
bone from another armature if desired.

## Center

The driver's center is the rotation of the bone at which the corrective shape key will be
fully activated. You can think of it as the line that goes travels through the apex of the
cone at the bone's head and the base of the cone.

For convenience you can select a rotation type (Euler, Quaternion or Axis/Angle) from the
dropdown menu below the center value. This allows you to view and edit the center in whatever
was is most convenient for you. It does not have an affect on the operation of the driver itself,
which will always use the quaternion rotation of the bone as it is the most stable.

Next to the center value, the [] button can be used to read the current rotation of the target
bone and assign it to the center value.

## Radius

The driver's radius controls how far from the center rotation the target bone should be to
activate the corrective shape key. You can think of it as the radius of the base of the cone.

The radius is adjustable from 0.0 to 1.0. A lower value will result in the shape key being activated
only when the target bone's rotation is closer to the center value. A high value will result in
the shape key beginning to activate from further away

Beside the value is a dropdown menu with two options for automatically calculating the radius.
These are useful if you have multiple corrective shape keys being driven by the same target
bone.

### Nearest Neighbor

If you select **Nearest Neighbor**, the addon will look for other cone-based corrective shape keys
that share the same target bone and calculate which one has a rotation center closest to the
shape key you are editing. It will then use the distance to that rotation as the basis for the
radius value.

In practice this means that adjusting the rotation of the target bone will smoothly interpolate
between the corrective shape keys.

### Nearest Neighbor (No Intersection)

This option is similar to **Nearest Neighbor**, with the difference that the corrective shape
key will only being activation when the nearest other shape key finishes activation.

## Easing

The easing curve provides an intuitive way of fine-tuning the activation of the corrective shape
key. You can choose from a range of presets (Linear, Quadratic, Cubic, etc.) or select the **Curve**
option to create a custom curve using a popup curve editor.

The buttons to the right of the curve display allow you to copy curves and paste them to other
corrective shape keys. 

## Goal

The goal value is the value that the corrective shape key should have when fully activated (when the
target bone's direction matches the center value). Normally this will remain at 1.0 (the default) but
you are free to adjust it if the effect of the shape key is too weak or strong.

## Removing Cone-Based Drivers

To remove a cone-based driver from the selected shape key, simply select the **Remove Cone-Based Driver**
option from the Shape Key Specials Menu in the Shape Keys panel. Not that this will remove the driver
from the shape key but will not remove the shape key itself.
