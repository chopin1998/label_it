from cProfile import label
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QPlainTextEdit
from PyQt5.QtCore import pyqtSignal, Qt

class KeyValueWidget(QWidget):
    item_modified = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.key_label = QLabel("Key:")
        self.value_label = QLabel("Value:")
        self.key_input = QLineEdit()
        self.value_input = QPlainTextEdit()
        self.value_input.setFixedHeight(50)
        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        self.key_list = QListWidget()
        self.value_list = QListWidget()
        self.value_list.setEditTriggers(QListWidget.EditTrigger.SelectedClicked | QListWidget.EditTrigger.DoubleClicked | QListWidget.EditTrigger.AnyKeyPressed)

        self.init_ui()

        self.curr_selected_index = -1

    def init_ui(self):
        layout = QVBoxLayout(self)

        key_value_layout = QHBoxLayout()
        key_value_layout.addWidget(self.key_label)
        key_value_layout.addWidget(self.key_input)
        key_value_layout.addWidget(self.value_label)
        key_value_layout.addWidget(self.value_input)

        result_layout = QHBoxLayout()
        result_layout.addWidget(self.key_list)
        result_layout.addWidget(self.value_list)

        layout.addLayout(key_value_layout)
        layout.addWidget(self.add_button)
        layout.addWidget(self.delete_button)
        layout.addLayout(result_layout)

        self.setLayout(layout)

        self.add_button.clicked.connect(self.slot_add_pair)
        self.delete_button.clicked.connect(self.slot_delete_pair)

        self.key_list.itemClicked.connect(self.slot_key_list_item_clicked)
        self.value_list.itemClicked.connect(self.slot_value_list_item_clicked)

        self.value_list.itemChanged.connect(self.slot_value_list_item_changed)

    def value_list_commitData(self, editor):
        print('commitData')

    def slot_key_list_item_clicked(self, item):
        print('key click')
        index = self.key_list.row(item)
        self.curr_selected_index = index
        self.value_list.setCurrentRow(index)
        # print(item.text(), index)

        self.key_input.setText(item.text())
        self.value_input.setPlainText(self.value_list.item(index).text())

        self.value_input.clear()

    def slot_value_list_item_clicked(self, item):
        print('value click')
        index = self.value_list.row(item)
        self.curr_selected_index = index

        # self.value_list.editItem(item)
        self.key_input.clear()
        self.value_input.clear()

        self.key_list.setCurrentRow(index)

    def slot_value_list_item_changed(self, item):        
        # print('changed', item.text())

        self.item_modified.emit(self.gen_all_pairs())
        
        next_index = self.curr_selected_index + 1
        if next_index >= self.key_list.count():
            next_index = 0
        
        self.value_list.setCurrentRow(next_index)
        self.key_list.setCurrentRow(next_index)
        self.curr_selected_index = next_index

    def slot_add_pair(self):
        key = self.key_input.text()
        value = self.value_input.toPlainText()

        if not key or not value:
            return

        k = self.key_list.findItems(key, Qt.MatchExactly)
        if k:
            index = self.key_list.row(k[0])
            self.value_list.item(index).setText(value)
            print('modified')
        else:
            self.key_list.addItem(key)
            self.value_list.addItem(value)
            self.value_list.item(self.value_list.count() - 1).setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.key_input.clear()
        self.value_input.clear()

        self.item_modified.emit(self.gen_all_pairs())

    def slot_delete_pair(self):
        if self.curr_selected_index < 0:
            return

        self.key_list.takeItem(self.curr_selected_index)
        self.value_list.takeItem(self.curr_selected_index)
        self.curr_selected_index = -1

        self.key_list.clearSelection()
        self.value_list.clearSelection()
        self.key_input.clear()
        self.value_input.clear()

        self.item_modified.emit(self.gen_all_pairs())

    def set_pairs(self, pairs:dict):
        self.key_list.clear()
        self.value_list.clear()
        for k, v in pairs.items():
            # print(k, v)
            self.key_list.addItem(k)
            self.value_list.addItem(v)
            self.value_list.item(self.value_list.count() - 1).setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            
        self.slot_key_list_item_clicked(self.key_list.item(0))
        self.slot_value_list_item_clicked(self.value_list.item(0))

    def gen_all_pairs(self) -> dict:
        rev = dict()
        for i in range(self.key_list.count()):
            rev[self.key_list.item(i).text()] = self.value_list.item(i).text()

        return rev


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = KeyValueWidget()
    widget.show()
    sys.exit(app.exec_())