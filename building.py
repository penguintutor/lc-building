import sys
from PySide6.QtWidgets import QApplication
from mainwindow import MainWindowUI
from scale import Scale
from laser import Laser
from interlocking import Interlocking
from wallwindow import WallWindowUI


class App(QApplication):
    def __init__ (self, args):
        super().__init__()
        

# Scale for output - default to OO
sc = Scale("OO")
# Pass scale instance to laser class
Laser.sc = sc

# Use scale to apply reverse scale to actual material_thickness
material_thickness = 3
scale_material = sc.reverse_scale_convert(material_thickness)
# Set material thickness for Interlocking (class variable)
Interlocking.material_thickness = scale_material
# Set default etchline width
#EtchLine.global_etch_width = config.etch_line_width

# Create QApplication instance 
app = App(sys.argv)

# Create a Qt widget - main window
window = MainWindowUI()

#Start event loop
app.exec()

# Application end