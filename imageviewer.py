from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsView, QFrame, QToolButton, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QApplication, QFileDialog
from PyQt5.QtGui import QColor, QBrush, QPixmap
from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QRectF

import cv2
import numpy as np

class ImageViewer(QGraphicsView):
    imageClicked = pyqtSignal(QPoint)
    imageCropped = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._draw_box = None
        self._draw_box_label = None

        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self.scale_level = 1.0
        self._scene.addItem(self._photo)
        self.setScene(self._scene)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        # self.setInteractive(True)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self._photo.setPixmap(pixmap)

            _qimg = self._photo.pixmap().toImage()
            _shape = _qimg.height(), _qimg.width()
            _shape += (4,)
            _ptr = _qimg.bits()
            _ptr.setsize(_qimg.byteCount())
            # print(_ptr.getsize())

            self.cv2_img = np.array(_ptr, dtype=np.uint8).reshape(_shape)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QPixmap())

        self.fit_in_view()

    def set_drawbox_color(self, color, width=2, style=Qt.PenStyle.SolidLine):
        self._draw_box.setPen(
            QtGui.QPen(color, width, Qt.PenStyle.SolidLine))

    def clear_draw_box(self):
        if self._draw_box is not None:
            self._scene.removeItem(self._draw_box)
            self._draw_box = None
        if self._draw_box_label is not None:
            self._scene.removeItem(self._draw_box_label)
            self._draw_box_label = None

    def add_text_in_draw_box(self, text):
        if self._draw_box is not None:
            if self._draw_box_label is None:
                self._draw_box_label = self._scene.addText(text, font=QtGui.QFont('Noto', 16))
            else:
                self._draw_box_label.setPlainText(text)
            self._draw_box_label.setPos(self._draw_box.rect().x(), self._draw_box.rect().y())

    def wheelEvent(self, event):
        if not self.has_photo():
            print('no photo')
            return
        
        super().wheelEvent(event)

        if event.angleDelta().y() > 0:
            factor = 1.1
            self._zoom += 1
        else:
            factor = 0.9
            self._zoom -= 1

        if self._zoom > 0:

            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            tf = self.transform()
            current_scale = min(tf.m11(), tf.m22())
            if current_scale > 1.5 and factor > 1:
                # print('zoom limited')
                # self.parent().parent().setWindowTitle('zoom limited')
                self._zoom -= 1
            else:
                # old_pos = self.mapToScene(event.pos())

                self.scale(factor, factor)

                # new_pos = self.mapToScene(event.pos())
                # delta = new_pos - old_pos
                # print(delta.x(), delta.y())
                # self.horizontalScrollBar().setValue(-int(delta.x()) + self.horizontalScrollBar().value())
                # self.verticalScrollBar().setValue(int(delta.y()) + self.verticalScrollBar().value())

        elif self._zoom == 0:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.fit_in_view()
        else:
            self._zoom = 0

    def mouseMoveEvent(self, event):

        ebtn = event.buttons()
        if ebtn == Qt.MouseButton.LeftButton:
            super().mouseMoveEvent(event)

        elif ebtn == Qt.MouseButton.RightButton:
            pos = self.mapToScene(event.pos())
            self._draw_box.setRect(self._start_point.x(),
                                   self._start_point.y(),
                                   pos.x() - self._start_point.x(),
                                   pos.y() - self._start_point.y())


    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if self._photo.isUnderMouse():
            self.imageClicked.emit(self.mapToScene(event.pos()).toPoint())

        ebtn = event.button()
        if ebtn == Qt.MouseButton.LeftButton:
            return
        elif ebtn == Qt.MouseButton.RightButton:
            self._start_point = self.mapToScene(event.pos())

            _pen = QtGui.QPen(Qt.GlobalColor.red, 2,
                                Qt.PenStyle.DashDotDotLine)
            if self._draw_box is not None:
                self.set_drawbox_color(Qt.GlobalColor.red, 2,
                                        Qt.PenStyle.DashDotDotLine)
                self._draw_box.setRect(self._start_point.x(),
                                        self._start_point.y(), 0, 0)
            else:
                self._draw_box = self._scene.addRect(self._start_point.x(),
                                                        self._start_point.y(),
                                                        0,
                                                        0,
                                                        pen=_pen)

    def mouseReleaseEvent(self, event):
        ebtn = event.button()

        if ebtn == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

        elif ebtn == Qt.MouseButton.RightButton:
            pos = self.mapToScene(event.pos())

            if pos.x() < self._start_point.x() and pos.y() < self._start_point.y():
                start_x, start_y = self._start_point.x(), self._start_point.y()
                self._start_point = pos
                pos = QtCore.QPointF(start_x, start_y)
            elif pos.x() < self._start_point.x():
                start_x = self._start_point.x()
                self._start_point.setX(pos.x())
                pos.setX(start_x)
            elif pos.y() < self._start_point.y():
                start_y = self._start_point.y()
                self._start_point.setY(pos.y())
                pos.setY(start_y)

            self._draw_box.setRect(self._start_point.x(), self._start_point.y(), pos.x() - self._start_point.x(), pos.y() - self._start_point.y())
            # print(self._draw_box.rect())
            _rect = self._draw_box.rect()
            if _rect.x() < 0:
                # print('x < 0')
                self._draw_box.setRect(0, _rect.y(), _rect.width() + _rect.x(), _rect.height())
                _rect = self._draw_box.rect()
            elif _rect.x() > self._photo.pixmap().width():
                # print('x > w')
                return
            if _rect.y() < 0:
                # print('y < 0')
                self._draw_box.setRect(_rect.x(), 0, _rect.width(), _rect.height() + _rect.y())
                _rect = self._draw_box.rect()
            elif _rect.y() > self._photo.pixmap().height():
                self._draw_box.setRect(_rect.x(), _rect.y(), _rect.width(), _rect.height() + _rect.y())
                _rect = self._draw_box.rect()
            if _rect.x() + _rect.width() > self._photo.pixmap().width():
                # print('x + w > w')
                self._draw_box.setRect(_rect.x(), _rect.y(), self._photo.pixmap().width() - _rect.x(), _rect.height())
                _rect = self._draw_box.rect()
            if _rect.y() + _rect.height() > self._photo.pixmap().height():
                # print('y + h > h')
                self._draw_box.setRect(_rect.x(), _rect.y(), _rect.width(), self._photo.pixmap().height() - _rect.y())
                _rect = self._draw_box.rect()

            self._start_point = None
            _rect = self._draw_box.rect()

            cropped = self.cv2_img[int(_rect.y()):int(_rect.y() + _rect.height()), int(_rect.x()):int(_rect.x() + _rect.width())]
            self.imageCropped.emit(cropped)





