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

        # --- left side bar of tools and buttons ---
        leftBar = QVBoxLayout()

        # --- button layout ---
        buttonLayout = QVBoxLayout()
        leftBar.addLayout(buttonLayout)

        # --- bottom right tools ---
        bottomRight = QVBoxLayout()
        leftBar.addLayout(bottomRight)

        # --- add left bar to layout ---
        self.wrapperLayout.addLayout(leftBar)

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

        # --- add rows of buttons to bottom right: row 1 ---
        row1 = QHBoxLayout()
        bottomRight.addLayout(row1)

        homeButton = QPushButton("Home Button", self)
        homeButton.setFixedSize(100,50)
        leftArrow = QPushButton("Left Arrow", self)
        leftArrow.setFixedSize(100,50)
        rightArrow = QPushButton("Right Arrow", self)
        rightArrow.setFixedSize(100,50)

        row1.addWidget(homeButton)
        row1.addWidget(leftArrow)
        row1.addWidget(rightArrow)

        # --- row 2 ---
        row2 = QHBoxLayout()
        bottomRight.addLayout(row2)

        move = QPushButton("Move", self)
        move.setFixedSize(100,50)
        find = QPushButton("Find", self)
        find.setFixedSize(100,50)
        adjust = QPushButton("Adjust", self)
        adjust.setFixedSize(100,50)
        stats = QPushButton("Stats", self)
        stats.setFixedSize(100,50)

        row2.addWidget(move)
        row2.addWidget(find)
        row2.addWidget(adjust)
        row2.addWidget(stats)

        widget = QWidget()
        widget.setLayout(self.wrapperLayout)
        self.setCentralWidget(widget)
        self.show()


if __name__ == '__main__':
    fix8 = QApplication([])
    window = Fix8()
    fix8.exec_()
