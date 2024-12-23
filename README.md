# lc-building
LaserCut Model Building Creation Tool

## Important note
This is in a very early development stage. It has very limited functionality.
More details will be provided as the code is developed further.


## Prerequisites
The following python modules are required
* Pyside6
* shapely
* svgwrite

At the time of writing this is not included in the standard repositories and so should be instaled through PIP.
As a result of PEP 704 this normally needs to be done by creating a virtual environment. The following is the recomended method for use on Linux, including Ubuntu or Raspberry Pi.

    mkdir ~/.venv
    python3 -m venv ~/.venv/pyside6
    source ~/.venv/pyside6/bin/activate
    pip install pyside6
    pip install shapely
    pip install svgwrite
    
If you are running Linux Mint then you may also need to install additional packages first using:

    sudo apt install python3.12-venv 
    sudo apt install libxcb-cursor0
    
On systems you may also need to install pip using

    sudo apt install python3-pip

Some may need a different version of venv (eg.)

    sudo apt install python3.*-venv
    
## Running the code


### Command line lcmake file
Currently configs are in the buildings directory, but are referenced by hard coding in the lcmake.py file.
This also needs a folder called output, if one does not already exist then it should be created.
After configuring the above then run

    python3 lcmake.py 


### GUI version
The Graphical User Interface version is under development. To see the current status you first need to enable Pyside 6 through a virtual environment. If using the same steps as mentioned above then use

    source ~/.venv/pyside6/bin/activate
    python3 building.py 
    
   
## Development tests
There are some limited tests provided.
Tests are written using unittest

Run using:

    python3 -m unittest tests
or

    python3 tests.py
    
## Limitations

### Everything in mm
All measurements should be based on mm of actual size.
Conversation to scale mm and then to pixels is done within the
application. It may be possible to add an interface to allow 
other units (eg. inches) to be used as an input, but they will
still be handled internally as mm.

### Overlapping etches
Some laser cutting software does not allow overlapping etches.
In the case of Lightburn it will not output any parts that overlap.
This is a limitation of the laser cutting software rather than this 
program.

It is recommended that you allow overlaps within this software and
then use the appropriate feature in the laser burning software. 
For example in Lightburn you will need to use the weld feature, or
you could edit in Inkscape. 

When creating templates it is much simpler to allow overlapping etches. 
Particularly when different scales can produce rounding errors when scaling
is applied.
For example shed hinges that overlap with the texture. It also helps with
etches that are padded into polygons as otherwise those would need to be
taken into consideration.

### Limitations of small scales
Small scales (smaller than HO/OO) may have problems when dealing with small
size shapes. These may need to be edit in Inkscape before burning, or choose
an "N friendly" template

### Delay in updating the info box
Under some circumstances when an object is selected there may be a delay before
the information box in the bottom right is updated. It is unknown why this is, 
perhaps related to internal redrawing of the object when it receives focus. It is 
not known to have another other impact on the software operation.

### History undo etc. not yet implemented
Changes are implemented immediately, but there is not currently a way to undo those changes, 
other than not saving them. 
Data is included in some of the functions and is likely to be included in future. Note that the history of edits is independant so changes to different parts may have unintentional consequences.
