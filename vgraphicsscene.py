# Create a child class to QGraphicsScene
# This allows to override some of the functionality normally in the QGraphicsScene
# In particular allows capturing some of the events (eg. mouse events) that would
# otherwise be past direct to higher level widgets
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QWheelEvent
from PySide6.QtCore import Qt, Signal
#from wallwindow import WallWindowUI

class ViewGraphicsScene (QGraphicsScene):
    
    focus_changed = Signal(list)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Triggers when a selection is changed within the scene
        self.selectionChanged.connect(self.new_focus)

    # Uses mouseReleaseEvent
    # Drag events don't trigger when dragging parts away
    # itemEvent triggers too often - so just look at when button is released
    # check to see if any of the items have moved in which case update
    # Detect mouse release to check if need to update positions
    def mouseReleaseEvent(self, event):
        #print ("Mouse released")
        # Has anything moved
        self.main_window.check_moved_update()
        event.ignore()
        
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

    def get_selected(self):
        return self.selectedItems()


    def new_focus(self):
        selected_items = self.selectedItems()
        #print (f"Focus changed {selected_items}")
        self.focus_changed.emit(selected_items)
        
    # Has any of the objects moved
    # Check all as it also updates position
    #def has_obj_moved(self):
    #    return self.main_window.check_obj_moved()
        #moved = False
        #for this_obj in self.main_window.get_scene_obj_views():
        #    if this_obj.has_moved():
        #        moved = True
        #return moved