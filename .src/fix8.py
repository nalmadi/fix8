from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
                             QHBoxLayout, QLabel, QSlider, QMainWindow, QMessageBox,
                             QPushButton, QSizePolicy, QVBoxLayout, QWidget, QButtonGroup, QLineEdit, QListWidget, QListWidgetItem)
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolBar
import emip_toolkit as emtk
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle
import json
from os import listdir
from os.path import isfile, join


class QtCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=12, height=8, dpi=100):
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
        img = mpimg.imread("./.images/welcome.png")
        self.ax.imshow(img)
        self.draw

    def clear(self):
        self.ax.clear()


class Fix8(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fix8")
        self.initUI()
        self.file, self.filePath, self.fileName, self.fileType, self.folderPath, self.fileList = None, None, None, None, None, None
        self.patches, self.aoi, self.backgroundColor = None, None, None
        self.fixations, self.trialData, self.scatter = None, None, None

    # --- open an image file, display to canvas ---
    def openFile(self):
        # --- open the file, grab the file name and file type ---
        qfd = QFileDialog()
        self.folderPath = qfd.getExistingDirectory(self, 'Select Folder')
        # self.file = qfd.getOpenFileName(self, 'Open File', 'c:\\')

        # --- make sure a folder was actually chosen, otherwise just cancel ---
        if self.folderPath:
            files = listdir(self.folderPath)
            if len(files) == 0:
                img = mpimg.imread("./.images/novalidfiles.png")
                self.canvas.ax.imshow(img)
                self.canvas.draw()
                self.blockButtons()
            else:
                self.fileList = []
                for file in files:
                    if file.endswith(".json"):
                        self.fileList.append(self.folderPath + "/" + file)

                if len(self.fileList) == 0:
                    img = mpimg.imread("./.images/novalidfiles.png")
                    self.canvas.ax.imshow(img)
                    self.canvas.draw()
                    self.blockButtons()
                else:
                    img = mpimg.imread("./.images/selecttrial.png")
                    self.canvas.ax.imshow(img)
                    self.canvas.draw()

                    # add the files to the file list window
                    listIndex = 0
                    for file in self.fileList:
                        fileToAdd = QListWidgetItem(file)
                        fileToAddName = str("Trial " + str(listIndex))
                        fileToAdd.setText(fileToAddName)
                        self.list_viewFiles.addItem(fileToAdd)
                        listIndex = listIndex + 1

                    # once trial is selected then initialize everything
                    self.initButtons()

        # --- make sure a png file is chosen, if cancelled don't do anything ---
        # if self.file:
        #     self.filePath = self.file[0]
        #     self.fileName = self.filePath.split('/')[-1]
        #     self.fileType = self.fileName.split('.')[-1]
        #
        #     if self.fileType.lower() != 'png':
        #         image = mpimg.imread('./.images/wrongFile.png')
        #         self.canvas.ax.imshow(image)
        #         self.canvas.draw()
        #         self.blockButtons()
        #     else:
        #         self.canvas.clear()
        #         image = mpimg.imread(self.file[0])
        #         self.canvas.ax.imshow(image)
        #         self.canvas.ax.set_title(str(self.fileName.split('.')[0]))
        #         self.canvas.draw()
        #         self.runTrial()
        #         self.initButtons()

    # --- find the AOIs for current image ---
    def findAOI(self):
        if self.file:
            self.aoi, self.backgroundColor = emtk.find_aoi(image=self.fileName, image_path=self.filePath.replace(self.fileName, ''))

    # --- draw the AOI to screen ---
    def drawAOI(self):
        color = "yellow" if self.backgroundColor == "black" else "black"
        self.patches = []

        for row in self.aoi.iterrows():
            xcord = row[1]['x']
            ycord = row[1]['y']
            height = row[1]['height']
            width = row[1]['width']
            self.patches.append(self.canvas.ax.add_patch(Rectangle((xcord, ycord), width-1, height-1,linewidth=0.8,edgecolor=color,facecolor="none",alpha=0.65)))

        self.canvas.draw()

    # --- clear AOIs from canvas
    def clearAOI(self):
        for patch in self.patches:
            patch.remove()
        self.canvas.draw()

    # --- triggered by the show AOI checkbox, show or hide AOIs ---
    def showAOI(self, state):
        if self.file:
            if self.checkbox_showAOI.isCheckable():
                if state == Qt.Checked:
                    self.drawAOI()
                elif state == Qt.Unchecked:
                    self.clearAOI()

    # --- find all fixations of the given trial ---
    def findFixations(self, trialPath):
        self.fixations = []
        with open(trialPath, 'r') as trial:
            self.trialData = json.load(trial)

        for x in self.trialData:
            self.fixations.append([self.trialData[x][0], self.trialData[x][1], self.trialData[x][2]])

        self.fixations = np.array(self.fixations)

    # --- draw fixations to canvas ---
    def drawFixations(self):
        x = self.fixations[:, 0]
        y = self.fixations[:, 1]
        duration = self.fixations[:, 2]

        self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = 'red')
        self.canvas.draw()

    # -- clear the fixations on the canvas ---
    def clearFixations(self):
        self.scatter.remove()
        self.scatter = None
        self.canvas.draw()

    # --- triggered by show fixations check box ---
    def showFixations(self, state):
        if self.file:
            if self.checkbox_showFixations.isCheckable():
                if state == Qt.Checked:
                    self.drawFixations()
                elif state == Qt.Unchecked:
                    self.clearFixations()

    def drawSaccades(self):
        line = self.canvas.ax.plot(self.fixations[:, 0], self.fixations[:, 1], alpha=0.4, c='blue', linewidth=2)

    # --- run the trial on the data given ---
    def runTrial(self):
        self.findAOI()
        self.findFixations('trial.json')
        self.drawSaccades()

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

        # --- file viewer window ---
        self.list_viewFiles = QListWidget()
        self.leftBar.addWidget(self.list_viewFiles)

        # --- right buttons below the canvas ---
        self.belowCanvas = QHBoxLayout()
        self.rightBar.addLayout(self.belowCanvas)

        # --- show AOI checkbox ---
        self.checkbox_showAOI = QCheckBox("Show Areas of Interest (AOIs)", self)
        self.checkbox_showAOI.setChecked(False)
        self.checkbox_showAOI.setCheckable(False)
        self.checkbox_showAOI.stateChanged.connect(self.showAOI)
        self.belowCanvas.addWidget(self.checkbox_showAOI)

        # --- show Fixations checkbox ---
        self.checkbox_showFixations = QCheckBox("Show Fixations", self)
        self.checkbox_showFixations.setChecked(False)
        self.checkbox_showFixations.setCheckable(False)
        self.checkbox_showFixations.stateChanged.connect(self.showFixations)
        self.belowCanvas.addWidget(self.checkbox_showFixations)

        # # --- show Saccades checkbox ---
        # self.checkbox_showSaccades = QCheckBox("Show Saccades", self)
        # self.checkbox_showSaccades.setChecked(False)
        # self.checkbox_showSaccades.setCheckable(False)
        # self.checkbox_showSaccades.stateChanged.connect(self.showSaccades)
        # self.belowCanvas.addWidget(self.checkbox_showSaccades)

        # --- add bars to layout ---
        self.wrapperLayout.addLayout(self.leftBar)
        self.wrapperLayout.addLayout(self.rightBar)

        widget = QWidget()
        widget.setLayout(self.wrapperLayout)
        self.setCentralWidget(widget)
        self.show()

        # --- drop down bar to open and manage files ---
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
        #
        #
        #
        # # --- bottom right tools ---
        # bottomRight = QVBoxLayout()
        # self.leftBar.addLayout(bottomRight)
        #
        #
        #
        #
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
        # testing progress bar
        # abovebottomButtons = QHBoxLayout()
        # self.rightBar.addLayout(abovebottomButtons)
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
        #


    # --- allows or blocks buttons from being interacted with depending on if a correct file was chosen
    def initButtons(self):
        self.checkbox_showAOI.setCheckable(True)
        self.checkbox_showFixations.setCheckable(True)

    def blockButtons(self):
        self.checkbox_showAOI.setCheckable(False)
        self.checkbox_showFixations.setCheckable(False)


if __name__ == '__main__':
    fix8 = QApplication([])
    window = Fix8()
    fix8.exec_()