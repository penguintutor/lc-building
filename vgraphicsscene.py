# Create a child class to QGraphicsScene
# This allows to override some of the functionality normally in the QGraphicsScene
# In particular allows capturing some of the events (eg. mouse events) that would
# otherwise be past direct to higher level widgets
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QWheelEvent
from PySide6.QtCore import Qt

class ViewGraphicsScene (QGraphicsScene):
    
    action_state = 0

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
    ## Code to handle CTRL & Scroll Wheel for zoom
    def wheelEvent(self, event):
        # If control key not pressed then use wheelEvent for normal window scroll
        if not event.modifiers() & Qt.ControlModifier:
            event.ignore()
            return
        
        num_pixels = event.delta()
        if num_pixels > 0 :
            self.main_window.zoom_in()
        if num_pixels < 0 :
            self.main_window.zoom_out()
        event.accept()

