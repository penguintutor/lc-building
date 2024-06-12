#Laser Cut Buildings file format

JSON format used for building and template files.

Building templates are designed around a typical building, including suggested dimensions, but not normally including features (doors / windows etc.)

Feature templates are doors / walls etc. which can be added to walls 

Building files are actual implementations typically generated from templates, but can be created as fixed instead. For both templates and buildings then the main dimensions are defined through variables which are substituted. For building when a feature is added this is normally saved as actual dimensions in the file. Where generated from a template that is referred to in case user would like to reapply template defaults.

All dimensions are in mm (full scale size). Normally from top left, except for textures and interlocking which are from the bottom left.

## Main Information
First section is general information 
* name
* type
* subtype
* description
* comments - info only useful to include comments in the json

## Defaults (templates only)
These are defaults for the template as a starting point. They will need to be changed if using a different size building
* depth (side wall from front to back)
* width (width of front wall)
* wall_height (height of main part of wall (excluding any apex)
* roof_height (height of apex of any applicable walls)
* [roof_width (deprecated - normally calculated) - was "roof_width": 1342]

## Typical (templates only)
These are default values that the user is unlikely to change, but may do so if required
* roof_right_overlap, roof_left_overlap (how much to extend for each side)
Also includes values related to textures. These are only set when required for the appropriate texture. examples:
* wood_height
* wood_etch (thickness of etch between wood)
* brick_height 
* brick_width
* brick_etch (mortar thickness)

## Parameters (buildings only)
All values including both defaults and typical
added as actual values

## Settings
Can be used to set particular settings
Can be a settings on either building or features etc.
* outertype (used on features for whether "cut" or "etches" used for outer perimeter - eg. does a door need to be cutout or just marked out)
A outer would normally be set as lines - not as a polygon as don't want to be filled
* interlocking set to true to add interlocking tabs
* material_thickness in mm used to determine how much to step the line


## Walls 

For walls the values can all be entered as strings including tokens (eg. value names from parameters / defaults). Can include simple calculations (eg. adding values , dividing by 2)
Parameters depend upon wall type
* WallRect - rectangular wall
    * width
    * wall_height
* WallApex
    * width
    * roof_height
    * wall_height
* Wall sloping (TBC) Rectangular wall, but with slight slope (eg. for flat roof to drain off)

In future may add custom wall (eg. WallPoly). Note if that's case then all lines must be
defined in a clockwise direction


## Roofs

Roofs are added separately in the building file, but will then be treated as if they were a wall.

* type
    * RoofFlat Covers full roof
        * Typically full width / height of building
        * requires height_difference for some kind of slope 
    * RoofApexLeft / ApexRight (from middle of front to left / right)
    * RoofApexFront / ApexRear (from middle of side to front / rear)
    * RoofPoly (TBC - allow sloping on one side - eg. Apex emerging from existing roof)

* dimensions lists
    * width (distance across top of roof) - possibly depth if apex at front/rear
    * depth (distance from top to front of roof) - possibly width if apex at front/rear
    * height-difference (roof height top - roof height bottom)
    
Dimensions are based on the space covered if projected to ground
eg. for a pitched roof it would be from centre of wall to outside of wall


## Textures 
Can be applied to walls / roofs. The wall it applies to is set by using the wall index number, which is based on list position across all walls (roofs appended to end of walls)


## Interlocking
If enabled in settings - otherwise ignore (eg. very small may not work with interlocking)
Needs to be applied to both sides of a joint, one side is primary (starts with protruding) other is secondary
Wall edges are referred to by number starting with top left.
For rect (eg. right is 1, left is 3) or apex (eg. right is 2, left is 4)
* primary: [wall, edge]
* secondary: [wall, edge]
* start: [primary, secondary] - or single entry for same (more common)
* end: [primary, secondary] - or single entry
* step: size of step
Start and End positions are relative to start of edge for primary - and end of edge for secondary. Eg. starts bottom left on primary (start of line) then equivalent is end of line (bottom right) on secondary. If lines do not match (eg. one has half wall) then needs to relative to current wall edge.

If start or end positions not included then applies to end of wall
Must not overlap with other interlocking if multiple applied to same edge.
Doing so may error, or may result in interlocking not lining up.
If last interlock is < end + 2 * step then ends early - only perform fixed step size

If not specified using start and not 0 then step is + 1 position from the start (so as not to encroach on bottom etc.)
If provide then start should consider what will happen on other wall (eg. 90 degs), but can be used to establish future cut positions
eg. set to +brick +1/2 mortar - to place cut in centre of mortar

Recommend that side with primary is left side, so starts at bottom. Also recommend that an edge has either primary
and secondary, but not both. It should be possible to have one primary and one secondary depending upon start and end positions, but unpredictable results if more than one of one type. Recommend that is avoided.



## Options (templates only)

Typical features that may be added. Can be overridden allowing any feature, but setups default list of suggestions.

