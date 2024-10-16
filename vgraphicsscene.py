from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QWheelEvent
from PySide6.QtCore import Qt

class ViewGraphicsScene (QGraphicsScene):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
    def wheelEvent(self, event):
        # If control not pressed then use wheelEvent for normal window scroll
        if not event.modifiers() & Qt.ControlModifier:
            event.accept()
            return
        
        # If control key pressed then zoom
            
        num_pixels = event.delta()
        if num_pixels > 0 :
            self.main_window.zoom_in()
        if num_pixels < 0 :
            self.main_window.zoom_out()

        event.ignore()
