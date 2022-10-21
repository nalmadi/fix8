from PyQt5.QtCore import *
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
                             QHBoxLayout, QLabel, QSlider, QMainWindow, QMessageBox,
                             QPushButton, QSizePolicy, QVBoxLayout, QWidget, QButtonGroup)


class Fix8(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fix8")
        self.initUI()

    def initUI(self):
        # --- size of UI ---
        self.setFixedWidth(1500)
        self.setFixedHeight(900)

        # --- wrapper layout ---
        self.wrapperLayout = QHBoxLayout()

        # button layout - the side bar of buttons
        buttonLayout = QVBoxLayout()
        self.wrapperLayout.addLayout(buttonLayout)

        # --- button to open a file ---
        openFileButton = QPushButton('Open File', self)
        openFileButton.setFixedSize(200,50)
        buttonLayout.addWidget(openFileButton)

        # --- next ---
        nextButton = QPushButton("Next Trial", self)
        nextButton.setFixedSize(200,50)
        buttonLayout.addWidget(nextButton)

        # --- back ---
        backButton = QPushButton("Previous Trial", self)
        backButton.setFixedSize(200,50)
        buttonLayout.addWidget(backButton)

        #  --- save ---
        saveButton = QPushButton("Save", self)
        saveButton.setFixedSize(200,50)
        buttonLayout.addWidget(saveButton)

        #  --- cancel ---
        cancelButton = QPushButton("Cancel", self)
        cancelButton.setFixedSize(200,50)
        buttonLayout.addWidget(cancelButton)

        buttonLayout.insertStretch(-1,0)
        buttonLayout.setSpacing(10)

        widget = QWidget()
        widget.setLayout(self.wrapperLayout)
        self.setCentralWidget(widget)
        self.show()


if __name__ == '__main__':
    fix8 = QApplication([])
    window = Fix8()
    fix8.exec_()
