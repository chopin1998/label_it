#!/usr/bin/python3

import os
import sys
import glob
import json

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication, QWidget, QFileDialog, QGraphicsScene, QGraphicsPixmapItem, QGraphicsView, QFrame, QVBoxLayout
from PyQt5.QtGui import QColor,  QBrush, QPixmap
from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QRectF, QTimer

from imageviewer import ImageViewer
from kvwidget import KeyValueWidget

from paddleocr import PaddleOCR


class LabelIt( QWidget ):

    DEFAULT_DIR = '/home/marco/downloads/datasets/hostpital_cases/img_symlinks_1k/'

    def __init__( self ):
        super().__init__()

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
        
        self.ui.loadBtn.clicked.connect(self.choose_dir)
        self.ui.prevBtn.clicked.connect(lambda: self.show_image(self.image_index - 1))
        self.ui.nextBtn.clicked.connect(lambda: self.show_image(self.image_index + 1))
        
        self.kvwidget = KeyValueWidget()
        kv_layout = QVBoxLayout(self.ui.kvFrame)
        kv_layout.addWidget(self.kvwidget)
        # kv_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.kvFrame.setLayout(kv_layout)
        
        self.kvwidget.item_modified.connect(self.slot_kv_item_modified)
        
        ###########

        _timer = QTimer()
        _timer.setInterval(10)
        _timer.singleShot(100, lambda: self.choose_dir(self.DEFAULT_DIR))
        _timer.start()

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

    def slot_kv_item_modified(self, item):
        # print(item)
        if not self.ui.autoSaveChk.isChecked():
            return
        
        # json_file = self.images_list[self.image_index] + '.json'
        json_file = os.path.join(self.json_dir, os.path.basename(self.images_list[self.image_index]) + '.json')
        json.dump(item, open(json_file, 'w'), indent=4, ensure_ascii=False)


#######################
if __name__ == '__main__':
    app = QApplication( sys.argv )
    ui = LabelIt()
    ui.show()
    sys.exit( app.exec_() )