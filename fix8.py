from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
                             QHBoxLayout, QLabel, QSlider, QMainWindow, QMessageBox,
                             QPushButton, QSizePolicy, QVBoxLayout, QWidget, QButtonGroup, QLineEdit)
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolBar
import findAOI



class QtCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=6, height=4, dpi=100):
        self.figure, self.ax = plt.subplots(
            ncols=1, nrows=1, figsize=(width, height))
        self.figure.tight_layout()

        FigureCanvasQTAgg.__init__(self, self.figure)
        self.setParent(parent)

        FigureCanvasQTAgg.setSizePolicy(
            self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

        self.initialize()
        self.history = []
        self.future = []
        self.suggestion = None
        self.trial = None
        self.current_fixation_number = None

    def initialize(self):
        """Initialize the Canvas object, display the welcome image
        """
        img = mpimg.imread("hello.jpg")
        self.ax.imshow(img)
        self.draw()


class Fix8(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fix8")
        self.initUI()

    # --- open an image file, display to canvas ---
    def openFile(self):
        # # --- open the file, grab the file name and file type ---
        qfd = QFileDialog()
        file = qfd.getOpenFileName(self, 'Open File', 'c:\\')
        #
        # --- make sure a png file is chosen, if cancelled don't do anything ---
        if file:
            fileName = file[0]
            fileName = fileName.split('/')[-1]
            fileType = fileName.split('.')[-1]

            if fileType.lower() != 'png':
                image = mpimg.imread('wrongFileType.png')
                self.canvas.ax.imshow(image)
                self.canvas.draw()
            else:
                image = mpimg.imread(str(fileName))
                self.canvas.ax.imshow(image)
                self.canvas.ax.set_title(str(fileName))
                self.canvas.draw()

    # --- UI structure ---
    def initUI(self):

        # --- wrapper layout ---
        self.wrapperLayout = QHBoxLayout()

        # --- two bar framework ---
        self.leftBar = QVBoxLayout()
        self.rightBar = QVBoxLayout()

        self.canvas = QtCanvas(self, width=12, height=8, dpi=200)
        self.rightBar.addWidget(self.canvas)

        # --- open file button ---
        self.button_openFile = QPushButton("Open File", self)
        self.leftBar.addWidget(self.button_openFile)
        self.button_openFile.clicked.connect(self.openFile)

        # --- add bars to layout ---
        self.wrapperLayout.addLayout(self.leftBar)
        self.wrapperLayout.addLayout(self.rightBar)

        # # --- drop down bar to open and manage files ---
        # manageFiles = QComboBox()
        # manageFiles.setEditable(True)
        #
        # manageFiles.addItem('Open')
        # manageFiles.addItem('Save')
        # manageFiles.setCurrentText('Select')
        #
        # manageFiles.setFixedSize(300,30)
        # manageFiles.lineEdit().setAlignment(Qt.AlignCenter)
        # manageFiles.lineEdit().setReadOnly(True)
        # leftBar.addWidget(manageFiles)



        # # --- bottom right tools ---
        # bottomRight = QVBoxLayout()
        # self.leftBar.addLayout(bottomRight)




        # # --- add rows of buttons to bottom right: row 1 ---
        # row1 = QHBoxLayout()
        # bottomRight.addLayout(row1)
        #
        # homeButton = QPushButton("Home Button", self)
        # # homeButton.setFixedSize(100,50)
        # leftArrow = QPushButton("Left Arrow", self)
        # # leftArrow.setFixedSize(100,50)
        # rightArrow = QPushButton("Right Arrow", self)
        # # rightArrow.setFixedSize(100,50)
        #
        # row1.addWidget(homeButton)
        # row1.addWidget(leftArrow)
        # row1.addWidget(rightArrow)
        #
        # # --- row 2 ---
        # row2 = QHBoxLayout()
        # bottomRight.addLayout(row2)
        #
        # move = QPushButton("Move", self)
        # move.setFixedSize(100,50)
        # find = QPushButton("Find", self)
        # find.setFixedSize(100,50)
        # adjust = QPushButton("Adjust", self)
        # adjust.setFixedSize(100,50)
        # stats = QPushButton("Stats", self)
        # stats.setFixedSize(100,50)
        #
        # row2.addWidget(move)
        # row2.addWidget(find)
        # row2.addWidget(adjust)
        # row2.addWidget(stats)
        #
        # # --- right side of tool ---
        # rightBar = QVBoxLayout()
        # self.wrapperLayout.addLayout(rightBar)
        #
        # #########################################
        # # testing progress bar
        # abovebottomButtons = QHBoxLayout()
        # rightBar.addLayout(abovebottomButtons)
        #
        # progressBar = QProgressBar(self)
        # progressBar.setGeometry(250, 80, 250, 20)
        # abovebottomButtons.addWidget(progressBar)
        # ##########################################
        #
        # bottomButtons = QHBoxLayout()
        # rightBar.addLayout(bottomButtons)
        #
        # previousButton = QPushButton('Previous', self)
        # bottomButtons.addWidget(previousButton)
        #
        # slider = QSlider(Qt.Horizontal)
        # slider.setMinimum(0)
        # slider.setMaximum(100)
        # bottomButtons.addWidget(slider)
        #
        # skipButton = QPushButton('Skip', self)
        # bottomButtons.addWidget(skipButton)
        #
        # nextButtonBottom = QPushButton('Next', self)
        # bottomButtons.addWidget(nextButtonBottom)
        #
        # selectAlgoButton = QComboBox(self)
        # selectAlgoButton.addItem('Select Correction Algorithm')
        # bottomButtons.addWidget(selectAlgoButton)
        #
        # # --- second row ---
        #
        # bottomButtons2 = QHBoxLayout()
        # rightBar.addLayout(bottomButtons2)
        #
        # showAOI = QCheckBox("Show Areas of Interest (AOIs)", self)
        # showAOI.setChecked(False)
        # bottomButtons2.addWidget(showAOI)
        #
        # showFixation = QCheckBox("Show Fixation", self)
        # showFixation.setChecked(False)
        # bottomButtons2.addWidget(showFixation)
        #
        # showSaccade = QCheckBox("Show Saccade", self)
        # showSaccade.setChecked(False)
        # bottomButtons2.addWidget(showSaccade)
        #
        # correctAllButton = QPushButton("Correct All", self)
        # bottomButtons2.addWidget(correctAllButton)

        widget = QWidget()
        widget.setLayout(self.wrapperLayout)
        self.setCentralWidget(widget)
        self.show()


if __name__ == '__main__':
    fix8 = QApplication([])
    window = Fix8()
    fix8.exec_()
