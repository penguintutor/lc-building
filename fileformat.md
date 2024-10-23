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

Wall is made up of points of a polygon. 
Convention is to start top left (where not top left - eg. apex then left takes priority). Then go clockwise. This makes it easier to identify the edge number.

First entry is name for the wall (for user), followed by a list of lines to define edges)

After list of points holds gui information, including view (eg. "front") and position within that view eg. [0,0]. Note this applies to position within that view only, not how it will output. New entries default to [0,0] and can be moved by the user.


## Roofs

Roofs are added separately in the building file, but will then be treated as if they were a wall.

* need to manually compensate for any differences to roof - eg. add extra to allow for slope
compared to flat (eg. math.sqrt (depth **2 + height_difference **2)). Rather than using this easier to 
add a small factor to ensure long enough - eg add 20% (0.2)
    
Dimensions are based on the space covered if projected to ground
eg. for a pitched roof it would be from centre of wall to outside of wall


## Textures
Can be applied to walls / roofs.

* type (eg. wood / brick)
* wall (wall it applies to)
* area polygon (optional) - defines constraints - otherwise defaults to entire wall
  - if defined then should be fully contained within polygon of the wall
* settings. Dict specific to type eg. wood_height / wood_etch  

When texture is applied it starts from bottom left and keep applying upwards.


## Features 
Features include doors and windows. Typically there area will be excluded from wall textures.
Then can contain cuts (always cut), etches (always etches) or outers (etch / cut depending on the outertype setting).These can be defined as line, rects, or polygon. 

Has a pos which indicates start point (top left) and all inner features are relative to that. Assuming bounding box is a rectangle then uses width, height to create a rectangle as the exclusion area. Alternatives use "exclude" followed by polygon for exclusion area (in which case width / height are ignored). If polygon is used then points should be relative to the pos

Any texture has to be defined explictly eg. as etches as would not normally apply a texture to a feature.

All values in features must be in mm (does not support tokens at the moment)

Etches have optional parameter strength, which indicates how much to burn by setting different colours. Value is 0 to 9, with 0 being lightest and 9 being darkest. The actual amount of burn is set in laser cutter software and/or settings. Without value then defaults to 5

Etch 
* type (eg. line)
* list with start & end, or points
* strength (optional)



## Interlocking
If enabled in settings - otherwise ignore (eg. very small may not work with interlocking)
Needs to be applied to both sides of a joint, one side is primary (starts with protruding) other is secondary
Wall edges are referred to by number starting with top left.
For rect (eg. right is 1, left is 3) or apex (eg. right is 2, left is 4)
* primary: [wall, edge, rev]
* secondary: [wall, edge, rev]
* start: [primary, secondary] - or single entry for same (more common)
* end: [primary, secondary] - or single entry
* step: size of step
Start and End positions are relative to start of edge for primary - and end of edge for secondary. Eg. starts bottom left on primary (start of line) then equivalent is end of line (bottom right) on secondary. If lines do not match (eg. one has half wall) then needs to relative to current wall edge (better still subdivide walls so they do match).

Reverse option indicates that the interlocking should be in the reverse direction of the edge.
ie. if primary then would start from distant end, if secondary would start from near end. To set to
reverse direction use "reverse"

If start or end positions not included then applies to end of wall
If last interlock is < end + 2 * step then ends early - only perform fixed step size

If not specified using start and not 0 then step is + 1 position from the start (so as not to encroach on bottom etc.)
If provide then start should consider what will happen on other wall (eg. 90 degs), but can be used to establish future cut positions
eg. set to +brick +1/2 mortar - to place cut in centre of mortar

Only one interlocking can be applied per edge, if attempt multiple then only one will be used (most likely last one, but not guarenteed).


## Options (templates only)

Typical features that may be added. Can be overridden allowing any feature, but setup a default list of suggestions.

