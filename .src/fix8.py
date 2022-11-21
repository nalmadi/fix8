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
import driftAlgorithms as da
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import threading
import copy


class QtCanvas(FigureCanvasQTAgg):

    '''Credit: Dr. Naser Al Madi and Ricky Peng'''
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
        self.init_UI()

        # fields relating to the stimulus
        self.file, self.file_path, self.file_name = None, None, None

        # fields relating to the trial folder
        self.folder_path, self.trial_path, self.trial_data = None, None, None

        # fields relating to fixations
        self.original_fixations, self.corrected_fixations, self.scatter = None, None, None
        self.current_fixation = 0

        # fields relating to AOIs
        self.patches, self.aoi, self.background_color = None, None, None

        # the algorithm the user selects, intially just the original
        self.algorithm = 'original'

        # fields relating to the drag and drop system
        self.selected_fixation = None
        self.epsilon = 11
        self.xy = None
        self.canvas.mpl_connect('button_press_event', self.button_press_callback)
        self.canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)

    '''get the selected fixation that the user picks, with the selection inside a specific diameter range (epsilon),
    selected_fixation is an index, not the actual scatter point'''
    def get_selected_fixation(self, event):
        if self.scatter is not None:
            self.xy = np.asarray(self.scatter.get_offsets())
            xyt = self.canvas.ax.transData.transform(self.xy)
            xt, yt = xyt[:, 0], xyt[:, 1]

            d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
            self.selected_fixation = d.argmin()

            if d[self.selected_fixation] >= self.epsilon:
                self.selected_fixation = None

            return self.selected_fixation

    def button_press_callback(self, event):
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self.selected_fixation = self.get_selected_fixation(event)

    '''when released the fixation, update the corrected fixations'''
    def button_release_callback(self, event):
        if self.selected_fixation is not None:
            self.corrected_fixations[self.selected_fixation][0] = self.xy[self.selected_fixation][0]
            self.corrected_fixations[self.selected_fixation][1] = self.xy[self.selected_fixation][1]
        if event.button != 1:
            return
        self.selected_fixation = None

    def motion_notify_callback(self, event):
        if self.selected_fixation is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        x, y = event.xdata, event.ydata
        self.xy = np.asarray(self.scatter.get_offsets())
        self.xy[self.selected_fixation] = np.array([x, y])
        self.scatter.set_offsets(self.xy)
        self.canvas.draw_idle()

    '''opens the stimulus, displays it to the canvas, and grabs the aois of the image'''
    def open_stimulus(self):
        # open the file, grab the file name and file type
        qfd = QFileDialog()
        self.file = qfd.getOpenFileName(self, 'Open File', 'c:\\')

        # make sure a file is chosen, if cancelled don't do anything
        if self.file[0] != '':
            self.file_path = self.file[0]
            self.file_name = self.file_path.split('/')[-1]
            fileType = self.file_name.split('.')[-1]

            # make sure the file is a png type
            if fileType.lower() != 'png':
                image = mpimg.imread('./.images/wrongFile.png')
                self.canvas.ax.imshow(image)
                self.canvas.draw()
                self.disable_relevant_buttons("not_a_PNG")
            else:
                # draw the image to the canvas
                self.canvas.clear()
                image = mpimg.imread(self.file[0])
                self.canvas.ax.imshow(image)
                self.canvas.ax.set_title(str(self.file_name.split('.')[0]))
                self.canvas.draw()

                self.find_aoi()

                self.enable_relevant_buttons("stimulus_chosen")


    '''open trial folder, display it to trial list window with list of JSON trials'''
    def open_trial_folder(self):

        qfd = QFileDialog()
        self.folder_path = qfd.getExistingDirectory(self, 'Select Folder')

        # --- make sure a folder was actually chosen, otherwise just cancel ---
        if self.folder_path != '':

            self.trial_list.clear()
            self.clear_fixations()

            # when open a new folder, block off all the relevant buttons that shouldn't be accesible until a trial is clicked
            self.disable_relevant_buttons("folder_opened")

            files = listdir(self.folder_path)

            if len(files) > 0:
                self.file_list = []
                for file in files:
                    if file.endswith(".json"):
                        self.file_list.append(self.folder_path + "/" + file)
                if len(self.file_list) > 0:
                    # add the files to the trial list window
                    list_index = 0
                    self.trials = {}
                    for file in self.file_list:
                        file_to_add = QListWidgetItem(file)
                        file_text = str(self.file_list[list_index])
                        file_to_add_name = file_text.split('/')[-1] # last part of file text
                        self.trials[file_to_add_name] = file
                        file_to_add.setText(file_to_add_name)
                        self.trial_list.addItem(file_to_add)
                        list_index = list_index + 1
                else:
                    qmb = QMessageBox()
                    qmb.setWindowTitle("Trial Folder Error")
                    qmb.setText("No JSONS")
                    qmb.exec_()
            else:
                qmb = QMessageBox()
                qmb.setWindowTitle("Trial Folder Error")
                qmb.setText("Empty Folder")
                qmb.exec_()

    '''when a trial from the trial list is double clicked, find the fixations of the trial
        parameters:
        item - the value passed through when clicking a trial object in the list'''
    def trial_double_clicked(self,item):
        self.trial_path = self.trials[item.text()]

        self.find_fixations(self.trial_path)
        self.corrected_fixations = copy.deepcopy(self.original_fixations)

        if self.checkbox_show_fixations.isChecked() == True:
            self.clear_fixations()
            self.draw_fixations()
        self.dropdown_select_algorithm.setCurrentIndex(0)
        # self.findSaccades()

    '''find the areas of interest (aoi) for the selected stimulus'''
    def find_aoi(self):
        if self.file[0] != '':
            self.aoi, self.background_color = emtk.find_aoi(image=self.file_name, image_path=self.file_path.replace(self.file_name, ''))

    '''draw the found aois to the canvas'''
    def draw_aoi(self):
        color = "yellow" if self.background_color == "black" else "black"
        self.patches = []

        for row in self.aoi.iterrows():
            # ---
            '''Credit: Dr. Naser Al Madi and Ricky Peng'''
            xcord = row[1]['x']
            ycord = row[1]['y']
            height = row[1]['height']
            width = row[1]['width']
            # ---

            self.patches.append(self.canvas.ax.add_patch(Rectangle((xcord, ycord), width-1, height-1,linewidth=0.8,edgecolor=color,facecolor="none",alpha=0.65)))

        self.canvas.draw()

    '''clear the aois from the canvas'''
    def clear_aoi(self):
        for patch in self.patches:
            patch.remove()
        self.canvas.draw()

    '''when the show aoi button is pressed, show or hide aois based on checkbox'''
    def show_aoi(self, state):
        if self.checkbox_show_aoi.isCheckable():
            if state == Qt.Checked:
                self.draw_aoi()
            elif state == Qt.Unchecked:
                self.clear_aoi()

    '''find all the fixations of the trial that was double clicked
        parameters:
        trial_path - the trial file path of the trial clicked on'''
    def find_fixations(self, trial_path):
        self.original_fixations = []
        with open(trial_path, 'r') as trial:
            try:
                self.trial_data = json.load(trial)
                for x in self.trial_data:
                    self.original_fixations.append([self.trial_data[x][0], self.trial_data[x][1], self.trial_data[x][2]])
                self.original_fixations = np.array(self.original_fixations)
                self.enable_relevant_buttons("trial_clicked")
            except json.decoder.JSONDecodeError:
                qmb = QMessageBox()
                qmb.setWindowTitle("Trial File Error")
                qmb.setText("Trial Error: JSON File Empty")
                qmb.exec_()

    '''Credit: Dr. Naser Al Madi and Ricky Peng'''
    def find_lines_y(self, aoi):
        results = []
        for index, row in aoi.iterrows():
            y, height = row['y'], row['height']

            if y + height / 2 not in results:
                results.append(y + height / 2)

        return results

    '''draw the fixations to the canvas
        parameters:
        fixations - 0 is default since the corrected fixations are the main thing to be shown,
        1 the original fixations is manually chosen'''
    def draw_fixations(self, fixations = 0):
        if fixations == 0: # default fixations to use
            fixations = self.corrected_fixations
        elif fixations == 1:
            fixations = self.original_fixations
        x = fixations[:, 0]
        y = fixations[:, 1]
        duration = fixations[:, 2]
        self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = 'red')
        self.canvas.draw()

    '''if the user clicks the show fixations checkbox, show or hide the fixations
        parameters:
        state - the checkbox being checked or unchecked'''
    def show_fixations(self, state):
        if self.folder_path != '':
            if self.checkbox_show_fixations.isCheckable():
                if state == Qt.Checked:
                    self.draw_fixations()
                    self.enable_relevant_buttons("show_fixations_checked")
                elif state == Qt.Unchecked:
                    self.clear_fixations()
                    self.disable_relevant_buttons("show_fixations_unchecked")

    '''clear the fixations from the canvas'''
    def clear_fixations(self):
        if self.scatter != None:
            self.scatter.remove()
            self.scatter = None
            self.canvas.draw()

    '''when the user selects an algorithm from the drop down menu, make it the current algorithm to use
        parameters:
        algorithm - the selected correction algorithm'''
    def get_algorithm_picked(self,algorithm):
        self.algorithm = algorithm
        print(self.algorithm)

    '''if the user selects a correction algorithm, correct the current position of the fixations
        parameters:
        algorithm - the selected correction algorithm'''
    def correct_all_fixations(self):
        print("corecting all..")
        self.algorithm = self.algorithm.lower()
        if self.algorithm == 'original':
            self.find_fixations(self.trial_path)
            self.clear_fixations()
            if self.checkbox_show_fixations.isChecked():
                self.draw_fixations(1) # 1 = draw originals

            # reset fixations
            self.corrected_fixations = copy.deepcopy(self.original_fixations)
        elif self.algorithm == 'attach':
            fixation_XY = self.corrected_fixations
            line_Y = self.find_lines_y(self.aoi)
            self.corrected_fixations = da.attach(fixation_XY, line_Y)
            self.clear_fixations()
            if self.checkbox_show_fixations.isChecked():
                self.draw_fixations()

    '''save a JSON object of the corrections to a file'''
    def save_corrections(self):
        if self.corrected_fixations is not None:
            list = self.corrected_fixations.tolist()
            corrected_fixations = {}
            for i in range(len(self.corrected_fixations)):
                corrected_fixations[i + 1] = list[i]
            with open(f"{self.trial_path.replace('.json', '_CORRECTED.json')}", 'w') as f:
                json.dump(corrected_fixations, f)
        else:
            qmb = QMessageBox()
            qmb.setWindowTitle("Save Error")
            qmb.setText("No Corrections Made")
            qmb.exec_()

    def next_fixation(self):
        self.current_fixation += 1
        fixations = np.asarray(self.scatter.get_offsets())


    '''initalize the tool window'''
    def init_UI(self):

        # wrapper layout
        self.wrapper_layout = QHBoxLayout()

        # left side is one half, right side is the other half of the tool
        self.left_side = QVBoxLayout()
        self.right_side = QVBoxLayout()

        self.canvas = QtCanvas(self, width=12, height=8, dpi=200)
        self.right_side.addWidget(self.canvas)

        # button to open stimulus (image)
        self.button_open_stimulus = QPushButton("Open Stimulus", self)
        self.left_side.addWidget(self.button_open_stimulus)
        self.button_open_stimulus.clicked.connect(self.open_stimulus)

        # button to open folder which contains trial data JSON files
        self.button_open_folder = QPushButton("Open Trial Folder", self)
        self.left_side.addWidget(self.button_open_folder)
        self.button_open_folder.clicked.connect(self.open_trial_folder)

        # button to save corrected fixations to a file
        self.button_save_corrections = QPushButton("Save Corrections", self)
        self.left_side.addWidget(self.button_save_corrections)
        self.button_save_corrections.clicked.connect(self.save_corrections)

        # window list to access trial data
        self.trial_list = QListWidget()
        self.left_side.addWidget(self.trial_list)
        self.trial_list.itemDoubleClicked.connect(self.trial_double_clicked)

        # layout below the trial list window
        self.below_trial_list = QHBoxLayout()

        # button to move to the next fixation
        self.button_next_fixation = QPushButton("Next Fixation")
        self.button_next_fixation.clicked.connect(self.next_fixation)
        self.below_trial_list.addWidget(self.button_next_fixation)

        self.left_side.addLayout(self.below_trial_list)

        # toolbar to interact with canvas
        self.toolbar = NavigationToolBar(self.canvas, self)
        self.toolbar.setStyleSheet("QToolBar { border: 0px }")
        self.left_side.addWidget(self.toolbar)

        # section on right side, below canvas
        self.below_canvas = QHBoxLayout()
        self.right_side.addLayout(self.below_canvas)

        # checkbox to show and hide AOIs
        self.checkbox_show_aoi = QCheckBox("Show Areas of Interest (AOIs)", self)
        self.checkbox_show_aoi.stateChanged.connect(self.show_aoi)
        self.below_canvas.addWidget(self.checkbox_show_aoi)

        # checkbox to show and hide fixations
        self.checkbox_show_fixations = QCheckBox("Show Fixations", self)
        self.checkbox_show_fixations.stateChanged.connect(self.show_fixations)
        self.below_canvas.addWidget(self.checkbox_show_fixations)

        # drop down menu to select correction algorithm
        self.dropdown_select_algorithm = QComboBox()
        self.dropdown_select_algorithm.setEditable(True)
        self.dropdown_select_algorithm.addItem('Original')
        self.dropdown_select_algorithm.addItem('Attach')
        self.dropdown_select_algorithm.lineEdit().setAlignment(Qt.AlignCenter)
        self.dropdown_select_algorithm.lineEdit().setReadOnly(True)
        self.below_canvas.addWidget(self.dropdown_select_algorithm)
        self.dropdown_select_algorithm.currentTextChanged.connect(self.get_algorithm_picked)

        # correct all fixations button
        self.button_correct_all_fixations = QPushButton("Correct All Fixations")
        self.below_canvas.addWidget(self.button_correct_all_fixations)
        self.button_correct_all_fixations.clicked.connect(self.correct_all_fixations)

        # add both sides to overall wrapper layout
        self.wrapper_layout.addLayout(self.left_side)
        self.wrapper_layout.addLayout(self.right_side)

        # initial button states
        self.button_open_folder.setEnabled(False)
        self.button_save_corrections.setEnabled(False)
        self.toolbar.setEnabled(False)
        self.checkbox_show_aoi.setChecked(False)
        self.checkbox_show_aoi.setCheckable(False)
        self.checkbox_show_fixations.setChecked(False)
        self.checkbox_show_fixations.setCheckable(False)
        self.dropdown_select_algorithm.setEditable(False)
        self.dropdown_select_algorithm.setEnabled(False)
        self.button_next_fixation.setEnabled(False)
        self.button_correct_all_fixations.setEnabled(False)

        widget = QWidget()
        widget.setLayout(self.wrapper_layout)
        self.setCentralWidget(widget)
        self.show()

    '''Disables any buttons that shouldn't be used with whatever element of the tool the user interacted with
        parameters:
        feature - the element the user interacted with
    '''
    def disable_relevant_buttons(self, feature):
        if feature == "not_a_PNG":
            self.button_open_folder.setEnabled(False)
            self.button_save_corrections.setEnabled(False)
            self.toolbar.setEnabled(False)
            self.checkbox_show_aoi.setChecked(False)
            self.checkbox_show_aoi.setCheckable(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setCheckable(False)
            self.dropdown_select_algorithm.setEditable(False)
            self.dropdown_select_algorithm.setEnabled(False)
            self.button_next_fixation.setEnabled(False)
            self.button_correct_all_fixations.setEnabled(False)
        elif feature == "folder_opened":
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setCheckable(False)
            self.dropdown_select_algorithm.setEnabled(False)
            self.button_save_corrections.setEnabled(False)
            self.button_next_fixation.setEnabled(False)
            self.button_correct_all_fixations.setEnabled(False)
        elif feature == "show_fixations_unchecked":
            self.button_next_fixation.setEnabled(False)
            self.button_correct_all_fixations.setEnabled(False)
        elif feature == "stimulus_chosen":
            self.button_save_corrections.setEnabled(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setCheckable(False)
            self.dropdown_select_algorithm.setEditable(False)
            self.dropdown_select_algorithm.setEnabled(False)
            self.button_next_fixation.setEnabled(False)
            self.button_correct_all_fixations.setEnabled(False)

    '''Enables any buttons that can be used with whatever element of the tool the user interacted with
        parameters:
        feature - the element the user interacted with
    '''
    def enable_relevant_buttons(self, feature):
        if feature == "stimulus_chosen":
            self.checkbox_show_aoi.setCheckable(True)
            self.checkbox_show_aoi.setChecked(False)
            self.toolbar.setEnabled(True)
            self.button_open_folder.setEnabled(True)
            self.disable_relevant_buttons(feature)
        elif feature == "trial_clicked":
            self.checkbox_show_fixations.setCheckable(True)
            self.dropdown_select_algorithm.setEnabled(True)
            self.button_save_corrections.setEnabled(True)
        elif feature == "show_fixations_checked":
            self.button_next_fixation.setEnabled(True)
            self.button_correct_all_fixations.setEnabled(True)

if __name__ == '__main__':
    fix8 = QApplication([])
    window = Fix8()
    fix8.exec_()
