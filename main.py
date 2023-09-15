#!/usr/bin/python3

import os
import sys
import glob
import json

from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import QWidget, QApplication, QWidget, QFileDialog, QVBoxLayout
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtCore import QTimer, Qt

from imageviewer import ImageViewer
from kvwidget import KeyValueWidget

from paddleocr import PaddleOCR
import cv2


#-----------------------------
from PyQt5.QtCore import QLibraryInfo

os.environ['NO_AT_BRIDGE'] = '1'
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath)
#-----------------------------



class LabelIt( QWidget ):

    DEFAULT_DIR = '/home/marco/downloads/datasets/hostpital_cases/img_symlinks_1k/'

    def __init__( self ):
        super().__init__()

        self.ocr = PaddleOCR(use_angle_cls=True, show_log=False)
        # self.ocr.use_gpu = False

        # init vars
        self.image_path = ''
        self.images_list = []
        self.image_index = 0
        ###########

        # init ui #
        self.ui = uic.loadUi('label.ui', self)

        self.image_viewer = ImageViewer()
        viewer_layout = QVBoxLayout(self.ui.pictureFrame)
        viewer_layout.addWidget(self.image_viewer)
        self.ui.pictureFrame.setLayout(viewer_layout)
        self.image_viewer.imageCropped.connect(self.slot_image_cropped)

        self.ui.loadBtn.clicked.connect(self.choose_dir)
        self.ui.prevBtn.clicked.connect(lambda: self.show_image(self.image_index - 1))
        self.ui.nextBtn.clicked.connect(lambda: self.show_image(self.image_index + 1))
        self.ui.prevBtn.clicked.connect(lambda: self.image_viewer.clear_draw_box())
        self.ui.nextBtn.clicked.connect(lambda: self.image_viewer.clear_draw_box())

        self.kvwidget = KeyValueWidget()
        kv_layout = QVBoxLayout(self.ui.kvFrame)
        kv_layout.addWidget(self.kvwidget)
        # kv_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.kvFrame.setLayout(kv_layout)

        self.kvwidget.item_modified.connect(self.slot_kv_item_modified)

        ###########

        _timer = QTimer()
        _timer.setInterval(10)
        # _timer.singleShot(100, lambda: self.choose_dir(self.DEFAULT_DIR))
        # _timer.start()

    def choose_dir(self, path=None):
        if not path:
            self.image_path = QFileDialog.getExistingDirectory(self, 'Choose Directory')
        else:
            self.image_path = path

        self.json_dir = self.image_path + '/jsons'
        if not os.path.exists(self.json_dir):
            print('create json dir', self.json_dir)
            os.mkdir(self.json_dir)

        if self.image_path:
            self.images_list = glob.glob(self.image_path + '/*')
            self.images_list.sort()
            self.image_index = 0
            self.show_image(0)

    def show_image(self, index):
        self.setWindowTitle(os.path.basename(self.images_list[index]))

        img_file = os.path.join(self.image_path, self.images_list[index])
        self.image_index = index
        self.image_viewer.set_photo(QPixmap(img_file))

        self.kvwidget.key_input.setText('')
        self.kvwidget.value_input.setPlainText('')

        self.load_json()

    def load_json(self):
        # json_file = self.images_list[self.image_index] + '.json'
        json_file = os.path.join(self.json_dir, os.path.basename(self.images_list[self.image_index]) + '.json')
        if os.path.exists(json_file):
            with open(json_file) as f:
                data = json.load(f)
                self.kvwidget.set_pairs(data)
                print('load json', data)
        else:
            for i in range(self.kvwidget.value_list.count()):
                self.kvwidget.value_list.item(i).setText(' ')

            self.kvwidget.key_list.setCurrentRow(0)
            self.kvwidget.value_list.setCurrentRow(0)


    def slot_kv_item_modified(self, item):
        if not self.ui.autoSaveChk.isChecked():
            return

        print('auto saved')
        # json_file = self.images_list[self.image_index] + '.json'
        json_file = os.path.join(self.json_dir, os.path.basename(self.images_list[self.image_index]) + '.json')
        json.dump(item, open(json_file, 'w'), indent=4, ensure_ascii=False)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)

        if e.key() == Qt.Key.Key_Escape:
            self.image_viewer.clear_draw_box()
        elif e.key() == Qt.Key.Key_R:
            # rotate img, save it to file then reload it
            self.image_viewer.clear_draw_box()
            
            img_file = os.path.join(self.image_path, self.images_list[self.image_index])
            img = cv2.imread(img_file)
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(img_file, img)
            self.show_image(self.image_index)
            pass


    def slot_image_cropped(self, img):

        # convert RGBA to RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        # cv2.imshow('slot_image_cropped', img)
        # print('slot_image_cropped', img)
        result = self.ocr.ocr(img)[0]
        print('result -->', result)

        if len(result) == 0:
            return

        confidence_sum = 0
        rev = []

        for line in result:
            if line:
                rev.append(line[1][0])
                confidence_sum += line[1][1]

        confidence_avg = confidence_sum / len(result)
        print('-->', rev, confidence_avg)
        if confidence_avg > 0.85:
            _color = Qt.GlobalColor.darkGreen
            _width = 10
        elif confidence_sum > 0.6:
            _color = Qt.GlobalColor.yellow
            _width = 5
        self.image_viewer.set_drawbox_color(Qt.GlobalColor.darkGreen, width=10)
        self.image_viewer.add_text_in_draw_box('\n'.join(rev))

        # copy to clipboard
        # QApplication.clipboard().setText('\n'.join(rev))

        # copy value to curr kv focused item
        self.kvwidget.value_list.currentItem().setText('\n'.join(rev))
        # self.kvwidget.value_list.setCurrentRow(self.kvwidget.value_list.currentRow() + 1)
        # self.kvwidget.key_list.setCurrentRow(self.kvwidget.key_list.currentRow() + 1)

        # print(result)
        # self.slot_kv_item_modified(self.kvwidget.get_pairs())
        # self.ui.grabBtn.setText('Grab')
        # self.image_viewer.leave_draw_box()
        # self.show_image(self.image_index + 1)



#######################
if __name__ == '__main__':
    app = QApplication( sys.argv )
    ui = LabelIt()
    ui.show()
    sys.exit( app.exec_() )