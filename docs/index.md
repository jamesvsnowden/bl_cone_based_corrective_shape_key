# Cone-Based Corrective Shape Keys

## The What

Cone-based drivers enable you to animate (in this case shape keys) based on the *direction* of a target bone. The
*direction* of a bone is not the same thing as its *orientation*; rather it is the just the direction in which
it is pointing, irrespective of where it is in space and how it is rotated around it's axis (the Y axis in the
case of Blender's bones). Additionally cone-based drivers provide a simple and intuitive mechanism for limiting
the range of the rotation that should be taken into account.

**Cone-Based Corrective Shape Keys** provides a simple workflow for setting up and managing cone-based drivers for
shape keys, and offers easey-to-use options to quickly attain the desired results.

## The Why

It's entirely possible to set up a cone-based driver for a shape key using Blender's native tools. In fact, this addon
uses Blender's drivers under the hood. Nevertheless, doing it manually is both time-consuming and tricky to get right
if you're not very familiar with Blender's FCurve and driver systems, or don't have a solid understanding of how
cone-based drivers work. This addon makes them quick and simple to set up, easy to manage, and gets the math right for
you so you can get on with the fun stuff.

## The How

Cone-based drivers typically use the direction of a pose bone as the input. There are a few approaches to achieving this
depending on the software being used.

One approach is to read the direction vector from the bone's transform matrix and then use the dot-product of that vector
with the desired target pose. This is computationally fast but has the drawback that the speed of the resulting
interpolation is affected by the scale of the bone, so if you're animating the bone's scale - or in fact the scale of any
parent bone - the velocity of the driver will be affected too. This can be mitigated by using proxy bones and constraints
but we don't really want to have to make structural changes to the rig unless we absolutely have to, and in this case we
don't.

To avoid the problem we need to get the direction of the bone somewhere else. Unfortunately this isn't all that
straightforward as it's not directly available to drivers in Blender in a form that's easily useable, but it can
be calculated relatively cheaply from the quaternion rotation components, and this is the approach the addon takes.
There is however a further issue that needs to be resolved.

Due to the characteristics of the dot-product calculation, the output of the driver isn't going to be linear; it's going
to have a sinusoidal-like curve to it. This may or may not be an issue for a particular driven shape key, but isn't
desirable because we want to have control over the easing of the shape key's value ourselves. The cone-based drivers
created with this addon therefore also invert the curve inherent in the calculation within the driver's expression, leaving
you to with full control over the animation of your shape keys.
