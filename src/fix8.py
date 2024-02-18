# Fix8
#
# Authors: Naser Al Madi <nsalmadi@colby.edu>
#          Brett Torra
#          Agnes Li
#          Najam Tariq
#          Ricky Peng (contributed to a previous version)
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
from state import State
import canvas_resources
import ui_main_window

# from PySide2 import QtWidgets
# from PyQt5 import QtWidgets
import pandas as pd
from qt_material import QtStyleTools, list_themes
import platform


class Fix8():
    def __init__(self):
        self.fix8 = QApplication([])
        self.ui = ui_main_window.Ui_Main_Window(self)

        # fields relating to the stimulus
        self.image_file_path = None

        # fields relating to the trial folder
        self.folder_path = None
        self.trial_path = None
        self.trial_name = None

        # fields relating to fixations
        self.eye_events = None              # dataframe of eye events
        self.original_fixations = None      # TODO: make this original_eye_events
        self.fixations = None               # TODO: replace with eye events:  timestamp, x, y, duration, pupil
        self.saccades = None                # TODO: replace with eye events:  timestamp, x, y, duration, x1, y1, amplitude, peak velocity 
        self.blinks = None                  # TODO: replace with eye events:  timestamp duration
        self.fixation_points = None
        self.saccade_lines = None
        self.current_fixation = -1

        # filed for tool undo/redo using memento pattern and state class
        self.state = State()

        # fields relating to AOIs
        self.aoi, self.background_color = None, None

        # fields relating to the correction algorithm
        self.algorithm = "manual"
        self.algorithm_function = None
        self.suggested_corrections, self.suggested_fixation = None, None

        # keeps track of how many times file was saved so duplicates can be saved instead of overriding previous save file
        self.timer_start = 0  # beginning time of trial
        self.metadata = ""

        self.saccade_opacity = 0.4
        self.fixation_opacity = 0.4

        # fields relating to the drag and drop system
        self.selected_fixation = None
        self.xy = None      

        # fields relating to aoi margin
        self.aoi_width = 7
        self.aoi_height = 4

        # fields relating to color filters
        self.fixation_color = "red"
        self.current_fixation_color = "magenta"
        self.suggested_fixation_color = "blue"
        self.saccade_color = "blue"
        self.aoi_color = "yellow"
        self.colorblind_assist_status = False
        
        # fields relating to fixation size
        self.fixation_size = 30
        # hide/show side panel until a folder is opened
        self.ui.hide_side_panel()


    def generate_fixations(self):
        minimum_value = 0
        maximum_value = 100
        default_value = 20
        title = "Dispersion"
        message = "Enter value for dispersion around the optimal viewing position in pixels(0-100)"
        dispersion, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        # clear history for undo
        self.state = State()

        # get aoi from the image
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )

        # generate fixations
        self.original_fixations = np.array(mini_emtk.generate_fixations_left(self.aoi, dispersion))
        self.ui.relevant_buttons("trial_clicked")

        #self.read_json_fixations(self.trial_path)
        self.suggested_corrections = None
        # double clicking trial should show all and make the current fixation the last one
        self.current_fixation = (len(self.original_fixations)-1)  

        # set the progress bar to the amount of fixations found
        self.ui.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.timer_start = time.time()
        self.metadata = "Generated fixations,," + str(time.time()) + "\n"

        if self.current_fixation is not None:
            if self.current_fixation == -1:
                self.ui.label_progress.setText(f"0/{len(self.original_fixations)}")
            else:
                self.ui.label_progress.setText(
                    f"{self.current_fixation}/{len(self.original_fixations)}"
                )

        # corrected fixations will be the current fixations on the screen and in the data
        self.fixations = copy.deepcopy(self.original_fixations)
        self.save_state()
        self.ui.checkbox_show_fixations.setChecked(True)
        self.ui.checkbox_show_saccades.setChecked(True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.status_text =" Generated synthetic data"
        self.ui.statusBar.showMessage(self.status_text)

    def generate_fixations_skip(self):
        minimum_value = 1
        maximum_value = 100
        default_value = 20
        title = "Skip"
        message = "Enter skip probability (1-100)"
        skip_probability, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        # clear history for undo
        self.state = State()

        # get aoi from the image
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )

        # generate fixations
        self.original_fixations = np.array(mini_emtk.generate_fixations_left_skip(self.aoi, skip_probability/100))
        self.ui.relevant_buttons("trial_clicked")

        #self.read_json_fixations(self.trial_path)
        self.suggested_corrections = None
        # double clicking trial should show all and make the current fixation the last one
        self.current_fixation = (len(self.original_fixations)-1)  

        # set the progress bar to the amount of fixations found
        self.ui.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.timer_start = time.time()
        self.metadata = "Generated fixations,," + str(time.time()) + "\n"

        if self.current_fixation is not None:
            if self.current_fixation == -1:
                self.ui.label_progress.setText(f"0/{len(self.original_fixations)}")
            else:
                self.ui.label_progress.setText(
                    f"{self.current_fixation}/{len(self.original_fixations)}"
                )

        # corrected fixations will be the current fixations on the screen and in the data
        self.fixations = copy.deepcopy(self.original_fixations)
        self.save_state()
        self.ui.checkbox_show_fixations.setChecked(True)
        self.ui.checkbox_show_saccades.setChecked(True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.status_text =" Generated synthetic data"
        self.ui.statusBar.showMessage(self.status_text)

    def generate_within_line_regression(self):
        minimum_value = 0
        maximum_value = 100
        default_value = 20
        title = "Within-line regression"
        message = "Enter within-line regression probability (0-100)"
        probability, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        # clear history for undo
        self.state = State()

        # get aoi from the image
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )

        # generate fixations
        self.original_fixations = np.array(mini_emtk.within_line_regression(self.aoi, probability/10))
        self.ui.relevant_buttons("trial_clicked")

        #self.read_json_fixations(self.trial_path)
        self.suggested_corrections = None
        # double clicking trial should show all and make the current fixation the last one
        self.current_fixation = (len(self.original_fixations)-1)  

        # set the progress bar to the amount of fixations found
        self.ui.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.timer_start = time.time()
        self.metadata = "Generated fixations,," + str(time.time()) + "\n"

        if self.current_fixation is not None:
            if self.current_fixation == -1:
                self.ui.label_progress.setText(f"0/{len(self.original_fixations)}")
            else:
                self.ui.label_progress.setText(
                    f"{self.current_fixation}/{len(self.original_fixations)}"
                )

        # corrected fixations will be the current fixations on the screen and in the data
        self.fixations = copy.deepcopy(self.original_fixations)
        self.save_state()
        
        self.ui.checkbox_show_fixations.setChecked(True)
        self.ui.checkbox_show_saccades.setChecked(True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.status_text =" Generated synthetic data"
        self.ui.statusBar.showMessage(self.status_text)

    def generate_between_line_regression(self):
        minimum_value = 0
        maximum_value = 100
        default_value = 20
        title = "Between-line regression"
        message = "Enter Between-line regression probability (0-100)"
        probability, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        # clear history for undo
        self.state = State()

        # get aoi from the image
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )

        # generate fixations
        self.original_fixations = np.array(mini_emtk.between_line_regression(self.aoi, probability/10))
        self.ui.relevant_buttons("trial_clicked")

        #self.read_json_fixations(self.trial_path)
        self.suggested_corrections = None
        # double clicking trial should show all and make the current fixation the last one
        self.current_fixation = (len(self.original_fixations)-1)  

        # set the progress bar to the amount of fixations found
        self.ui.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.timer_start = time.time()
        self.metadata = "Generated fixations,," + str(time.time()) + "\n"

        if self.current_fixation is not None:
            if self.current_fixation == -1:
                self.ui.label_progress.setText(f"0/{len(self.original_fixations)}")
            else:
                self.ui.label_progress.setText(
                    f"{self.current_fixation}/{len(self.original_fixations)}"
                )

        # corrected fixations will be the current fixations on the screen and in the data
        self.fixations = copy.deepcopy(self.original_fixations)
        self.save_state()
        
        self.ui.checkbox_show_fixations.setChecked(True)
        self.ui.checkbox_show_saccades.setChecked(True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.status_text =" Generated synthetic data"
        self.ui.statusBar.showMessage(self.status_text)

    def generate_noise(self):
        minimum_value = 1
        maximum_value = 10
        default_value = 5
        title = "Noise Distortion"
        message = "Magnitude of noise distortion (1-10)"
        threshold, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "generate,noise "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )
        self.save_state()

        self.fixations = self.fixations + np.random.normal(0, threshold, self.fixations.shape)

        if self.algorithm != "manual" and self.suggested_corrections is not None:

            self.suggested_corrections[:, 0] = self.fixations[:, 0]

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation, draw=True)

    def generate_slope(self):
        minimum_value = 1
        maximum_value = 10
        default_value = 5
        title = "Slope Distortion"
        message = "Magnitude of skope distortion (1-10)"
        threshold, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "generate,slope "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )
        self.save_state()

        self.fixations = np.array(mini_emtk.error_droop(threshold, self.fixations))

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation, draw=True)


    def generate_offset(self):
        minimum_value = 1
        maximum_value = 300
        default_value = 30
        title = "Offset Distortion"
        message = "Magnitude of offset distortion (1-300)"
        threshold, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "generate,offset "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )
        self.save_state()

        self.fixations = np.array(mini_emtk.error_offset(threshold, self.fixations))

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation, draw=True)

    def generate_shift(self):
        minimum_value = 1
        maximum_value = 10
        default_value = 5
        title = "Shift Distortion"
        message = "Magnitude of Shift distortion (1-10)"
        threshold, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "generate,shift "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )
        self.save_state()

        # get aoi from the image
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )

        # get line_Y from aoi
        line_Y = self.find_lines_y(self.aoi)

        self.fixations = np.array(mini_emtk.error_shift(threshold, line_Y, self.fixations))

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation, draw=True)

    def ascii_to_csv_converter(self):
        # open ascii file through file dialog limit to .asc files
        qfd = QFileDialog()
        ascii_file = qfd.getOpenFileName(self.ui, "Select ascii file", "", "ASCII Files (*.asc)")[0]

        if ascii_file == "":
            self.show_error_message("Error", "No file selected")
            return

        # ask user for file name to save csv through file dialog
        qfd = QFileDialog()
        default_file_name = ascii_file.replace('.asc', '') + '.csv'
        new_correction_file_name, _ = qfd.getSaveFileName(self.ui, "Save converted CSV file", default_file_name)
        
        if new_correction_file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        if '.csv' not in new_correction_file_name:
            new_correction_file_name += '.csv'

        self.show_error_message("Warning", "Conversion may take a while")

        # convert and save csv file
        mini_emtk.read_EyeLink1000(ascii_file, new_correction_file_name)


    def eyelink_experiment_to_csv_converter(self):
        ''' convert eyelink experiment to csv files from ASCII and runtime folder '''
        # open ascii file through file dialog limit to .asc files
        qfd = QFileDialog()
        ascii_file = qfd.getOpenFileName(self.ui, "Select ascii file", "", "ASCII Files (*.asc)")[0]

        if ascii_file == "":
            self.show_error_message("Error", "No file selected")
            return

        # ask user for file name to save csv through file dialog
        qfd = QFileDialog()
        save_folder = qfd.getExistingDirectory(self.ui, "Save experiment trials to folder")
        
        if save_folder == "":
            self.show_error_message("Error", "No save folder selected")
            return

        self.show_error_message("Warning", "Conversion may take a while")

        # convert and save csv file
        mini_emtk.read_EyeLink1000_experiment(ascii_file, save_folder)


    def outlier_duration_filter(self):
        minimum_value = 1
        maximum_value = 4
        default_value = 2.5
        title = "Duration Filter"
        message = "Remove fixations with durations X standard deviations away from the mean"
        threshold, ok = QInputDialog.getDouble(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "filter,removed fixations X standard deviations away from the mean "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )
        self.save_state()

        # get mean duration and standard deviation
        mean = np.mean(self.fixations[:, 2])
        std = np.std(self.fixations[:, 2])

        # remove fixations X standard deviations away from the mean
        self.fixations = self.fixations[((self.fixations[:, 2] - mean) / std) < threshold]

        self.current_fixation = 0

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            if self.current_fixation == len(self.fixations):
                self.current_fixation = len(self.fixations) - 1

            self.suggested_corrections = self.suggested_corrections[self.suggested_corrections[:, 2] < mean + threshold * std]

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation, draw=True)


    def undo(self):
        ''' implement undo using memento pattern and state class ''' 
        if not self.state.is_empty():
            
            at_max = False
            # check if progressbar is at end of progressbar range
            if self.ui.progress_bar.value() == self.ui.progress_bar.maximum():
                at_max = True
             
        
            self.fixations = self.state.get_state()

            # update progress bar
            self.ui.progress_bar.setMaximum(len(self.fixations) - 1)

            if self.current_fixation >= len(self.fixations) or at_max:
                self.current_fixation = len(self.fixations) - 1

            self.progress_bar_updated(self.current_fixation, draw=True)


    def save_state(self):
        self.state.set_state(self.fixations)


    def outside_screen_filter(self):
        self.metadata += "filter,removed fixations outside screen," + str(time.time()) + "\n"

        # get image dimentions from self.image_file_path
        image = mpimg.imread(self.image_file_path)
        screen_width = image.shape[1]
        screen_height = image.shape[0]

        self.save_state()

        self.fixations = self.fixations[
            (self.fixations[:, 0] >= 0)
            & (self.fixations[:, 0] <= screen_width)
            & (self.fixations[:, 1] >= 0)
            & (self.fixations[:, 1] <= screen_height)
        ]

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            self.suggested_corrections = self.suggested_corrections[
                (self.suggested_corrections[:, 0] >= 0)
                & (self.suggested_corrections[:, 0] <= screen_width)
                & (self.suggested_corrections[:, 1] >= 0)
                & (self.suggested_corrections[:, 1] <= screen_height)
            ]

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)


    def lowpass_duration_filter(self):
        minimum_value = 1
        maximum_value = 99
        default_value = 80
        title = "Duration Filter"
        message = "Remove fixations with durations less than"
        threshold, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "filter,removed fixations less than "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )
        self.save_state()

        self.fixations = self.fixations[self.fixations[:, 2] > int(threshold)]
        self.current_fixation = 0

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            if self.current_fixation == len(self.fixations):
                self.current_fixation = len(self.fixations) - 1

            self.suggested_corrections = self.suggested_corrections[self.suggested_corrections[:, 2] > int(threshold)]

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)


    def highpass_duration_filter(self):
        minimum_value = 100
        maximum_value = 2000
        default_value = 800
        title = "Duration Filter"
        message = "Remove fixations with durations greater than"
        threshold, ok = QInputDialog.getInt(self.ui, title, message, default_value, minimum_value, maximum_value)

        if not ok:
            return

        self.metadata += (
            "filter,removed fixations greater than "
            + str(threshold)
            + ","
            + str(time.time())
            + "\n"
        )

        self.save_state()

        self.fixations = self.fixations[self.fixations[:, 2] < int(threshold)]
        self.current_fixation = 0

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            if self.current_fixation == len(self.fixations):
                self.current_fixation = len(self.fixations) - 1

            self.suggested_corrections = self.suggested_corrections[self.suggested_corrections[:, 2] < int(threshold)]

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)


    def merge_fixations(self):
        dialog = InputDialog(self.ui)
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

        self.save_state()

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

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
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

        # run algorithm, warp uses word_xy, others use line_Y
        if self.algorithm != "warp":
            self.suggested_corrections[:, 0:2] = self.algorithm_function(fixation_XY, line_Y)
        else:
            self.suggested_corrections[:, 0:2] = self.algorithm_function(fixation_XY, word_XY)

        self.status_text = self.algorithm + " Algorithm Selected"
        self.ui.statusBar.showMessage(self.status_text)
        self.ui.relevant_buttons("algorithm_selected")


    def run_algorithm(self, algorithm_name, algorithm_function, mode):

        self.algorithm = algorithm_name
        self.algorithm_function = algorithm_function
        self.run_correction()

        # write metadata
        self.metadata += ("selected, algorithm " + str(self.algorithm) + "," + str(time.time()) + "\n")

        if mode == 'semi':
            # show suggestion
            self.ui.checkbox_show_suggestion.setCheckable(True)
            self.ui.checkbox_show_suggestion.setEnabled(True)
            self.ui.checkbox_show_suggestion.setChecked(True)
            # update progress bar to end
            self.ui.progress_bar.setValue(self.ui.progress_bar.minimum())
        else:
            # correct all
            self.correct_all_fixations()
            # hide suggestion
            self.ui.checkbox_show_suggestion.setEnabled(False)
            self.ui.checkbox_show_suggestion.setChecked(False)
            self.ui.checkbox_show_suggestion.setCheckable(False)
            # update progress bar to end
            self.ui.progress_bar.setValue(self.ui.progress_bar.maximum())


    def manual_correction(self):
        self.algorithm_function = None
        self.algorithm = "manual"

        # write metadata
        self.metadata += ("selected, " + str(self.algorithm) + "," + str(time.time()) + "\n")

        self.suggested_corrections = copy.deepcopy(self.fixations)
        self.ui.checkbox_show_suggestion.setEnabled(False)

        # hide suggestion
        self.ui.checkbox_show_suggestion.setChecked(False)

    
    def get_selected_fixation(self, event):
        """
        get the selected fixation that the user picks, with the selection 
        inside a specific diameter range (epsilon), selected_fixation is an 
        index, not the actual scatter point
        """
        if self.fixation_points is not None:

            self.xy = np.asarray(self.fixation_points.get_offsets())
            xyt = self.ui.canvas.ax.transData.transform(self.xy)
            xt, yt = xyt[:, 0], xyt[:, 1]
            d = np.sqrt((xt - event.x) ** 2 + (yt - event.y) ** 2)
            self.selected_fixation = d.argmin()

            duration = self.fixations[self.selected_fixation][2]
            #epsilon = 11  # diameter range
            area = 30 * (duration / 50) ** 2

            # divide are a by pi and take the square root to get the radius
            epsilon = (area / np.pi) ** 0.5

            if epsilon < 5:
                epsilon = 5

            if d[self.selected_fixation] >= epsilon:
                self.selected_fixation = None

            return self.selected_fixation


    def move_left_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
            self.fixations[self.selected_fixation][0] -= 2

        self.draw_canvas(self.fixations)

    def move_right_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
            self.fixations[self.selected_fixation][0] += 2

        self.draw_canvas(self.fixations)

    def move_down_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
            self.fixations[self.selected_fixation][1] += 2

        self.draw_canvas(self.fixations)

    def move_up_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
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
            self.save_state()

            # move fixation
            self.fixations[self.selected_fixation][0] = self.xy[self.selected_fixation][0]
            self.fixations[self.selected_fixation][1] = self.xy[self.selected_fixation][1]

            # update correction based on algorithm

            if self.algorithm != "manual" and self.algorithm is not None:
                self.run_correction()

            if self.ui.checkbox_show_saccades.isChecked():
                self.clear_saccades()
                self.show_saccades(Qt.Checked)
            else:
                self.show_saccades(Qt.Unchecked)
        
        if event.button != 1:
            return
        # self.selected_fixation = None

        self.draw_canvas(self.fixations)
        # self.ui.canvas.update()

    def motion_notify_callback(self, event):
        if self.selected_fixation is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return

        x, y = event.xdata, event.ydata

        #self.xy = np.asarray(self.scatter.get_offsets())
        self.xy[self.selected_fixation] = np.array([x, y])
        #self.scatter.set_offsets(self.xy)
        # self.ui.canvas.draw_idle()

        self.ui.canvas.restore_region(self.ui.canvas.background)
        self.ui.canvas.ax.draw_artist(self.fixation_points)
        #self.ui.canvas.ax.draw_artist(self.saccades)
        self.ui.canvas.blit(self.ui.canvas.ax.bbox)


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

        # a: next is 65
        if e.key() == 65 and self.ui.button_next_fixation.isEnabled():
            self.metadata += "key,next," + str(time.time()) + "\n"
            self.next_fixation()

        # z: back is 90
        if e.key() == 90 and self.ui.button_previous_fixation.isEnabled():
            self.metadata += "key,previous," + str(time.time()) + "\n"
            self.previous_fixation()

        # spacebar: accept and next is 32
        if e.key() == 32 and self.algorithm_function != None:
            self.metadata += "key,accept suggestion," + str(time.time()) + "\n"
            self.confirm_suggestion()

        # backspace
        if e.key() == 16777219:
            self.metadata += "key,remove fixation," + str(time.time()) + "\n"
            if self.fixations is not None and self.selected_fixation is not None:
                if self.selected_fixation < len(self.fixations):
                    self.save_state()

                    self.fixations = np.delete(self.fixations, self.selected_fixation, 0)  # delete the row of selected fixation
                    if self.current_fixation == 0:
                        self.current_fixation = len(self.fixations)
                        self.current_fixation -= 1
                        temp = self.current_fixation
                    else:
                        self.current_fixation -= 1
                        temp = self.current_fixation

                    self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
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


    def show_error_message(self, window_title, message):
        qmb = QMessageBox(self.ui)
        qmb.setWindowTitle(window_title)
        qmb.setText(message)
        qmb.exec_()


    def open_trial_folder(self):
        """open trial folder, display it to trial list window with list of JSON trials"""
        qfd = QFileDialog()
        self.folder_path = qfd.getExistingDirectory(self.ui, "Select Folder")

        # --- make sure a folder was actually chosen, otherwise just cancel ---
        if self.folder_path != "":
            # clear the data since a new folder was open, no trial is chosen at this point
            self.ui.trial_list.clear()
            self.clear_fixations()
            self.clear_saccades()

            # when open a new folder, block off all the relevant buttons that shouldn't be accesible until a trial is clicked
            self.ui.relevant_buttons("opened_folder")
            self.status_text = "Trial Folder Opened: " + self.folder_path
            self.ui.statusBar.showMessage(self.status_text)

            files = listdir(self.folder_path)

            image_file = ""

            if len(files) > 0:
                self.file_list = []
                for file in files:
                    if file.endswith(".json") or file.endswith(".csv"):
                        self.file_list.append(self.folder_path + "/" + file)

                    elif (file.endswith(".png")
                        or file.endswith(".jpeg")
                        or file.endswith(".jpg")):
                        if image_file == "":  # only get the first image found
                            image_file = self.folder_path + "/" + file
                            self.image_file_path = self.folder_path + "/" + file
                
                if len(self.file_list) > 0:
                    # add the files to the trial list window
                    self.trials = {}
                    for file in self.file_list:
                        file_to_add = QListWidgetItem(file)
                        file_to_add_name = file.split("/")[-1]  # last part of file text
                        self.trials[file_to_add_name] = file
                        file_to_add.setText(file_to_add_name)
                        self.ui.trial_list.addItem(file_to_add)
                else:
                    self.show_error_message("Trial Folder Error", "No JSONS")

            else:
                self.show_error_message("Trial Folder Error", "Empty Folder")

            if image_file == "":  # image file wasn't found
                self.show_error_message("Trial Folder Error", "No Compatible Image")

            else:
                self.set_canvas_image(image_file)
                self.ui.canvas.draw()
                self.find_aoi()
                self.ui.relevant_buttons("opened_stimulus")
                # hide side panel until a folder is opened
                self.ui.show_side_panel()


    def open_image(self):
        qfd = QFileDialog()
        self.image_file_path = qfd.getOpenFileName(self.ui, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")[0]

        if self.image_file_path != "":
            self.set_canvas_image(self.image_file_path)
            self.find_aoi()
            self.ui.relevant_buttons("opened_stimulus")
            self.ui.canvas.draw_idle()
            
            self.ui.generate_menu.setEnabled(True)
        else:
            self.show_error_message("Image Error", "No Image Selected")


    def set_canvas_image(self, image_file):
        self.ui.canvas.clear()
        image = mpimg.imread(image_file)
        # show image with highest quality
        self.ui.canvas.ax.imshow(image, interpolation="hanning")
        #self.ui.canvas.ax.set_title(str(image_file.split('/')[-1].split(".")[0]))


    def trial_double_clicked(self, item):
        """
        when a trial from the trial list is double clicked, find the fixations of the trial
        parameters:
        item - the value passed through when clicking a trial object in the list
        """
        
        # reset times saved if a DIFFERENT trial was selected
        self.trial_name = item.text()
        self.trial_path = self.trials[item.text()]

        if self.trial_path.endswith(".json"):
            self.read_json_fixations(self.trial_path)
        elif self.trial_path.endswith(".csv"):
            self.read_csv_fixations(self.trial_path)

        # clear history for undo
        self.state = State()

        self.suggested_corrections = None
        self.current_fixation = (len(self.original_fixations)-1)  

        # set the progress bar to the amount of fixations found
        self.ui.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.timer_start = time.time()
        self.metadata = "started,," + str(time.time()) + "\n"

        if self.current_fixation is not None:
            if self.current_fixation == -1:
                self.ui.label_progress.setText(f"0/{len(self.original_fixations)}")
            else:
                self.ui.label_progress.setText(
                    f"{self.current_fixation}/{len(self.original_fixations)}"
                )

        self.fixations = copy.deepcopy(self.original_fixations)
        self.save_state()
        self.ui.checkbox_show_fixations.setChecked(True)
        self.ui.checkbox_show_saccades.setChecked(True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.draw_canvas(self.fixations, draw_all=True)

        self.status_text = self.trial_name + " Opened (Default: Manual Mode)"
        self.ui.statusBar.showMessage(self.status_text)


    def find_aoi(self):
        """find the areas of interest (aoi) for the selected stimulus"""
        if self.image_file_path != "":
            self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
                self.image_file_path,
                margin_height=self.aoi_height,
                margin_width=self.aoi_width,
            )


    def draw_aoi(self):
        """draw the found aois to the canvas"""
        color = self.aoi_color if self.background_color == "black" else "black"

        for row in self.aoi.iterrows():

            xcord = row[1]["x"]
            ycord = row[1]["y"]
            height = row[1]["height"]
            width = row[1]["width"]
            
            self.ui.canvas.ax.add_patch(
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
        
        self.ui.canvas.draw()


    def clear_aoi(self):
        """clear the aois from the canvas"""
        self.ui.canvas.ax.patches.clear()
        self.ui.canvas.draw()


    def show_aoi(self, state):
        """when the show aoi button is pressed, show or hide aois based on checkbox"""
        if self.ui.checkbox_show_aoi.isCheckable():
            if state == Qt.Checked:
                self.draw_aoi()
            elif state == Qt.Unchecked:
                self.clear_aoi()

    
    def read_json_fixations(self, trial_path):
        """find all the fixations of the trial that was double clicked
        parameters:
        trial_path - the trial file path of the trial clicked on"""
        self.original_fixations = []
        x_cord = []
        y_cord = []
        duration = []

        with open(trial_path, "r") as trial:
            try:
                trial_data = json.load(trial)
                for key in trial_data:
                    x_cord.append(trial_data[key][0])
                    y_cord.append(trial_data[key][1])
                    duration.append(trial_data[key][2])

            except json.decoder.JSONDecodeError:
                self.show_error_message("Trial File Error", "JSON File Empty")

        # create an empty dataframe
        self.eye_events = pd.DataFrame(columns=["x_cord", "y_cord", "duration"])
        self.eye_events["x_cord"] = x_cord
        self.eye_events["y_cord"] = y_cord
        self.eye_events["duration"] = duration
        self.eye_events["eye_event"] = "fixation"

        self.original_fixations = self.eye_events[self.eye_events["eye_event"] == "fixation"]
        self.original_fixations.drop(columns=["eye_event"], inplace=True)

        self.original_fixations = np.array(self.original_fixations)
        self.ui.relevant_buttons("trial_clicked")


    def read_csv_fixations(self, trial_path):
        """find all the fixations of the trial that was double clicked
        parameters:
        trial_path - the trial file path of the trial clicked on"""
        self.original_fixations = []

        try:
            # open the csv file with pandas
            self.eye_events = pd.read_csv(trial_path)

        except:
            self.show_error_message("Trial File Error", "Problem reading CSV File")     
            return

        # get the fixations from the csv file
        fixations = self.eye_events[self.eye_events["eye_event"] == "fixation"]

        # get the x, y, and duration of the fixations
        for index, row in fixations.iterrows():
            self.original_fixations.append([row["x_cord"], row["y_cord"], row["duration"]])

        self.original_fixations = np.array(self.original_fixations)
        self.ui.relevant_buttons("trial_clicked")


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
        self.fixation_points = self.ui.canvas.ax.scatter(
            x,
            y,
            s=30 * (duration / 50) ** 1.8,
            alpha=self.fixation_opacity,
            c=self.fixation_color,
        )
        self.ui.canvas.draw()

    

    def show_fixations(self, state):
        """if the user clicks the show fixations checkbox, show or hide the fixations
        parameters:
        state - the checkbox being checked or unchecked"""
        if self.folder_path != "":
            if self.ui.checkbox_show_fixations.isCheckable():
                if state == Qt.Checked:
                    self.draw_fixations()
                elif state == Qt.Unchecked:
                    self.clear_fixations()

    

    def show_saccades(self, state):
        """if the user clicks saccades, show or hide them"""
        if self.folder_path != "":
            if self.ui.checkbox_show_saccades.isCheckable():
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
        self.saccade_lines = self.ui.canvas.ax.plot(
            x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1
        )
        self.ui.canvas.draw()

    

    def clear_saccades(self):
        """remove the saccades from the canvas (this does not erase the data, just visuals)"""
        if self.saccade_lines != None:
            self.ui.canvas.ax.lines.clear()  # <-- if this line crashes the tool

            # for line in self.ui.canvas.ax.lines:  #<-- use this instead
            #    line.remove()

            self.saccade_lines = None
            self.ui.canvas.draw()

    

    def clear_fixations(self):
        """clear the fixations from the canvas"""
        if self.fixation_points != None:
            # self.scatter.remove()
            self.fixation_points = None
            # clear scatter data from canvas but not the background image
            self.ui.canvas.ax.collections.clear()  # <-- If this line crashes the tool

            # for collection in self.ui.canvas.ax.collections: #<-- use this instead
            #    collection.remove()
            self.ui.canvas.draw()


    # draw fixations2 is similar to the normal draw fixations, excpet this one only draws to the current fixation
    def draw_canvas(self, fixations, draw_all=False):

        if fixations is None:
            return

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
        if self.ui.checkbox_show_fixations.isCheckable():
            if self.ui.checkbox_show_fixations.isChecked():
                list_colors = [self.fixation_color] * (len(x) - 1)
                colors = np.array(list_colors + [self.current_fixation_color])
                self.fixation_points = self.ui.canvas.ax.scatter(
                    x,
                    y,
                    s=self.fixation_size * (duration / 50) ** 1.8,
                    alpha=self.fixation_opacity,
                    c=colors,
                )
                self.ui.canvas.background = self.ui.canvas.copy_from_bbox(self.ui.canvas.ax.bbox)
                # self.scatter = self.ui.canvas.ax.scatter(x[-1], y[-1], s=30 * (duration[-1]/50)**1.8, alpha = self.fixation_opacity, c = "yellow")

        if self.ui.checkbox_show_saccades.isCheckable():
            if self.ui.checkbox_show_saccades.isChecked():
                self.saccade_lines = self.ui.canvas.ax.plot(
                    x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1
                )

        # draw suggested fixation in blue
        if self.ui.checkbox_show_suggestion.isChecked():
            x = self.suggested_corrections[self.current_fixation][0]
            y = self.suggested_corrections[self.current_fixation][1]
            duration = self.fixations[self.current_fixation][2]

            self.suggested_fixation = self.ui.canvas.ax.scatter(
                x,
                y,
                s=30 * (duration / 50) ** 1.8,
                alpha=self.fixation_opacity,
                c=self.suggested_fixation_color,
            )

        self.ui.canvas.draw()


    def quick_draw_canvas(self, all_fixations=False):

        self.ui.canvas.restore_region(self.ui.canvas.background)

        if all_fixations:
            x = self.fixations[:, 0]
            y = self.fixations[:, 1]
            duration = self.fixations[:, 2]
        else:
            x = self.fixations[0 : self.current_fixation + 1, 0]
            y = self.fixations[0 : self.current_fixation + 1, 1]
            duration = self.fixations[0 : self.current_fixation + 1, 2]

        # generate colors for fixations
        list_colors = [self.fixation_color] * (len(x) - 1)
        colors = np.array(list_colors + [self.current_fixation_color])

        # draw fixations
        self.fixation_points = self.ui.canvas.ax.scatter(
            x,
            y,
            s=30 * (duration / 50) ** 1.8,
            alpha=self.fixation_opacity,
            c=colors,
        )

        # draw saccades
        self.saccade_lines = self.ui.canvas.ax.plot(
            x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1
        )

        # draw suggested fixation in blue (or selected color)
        if self.ui.checkbox_show_suggestion.isChecked():
            x = self.suggested_corrections[self.current_fixation][0]
            y = self.suggested_corrections[self.current_fixation][1]
            duration = self.fixations[self.current_fixation][2]

            self.suggested_fixation = self.ui.canvas.ax.scatter(
                x,
                y,
                s=30 * (duration / 50) ** 1.8,
                alpha=self.fixation_opacity,
                c=self.suggested_fixation_color,
            )
            self.ui.canvas.ax.draw_artist(self.suggested_fixation)

        self.ui.canvas.ax.draw_artist(self.fixation_points)
        self.ui.canvas.ax.draw_artist(self.saccade_lines[0])
        
        self.ui.canvas.blit(self.ui.canvas.ax.bbox)


    def correct_all_fixations(self):
        """if the user presses the correct all fixations button,
        make the corrected fixations the suggested ones from the correction algorithm"""
        if self.suggested_corrections is not None:
            self.save_state()
            self.fixations = copy.deepcopy(self.suggested_corrections)
            self.draw_canvas(self.fixations)

        self.metadata += (
            "correct_all, all fixations corrected automatically"
            + ","
            + str(time.time())
            + "\n"
        )
        self.status_text = "Correct All Fixations!"
        self.ui.statusBar.showMessage(self.status_text)

    def previous_fixation(self):
        # if self.suggested_corrections is not None:
        if self.current_fixation != 0:
            self.current_fixation -= 1

        #self.draw_canvas(self.fixations)
        self.progress_bar_updated(self.current_fixation, draw=False)

        # if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
        #    self.update_suggestion()


    def next_fixation(self):
        if self.current_fixation == -1 and self.original_fixations == None:
            # Tour
            self.set_canvas_image('./.images/fix8-tour-1.png')
            self.ui.canvas.draw()
            self.ui.button_next_fixation.setEnabled(False)
            return
        
        if self.current_fixation != len(self.fixations) - 1:
            self.current_fixation += 1

        #self.ui.canvas.ax.lines
        #self.draw_canvas(self.fixations)
        self.progress_bar_updated(self.current_fixation, draw=False)



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
        self.save_state()

        self.fixations[self.current_fixation][0] = self.suggested_corrections[self.current_fixation][0]
        self.fixations[self.current_fixation][1] = self.suggested_corrections[self.current_fixation][1]

        self.quick_draw_canvas(all_fixations=False)
        self.next_fixation()


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
        default_file_name = self.trial_path.replace('.json', '') + '_CORRECTED.json'
        new_correction_file_name, _ = qfd.getSaveFileName(self.ui, "Save correction", default_file_name)

        if '.json' not in new_correction_file_name:
            new_correction_file_name += '.json'

        if len(self.fixations) > 0:
            list = self.fixations.tolist()

            corrected_fixations = {}
            for i in range(len(self.fixations)):
                corrected_fixations[i + 1] = list[i]

            with open(f"{new_correction_file_name}", "w") as f:
                json.dump(corrected_fixations, f)
                
            duration = (time.time() - self.timer_start)
            today = date.today()

            self.metadata += (
                "Saved,Date "
                + str(today)
                + " Trial Name"
                + str(self.trial_name)
                + " File Path "
                + str(new_correction_file_name)
                + " Duration "
                + str(duration)
                + ","
                + str(time.time())
                + "\n"
            )

            self.save_metadata_file(new_correction_file_name)

            self.status_text = "Corrections Saved to" + " " + new_correction_file_name
            self.ui.statusBar.showMessage(self.status_text)

        else:
            self.show_error_message("Save Error", "No Corrections Made")

    def progress_bar_updated(self, value, draw=True):
        # update the current suggested correction to the last fixation of the list
        self.current_fixation = value

        # update current suggestion to the progress bar
        if self.current_fixation is not None:
            self.ui.label_progress.setText(
                f"{self.current_fixation}/{len(self.fixations)}"
            )
            self.ui.progress_bar.setValue(self.current_fixation)

        if draw:

            #self.xy = np.asarray(self.scatter.get_offsets())
            #self.xy[self.selected_fixation] = np.array([x, y])
            #self.scatter.set_offsets(self.xy)
            # self.ui.canvas.draw_idle()
            if self.ui.canvas.background is None:
                self.draw_canvas(self.fixations)
                return

            self.quick_draw_canvas(all_fixations=False)

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

        self.quick_draw_canvas(all_fixations=False)

    def select_current_fixation_color(self):
        color = QColorDialog.getColor(initial=Qt.red)
        if color.isValid():
            self.current_fixation_color = str(color.name())
        else:
            self.current_fixation_color = "magenta"

        self.quick_draw_canvas(all_fixations=False)

    def select_suggested_fixation_color(self):
        color = QColorDialog.getColor(initial=Qt.red)
        if color.isValid():
            self.suggested_fixation_color = str(color.name())
        else:
            self.suggested_fixation_color = "blue"

        self.quick_draw_canvas(all_fixations=False)

    def select_saccade_color(self):
        color = QColorDialog.getColor(initial=Qt.blue)
        if color.isValid():
            self.saccade_color = str(color.name())
        else:
            self.saccade_color = "blue"

        self.quick_draw_canvas(all_fixations=False)

    def colorblind_assist(self):
        if self.colorblind_assist_status == False:
            self.fixation_color = "#FF9E0A"
            # TODO: Agnes, please figure out what color is best for current fixations
            # self.current_fixation_color = "yellow"
            self.saccade_color = "#3D00CC"
            self.aoi_color = "#28AAFF"
            self.colorblind_assist_status = True
            self.quick_draw_canvas(all_fixations=False)
        else:
            self.fixation_color = "red"
            self.saccade_color = "blue"
            self.aoi_color = "yellow"
            self.colorblind_assist_status = False
            self.quick_draw_canvas(all_fixations=False)

    def saccade_opacity_changed(self, value):
        self.saccade_opacity = float(value / 10)
        self.quick_draw_canvas(all_fixations=False)

    def fixation_opacity_changed(self, value):
        self.fixation_opacity = float(value / 10)
        self.quick_draw_canvas(all_fixations=False)

    def fixation_size_changed(self, value):
        self.fixation_size = value*6
        self.draw_canvas(self.fixations)
    

if __name__ == "__main__":

    if platform.system() == "Windows":
        import ctypes
        myappid = 'ThisCanBeAnything' # arbitrary string

        # This helps Windows manage and group windows of this application together
        # And helps us maintain the taskbar icon
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    window = Fix8()
    window.fix8.exec_()