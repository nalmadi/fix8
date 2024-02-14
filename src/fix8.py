# Fix8
#
# Authors: Naser Al Madi <nsalmadi@colby.edu>
#          Brett Torra
#          Agnes Li
#          Najam Tariq
#          Ricky Peng
#
#
# URL: https://github.com/nalmadi/fix8
#
#
# The algorithms were implemented by:
#          Jon Carr
# URL: https://github.com/jwcarr/drift
# For license information, see LICENSE.TXT

"""
Fix8 (Fixate) is an open source Python GUI tool for visualizing and correcting
eye tracking data.  Fix8 supports manual, automated, and semi-automated 
correction methods for eye tracking data in reading tasks.

(If you use Fix8 in academic research, please cite our paper)
"""

import time

# from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (
    QFrame,
    QApplication,
    QCheckBox,
    QFileDialog,
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QSlider,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QStatusBar,
    QAction,
)
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolBar
from matplotlib.patches import Rectangle
import json
from os import listdir
import driftAlgorithms as da
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)
import copy

# import matplotlib.animation as animation
from datetime import date
from pathlib import Path

import mini_emtk
from merge_fixations_dialog import InputDialog

# from PySide2 import QtWidgets
# from PyQt5 import QtWidgets
# from qt_material import apply_stylesheet


class QtCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=12, height=8, dpi=100):
        self.figure, self.ax = plt.subplots(ncols=1, nrows=1, figsize=(width, height))
        self.figure.tight_layout()

        FigureCanvasQTAgg.__init__(self, self.figure)
        self.setParent(parent)

        FigureCanvasQTAgg.setSizePolicy(
            self, QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        FigureCanvasQTAgg.updateGeometry(self)

        self.initialize()
        self.history = []
        self.future = []
        self.suggestion = None
        self.trial = None

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
        self.setWindowIcon(QIcon("icon.ico"))
        self.init_UI()

        # add menues
        self.file_menu = self.menuBar().addMenu("File")
        self.edit_menu = self.menuBar().addMenu("Edit")
        self.filters_menu = self.menuBar().addMenu("Filters")
        #self.generate_menu = self.menuBar().addMenu("Generate")
        self.correction_menu = self.menuBar().addMenu("Correction")
        self.automated_correction_menu = self.correction_menu.addMenu("Automatic")
        self.semi_auto_correction_menu = self.correction_menu.addMenu("Assisted")

        # add actions
        self.new_file_action = QAction(QIcon("./.images/open.png"), "Open Folder", self)
        self.save_correction_action = QAction( QIcon("./.images/save.png"), "Save Correction", self)

        self.next_fixation_action = QAction("Next Fixation", self)
        self.previous_fixation_action = QAction("Previous Fixation", self)
        self.accept_and_next_action = QAction("Accept suggestion and next", self)
        self.delete_fixation_action = QAction("Delete Fixation", self)

        self.lowpass_duration_filter_action = QAction("Filters less than", self)
        self.highpass_duration_filter_action = QAction("Filters greater than", self)
        self.merge_fixations_filter_action = QAction("Merge Fixations", self)

        self.manual_correction_action = QAction("Manual", self)
        self.warp_auto_action = QAction("Warp", self)
        self.warp_semi_action = QAction("Warp", self)

        # add shortcuts
        self.new_file_action.setShortcut("Ctrl+O")
        self.save_correction_action.setShortcut("Ctrl+S")

        self.next_fixation_action.setShortcut("a")
        self.previous_fixation_action.setShortcut("z")
        self.accept_and_next_action.setShortcut("Alt")
        self.delete_fixation_action.setShortcut("Del")

        # enable/disable
        self.save_correction_action.setEnabled(False)
        self.edit_menu.setEnabled(False)
        self.filters_menu.setEnabled(False)
        self.correction_menu.setEnabled(False)

        # connect functions
        self.new_file_action.triggered.connect(self.open_trial_folder)
        self.save_correction_action.triggered.connect(self.save_corrections)

        self.next_fixation_action.triggered.connect(self.next_fixation)
        self.previous_fixation_action.triggered.connect(self.previous_fixation)

        self.lowpass_duration_filter_action.triggered.connect(self.lowpass_duration_filter)
        self.highpass_duration_filter_action.triggered.connect(self.highpass_duration_filter)
        self.merge_fixations_filter_action.triggered.connect(self.merge_fixations)
        
        self.warp_auto_action.triggered.connect(lambda: self.run_algorithm('warp', da.warp, 'auto'))
        self.warp_semi_action.triggered.connect(lambda: self.run_algorithm('warp', da.warp, 'semi'))
        self.manual_correction_action.triggered.connect(self.manual_correction)

        # add actions to menu
        self.file_menu.addAction(self.new_file_action)
        self.file_menu.addAction(self.save_correction_action)

        self.edit_menu.addAction(self.next_fixation_action)
        self.edit_menu.addAction(self.previous_fixation_action)
        self.edit_menu.addAction(self.accept_and_next_action)
        self.edit_menu.addAction(self.delete_fixation_action)

        self.filters_menu.addAction(self.lowpass_duration_filter_action)
        self.filters_menu.addAction(self.highpass_duration_filter_action)
        self.filters_menu.addAction(self.merge_fixations_filter_action)

        self.correction_menu.addAction(self.manual_correction_action)
        self.automated_correction_menu.addAction(self.warp_auto_action)
        self.semi_auto_correction_menu.addAction(self.warp_semi_action)

        # fields relating to the stimulus
        self.file, self.file_path, self.file_name = None, None, None

        # fields relating to the trial folder
        self.folder_path, self.trial_path, self.trial_data, self.trial_name = (
            None,
            None,
            None,
            None,
        )

        # fields relating to fixations
        self.original_fixations, self.fixations, self.scatter, self.saccades = (
            None,
            None,
            None,
            None,
        )
        self.current_fixation = -1

        # fields relating to AOIs
        self.patches, self.aoi, self.background_color = None, None, None

        # fields relating to the correction algorithm
        self.algorithm = "manual"
        self.algorithm_function = None
        self.suggested_corrections, self.suggested_suggestion = None, None
        # single suggestion is the current suggestion

        # keeps track of how many times file was saved so duplicates can be saved instead of overriding previous save file
        self.timer_start = 0  # beginning time of trial
        self.duration = 0
        self.user = ""
        self.metadata = ""

        self.saccade_opacity = 0.4
        self.fixation_opacity = 0.4

        # fields relating to the drag and drop system
        self.selected_fixation = None
        self.epsilon = 11
        self.xy = None
        self.canvas.mpl_connect("button_press_event", self.button_press_callback)
        self.canvas.mpl_connect("button_release_event", self.button_release_callback)
        self.canvas.mpl_connect("motion_notify_event", self.motion_notify_callback)

        # fields relating to aoi margin
        self.aoi_width = 7
        self.aoi_height = 4

        # fields relating to color filters
        self.fixation_color = "red"
        self.current_fixation_color = "yellow"
        self.suggested_fixation_color = "blue"
        self.saccade_color = "blue"
        self.aoi_color = "yellow"
        self.colorblind_assist_status = False


    def lowpass_duration_filter(self):
        
        minimum_value = 1
        maximum_value = 99
        default_value = 80
        title = "Less Than Duration Filter"
        message = "Remove fixations with durations less than"
        threshold, ok = QInputDialog.getInt(self, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "filter,removed fixations less than "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )

        self.fixations = self.fixations[self.fixations[:, 2] > int(threshold)]
        self.current_fixation = 0

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            if self.current_fixation == len(self.fixations):
                self.current_fixation = len(self.fixations) - 1

            self.suggested_corrections = self.suggested_corrections[self.suggested_corrections[:, 2] > int(threshold)]

        self.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)

    
    def highpass_duration_filter(self):
        minimum_value = 100
        maximum_value = 2000
        default_value = 800
        title = "Greater Than Duration Filter"
        message = "Remove fixations with durations greater than"
        threshold, ok = QInputDialog.getInt(self, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "filter,removed fixations greater than "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )

        self.fixations = self.fixations[self.fixations[:, 2] < int(threshold)]
        self.current_fixation = 0

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            if self.current_fixation == len(self.fixations):
                self.current_fixation = len(self.fixations) - 1

            self.suggested_corrections = self.suggested_corrections[self.suggested_corrections[:, 2] < int(threshold)]

        self.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)


    def merge_fixations(self):
        dialog = InputDialog()
        dialog.exec()
        
        duration_threshold, dispersion_threshold = dialog.getInputs()
        # check empty
        if duration_threshold == '' and dispersion_threshold == '':
            return
        
        # check ints
        try:
            duration_threshold = int(duration_threshold)
            dispersion_threshold = int(dispersion_threshold)
        except:
            return
    
        # write metadata
        self.metadata += (
            "filter,merge fixations less than "
            + str(duration_threshold)
            + ", dispersion_threshold"
            + str(dispersion_threshold)
            + ", "
            + str(time.time())
            + "\n"
        )

        # merge fixations
        new_fixations = list(self.fixations).copy()
        index = 0
        while index < len(new_fixations) - 1:
            
            # if either fixation is short and distance is small, merge
            if ((new_fixations[index][2] <= duration_threshold or new_fixations[index+1][2] <= duration_threshold)
                and mini_emtk.distance(new_fixations[index], new_fixations[index + 1]) <= dispersion_threshold):

                new_fixations[index + 1][2] += new_fixations[index][2]
                new_fixations.pop(index)
            else:
                index += 1

        self.fixations = np.array(new_fixations)

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            self.run_correction()

        if self.current_fixation >= len(self.fixations):
            self.current_fixation = len(self.fixations) - 1

        self.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)


    def run_correction(self):

        fixation_XY = copy.deepcopy(self.fixations)
        fixation_XY = fixation_XY[:, 0:2]
        fixation_XY = np.array(fixation_XY)
        line_Y = self.find_lines_y(self.aoi)
        line_Y = np.array(line_Y)
        word_XY = self.find_word_centers(self.aoi)
        word_XY = np.array(word_XY)

        self.suggested_corrections = copy.deepcopy(self.fixations)

        # run warp as an algorithm
        if self.algorithm != "warp":
            self.suggested_corrections[:, 0:2] = self.algorithm_function(fixation_XY, line_Y)
        else:
            self.suggested_corrections[:, 0:2] = self.algorithm_function(fixation_XY, word_XY)

        self.status_text = self.algorithm + " Algorithm Selected"
        self.statusBar.showMessage(self.status_text)
        self.relevant_buttons("algorithm_selected")

    def run_algorithm(self, algorithm_name, algorithm_function, mode):

        self.algorithm = algorithm_name
        self.algorithm_function = algorithm_function
        self.run_correction()

        # write metadata
        self.metadata += ("selected, algorithm " + str(self.algorithm) + "," + str(time.time()) + "\n")

        if mode == 'semi':
            # show suggestion
            self.checkbox_show_suggestion.setCheckable(True)
            self.checkbox_show_suggestion.setEnabled(True)
            self.checkbox_show_suggestion.setChecked(True)
            # update progress bar to end
            self.progress_bar.setValue(self.progress_bar.minimum())
        else:
            # correct all
            self.correct_all_fixations()
            # hide suggestion
            self.checkbox_show_suggestion.setEnabled(False)
            self.checkbox_show_suggestion.setChecked(False)
            self.checkbox_show_suggestion.setCheckable(False)
            # update progress bar to end
            self.progress_bar.setValue(self.progress_bar.maximum())

    def manual_correction(self):

        self.algorithm_function = None
        self.algorithm = "manual"

        # write metadata
        self.metadata += ("selected, " + str(self.algorithm) + "," + str(time.time()) + "\n")

        self.suggested_corrections = copy.deepcopy(self.fixations)
        self.checkbox_show_suggestion.setEnabled(False)

        # show suggestion
        self.checkbox_show_suggestion.setChecked(False)

    def get_selected_fixation(self, event):
        """
        get the selected fixation that the user picks, with the selection 
        inside a specific diameter range (epsilon), selected_fixation is an 
        index, not the actual scatter point
        """
        if self.scatter is not None:
            self.xy = np.asarray(self.scatter.get_offsets())

            xyt = self.canvas.ax.transData.transform(self.xy)
            xt, yt = xyt[:, 0], xyt[:, 1]

            d = np.sqrt((xt - event.x) ** 2 + (yt - event.y) ** 2)
            self.selected_fixation = d.argmin()

            if d[self.selected_fixation] >= self.epsilon:
                self.selected_fixation = None

            return self.selected_fixation

    def move_left_selected_fixation(self):
        if self.selected_fixation != None:
            self.fixations[self.selected_fixation][0] -= 2

        self.draw_canvas(self.fixations)

    def move_right_selected_fixation(self):
        if self.selected_fixation != None:
            self.fixations[self.selected_fixation][0] += 2

        self.draw_canvas(self.fixations)

    def move_down_selected_fixation(self):
        if self.selected_fixation != None:
            self.fixations[self.selected_fixation][1] += 2

        self.draw_canvas(self.fixations)

    def move_up_selected_fixation(self):
        if self.selected_fixation != None:
            self.fixations[self.selected_fixation][1] -= 2

        self.draw_canvas(self.fixations)

    def button_press_callback(self, event):
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self.selected_fixation = self.get_selected_fixation(event)
        # print(self.selected_fixation)


    def button_release_callback(self, event):
        """when released the fixation, update the corrected fixations"""

        if self.selected_fixation is not None:
            # write metadata
            self.metadata += (
                "manual_moving, fixation "
                + str(self.selected_fixation)
                + " moved from x:"
                + str(self.fixations[self.selected_fixation][0])
                + " y:"
                + str(self.fixations[self.selected_fixation][1])
                + " to x:"
                + str(self.xy[self.selected_fixation][0])
                + " y:"
                + str(self.xy[self.selected_fixation][1])
                + ","
                + str(time.time())
                + "\n"
            )

            # move fixation
            self.fixations[self.selected_fixation][0] = self.xy[self.selected_fixation][0]
            self.fixations[self.selected_fixation][1] = self.xy[self.selected_fixation][1]

            # update correction based on algorithm

            if self.algorithm != "manual" and self.algorithm is not None:
                self.run_correction()
                # # run correction
                # fixation_XY = np.array([self.fixations[self.selected_fixation]])
                # fixation_XY = fixation_XY[:, 0:2]
                # line_Y = self.find_lines_y(self.aoi)
                # line_Y = np.array(line_Y)

                # word_XY = self.find_word_centers(self.aoi)
                # word_XY = np.array(word_XY)

                # if self.algorithm == "attach":
                #     updated_correction = da.attach(copy.deepcopy(fixation_XY), line_Y)[
                #         0
                #     ]
                # elif self.algorithm == "chain":
                #     updated_correction = da.chain(copy.deepcopy(fixation_XY), line_Y)[0]
                # # elif self.algorithm == 'cluster':
                # #     updated_correction = da.cluster(copy.deepcopy(fixation_XY), line_Y)[0]
                # elif self.algorithm == "merge":
                #     self.suupdated_correction = da.merge(
                #         copy.deepcopy(fixation_XY), line_Y
                #     )[0]
                # elif self.algorithm == "regress":
                #     updated_correction = da.regress(copy.deepcopy(fixation_XY), line_Y)[
                #         0
                #     ]
                # elif self.algorithm == "segment":
                #     updated_correction = da.segment(copy.deepcopy(fixation_XY), line_Y)[
                #         0
                #     ]
                # # elif self.algorithm == 'split':
                # #     updated_correction = da.split(copy.deepcopy(fixation_XY), line_Y)[0]
                # elif self.algorithm == "stretch":
                #     updated_correction = da.stretch(copy.deepcopy(fixation_XY), line_Y)[
                #         0
                #     ]
                # elif self.algorithm == "warp":
                #     updated_correction = da.warp(copy.deepcopy(fixation_XY), word_XY)[0]

                # self.suggested_corrections[self.selected_fixation, :2] = updated_correction
                # self.update_suggestion()

            if self.checkbox_show_saccades.isChecked():
                self.clear_saccades()
                self.show_saccades(Qt.Checked)
            else:
                self.show_saccades(Qt.Unchecked)
        
        if event.button != 1:
            return
        # self.selected_fixation = None

        self.draw_canvas(self.fixations)
        # self.canvas.update()

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

    def keyPressEvent(self, e):
        # j: move to the left is 74
        if e.key() == 74:
            self.move_left_selected_fixation()

        # l: move to the right is 76
        if e.key() == 76:
            self.move_right_selected_fixation()

        # k: move down is 75
        if e.key() == 75:
            self.move_down_selected_fixation()

        # i: move up is 73
        if e.key() == 73:
            self.move_up_selected_fixation()

        # print(e.key())
        # a: next is 65
        if e.key() == 65 and self.button_next_fixation.isEnabled():
            self.metadata += "key,next," + str(time.time()) + "\n"
            self.next_fixation()

        # z: back is 90
        if e.key() == 90 and self.button_previous_fixation.isEnabled():
            self.metadata += "key,previous," + str(time.time()) + "\n"
            self.previous_fixation()

        # alt: accept and next 16777251
        if e.key() == 16777251 and self.algorithm_function != None:
            self.metadata += "key,accept suggestion," + str(time.time()) + "\n"
            self.confirm_suggestion()

        # backspace
        if e.key() == 16777219:
            self.metadata += "key,remove fixation," + str(time.time()) + "\n"
            if self.fixations is not None and self.selected_fixation is not None:
                if self.selected_fixation < len(self.fixations):
                    self.fixations = np.delete(
                        self.fixations, self.selected_fixation, 0
                    )  # delete the row of selected fixation
                    if self.current_fixation == 0:
                        self.current_fixation = len(self.fixations)
                        self.current_fixation -= 1
                        temp = self.current_fixation
                    else:
                        self.current_fixation -= 1
                        temp = self.current_fixation

                    self.progress_bar.setMaximum(len(self.fixations) - 1)
                    self.progress_bar_updated(temp, draw=False)

                    if self.suggested_corrections is not None:
                        self.suggested_corrections = np.delete(
                            self.suggested_corrections, self.selected_fixation, 0
                        )  # delete the row of selected fixation

                    self.selected_fixation = None

                    if self.algorithm != "manual":
                        if self.current_fixation == len(self.fixations):
                            # off by one error
                            self.current_fixation -= 1
                        # self.update_suggestion()

                    self.draw_canvas(self.fixations)
                    self.progress_bar_updated(self.current_fixation, draw=False)

    

    def open_trial_folder(self):
        """open trial folder, display it to trial list window with list of JSON trials"""
        qfd = QFileDialog()
        self.folder_path = qfd.getExistingDirectory(self, "Select Folder")

        # --- make sure a folder was actually chosen, otherwise just cancel ---
        if self.folder_path != "":
            # clear the data since a new folder was open, no trial is chosen at this point
            self.trial_list.clear()
            self.clear_fixations()
            self.clear_saccades()

            # when open a new folder, block off all the relevant buttons that shouldn't be accesible until a trial is clicked
            self.relevant_buttons("opened_folder")
            self.status_text = "Trial Folder Opened: " + self.folder_path
            self.statusBar.showMessage(self.status_text)

            files = listdir(self.folder_path)

            image_file = ""
            image_name = ""

            if len(files) > 0:
                self.file_list = []
                for file in files:
                    if file.endswith(".json"):
                        self.file_list.append(self.folder_path + "/" + file)

                    elif (
                        file.endswith(".png")
                        or file.endswith(".jpeg")
                        or file.endswith(".jpg")
                    ):
                        if image_file == "":  # only get the first image found
                            image_file = self.folder_path + "/" + file
                            image_name = file

                            self.file = image_file
                            self.file_path = self.file
                            self.file_name = image_name
                if len(self.file_list) > 0:
                    # add the files to the trial list window
                    list_index = 0
                    self.trials = {}
                    for file in self.file_list:
                        file_to_add = QListWidgetItem(file)
                        file_text = str(self.file_list[list_index])
                        file_to_add_name = file_text.split("/")[
                            -1
                        ]  # last part of file text
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

            if image_file == "":  # image file wasn't found
                qmb = QMessageBox()
                qmb.setWindowTitle("Trial Folder Error")
                qmb.setText("No Compatible Image")
                qmb.exec_()
            else:
                self.canvas.clear()
                image = mpimg.imread(image_file)
                self.canvas.ax.imshow(image)
                self.canvas.ax.set_title(str(image_name.split(".")[0]))
                self.canvas.draw()

                self.find_aoi()

                self.relevant_buttons("opened_stimulus")



    def trial_double_clicked(self, item):
        """
        when a trial from the trial list is double clicked, find the fixations of the trial
        parameters:
        item - the value passed through when clicking a trial object in the list
        """
        
        # reset times saved if a DIFFERENT trial was selected
        self.trial_name = item.text()
        self.trial_path = self.trials[item.text()]

        self.find_fixations(self.trial_path)
        self.suggested_corrections = None
        self.current_fixation = (
            len(self.original_fixations) - 1
        )  # double clicking trial should show all and make the current fixation the last one

        # set the progress bar to the amount of fixations found
        self.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.timer_start = time.time()
        self.metadata = "started,," + str(time.time()) + "\n"

        if self.current_fixation is not None:
            if self.current_fixation == -1:
                self.label_progress.setText(f"0/{len(self.original_fixations)}")
            else:
                self.label_progress.setText(
                    f"{self.current_fixation}/{len(self.original_fixations)}"
                )

        self.fixations = copy.deepcopy(
            self.original_fixations
        )  # corrected fixations will be the current fixations on the screen and in the data
        self.checkbox_show_fixations.setChecked(True)
        self.checkbox_show_saccades.setChecked(True)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)

        self.status_text = self.trial_name + " Opened (Default: Manual Mode)"
        self.statusBar.showMessage(self.status_text)


    def find_aoi(self):
        """find the areas of interest (aoi) for the selected stimulus"""
        if self.file_path != "":
            self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
                self.file_name,
                self.file_path.replace(self.file_name, ""),
                margin_height=self.aoi_height,
                margin_width=self.aoi_width,
            )


    def draw_aoi(self):
        """draw the found aois to the canvas"""
        color = self.aoi_color if self.background_color == "black" else "black"
        self.patches = []

        for row in self.aoi.iterrows():

            xcord = row[1]["x"]
            ycord = row[1]["y"]
            height = row[1]["height"]
            width = row[1]["width"]

            self.patches.append(
                self.canvas.ax.add_patch(
                    Rectangle(
                        (xcord, ycord),
                        width - 1,
                        height - 1,
                        linewidth=0.8,
                        edgecolor=color,
                        facecolor="none",
                        alpha=0.65,
                    )
                )
            )

        self.canvas.draw()


    def clear_aoi(self):
        """clear the aois from the canvas"""
        if self.patches is not None:
            for patch in self.patches:
                patch.remove()
            self.canvas.draw()


    def show_aoi(self, state):
        """when the show aoi button is pressed, show or hide aois based on checkbox"""
        if self.checkbox_show_aoi.isCheckable():
            if state == Qt.Checked:
                self.draw_aoi()
            elif state == Qt.Unchecked:
                self.clear_aoi()

    
    def find_fixations(self, trial_path):
        """find all the fixations of the trial that was double clicked
        parameters:
        trial_path - the trial file path of the trial clicked on"""
        self.original_fixations = []
        with open(trial_path, "r") as trial:
            try:
                self.trial_data = json.load(trial)
                for x in self.trial_data:
                    self.original_fixations.append(
                        [
                            self.trial_data[x][0],
                            self.trial_data[x][1],
                            self.trial_data[x][2],
                        ]
                    )
                self.original_fixations = np.array(self.original_fixations)
                self.relevant_buttons("trial_clicked")
            except json.decoder.JSONDecodeError:
                qmb = QMessageBox()
                qmb.setWindowTitle("Trial File Error")
                qmb.setText("Trial Error: JSON File Empty")
                qmb.exec_()


    def find_lines_y(self, aoi):
        results = []
        for index, row in aoi.iterrows():
            y, height = row["y"], row["height"]

            if y + height / 2 not in results:
                results.append(y + height / 2)

        return results

    def find_word_centers(self, aois):
        """returns a list of word centers"""
        results = []

        for index, row in aois.iterrows():
            x, y, height, width = row["x"], row["y"], row["height"], row["width"]

            center = [int(x + width // 2), int(y + height // 2)]

            if center not in results:
                results.append(center)

        return results

    

    def draw_fixations(self, fixations=0):
        """draw the fixations to the canvas
        parameters:
        fixations - 0 is default since the corrected fixations are the main thing to be shown,
        1 the original fixations is manually chosen (not currently needed as this isn't in option in algorithms)"""

        if fixations == 0:  # default fixations to use
            fixations = self.fixations
        elif fixations == 1:
            fixations = self.original_fixations

        x = fixations[0 : self.current_fixation + 1, 0]
        y = fixations[0 : self.current_fixation + 1, 1]
        duration = fixations[0 : self.current_fixation + 1, 2]
        self.scatter = self.canvas.ax.scatter(
            x,
            y,
            s=30 * (duration / 50) ** 1.8,
            alpha=self.fixation_opacity,
            c=self.fixation_color,
        )

        self.canvas.draw()

    

    def show_fixations(self, state):
        """if the user clicks the show fixations checkbox, show or hide the fixations
        parameters:
        state - the checkbox being checked or unchecked"""
        if self.folder_path != "":
            if self.checkbox_show_fixations.isCheckable():
                if state == Qt.Checked:
                    self.draw_fixations()
                elif state == Qt.Unchecked:
                    self.clear_fixations()

    

    def show_saccades(self, state):
        """if the user clicks saccades, show or hide them"""
        if self.folder_path != "":
            if self.checkbox_show_saccades.isCheckable():
                if state == Qt.Checked:
                    self.draw_saccades()
                elif state == Qt.Unchecked:
                    self.clear_saccades()

    

    def draw_saccades(self):
        """draw the scatter plot to the canvas"""
        fixations = self.fixations
        x = fixations[0 : self.current_fixation + 1, 0]
        y = fixations[0 : self.current_fixation + 1, 1]
        duration = fixations[0 : self.current_fixation + 1, 2]
        self.saccades = self.canvas.ax.plot(
            x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1
        )
        self.canvas.draw()

    

    def clear_saccades(self):
        """remove the saccades from the canvas (this does not erase the data, just visuals)"""
        if self.saccades != None:
            self.canvas.ax.lines.clear()  # <-- if this line crashes the tool

            # for line in self.canvas.ax.lines:  #<-- use this instead
            #    line.remove()

            self.saccades = None
            # self.canvas.draw()

    

    def clear_fixations(self):
        """clear the fixations from the canvas"""
        if self.scatter != None:
            # self.scatter.remove()
            self.scatter = None
            # clear scatter data from canvas but not the background image
            self.canvas.ax.collections.clear()  # <-- If this line crashes the tool

            # for collection in self.canvas.ax.collections: #<-- use this instead
            #    collection.remove()

            # self.canvas.draw()

    # draw fixations2 is similar to the normal draw fixations, excpet this one only draws to the current fixation
    def draw_canvas(self, fixations, draw_all=False):
        if draw_all:
            x = fixations[:, 0]
            y = fixations[:, 1]
            duration = fixations[:, 2]
        else:
            x = fixations[0 : self.current_fixation + 1, 0]
            y = fixations[0 : self.current_fixation + 1, 1]
            duration = fixations[0 : self.current_fixation + 1, 2]

        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()

        # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
        # do the same for saccades
        if self.checkbox_show_fixations.isCheckable():
            if self.checkbox_show_fixations.isChecked():
                list_colors = [self.fixation_color] * (len(x) - 1)
                colors = np.array(list_colors + [self.current_fixation_color])
                self.scatter = self.canvas.ax.scatter(
                    x,
                    y,
                    s=30 * (duration / 50) ** 1.8,
                    alpha=self.fixation_opacity,
                    c=colors,
                )
                # self.scatter = self.canvas.ax.scatter(x[-1], y[-1], s=30 * (duration[-1]/50)**1.8, alpha = self.fixation_opacity, c = "yellow")

        if self.checkbox_show_saccades.isCheckable():
            if self.checkbox_show_saccades.isChecked():
                self.saccades = self.canvas.ax.plot(
                    x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1
                )

        # draw suggested fixation in blue
        if self.checkbox_show_suggestion.isChecked():
            x = self.suggested_corrections[self.current_fixation][0]
            y = self.suggested_corrections[self.current_fixation][1]
            duration = self.fixations[self.current_fixation][2]

            self.suggested_suggestion = self.canvas.ax.scatter(
                x,
                y,
                s=30 * (duration / 50) ** 1.8,
                alpha=self.fixation_opacity,
                c=self.suggested_fixation_color,
            )

        # draw whatever was updated
        self.canvas.draw()

    # def get_algorithm_picked(self, algorithm):
    #     """
    #     when the user selects an algorithm from the drop down menu,
    #     make it the current algorithm to use for automated and semi automated use
    #     parameters:
    #     algorithm - the selected correction algorithm
    #     """

    #     self.algorithm = algorithm.lower()

    #     # write metadata
    #     self.metadata += (
    #         "selected,algorithm " + str(algorithm) + "," + str(time.time()) + "\n"
    #     )

    #     # run correction
    #     fixation_XY = copy.deepcopy(self.fixations)
    #     fixation_XY = fixation_XY[:, 0:2]
    #     fixation_XY = np.array(fixation_XY)
    #     line_Y = self.find_lines_y(self.aoi)
    #     line_Y = np.array(line_Y)

    #     word_XY = self.find_word_centers(self.aoi)
    #     word_XY = np.array(word_XY)

    #     self.suggested_corrections = copy.deepcopy(self.fixations)
    #     # print(self.corrected_fixations)

    #     if len(self.fixations) > 0:
    #         if self.algorithm == "attach":
    #             self.suggested_corrections[:, 0:2] = da.attach(
    #                 copy.deepcopy(fixation_XY), line_Y
    #             )
    #             self.status_text = self.algorithm + " Algorithm Selected"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("algorithm_selected")
    #             # self.update_suggestion()  # update the current suggestion as well
    #         elif self.algorithm == "chain":
    #             self.suggested_corrections[:, 0:2] = da.chain(
    #                 copy.deepcopy(fixation_XY), line_Y
    #             )
    #             self.status_text = self.algorithm + " Algorithm Selected"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("algorithm_selected")
    #             # self.update_suggestion()
    #         # elif self.algorithm == 'cluster':
    #         #     self.suggested_corrections[:, 0:2] = da.cluster(copy.deepcopy(fixation_XY), line_Y)
    #         #     self.relevant_buttons("algorithm_selected")
    #         # self.update_suggestion()
    #         elif self.algorithm == "merge":
    #             self.suggested_corrections[:, 0:2] = da.merge(
    #                 copy.deepcopy(fixation_XY), line_Y
    #             )
    #             self.status_text = self.algorithm + " Algorithm Selected"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("algorithm_selected")
    #             # self.update_suggestion()
    #         elif self.algorithm == "regress":
    #             self.suggested_corrections[:, 0:2] = da.regress(
    #                 copy.deepcopy(fixation_XY), line_Y
    #             )
    #             self.status_text = self.algorithm + " Algorithm Selected"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("algorithm_selected")
    #             # self.update_suggestion()
    #         elif self.algorithm == "segment":
    #             self.suggested_corrections[:, 0:2] = da.segment(
    #                 copy.deepcopy(fixation_XY), line_Y
    #             )
    #             self.status_text = self.algorithm + " Algorithm Selected"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("algorithm_selected")
    #             # self.update_suggestion()
    #         # elif self.algorithm == 'split':
    #         #     self.suggested_corrections[:, 0:2] = da.split(copy.deepcopy(fixation_XY), line_Y)
    #         #     self.relevant_buttons("algorithm_selected")
    #         # self.update_suggestion()
    #         elif self.algorithm == "stretch":
    #             self.suggested_corrections[:, 0:2] = da.stretch(
    #                 copy.deepcopy(fixation_XY), line_Y
    #             )
    #             self.status_text = self.algorithm + " Algorithm Selected"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("algorithm_selected")
    #             # self.update_suggestion()
    #         elif self.algorithm == "warp":
    #             self.suggested_corrections[:, 0:2] = da.warp(fixation_XY, word_XY)
    #             self.status_text = self.algorithm + " Algorithm Selected"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("algorithm_selected")
    #             # self.update_suggestion()
    #         else:
    #             self.status_text = "No Selected Algorithm"
    #             self.statusBar.showMessage(self.status_text)
    #             self.relevant_buttons("no_selected_algorithm")
    #             self.algorithm = None
    #             # self.update_suggestion()
    #         self.checkbox_show_suggestion.setChecked(True)

    #         # reset progress bar when algorithm is selected, saving the user one manual step
    #         self.progress_bar.setValue(self.progress_bar.minimum())

    

    def correct_all_fixations(self):
        """if the user presses the correct all fixations button,
        make the corrected fixations the suggested ones from the correction algorithm"""
        if self.suggested_corrections is not None:
            self.fixations = copy.deepcopy(self.suggested_corrections)
            self.draw_canvas(self.fixations)

        self.metadata += (
            "correct_all, all fixations corrected automatically"
            + ","
            + str(time.time())
            + "\n"
        )
        self.status_text = "Correct All Fixations!"
        self.statusBar.showMessage(self.status_text)

    def previous_fixation(self):
        # if self.suggested_corrections is not None:
        if self.current_fixation != 0:
            self.current_fixation -= 1

        self.draw_canvas(self.fixations)
        self.progress_bar_updated(self.current_fixation, draw=False)

        # if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
        #    self.update_suggestion()


    def next_fixation(self):
        """when the next fixation button is clicked, call this function and find the suggested correction for this fixation"""
        # if self.suggested_corrections is not None:
        if self.current_fixation != len(self.fixations) - 1:
            self.current_fixation += 1

        self.draw_canvas(self.fixations)
        self.progress_bar_updated(self.current_fixation, draw=False)

        # if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
        #    self.update_suggestion()

    # def show_suggestion(self,state):
    #     if self.checkbox_show_suggestion.isCheckable():
    #         self.update_suggestion()

    # def update_suggestion(self):

    #     if self.current_fixation != -1:
    #         pass
    # remove and replace the last suggestion for the current suggestion
    # if self.single_suggestion != None:
    #     #self.single_suggestion.remove()
    #     self.single_suggestion = None
    #     self.canvas.draw()

    # if checkbox is checked draw the suggestion, else remove it
    # if self.checkbox_show_suggestion.isChecked():
    #     x = self.suggested_corrections[self.current_fixation][0]
    #     y = self.suggested_corrections[self.current_fixation][1]
    #     duration = self.corrected_fixations[self.current_fixation][2]

    #     self.single_suggestion = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = 'blue')
    #     self.canvas.draw()

    # elif self.single_suggestion != None:
    #         #self.single_suggestion.remove()
    #         self.single_suggestion = None
    #         self.canvas.draw()

    def back_to_beginning(self):
        self.current_fixation = 1
        self.update_suggestion()



    def confirm_suggestion(self):
        """ when the confirm button is clicked, the suggested correction replaces the current fixation"""
        self.metadata += (
            "auto_moving, fixation "
            + str(self.current_fixation)
            + " moved from x:"
            + str(self.fixations[self.current_fixation][0])
            + " y:"
            + str(self.fixations[self.current_fixation][1])
            + " to x:"
            + str(self.suggested_corrections[self.current_fixation][0])
            + " y:"
            + str(self.suggested_corrections[self.current_fixation][1])
            + ","
            + str(time.time())
            + "\n"
        )

        x = self.suggested_corrections[self.current_fixation][0]
        y = self.suggested_corrections[self.current_fixation][1]
        self.fixations[self.current_fixation][0] = x
        self.fixations[self.current_fixation][1] = y

        self.next_fixation()


    def undo_suggestion(self):
        self.metadata += (
            "auto_undo, fixation "
            + str(self.current_fixation - 1)
            + " moved from x:"
            + str(self.fixations[self.current_fixation - 1][0])
            + " y:"
            + str(self.fixations[self.current_fixation - 1][1])
            + " to x:"
            + str(self.original_fixations[self.current_fixation - 1][0])
            + " y:"
            + str(self.original_fixations[self.current_fixation - 1][1])
            + ","
            + str(time.time())
            + "\n"
        )

        x = self.original_fixations[self.current_fixation - 1][0]
        y = self.original_fixations[self.current_fixation - 1][1]
        self.fixations[self.current_fixation - 1][0] = x
        self.fixations[self.current_fixation - 1][1] = y

        self.previous_fixation()


    def save_metadata_file(self, new_correction_file_path):
    
        metadata_file_name = new_correction_file_path.replace('.json', '') + '_metadata.csv'
        metadata_file_path = Path(f"{metadata_file_name}")

        headers = "event,event details,timestamp\n"

        with open(metadata_file_path, "w", newline="") as meta_file:
                meta_file.write(headers)
                meta_file.write(self.metadata)
                self.metadata = ""


    def save_corrections(self):
        """ save correction to a json file and metadata to csv file """

        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.json', '') + '_CORRECTED_json'
        new_correction_file_name, _ = qfd.getSaveFileName(self, "Save correction", default_file_name)

        if '.json' not in new_correction_file_name:
            new_correction_file_name += '.json'

        if len(self.fixations) > 0:
            list = self.fixations.tolist()

            corrected_fixations = {}
            for i in range(len(self.fixations)):
                corrected_fixations[i + 1] = list[i]

            with open(f"{new_correction_file_name}", "w") as f:
                json.dump(corrected_fixations, f)
                
            self.duration = (time.time() - self.timer_start)
            today = date.today()

            self.metadata += (
                "Saved,Date "
                + str(today)
                + " Trial Name"
                + str(self.trial_name)
                + " File Path "
                + str(self.file_path)
                + " Duration "
                + str(self.duration)
                + ","
                + str(time.time())
                + "\n"
            )

            self.save_metadata_file(new_correction_file_name)

            self.status_text = "Corrections Saved to" + " " + new_correction_file_name
            self.statusBar.showMessage(self.status_text)

        else:
            qmb = QMessageBox()
            qmb.setWindowTitle("Save Error")
            qmb.setText("No Corrections Made")
            qmb.exec_()

    def progress_bar_updated(self, value, draw=True):
        # update the current suggested correction to the last fixation of the list
        self.current_fixation = value

        # update current suggestion to the progress bar
        if self.current_fixation is not None:
            self.label_progress.setText(
                f"{self.current_fixation}/{len(self.fixations)}"
            )
            self.progress_bar.setValue(self.current_fixation)

        if draw:
            self.draw_canvas(self.fixations)

        # if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
        #    self.update_suggestion()


    # def lesser_value_changed(self, value):
    #     """Activates when the lesser value filter changes"""
    #     self.lesser_value = value

    # def lesser_value_confirmed(self):
    #     # set lesser_value to value of the greater value filter
    #     self.lesser_value = self.input_lesser.text()

    #     # writing a log in metadata
    #     self.metadata += (
    #         "filter,removed fixations less than "
    #         + self.lesser_value
    #         + ","
    #         + str(time.time())
    #         + "\n"
    #     )

    #     self.fixations = self.fixations[self.fixations[:, 2] > int(self.lesser_value)]
    #     self.current_fixation = 0
    #     if self.algorithm != "manual" and self.suggested_corrections is not None:
    #         if self.current_fixation == len(self.fixations):
    #             # off by one error, since deleting fixation moves current onto the next fixation
    #             self.current_fixation -= 1
    #         self.suggested_corrections = self.suggested_corrections[
    #             self.suggested_corrections[:, 2] > int(self.lesser_value)
    #         ]

    #     temp = self.current_fixation
    #     self.progress_bar.setMaximum(len(self.fixations) - 1)
    #     self.progress_bar_updated(temp)

    #     self.draw_canvas(self.fixations, draw_all=True)
    #     self.progress_bar_updated(self.current_fixation, draw=False)


    # def greater_value_changed(self, value):
    #     """Activates when the greater value filter changes"""
    #     self.greater_value = value

    # def greater_value_confirmed(self):
    #     # set greater_value to value of the greater value filter
    #     self.greater_value = self.input_greater.text()

    #     # writing a log in metadata
    #     self.metadata += (
    #         "filter,removed fixations greater than "
    #         + self.greater_value
    #         + ","
    #         + str(time.time())
    #         + "\n"
    #     )

    #     self.fixations = self.fixations[self.fixations[:, 2] < int(self.greater_value)]
    #     self.current_fixation = 0
    #     if self.algorithm != "manual" and self.suggested_corrections is not None:
    #         if self.current_fixation == len(self.fixations):
    #             # off by one error, since deleting fixation moves current onto the next fixation
    #             self.current_fixation -= 1

    #         self.suggested_corrections = self.suggested_corrections[
    #             self.suggested_corrections[:, 2] < int(self.greater_value)
    #         ]

    #     temp = self.current_fixation
    #     self.progress_bar.setMaximum(len(self.fixations) - 1)
    #     self.progress_bar_updated(temp)

    #     self.draw_canvas(self.fixations, draw_all=True)
    #     self.progress_bar_updated(self.current_fixation, draw=False)

    def aoi_height_changed(self, value):
        self.aoi_height = value
        self.find_aoi()
        self.clear_aoi()
        self.draw_aoi()

    def aoi_width_changed(self, value):
        self.aoi_width = value
        self.find_aoi()
        self.clear_aoi()
        self.draw_aoi()

    def select_fixation_color(self):
        color = QColorDialog.getColor(initial=Qt.red)
        if color.isValid():
            self.fixation_color = str(color.name())
        else:
            self.fixation_color = "red"

        self.draw_canvas(self.fixations)

    def select_current_fixation_color(self):
        color = QColorDialog.getColor(initial=Qt.red)
        if color.isValid():
            self.current_fixation_color = str(color.name())
        else:
            self.current_fixation_color = "yellow"

        self.draw_canvas(self.fixations)

    def select_suggested_fixation_color(self):
        color = QColorDialog.getColor(initial=Qt.red)
        if color.isValid():
            self.suggested_fixation_color = str(color.name())
        else:
            self.suggested_fixation_color = "blue"

        self.draw_canvas(self.fixations)

    def select_saccade_color(self):
        color = QColorDialog.getColor(initial=Qt.blue)
        if color.isValid():
            self.saccade_color = str(color.name())
        else:
            self.saccade_color = "blue"

        self.draw_canvas(self.fixations)

    def colorblind_assist(self):
        if self.colorblind_assist_status == False:
            self.fixation_color = "#FF9E0A"
            # self.current_fixation_color = "yellow"
            self.saccade_color = "#3D00CC"
            self.aoi_color = "#28AAFF"
            self.colorblind_assist_status = True
            self.draw_canvas(self.fixations)
        else:
            self.fixation_color = "red"
            self.saccade_color = "blue"
            self.aoi_color = "yellow"
            self.colorblind_assist_status = False
            self.draw_canvas(self.fixations)

    def saccade_opacity_changed(self, value):
        self.saccade_opacity = float(value / 10)
        self.draw_canvas(self.fixations)

    def fixation_opacity_changed(self, value):
        self.fixation_opacity = float(value / 10)
        self.draw_canvas(self.fixations)

    

    def init_UI(self):
        """initalize the tool window"""
        # wrapper layout
        self.wrapper_layout = QHBoxLayout()

        # --- left side
        self.left_side = QVBoxLayout()

        # self.button_open_folder = QPushButton("Open Folder", self)
        # self.button_open_folder.setEnabled(True)
        # self.button_open_folder.clicked.connect(self.open_trial_folder)

        # self.button_save_corrections = QPushButton("Save Corrections", self)
        # self.button_save_corrections.setEnabled(False)
        # self.button_save_corrections.clicked.connect(self.save_corrections)

        self.trial_list = QListWidget()
        self.trial_list.itemDoubleClicked.connect(self.trial_double_clicked)

        # section for fixation size filters
        # self.greater_inputs = QHBoxLayout()
        # self.input_greater = QLineEdit()
        # self.input_greater.textChanged.connect(self.greater_value_changed)
        # self.input_greater.setEnabled(False)
        # self.input_greater.setText("1000")
        # self.button_greater = QPushButton("Remove Fixations >")
        # self.button_greater.setEnabled(False)
        # self.button_greater.clicked.connect(self.greater_value_confirmed)
        # self.greater_inputs.addWidget(self.input_greater)
        # self.greater_inputs.addWidget(self.button_greater)

        # self.lesser_inputs = QHBoxLayout()
        # self.input_lesser = QLineEdit()
        # self.input_lesser.textChanged.connect(self.lesser_value_changed)
        # self.input_lesser.setEnabled(False)
        # self.input_lesser.setText("50")
        # self.button_lesser = QPushButton("Remove Fixations <")
        # self.button_lesser.setEnabled(False)
        # self.button_lesser.clicked.connect(self.lesser_value_confirmed)
        # self.lesser_inputs.addWidget(self.input_lesser)
        # self.lesser_inputs.addWidget(self.button_lesser)

        widget_list = [self.trial_list]

        for w in widget_list:
            self.left_side.addWidget(w)

        # self.left_side.addLayout(self.greater_inputs)
        # self.left_side.addLayout(self.lesser_inputs)
        # ---

        # --- canvas
        self.right_side = QVBoxLayout()

        self.canvas = QtCanvas(self, width=12, height=8, dpi=200)
        self.right_side.addWidget(self.canvas)

        self.progress_tools = QHBoxLayout()

        # initialize status bar
        self.status_text = "Beginning..."
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(self.status_text)

        # this is needed to remove the coodinates next to the navigation panel when hovering over canvas
        class Toolbar(NavigationToolBar):
            def __init__(self, canvas, parent):
                super().__init__(canvas, parent)

                # Remove unwanted default actions
                self.removeUnwantedActions()

            def removeUnwantedActions(self):
                # List of action names/icons to be kept
                wanted_actions = ["Home", "Pan", "Zoom", "Save"]  # Adjust as needed

                # Iterate through existing actions and remove unwanted ones
                for action in self.actions():
                    if action.text() not in wanted_actions:
                        self.removeAction(action)

            def set_message(self, s):
                pass

        self.toolbar = Toolbar(self.canvas, self)
        self.toolbar.setStyleSheet("QToolBar { border: 0px }")
        self.toolbar.setEnabled(False)
        self.progress_tools.addWidget(self.toolbar)

        self.button_previous_fixation = QPushButton("Previous Fixation", self)
        self.button_previous_fixation.setEnabled(False)
        self.button_previous_fixation.clicked.connect(self.previous_fixation)
        self.progress_tools.addWidget(self.button_previous_fixation)

        self.button_next_fixation = QPushButton("Next Fixation", self)
        self.button_next_fixation.setEnabled(False)
        self.button_next_fixation.clicked.connect(self.next_fixation)
        self.progress_tools.addWidget(self.button_next_fixation)

        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setEnabled(False)
        self.progress_bar.valueChanged.connect(self.progress_bar_updated)
        self.progress_tools.addWidget(self.progress_bar)

        self.label_progress = QLabel("0/0")
        self.progress_tools.addWidget(self.label_progress)

        self.right_side.addLayout(self.progress_tools)

        self.below_canvas = QHBoxLayout()

        # --- section for semi automated tools
        # self.semi_automation = QVBoxLayout()

        # self.label_semi_automation = QLabel("Semi-Automation")
        # self.label_semi_automation.setAlignment(Qt.AlignCenter)
        # self.semi_automation.addWidget(self.label_semi_automation)

        # self.semi_automation_second_row = QHBoxLayout()

        # self.button_next_fixation = QPushButton("Next Fixation", self)
        # #self.button_next_fixation.setEnabled(False)
        # self.button_next_fixation.clicked.connect(self.next_fixation)

        # self.button_previous_fixation = QPushButton("Previous Fixation", self)
        # self.button_previous_fixation.setEnabled(False)
        # self.button_previous_fixation.clicked.connect(self.previous_fixation)

        # self.semi_automation_second_row.addWidget(self.button_previous_fixation)
        # self.semi_automation_second_row.addWidget(self.button_next_fixation)

        # self.semi_automation.addLayout(self.semi_automation_second_row)

        # self.button_confirm_suggestion = QPushButton("Accept Suggestion and Next", self)
        # self.button_confirm_suggestion.setEnabled(False)
        # self.button_confirm_suggestion.clicked.connect(self.confirm_suggestion)
        # self.semi_automation.addWidget(self.button_confirm_suggestion)

        # self.button_undo_suggestion = QPushButton("Undo Correction", self)
        # self.button_undo_suggestion.setEnabled(False)
        # self.button_undo_suggestion.clicked.connect(self.undo_suggestion)
        # self.semi_automation.addWidget(self.button_undo_suggestion)

        # self.button1 = QPushButton()
        # self.semi_automation.addWidget(self.button1)
        # retain = self.button1.sizePolicy()
        # retain.setRetainSizeWhenHidden(True)
        # self.button1.setSizePolicy(retain)
        # self.button1.hide()

        # self.frame = QFrame()
        # self.frame.setStyleSheet(
        #     " QFrame {border: 2px solid black; margin: 0px; padding: 0px;}"
        # )
        # self.label_semi_automation.setStyleSheet("QLabel { border: 0px }")
        # self.frame.setLayout(self.semi_automation)
        # self.below_canvas.addWidget(self.frame)
        # ---

        # --- section for automated tools
        # self.automation = QVBoxLayout()

        # self.label_automation = QLabel("Automation")
        # self.label_automation.setAlignment(Qt.AlignCenter)
        # self.automation.addWidget(self.label_automation)

        # self.button_correct_all_fixations = QPushButton("Correct All Fixations", self)
        # self.button_correct_all_fixations.setEnabled(False)
        # self.button_correct_all_fixations.clicked.connect(self.correct_all_fixations)

        # self.dropdown_select_algorithm = QComboBox()
        # self.dropdown_select_algorithm.setEditable(True)
        # self.dropdown_select_algorithm.addItem("Manual Correction")
        # self.dropdown_select_algorithm.addItem("Attach")
        # self.dropdown_select_algorithm.addItem("Chain")
        # # self.dropdown_select_algorithm.addItem('Cluster')
        # self.dropdown_select_algorithm.addItem("Merge")
        # self.dropdown_select_algorithm.addItem("Regress")
        # self.dropdown_select_algorithm.addItem("Segment")
        # # self.dropdown_select_algorithm.addItem('Split')
        # self.dropdown_select_algorithm.addItem("Stretch")
        # # self.dropdown_select_algorithm.addItem('Compare')
        # self.dropdown_select_algorithm.addItem("Warp")
        # # self.dropdown_select_algorithm.addItem('Time Warp')
        # # self.dropdown_select_algorithm.addItem('Slice')
        # self.dropdown_select_algorithm.lineEdit().setAlignment(Qt.AlignCenter)
        # self.dropdown_select_algorithm.lineEdit().setReadOnly(True)
        # self.dropdown_select_algorithm.setEnabled(False)
        # self.dropdown_select_algorithm.currentTextChanged.connect(
        #     self.get_algorithm_picked
        # )

        # self.automation.addWidget(self.dropdown_select_algorithm)
        # self.automation.addWidget(self.button_correct_all_fixations)

        # buttons to fill in space
        # self.button2 = QPushButton()
        # self.automation.addWidget(self.button2)
        # retain = self.button2.sizePolicy()
        # retain.setRetainSizeWhenHidden(True)
        # self.button2.setSizePolicy(retain)
        # self.button2.hide()

        # self.button3 = QPushButton()
        # self.automation.addWidget(self.button3)
        # retain = self.button3.sizePolicy()
        # retain.setRetainSizeWhenHidden(True)
        # self.button3.setSizePolicy(retain)
        # self.button3.hide()

        # self.frame2 = QFrame()
        # self.frame2.setStyleSheet(
        #     " QFrame {border: 2px solid black; margin: 0px; padding: 0px;}"
        # )
        # self.label_automation.setStyleSheet("QLabel { border: 0px }")
        # self.frame2.setLayout(self.automation)
        # self.below_canvas.addWidget(self.frame2)
        # ---

        # --- section for filters
        self.filters = QVBoxLayout()

        self.label_filters = QLabel("Visualization")
        self.label_filters.setAlignment(Qt.AlignCenter)
        self.filters.addWidget(self.label_filters)

        # laers for aoi margin width and height
        self.aoi_layer_width = QHBoxLayout()
        self.aoi_layer_height = QHBoxLayout()
        self.checkbox_show_aoi = QCheckBox("Show AOIs")
        self.checkbox_show_aoi.setEnabled(False)
        self.checkbox_show_aoi_fillSpace = QCheckBox("Show AOIs")
        self.checkbox_show_aoi_fillSpace.setEnabled(False)
        self.checkbox_show_aoi_fillSpace.hide()
        self.checkbox_show_aoi.stateChanged.connect(self.show_aoi)
        self.toggle_aoi_width = QSpinBox()
        self.toggle_aoi_width.setMaximum(50)
        self.toggle_aoi_width.setMinimum(1)
        self.toggle_aoi_width.setValue(7)
        self.toggle_aoi_height = QSpinBox()
        self.toggle_aoi_height.setMaximum(100)
        self.toggle_aoi_height.setMinimum(1)
        self.toggle_aoi_height.setValue(4)
        self.toggle_aoi_width.valueChanged.connect(self.aoi_width_changed)
        self.toggle_aoi_height.valueChanged.connect(self.aoi_height_changed)
        self.aoi_width_text = QLabel("Width")
        self.aoi_height_text = QLabel("Height")
        self.aoi_layer_width.addWidget(self.checkbox_show_aoi)
        self.aoi_layer_width.addWidget(self.toggle_aoi_width)
        self.aoi_layer_width.addWidget(self.aoi_width_text)
        self.aoi_layer_height.addWidget(self.checkbox_show_aoi)
        self.aoi_layer_height.addWidget(self.toggle_aoi_height)
        self.aoi_layer_height.addWidget(self.aoi_height_text)

        self.filters.addLayout(self.aoi_layer_width)
        self.filters.addLayout(self.aoi_layer_height)

        self.toggle_aoi_width.setEnabled(False)
        self.toggle_aoi_height.setEnabled(False)
        # ---

        # layers for fixation and saccade visuals
        self.fixation_layer = QHBoxLayout()
        self.checkbox_show_fixations = QCheckBox("Show Fixations")
        self.checkbox_show_fixations.setEnabled(False)
        self.checkbox_show_fixations.stateChanged.connect(self.show_fixations)
        self.toggle_fixation_opacity = QSpinBox()
        self.toggle_fixation_opacity.setMaximum(10)
        self.toggle_fixation_opacity.setMinimum(1)
        self.toggle_fixation_opacity.valueChanged.connect(self.fixation_opacity_changed)
        self.fixation_opacity_text = QLabel("Fixation Opacity")
        self.fixation_layer.addWidget(self.checkbox_show_fixations)
        self.fixation_layer.addWidget(self.toggle_fixation_opacity)
        self.fixation_layer.addWidget(self.fixation_opacity_text)

        self.filters.addLayout(self.fixation_layer)

        self.saccade_layer = QHBoxLayout()
        self.checkbox_show_saccades = QCheckBox("Show Saccades")
        self.checkbox_show_saccades.setEnabled(False)
        self.checkbox_show_saccades.stateChanged.connect(self.show_saccades)
        self.toggle_saccade_opacity = QSpinBox()
        self.toggle_saccade_opacity.setMaximum(10)
        self.toggle_saccade_opacity.setMinimum(1)
        self.toggle_saccade_opacity.valueChanged.connect(self.saccade_opacity_changed)
        self.saccade_opacity_text = QLabel("Saccade Opacity")
        self.saccade_layer.addWidget(self.checkbox_show_saccades)
        self.saccade_layer.addWidget(self.toggle_saccade_opacity)
        self.saccade_layer.addWidget(self.saccade_opacity_text)

        self.filters.addLayout(self.saccade_layer)

        self.toggle_fixation_opacity.setEnabled(False)
        self.toggle_saccade_opacity.setEnabled(False)
        # ---

        self.checkbox_show_suggestion = QCheckBox("Show Suggested Correction")
        self.checkbox_show_suggestion.setEnabled(False)
        # self.checkbox_show_suggestion.stateChanged.connect(self.show_suggestion)
        self.filters.addWidget(self.checkbox_show_suggestion)
        self.frame3 = QFrame()
        self.frame3.setStyleSheet(
            " QFrame {border: 2px solid black; margin: 0px; padding: 0px;}"
        )
        self.label_filters.setStyleSheet("QLabel { border: 0px }")
        self.frame3.setLayout(self.filters)
        self.below_canvas.addWidget(self.frame3)

        # --
        self.button_fixation_color = QPushButton("Select Fixation Color")
        self.button_fixation_color.clicked.connect(self.select_fixation_color)
        
        self.button_saccade_color = QPushButton("Select Saccade Color")
        self.button_saccade_color.clicked.connect(self.select_saccade_color)

        self.button_current_fixation_color = QPushButton("Current Fixation Color")
        self.button_current_fixation_color.clicked.connect(self.select_current_fixation_color)

        self.button_suggested_fixation_color = QPushButton("Suggestion Color")
        self.button_suggested_fixation_color.clicked.connect(self.select_suggested_fixation_color)

        self.button_coloblind_assist = QPushButton("Colorblind Assist")
        self.button_coloblind_assist.clicked.connect(self.colorblind_assist)

        self.button_fixation_color.setEnabled(False)
        self.button_saccade_color.setEnabled(False)
        self.button_current_fixation_color.setEnabled(False)
        self.button_suggested_fixation_color.setEnabled(False)
        self.button_coloblind_assist.setEnabled(False)

        self.layer_fixation_color = QHBoxLayout()
        self.layer_fixation_color.addWidget(self.button_fixation_color)
        self.layer_fixation_color.addWidget(self.button_saccade_color)
        self.layer_fixation_color.addWidget(self.button_current_fixation_color)

        self.second_layer_fixation_color = QHBoxLayout()

        self.second_layer_fixation_color.addWidget(self.button_suggested_fixation_color)
        self.second_layer_fixation_color.addWidget(self.button_coloblind_assist)

        self.filters.addLayout(self.layer_fixation_color)
        self.filters.addLayout(self.second_layer_fixation_color)

        self.left_side.addLayout(self.below_canvas)
        # --

        #self.right_side.addLayout(self.below_canvas)

        # add both sides to overall wrapper layout
        self.wrapper_layout.addLayout(self.left_side)
        self.wrapper_layout.addLayout(self.right_side)
        self.wrapper_layout.setStretch(0, 1)
        self.wrapper_layout.setStretch(1, 3)

        # initial button states
        # self.button_open_folder.setEnabled(True)
        # self.button_save_corrections.setEnabled(False)
        self.toolbar.setEnabled(False)
        self.checkbox_show_aoi.setChecked(False)
        self.checkbox_show_aoi.setCheckable(False)
        self.checkbox_show_fixations.setChecked(False)
        self.checkbox_show_fixations.setCheckable(False)

        # self.dropdown_select_algorithm.setEditable(False)
        # self.dropdown_select_algorithm.setEnabled(False)
        # self.button_correct_all_fixations.setEnabled(False)

        self.button_next_fixation.setEnabled(False)
        self.checkbox_show_suggestion.setChecked(False)
        self.checkbox_show_suggestion.setCheckable(False)

        widget = QWidget()
        widget.setLayout(self.wrapper_layout)
        self.setCentralWidget(widget)
        self.showMaximized()

    def relevant_buttons(self, feature):
        if feature == "opened_stimulus":
            # self.button_open_folder.setEnabled(True)
            self.checkbox_show_aoi.setCheckable(True)
            self.checkbox_show_aoi.setChecked(False)
            self.checkbox_show_aoi.setEnabled(True)
            self.toggle_aoi_width.setEnabled(True)
            self.toggle_aoi_height.setEnabled(True)
            self.toolbar.setEnabled(True)
            self.checkbox_show_fixations.setCheckable(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setCheckable(True)
            self.checkbox_show_saccades.setCheckable(False)
            self.checkbox_show_saccades.setChecked(False)
            self.checkbox_show_saccades.setCheckable(True)
        elif feature == "opened_folder":
            # self.button_save_corrections.setEnabled(False)
            self.button_previous_fixation.setEnabled(False)
            self.button_next_fixation.setEnabled(False)
            # self.button_correct_all_fixations.setEnabled(False)
            # self.button_confirm_suggestion.setEnabled(False)

            self.checkbox_show_fixations.setCheckable(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setEnabled(False)
            # self.input_lesser.setEnabled(False)
            # self.input_greater.setEnabled(False)
            # self.button_lesser.setEnabled(False)
            # self.button_greater.setEnabled(False)

            # IMPORTANT: here, set checked to false first so it activates suggestion removal since the removal
            # happens in the checkbox connected method,
            # then make in uncheckable so it won't activate by accident anymore; there is no helper function
            # for removing suggestions, so clearing suggestions isn't called anywhere in the code
            self.checkbox_show_suggestion.setChecked(False)
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setEnabled(False)

            self.checkbox_show_saccades.setCheckable(False)
            self.checkbox_show_saccades.setChecked(False)
            self.checkbox_show_saccades.setEnabled(False)
            self.progress_bar.setEnabled(False)
            self.progress_bar.setValue(self.progress_bar.minimum())
            self.button_fixation_color.setEnabled(False)
            self.button_saccade_color.setEnabled(False)
            self.button_suggested_fixation_color.setEnabled(False)
            self.button_current_fixation_color.setEnabled(False)
            self.toggle_aoi_width.setEnabled(False)
            self.toggle_aoi_height.setEnabled(False)
            self.button_coloblind_assist.setEnabled(False)
            self.toggle_fixation_opacity.setEnabled(False)
            self.toggle_saccade_opacity.setEnabled(False)

            # self.dropdown_select_algorithm.setEnabled(False)
        elif feature == "trial_clicked":
            # self.button_save_corrections.setEnabled(True)
            self.save_correction_action.setEnabled(True)
            self.edit_menu.setEnabled(True)
            self.filters_menu.setEnabled(True)
            self.correction_menu.setEnabled(True)

            self.button_previous_fixation.setEnabled(True)
            self.button_next_fixation.setEnabled(True)
            # self.button_correct_all_fixations.setEnabled(False)
            # self.button_confirm_suggestion.setEnabled(False)

            # self.dropdown_select_algorithm.setEnabled(True)
            # self.dropdown_select_algorithm.setCurrentIndex(0)

            self.checkbox_show_aoi.setCheckable(True)
            self.checkbox_show_aoi.setEnabled(True)

            self.checkbox_show_fixations.setCheckable(True)
            self.checkbox_show_fixations.setEnabled(True)

            self.checkbox_show_saccades.setCheckable(True)
            self.checkbox_show_saccades.setEnabled(True)

            # self.input_lesser.setEnabled(True)
            # self.input_greater.setEnabled(True)
            # self.button_lesser.setEnabled(True)
            # self.button_greater.setEnabled(True)

            self.toggle_aoi_width.setEnabled(True)
            self.toggle_aoi_height.setEnabled(True)
            self.button_fixation_color.setEnabled(True)
            self.button_saccade_color.setEnabled(True)
            self.button_suggested_fixation_color.setEnabled(False)
            self.button_current_fixation_color.setEnabled(True)
            self.toggle_fixation_opacity.setEnabled(True)
            self.toggle_saccade_opacity.setEnabled(True)
            self.button_coloblind_assist.setEnabled(True)

            # IMPORTANT: here, set checked to false first so it activates suggestion removal since the removal
            # happens in the checkbox connected method,
            # then make in uncheckable so it won't activate by accident anymore; there is no helper
            # function for removing suggestions
            self.checkbox_show_suggestion.setChecked(False)
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setEnabled(False)

            self.progress_bar.setValue(self.progress_bar.minimum())
            self.progress_bar.setEnabled(True)
        elif feature == "no_selected_algorithm":
            # self.button_previous_fixation.setEnabled(False)
            # self.button_next_fixation.setEnabled(False)
            # self.button_correct_all_fixations.setEnabled(False)
            # self.button_confirm_suggestion.setEnabled(False)
            # self.button_undo_suggestion.setEnabled(False)
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setChecked(
                False
            )  # the no algorithm selection updates the suggestions
            # which clears them in the function itself
            self.checkbox_show_suggestion.setEnabled(False)
        elif feature == "algorithm_selected":
            self.button_previous_fixation.setEnabled(True)
            self.button_next_fixation.setEnabled(True)
            self.button_suggested_fixation_color.setEnabled(True)
            # self.button_correct_all_fixations.setEnabled(True)
            # self.button_confirm_suggestion.setEnabled(True)
            # self.button_undo_suggestion.setEnabled(True)
            


if __name__ == "__main__":
    fix8 = QApplication([])
    window = Fix8()
    # apply_stylesheet(fix8, 'my_theme.xml')
    fix8.exec_()
