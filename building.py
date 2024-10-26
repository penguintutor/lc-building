import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Qt, QCoreApplication, QUrl
from PySide6.QtUiTools import QUiLoader
from mainwindow import MainWindowUI
from scale import Scale
from zoom import Zoom
from laser import Laser
from interlocking import Interlocking


class App(QApplication):
    def __init__ (self, args):
        super().__init__()
        

# Scale for output - default to OO
sc = Scale("G")
# Pass scale instance to laser class
Laser.sc = sc
# Zoom level for display (not used)
zl = Zoom()
Laser.zl = zl

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
