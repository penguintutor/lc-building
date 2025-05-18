from PySide6.QtWidgets import QGraphicsItem, QGraphicsItemGroup
from PySide6.QtGui import QPolygonF, QPen, QBrush, QColor

class ObjGroup(QGraphicsItemGroup):
    def __init__(self, gconfig):
        super().__init__()
        self.gconfig = gconfig
        #self.pen_highlight = QPen(QColor(255,0,0))
        #self.pen_highlight.setWidth(3)
        
    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(self.gconfig.pen_highlight)
            painter.drawRect(self.boundingRect().toRect())
