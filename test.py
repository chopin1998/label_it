import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget

class KeyValueWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.key_label = QLabel("Key:")
        self.value_label = QLabel("Value:")
        self.key_input = QLineEdit()
        self.value_input = QLineEdit()
        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        self.key_value_list = QListWidget()
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        key_value_layout = QHBoxLayout()
        
        key_value_layout.addWidget(self.key_label)
        key_value_layout.addWidget(self.key_input)
        key_value_layout.addWidget(self.value_label)
        key_value_layout.addWidget(self.value_input)
        
        layout.addLayout(key_value_layout)
        layout.addWidget(self.add_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.key_value_list)
        
        self.setLayout(layout)
        
        self.add_button.clicked.connect(self.add_pair)
        self.delete_button.clicked.connect(self.delete_pair)
    
    def add_pair(self):
        key = self.key_input.text()
        value = self.value_input.text()
        
        if key and value:
            self.key_value_list.addItem(f"{key}: {value}")
            self.key_input.clear()
            self.value_input.clear()
    
    def delete_pair(self):
        selected = self.key_value_list.currentItem()
        if selected:
            self.key_value_list.takeItem(self.key_value_list.row(selected))
    
    def get_all_pairs(self):
        pairs = []
        for i in range(self.key_value_list.count()):
            pair = self.key_value_list.item(i).text().split(": ")
            key = pair[0]
            value = pair[1]
            pairs.append((key, value))
        return pairs

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = KeyValueWidget()
    widget.show()
    sys.exit(app.exec_())