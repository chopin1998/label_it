from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsView, QFrame, QToolButton, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QApplication, QFileDialog
from PyQt5.QtGui import QColor, QBrush, QPixmap
from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QRectF



class ImageViewer(QGraphicsView):
    photoClicked = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self.scale_level = 1.0
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(100, 100, 100)))
        self.setFrameShape(QFrame.Shape.NoFrame)

    def has_photo(self):
        return not self._empty

    def fit_in_view(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.has_photo():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def set_photo(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())

        self.fit_in_view()

    def wheelEvent(self, event):
        if not self.has_photo():
            return

        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1

        if self._zoom > 0:
            tf = self.transform()
            current_scale = min(tf.m11(), tf.m22())
            if current_scale > 2 and factor > 1:
                print('zoom limited')
                # self.parent().parent().setWindowTitle('zoom limited')
                self._zoom -= 1
            else:
                self.scale(factor, factor)
        elif self._zoom == 0:
            self.fit_in_view()
        else:
            self._zoom = 0

    def mouseMoveEvent(self, event):
        # print('mouseMoveEvent', event.pos().x(), event.pos().y())
        
        super(ImageViewer, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super(ImageViewer, self).mousePressEvent(event)




class Window(QWidget):

    def __init__(self):
        super(Window, self).__init__()
        self.viewer = ImageViewer(self)
        # 'Load image' button
        self.btn_load = QToolButton(self)
        self.btn_load.setText('Load image')
        self.btn_load.clicked.connect(self.load_image)
        
        # Arrange layout
        vblayout = QVBoxLayout(self)
        vblayout.addWidget(self.viewer)
        hblayout = QHBoxLayout()
        hblayout.setAlignment(QtCore.Qt.AlignLeft)
        hblayout.addWidget(self.btn_load)
        vblayout.addLayout(hblayout)

    def load_image(self):
        img = QFileDialog.getOpenFileName(self, 'Open image')[0]
        self.viewer.set_photo(QtGui.QPixmap(img))


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 300, 800, 600)
    window.show()
    sys.exit(app.exec_())