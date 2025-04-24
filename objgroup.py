from PySide6.QtWidgets import QGraphicsItem, QGraphicsItemGroup
from PySide6.QtGui import QPolygonF, QPen, QBrush, QColor

class ObjGroup(QGraphicsItemGroup):
    def __init__(self):
        super().__init__()
        self.pen_highlight = QPen(QColor(255,0,0))
        self.pen_highlight.setWidth(6)
        
    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(self.pen_highlight)
            painter.drawRect(self.boundingRect().toRect())