if __name__ == '__main__':

    class Window(QWidget):

        def __init__(self):
            super(Window, self).__init__()
            self.viewer = ImageViewer(self)

            # self.viewer.photoClicked.connect(lambda pos: print("Clicked:", pos))
            self.viewer.imageCropped.connect(self.slot_show_cropped)

            # 'Load image' button
            self.btn_load = QToolButton(self)
            self.btn_load.setText('Load image')
            self.btn_load.clicked.connect(self.load_image)

            # self.draw_toggle = QToolButton(self)
            # self.draw_toggle.setText('Draw')
            # self.draw_toggle.clicked.connect(self.slot_draw_toggle)

            # Arrange layout
            vblayout = QVBoxLayout(self)
            vblayout.addWidget(self.viewer)
            hblayout = QHBoxLayout()
            hblayout.setAlignment(QtCore.Qt.AlignLeft)
            hblayout.addWidget(self.btn_load)
            # hblayout.addWidget(self.draw_toggle)
            vblayout.addLayout(hblayout)

        def load_image(self):
            img = QFileDialog.getOpenFileName(self, 'Open image')[0]
            self.viewer.set_photo(QtGui.QPixmap(img))

        # def slot_draw_toggle(self):
        #     if self.viewer._under_draw:
        #         self.draw_toggle.setText('Draw')
        #         self.viewer.leave_draw_box()
        #     else:
        #         self.draw_toggle.setText('Stop')
        #         self.viewer.enter_draw_box()

        def slot_show_cropped(self, cropped):
            cv2.imshow('cropped here', cropped)
            cv2.waitKey(1)

        def keyPressEvent(self, e):
            super().keyPressEvent(e)

            if e.key() == Qt.Key.Key_Escape:
                self.viewer.clear_draw_box()

    import sys
    from paddleocr import PaddleOCR

    app = QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 300, 800, 600)
    _timer = QtCore.QTimer()
    _timer.singleShot(100, lambda: window.viewer.set_photo(QtGui.QPixmap('/home/marco/arts/eso1242a.jpg')))
    window.show()
    sys.exit(app.exec_())