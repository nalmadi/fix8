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
from PyQt5.QtGui import QColor

# from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QColorDialog,
    QMessageBox,
    QInputDialog,
    QListWidgetItem,
    QTableWidgetItem,
)
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np


from matplotlib.patches import Rectangle
import json
from os import listdir
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)
import copy

# import matplotlib.animation as animation
from datetime import date
from pathlib import Path

from . import mini_emtk
from .merge_fixations_dialog import MergeFixationsDialog
from .generate_fixations_skip_dialog import GenerateFixationsSkipDialog
from .eyelink_csv_dialog import EyelinkDialog
from .state import Fix8State, History
from . import ui_main_window

# from PySide2 import QtWidgets
# from PyQt5 import QtWidgets
import pandas as pd
import platform


class Fix8():
    def __init__(self):
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
        self.current_fixation = -1          # progress bar
        self.suggested_corrections = None

        # filed for tool undo/redo using memento pattern and state class
        self.state_history = History()

        # fields relating to AOIs
        self.aoi, self.background_color = None, None

        # fields relating to the correction algorithm
        self.algorithm = "manual"
        self.algorithm_function = None
        self.secondery_algorithm_function = None
        self.suggested_corrections, self.suggested_fixation = None, None

        # keeps track of how many times file was saved so duplicates can be saved instead of overriding previous save file
        self.timer_start = 0  # beginning time of trial
        self.metadata = ""

        self.saccade_opacity = 0.4
        self.fixation_opacity = 0.4

        # fields relating to the drag and drop system
        self.selected_fixation = None           # clicked fixation
        self.xy = None
        self.locked_x = False    

        # fields relating to aoi margin
        self.aoi_width = 7
        self.aoi_height = 4

        # fields relating to color filters
        self.fixation_color = "red"
        self.current_fixation_color = "magenta"
        self.suggested_fixation_color = "blue"
        self.remaining_fixation_color = "grey"
        self.saccade_color = "blue"
        self.aoi_color = "black"
        self.colorblind_assist_status = False
        
        # fields relating to fixation size
        self.fixation_size = 30

        # fields relating to saccade line width
        self.saccade_line_size = 1

        # create the main window
        self.fix8 = QApplication([])
        self.ui = ui_main_window.Ui_Main_Window(self)

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
        self.state_history = History()

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
        self.update_trial_statistics()


    def generate_fixations_skip(self):

        dialog = GenerateFixationsSkipDialog(self.ui)
        dialog.exec()
        approximate_letter_width, lam, k_value = dialog.getInputs()

        if not approximate_letter_width or not lam or not k_value:
            return

        # clear history for undo
        self.state_history = History()

        # get aoi from the image
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )
        
        # generate fixations
        self.original_fixations = np.array(mini_emtk.generate_fixations_left_skip(self.aoi, approximate_letter_width, lam, k_value))
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
        self.update_trial_statistics()


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
        self.state_history = History()

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
        self.update_trial_statistics()

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
        self.state_history = History()

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
        self.update_trial_statistics()

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
        line_Y = mini_emtk.find_lines_y(self.aoi)

        self.fixations = np.array(mini_emtk.error_shift(threshold, line_Y, self.fixations))

        self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(self.current_fixation, draw=True)


    def calculate_fixation_report(self):
        # get save file name
        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.json', '') + '_fixation_report.csv'
        file_name, _ = qfd.getSaveFileName(self.ui, "Save Fixations Report", default_file_name)

        if file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        # get fixations from self.eye_events dataframe, filter by eye_event == "fixation"
        fixation_data = self.eye_events[self.eye_events["eye_event"] == "fixation"]

        fixation_data.to_csv(file_name, index=False)


    def calculate_saccade_report(self):
        # get save file name
        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.json', '') + '_saccade_report.csv'
        file_name, _ = qfd.getSaveFileName(self.ui, "Save Saccades Report", default_file_name)

        if file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        # get saccades from self.eye_events dataframe, filter by eye_event == "saccade"
        saccade_data = self.eye_events[self.eye_events["eye_event"] == "saccade"]

        saccade_data.to_csv(file_name, index=False)


    def calculate_aoi_report(self):
        # open hit test dialog to get radius
        default_radius = 10
        minimum_value = 1
        maximum_value = 100
        qfd = QFileDialog()
        radius, ok = QInputDialog.getInt(self.ui, "Radius", "Enter inclusion radius for hit test (pixels)", default_radius, minimum_value, maximum_value)

        if not ok:
            self.show_error_message("Error", "No radius selected")
            return
        
        # get save file name
        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.json', '') + '_AOI_report.csv'
        file_name, _ = qfd.getSaveFileName(self.ui, "Save AOI Report", default_file_name)

        if file_name == "":
            self.show_error_message("Error", "No file selected")
            return
        
        hit_test_data = mini_emtk.hit_test(self.fixations, self.trial_path, self.aoi, radius=radius)
    
        # write hit test data to file
        hit_test_data.to_csv(file_name, index=False)
    
    def calculate_aoi_metrics(self):
        # open hit test dialog to get radius
        default_radius = 10
        minimum_value = 0
        maximum_value = 100
        qfd = QFileDialog()
        radius, ok = QInputDialog.getInt(self.ui, "Radius", "Enter inclusion radius for hit test (pixels)", default_radius, minimum_value, maximum_value)

        if not ok:
            self.show_error_message("Error", "No radius selected")
            return
        
        # get save file name
        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.json', '') + '_AOI_metrics.csv'
        file_name, _ = qfd.getSaveFileName(self.ui, "Save AOI Metrics Report", default_file_name)

        if file_name == "":
            self.show_error_message("Error", "No file selected")
            return
        
        # run hit test
        hit_test_data = mini_emtk.hit_test(self.fixations, self.trial_path, self.aoi, radius=radius)

        single_fixation_duration = []
        first_fixation_duration = []
        gaze_duration = []
        total_time = []
        fixation_count = []

        eye_metrics_data = self.aoi.copy()

        for index, row in self.aoi.iterrows():
            # get part and line from row index
            token_line_part = self.aoi.loc[index, "name"]
            line = int(token_line_part.split(" ")[1])
            part = int(token_line_part.split(" ")[3])

            # convert line and part columns in hit_test_data to int
            hit_test_data['line'] = hit_test_data['line'].astype(int)
            hit_test_data['part'] = hit_test_data['part'].astype(int)

            single_fixation_duration.append(mini_emtk.get_single_fixation_duration(hit_test_data, line, part))
            first_fixation_duration.append(mini_emtk.get_first_fixation_duration(hit_test_data, line, part))
            gaze_duration.append(mini_emtk.get_gaze_duration(hit_test_data, line, part))
            total_time.append(mini_emtk.get_total_time(hit_test_data, line, part))
            fixation_count.append(mini_emtk.get_fixation_count(hit_test_data, line, part))

        eye_metrics_data['single_fixation_duration'] = single_fixation_duration
        eye_metrics_data['first_fixation_duration'] = first_fixation_duration
        eye_metrics_data['gaze_duration'] = gaze_duration
        eye_metrics_data['total_time'] = total_time
        eye_metrics_data['fixation_count'] = fixation_count
    
        # write eye metrics data to file
        eye_metrics_data.to_csv(file_name, index=False)
        
    

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

    def json_to_csv_converter(self):
        # open json file through file dialog limit to .asc files
        qfd = QFileDialog()
        json_file = qfd.getOpenFileName(self.ui, "Select Json file", "", "Json Files (*.json)")[0]

        if json_file == "":
            self.show_error_message("Error", "No file selected")
            return

        # ask user for file name to save csv through file dialog
        qfd = QFileDialog()
        default_file_name = json_file.replace('.json', '') + '.csv'
        new_correction_file_name, _ = qfd.getSaveFileName(self.ui, "Save converted CSV file", default_file_name)
        
        if new_correction_file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        if '.csv' not in new_correction_file_name:
            new_correction_file_name += '.csv'

        self.show_error_message("Warning", "Conversion may take a while")

        # convert and save csv file
        dataframe = self.json_to_df(json_file)
        dataframe.to_csv(new_correction_file_name, index=False)

    def csv_to_json_converter(self):
        # open csv file through file dialog limit to .asc files
        qfd = QFileDialog()
        csv_file = qfd.getOpenFileName(self.ui, "Select CSV file", "", "CSV Files (*.csv)")[0]

        if csv_file == "":
            self.show_error_message("Error", "No file selected")
            return

        # ask user for file name to save csv through file dialog
        qfd = QFileDialog()
        default_file_name = csv_file.replace('.csv', '') + '.json'
        new_correction_file_name, _ = qfd.getSaveFileName(self.ui, "Save converted json file", default_file_name)
        
        if new_correction_file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        if '.json' not in new_correction_file_name:
            new_correction_file_name += '.json'

        self.show_error_message("Warning", "Conversion may take a while")

        # convert and save csv file
        dataframe = pd.read_csv(csv_file)

        # get the fixations from the csv file
        fixation_data = dataframe[dataframe["eye_event"] == "fixation"]
        fixations = []

        # get the x, y, and duration of the fixations
        for index, row in fixation_data.iterrows():
            fixations.append([row["x_cord"], row["y_cord"], row["duration"]])

        corrected_fixations = {'fixations': fixations}
        # for i in range(len(fixations)):
        #     corrected_fixations[i + 1] = fixations[i]

        with open(f"{new_correction_file_name}", "w") as f:
            json.dump(corrected_fixations, f)
        


    def eyelink_experiment_to_csv_converter(self):
        ''' convert eyelink experiment to csv files from ASCII and runtime folder '''
        dialog = EyelinkDialog(self.ui)

        # get user inputs
        ascii_file, runtime_folder, save_folder = dialog.getInputs()

        if not ascii_file or not runtime_folder or not save_folder:
            self.show_error_message("Error", "Required fields are missing")
            return

        self.show_error_message("Warning", "Conversion may take a while")
        mini_emtk.read_EyeLink1000_experiment(ascii_file, save_folder, runtime_folder=runtime_folder)

    def outlier_duration_filter(self):
        minimum_value = 0.1
        maximum_value = 5
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
        self.update_trial_statistics()


    def undo(self):
        ''' implement undo using memento pattern and state class ''' 
        if not self.state_history.is_empty():
            
            at_max = False
            # check if progressbar is at end of progressbar range
            if self.ui.progress_bar.value() == self.ui.progress_bar.maximum():
                at_max = True
             
            fix8_state = self.state_history.get_state()
            self.fixations, self.saccades, self.blinks, self.suggested_corrections, self.current_fixation, self.selected_fixation = fix8_state.get_state()

            # update progress bar
            self.ui.progress_bar.setMaximum(len(self.fixations) - 1)

            if self.current_fixation >= len(self.fixations) or at_max:
                self.current_fixation = len(self.fixations) - 1

            self.progress_bar_updated(self.current_fixation, draw=True)
            self.update_trial_statistics()


    def save_state(self):

        current_state = Fix8State(
            self.fixations,
            self.saccades,
            self.blinks,
            self.suggested_corrections,
            self.current_fixation,
            self.selected_fixation,
        )
        self.state_history.set_state(current_state)


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

        self.draw_canvas(draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.update_trial_statistics()


    def lowpass_duration_filter(self):
        minimum_value = 1
        maximum_value = 101
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

        self.draw_canvas(draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.update_trial_statistics()


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

        self.draw_canvas(draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.update_trial_statistics()


    def merge_fixations(self):
        dialog = MergeFixationsDialog(self.ui)
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

        self.draw_canvas(draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)
        self.update_trial_statistics()


    def run_correction(self):

        fixation_XY = copy.deepcopy(self.fixations)
        fixation_XY = fixation_XY[:, 0:2]
        fixation_XY = np.array(fixation_XY)
        line_Y = mini_emtk.find_lines_y(self.aoi)
        line_Y = np.array(line_Y)
        word_XY = mini_emtk.find_word_centers(self.aoi)
        word_XY = np.array(word_XY)
        self.suggested_corrections = copy.deepcopy(self.fixations)

        # run algorithm, warp uses word_xy, others use line_Y
        if "warp" not in self.algorithm:
            self.suggested_corrections[:, 0:2] = self.algorithm_function(fixation_XY, line_Y)
        
        elif "+" in self.algorithm:
            # hybrid
            self.suggested_corrections[:, 0:2] = self.algorithm_function(fixation_XY, line_Y, word_XY, self.secondery_algorithm_function)

        else:
            # warp
            self.suggested_corrections[:, 0:2] = self.algorithm_function(fixation_XY, word_XY)
        
        self.status_text = self.algorithm + " Algorithm Selected"
        self.ui.statusBar.showMessage(self.status_text)
        self.ui.relevant_buttons("algorithm_selected")


    def run_algorithm(self, algorithm_name, algorithm_function, mode, secondery_algorithm_function=None):

        self.algorithm = algorithm_name
        self.algorithm_function = algorithm_function
        self.secondery_algorithm_function = secondery_algorithm_function
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
        self.secondery_algorithm_function = None
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
            #self.selected_fixation = d.argmin()

            for fixation_index in range(len(d)): 

                duration = self.fixations[fixation_index][2]
                #epsilon = 11  # diameter range
                area = self.fixation_size * (duration / 50) ** 2

                # divide are a by pi and take the square root to get the radius
                epsilon = (area / np.pi) ** 0.5

                if epsilon < 5:
                    epsilon = 5

                if d[fixation_index] < epsilon * 0.91:
                    self.selected_fixation = fixation_index
                    return self.selected_fixation
            
            return None


    def move_left_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
            self.fixations[self.selected_fixation][0] -= 2

        self.draw_canvas()

    def move_right_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
            self.fixations[self.selected_fixation][0] += 2

        self.draw_canvas()

    def move_down_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
            self.fixations[self.selected_fixation][1] += 2

        self.draw_canvas()

    def move_up_selected_fixation(self):
        if self.selected_fixation != None:
            self.save_state()
            self.fixations[self.selected_fixation][1] -= 2

        self.draw_canvas()

    def button_press_callback(self, event):
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self.selected_fixation = self.get_selected_fixation(event)
        # print(self.selected_fixation)


    def button_release_callback(self, event):
        """when released the fixation after a move, update the fixations"""

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

        if event.button != 1:
            return
        # self.selected_fixation = None
        self.quick_draw_canvas()
        #self.draw_canvas()
        # self.ui.canvas.update()

    def motion_notify_callback(self, event):
        ''' called when fixation is being dragged '''
        
        if self.selected_fixation is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return

        x, y = event.xdata, event.ydata

        #self.xy = np.asarray(self.scatter.get_offsets())
        if self.locked_x:
            self.xy[self.selected_fixation] = np.array([self.fixations[self.selected_fixation][0], y])
        else:
            self.xy[self.selected_fixation] = np.array([x, y])
        #self.scatter.set_offsets(self.xy)
        # self.ui.canvas.draw_idle()

        self.ui.canvas.restore_region(self.ui.canvas.background)
        self.ui.canvas.ax.draw_artist(self.fixation_points)
        #self.ui.canvas.ax.draw_artist(self.saccades)
        self.ui.canvas.blit(self.ui.canvas.ax.bbox)

    def lock_x_axis(self):
        
        if self.locked_x:
            self.locked_x = False
            self.ui.lock_x_axis_action.setText("Lock X Axis")
        else:
            self.locked_x = True
            self.ui.lock_x_axis_action.setText("Unlock X Axis")

        pass


    def keyPressEvent(self, e):
        print(e.key(), 'pressed')
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
            #self.next_fixation()
            print('a pressed')
            self.assign_fixation_above()

        # z: back is 90
        if e.key() == 90 and self.ui.button_previous_fixation.isEnabled():
            self.metadata += "key,previous," + str(time.time()) + "\n"
            #self.previous_fixation()
            self.assign_fixation_below()

        # spacebar: accept and next is 32
        if e.key() == 32 and self.algorithm_function != None:
            self.metadata += "key,accept suggestion," + str(time.time()) + "\n"
            self.confirm_suggestion()

        # backspace
        if e.key() == 16777219:
            self.metadata += "key,remove fixation," + str(time.time()) + "\n"
            self.remove_fixation()


    def remove_fixation(self):
        if self.fixations is not None and self.selected_fixation is not None:
                if self.selected_fixation < len(self.fixations):
                    self.save_state()

                    self.fixations = np.delete(self.fixations, self.selected_fixation, 0)  # delete the row of selected fixation
                    self.current_fixation -= 1

                    self.ui.progress_bar.setMaximum(len(self.fixations) - 1)
                    self.progress_bar_updated(self.current_fixation, draw=False)

                    if self.suggested_corrections is not None and len(self.suggested_corrections) > 0:
                        self.suggested_corrections = np.delete(self.suggested_corrections, self.selected_fixation, 0)  # delete the row of selected fixation

                    self.selected_fixation = None

                    self.draw_canvas()
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
                    if file.endswith(".json") or file.endswith(".csv") and file.endswith("_AOI.csv") == False and file.endswith("_hit_test.csv") == False:
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
                # clear self.ui.canvas
                #self.ui.canvas.clear()
                
                self.set_canvas_image(image_file)
                #self.ui.canvas.background = self.ui.canvas.copy_from_bbox(self.ui.canvas.ax.bbox)
                self.ui.canvas.draw()
                #self.draw_canvas()
                #self.ui.canvas.draw_idle()
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
            self.ui.open_trial_action.setEnabled(True)
            self.ui.open_aoi_action.setEnabled(True)
        else:
            self.show_error_message("Image Error", "No Image Selected")

    def open_trial(self):
        qfd = QFileDialog()
        self.trial_path = qfd.getOpenFileName(self.ui, "Select Trial file", "", "CSV or Json (*.csv *.json)")[0]

        if self.trial_path == "":
            self.show_error_message("Error", "No file selected")
            return

        if self.image_file_path == "":
            self.show_error_message("Image Error", "No Image Selected")
        
        # reset times saved if a DIFFERENT trial was selected
        self.trial_name = self.trial_path.split("/")[-1]
        
        if self.trial_path.endswith(".json"):
            ok = self.read_json_fixations(self.trial_path)
            if not ok:
                self.trial_name = None
                self.trial_path = None
                return

        elif self.trial_path.endswith(".csv"):
            ok = self.read_csv_fixations(self.trial_path)
            if not ok:
                self.trial_name = None
                self.trial_path = None
                return

        # clear history for undo
        self.state_history = History()

        self.suggested_corrections = None
        self.current_fixation = (len(self.original_fixations)-1)  

        # set the progress bar to the amount of fixations found
        self.ui.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.timer_start = time.time()
        self.metadata = "started, open trial," + str(time.time()) + "\n"

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
        self.draw_canvas(draw_all=True)

        self.status_text = self.trial_name + " Opened (Default: Manual Mode)"
        self.ui.statusBar.showMessage(self.status_text)
        self.update_trial_statistics()


    def update_trial_statistics(self):

        # eye events has a timestamp column, find the duration of the trial by subtracting the first and last timestamp
        if self.eye_events is not None and 'time_stamp' in self.eye_events.columns:
            duration = self.eye_events.iloc[-1]["time_stamp"] - self.eye_events.iloc[0]["time_stamp"]
            self.ui.statistics_table.setItem(0, 1, QTableWidgetItem(str(duration//1000) + " sec"))
        else:
            self.ui.statistics_table.setItem(0, 1, QTableWidgetItem("-"))

        # get maximum fixation duration
        if self.fixations is not None:
            self.ui.statistics_table.setItem(1, 1, QTableWidgetItem(str(np.max(self.fixations[:, 2]))))
        else:
            self.ui.statistics_table.setItem(1, 1, QTableWidgetItem("-"))

        # get minimum fixation duration
        if self.fixations is not None:
            self.ui.statistics_table.setItem(2, 1, QTableWidgetItem(str(np.min(self.fixations[:, 2]))))
        else:
            self.ui.statistics_table.setItem(2, 1, QTableWidgetItem("-"))

        # get the number of aois
        if self.aoi is not None:
            self.ui.statistics_table.setItem(3, 1, QTableWidgetItem(str(len(self.aoi))))
        else:
            self.ui.statistics_table.setItem(3, 1, QTableWidgetItem("-"))

        # if self.current_fixation is not None:
        #     self.ui.statistics_table.setItem(5, 1, QTableWidgetItem(str(self.fixations[self.current_fixation])))

        #self.ui.statistics_table.setHidden(False)



    def open_aoi(self):
        qfd = QFileDialog()
        aoi_file = qfd.getOpenFileName(self.ui, "Select AOI", "", "AOI Files (*.csv)")[0]

        
        if aoi_file == "":
            self.show_error_message("Error", "No aoi file selected")
            return

        if self.image_file_path == "":
            self.show_error_message("Image Error", "No Image Selected")

        # open aoi file
        self.aoi = pd.read_csv(aoi_file)
        self.save_state()

        # draw canvas
        self.draw_canvas()

        self.status_text = self.trial_name + " Opened (Default: Manual Mode)"
        self.ui.statusBar.showMessage(self.status_text)
        self.update_trial_statistics()



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
            ok = self.read_json_fixations(self.trial_path)
            if not ok:
                self.trial_name = None
                self.trial_path = None
                return

        elif self.trial_path.endswith(".csv"):
            ok = self.read_csv_fixations(self.trial_path)
            if not ok:
                self.trial_name = None
                self.trial_path = None
                return

        # clear history for undo
        self.state_history = History()

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
        self.draw_canvas(draw_all=True)

        self.status_text = self.trial_name + " Opened (Default: Manual Mode)"
        self.ui.statusBar.showMessage(self.status_text)
        self.update_trial_statistics()


    def find_aoi(self):
        """find the areas of interest (aoi) for the selected stimulus"""
        if self.image_file_path != "":
            self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
                self.image_file_path,
                margin_height=self.aoi_height,
                margin_width=self.aoi_width,
            )

    def json_to_df(self, trial_path):
        x_cord = []
        y_cord = []
        duration = []

        with open(trial_path, "r") as trial:

            trial_data = json.load(trial)

            if 'fixations' not in trial_data.keys():
                # old JSON format
                for key in trial_data:
                    x_cord.append(trial_data[key][0])
                    y_cord.append(trial_data[key][1])
                    duration.append(trial_data[key][2])
            else:
                # new JSON format
                for fixation in trial_data["fixations"]:
                    x_cord.append(fixation[0])
                    y_cord.append(fixation[1])
                    duration.append(fixation[2])

        # create an empty dataframe
        eye_events = pd.DataFrame(columns=["x_cord", "y_cord", "duration"])
        eye_events["x_cord"] = x_cord
        eye_events["y_cord"] = y_cord
        eye_events["duration"] = duration
        eye_events["eye_event"] = "fixation"

        return eye_events
    
    def read_json_fixations(self, trial_path):
        """find all the fixations of the trial that was double clicked
        parameters:
        trial_path - the trial file path of the trial clicked on"""

        try:
            self.eye_events = self.json_to_df(trial_path)
            self.original_fixations = self.eye_events.drop(columns=["eye_event"])
            self.original_fixations = np.array(self.original_fixations)
        except:
            self.show_error_message("Trial File Error", "Problem reading CSV File")     
            return False
        
        self.ui.relevant_buttons("trial_clicked")
        return True


    def read_csv_fixations(self, trial_path):
        """find all the fixations of the trial that was double clicked
        parameters:
        trial_path - the trial file path of the trial clicked on"""
        self.original_fixations = []

        try:
            # open the csv file with pandas
            self.eye_events = pd.read_csv(trial_path)
            
            # get the fixations from the csv file
            fixations = self.eye_events[self.eye_events["eye_event"] == "fixation"]

        except:
            self.show_error_message("Trial File Error", "Problem reading CSV File")     
            return False

        # get the x, y, and duration of the fixations
        for index, row in fixations.iterrows():
            self.original_fixations.append([row["x_cord"], row["y_cord"], row["duration"]])

        self.original_fixations = np.array(self.original_fixations)
        self.ui.relevant_buttons("trial_clicked")
        return True
    

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

    
    def clear_aois(self):
        """clear the areas of interest from the canvas"""
        if self.ui.canvas.ax.patches != None:
            self.ui.canvas.ax.patches.clear()

            for patch in self.ui.canvas.ax.patches:
                patch.remove()
            self.ui.canvas.draw()



    # draw fixations2 is similar to the normal draw fixations, excpet this one only draws to the current fixation
    def draw_canvas(self, draw_all=False):

        if self.fixations is None:
            return

        if draw_all:
            x = self.fixations[:, 0]
            y = self.fixations[:, 1]
            duration = self.fixations[:, 2]
        else:
            x = self.fixations[0 : self.current_fixation + 1, 0]
            y = self.fixations[0 : self.current_fixation + 1, 1]
            duration = self.fixations[0 : self.current_fixation + 1, 2]

        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()
        self.clear_aois()
        

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

        if self.ui.checkbox_show_saccades.isCheckable():
            if self.ui.checkbox_show_saccades.isChecked():
                self.saccade_lines = self.ui.canvas.ax.plot(
                    x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=self.saccade_line_size
                )

        # draw suggested fixation in blue
        if self.ui.checkbox_show_suggestion.isChecked():
            if self.current_fixation < len(self.suggested_corrections):
                x = self.suggested_corrections[self.current_fixation][0]
                y = self.suggested_corrections[self.current_fixation][1]
                duration = self.fixations[self.current_fixation][2]

                self.suggested_fixation = self.ui.canvas.ax.scatter(
                    x,
                    y,
                    s=self.fixation_size * (duration / 50) ** 1.8,
                    alpha=self.fixation_opacity,
                    c=self.suggested_fixation_color,
                )

        # draw remaining fixations in grey
        if self.ui.checkbox_show_all_fixations.isChecked():
            if self.current_fixation < len(self.fixations):
                x = self.fixations[self.current_fixation + 1:, 0]
                y = self.fixations[self.current_fixation + 1:, 1]
                duration = self.fixations[self.current_fixation + 1:, 2]

                self.remaining_fixations = self.ui.canvas.ax.scatter(
                    x,
                    y,
                    s=self.fixation_size * (duration / 50) ** 1.8,
                    alpha=self.fixation_opacity,
                    c=self.remaining_fixation_color,
                )

        # draw aois
        if self.ui.checkbox_show_aoi.isChecked():
            color = self.aoi_color 


            for row in self.aoi.iterrows():
                xcord = row[1]["x"]
                ycord = row[1]["y"]
                height = row[1]["height"]
                width = row[1]["width"]
                aoi_box = self.ui.canvas.ax.add_patch(
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


    def quick_draw_canvas(self, all_fixations=False):

        # TODO: temporary fix for the all_fixations bug, this should be fixed
        if all_fixations == 2:
            all_fixations = False

        if self.fixations is None:
            return

        if self.ui.canvas.background is None:
            self.ui.canvas.background = self.ui.canvas.copy_from_bbox(self.ui.canvas.ax.bbox)
            
        self.ui.canvas.restore_region(self.ui.canvas.background)

        # figure out which fixations to draw
        if all_fixations:
            x = self.fixations[:, 0]
            y = self.fixations[:, 1]
            duration = self.fixations[:, 2]
        else:
            x = self.fixations[0 : self.current_fixation + 1, 0]
            y = self.fixations[0 : self.current_fixation + 1, 1]
            duration = self.fixations[0 : self.current_fixation + 1, 2]


        # draw fixations
        if self.ui.checkbox_show_fixations.isChecked():
            # generate colors for fixations
            list_colors = [self.fixation_color] * (len(x) - 1)
            colors = np.array(list_colors + [self.current_fixation_color])

            # draw fixations
            self.fixation_points = self.ui.canvas.ax.scatter(
                x,
                y,
                s=self.fixation_size * (duration / 50) ** 1.8,
                alpha=self.fixation_opacity,
                c=colors,
            )
            self.ui.canvas.ax.draw_artist(self.fixation_points)

        # draw saccades
        if self.ui.checkbox_show_saccades.isChecked():
            self.saccade_lines = self.ui.canvas.ax.plot(
                x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=self.saccade_line_size
            )
            self.ui.canvas.ax.draw_artist(self.saccade_lines[0])

        # draw suggested fixation in blue (or selected color)
        if self.ui.checkbox_show_suggestion.isChecked():
            if self.current_fixation < len(self.suggested_corrections):
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

        # draw remaining fixations and saccades in grey
        if self.ui.checkbox_show_all_fixations.isChecked():
            if self.current_fixation < len(self.fixations):
                x = self.fixations[self.current_fixation + 1:, 0]
                y = self.fixations[self.current_fixation + 1:, 1]
                duration = self.fixations[self.current_fixation + 1:, 2]

                self.remaining_fixations = self.ui.canvas.ax.scatter(
                    x,
                    y,
                    s=self.fixation_size * (duration / 50) ** 1.8,
                    alpha=self.fixation_opacity,
                    c=self.remaining_fixation_color,
                )
                self.ui.canvas.ax.draw_artist(self.remaining_fixations)


                # draw remaining saccades
                # x = self.fixations[self.current_fixation:, 0]
                # y = self.fixations[self.current_fixation:, 1] 
                saccade_lines = self.ui.canvas.ax.plot(
                x, y, alpha=self.saccade_opacity, c=self.remaining_fixation_color, linewidth=self.saccade_line_size
                )
                self.ui.canvas.ax.draw_artist(saccade_lines[0])

        # draw aois
        if self.ui.checkbox_show_aoi.isChecked():
            for row in self.aoi.iterrows():

                xcord = row[1]["x"]
                ycord = row[1]["y"]
                height = row[1]["height"]
                width = row[1]["width"]
                
                aoi_box = self.ui.canvas.ax.add_patch(
                    Rectangle(
                        (xcord, ycord),
                        width - 1,
                        height - 1,
                        linewidth=0.8,
                        edgecolor=self.aoi_color,
                        facecolor="none",
                        alpha=0.65,
                    )
                )
                self.ui.canvas.ax.draw_artist(aoi_box)

        self.ui.canvas.blit(self.ui.canvas.ax.bbox)


    def correct_all_fixations(self):
        """if the user presses the correct all fixations button,
        make the corrected fixations the suggested ones from the correction algorithm"""
        if self.suggested_corrections is not None:
            self.save_state()
            self.fixations = copy.deepcopy(self.suggested_corrections)
            #self.draw_canvas()
            self.quick_draw_canvas(all_fixations=True)

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

        self.progress_bar_updated(self.current_fixation, draw=False)



    def next_fixation(self):
        if self.current_fixation == -1 and self.original_fixations == None:
            # Tour
            self.set_canvas_image('src/.images/fix8-tour-1.png')
            self.ui.canvas.draw()
            self.ui.button_next_fixation.setEnabled(False)
            return
        
        if self.current_fixation != len(self.fixations) - 1:
            self.current_fixation += 1

        self.progress_bar_updated(self.current_fixation, draw=False)


    def assign_fixation_above(self):
        """assign the fixation to the closest line above the current fixation"""

        # find the closest line above the current fixation
        if self.aoi is not None:
            
            line_Y = mini_emtk.find_lines_y(self.aoi)

            distances = []
            for line in line_Y:
                distances.append(self.fixations[self.current_fixation][1] - line)

            closest_line = line_Y[0]

            smallest_distance = 9999999
            for index, distance in enumerate(distances):
                if distance < smallest_distance and line_Y[index] < self.fixations[self.current_fixation][1]:
                    smallest_distance = distance
                    closest_line = line_Y[index]

            self.fixations[self.current_fixation][1] = closest_line
            self.quick_draw_canvas(all_fixations=False)
            self.next_fixation()
        

    def assign_fixation_below(self):
        """assign the fixation to the closest line below the current fixation"""

        # find the closest line below the current fixation
        if self.aoi is not None:
            line_Y = mini_emtk.find_lines_y(self.aoi)

            distances = []
            for line in line_Y:
                distances.append(abs(self.fixations[self.current_fixation][1] - line))

            closest_line = line_Y[-1]

            smallest_distance = 9999999
            for index, distance in enumerate(distances):
                if distance < smallest_distance and line_Y[index] > self.fixations[self.current_fixation][1]:
                    smallest_distance = distance
                    closest_line = line_Y[index]

            self.fixations[self.current_fixation][1] = closest_line
            self.quick_draw_canvas(all_fixations=False)
            self.next_fixation()


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


    def save_corrections_json(self):
        """ save correction to a json file and metadata to csv file """

        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.json', '') + '_CORRECTED.json'
        new_correction_file_name, _ = qfd.getSaveFileName(self.ui, "Save correction", default_file_name)

        if new_correction_file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        if '.json' not in new_correction_file_name:
            new_correction_file_name += '.json'

        if len(self.fixations) > 0:
            list = self.fixations.tolist()

            corrected_fixations = {'fixations': []}
            for i in range(len(self.fixations)):
                corrected_fixations['fixations'].append(list[i])

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

            #self.save_metadata_file(new_correction_file_name)

            self.status_text = "Corrections Saved to" + " " + new_correction_file_name
            self.ui.statusBar.showMessage(self.status_text)

        else:
            self.show_error_message("Save Error", "No Corrections Made")

    def save_corrections_csv(self):
        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.csv', '') + '_CORRECTED.csv'
        new_correction_file_name, _ = qfd.getSaveFileName(self.ui, "Save correction", default_file_name)

        if new_correction_file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        if '.csv' not in new_correction_file_name:
            new_correction_file_name += '.csv'

        if len(self.fixations) > 0:

            self.eye_events.to_csv(new_correction_file_name, index=False)
                
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

            #self.save_metadata_file(new_correction_file_name)

            self.status_text = "Corrections Saved to" + " " + new_correction_file_name
            self.ui.statusBar.showMessage(self.status_text)

        else:
            self.show_error_message("Save Error", "No Corrections Made")

    def save_aoi_csv(self):
        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.csv', '').replace('.json', '') + '_AOI.csv'
        new_aoi_file_name, _ = qfd.getSaveFileName(self.ui, "Save AOI", default_file_name)
        
        if new_aoi_file_name == "":
            self.show_error_message("Error", "No file selected")
            return

        if '.csv' not in new_aoi_file_name:
            new_aoi_file_name += '.csv'

        if len(self.fixations) > 0:

            self.aoi.to_csv(new_aoi_file_name, index=False)
            self.status_text = "AOI Saved to" + " " + new_aoi_file_name
            self.ui.statusBar.showMessage(self.status_text)

        else:
            self.show_error_message("Save Error", "No AOI Found")

    
    def save_image(self):
        # save image with png, jpg, or jpeg, default to png 
        # dpi is set to 300 for high quality
        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.csv', '').replace('.json', '') + '_FIX8.png'
        new_image_file_name, _ = qfd.getSaveFileName(self.ui, "Save Image", default_file_name)

        if new_image_file_name == "":
            self.show_error_message("Error", "No file selected")
            return
        
        if ('.png' not in new_image_file_name 
            and '.jpg' not in new_image_file_name 
            and '.jpeg' not in new_image_file_name
            and '.svg' not in new_image_file_name
            ):
            new_image_file_name += '.png'

        # if name includes svg, save as svg
        if '.svg' in new_image_file_name:
            self.ui.canvas.ax.figure.savefig(new_image_file_name, dpi=300, format='svg', transparent=True, bbox_inches='tight')
        else:
            self.ui.canvas.ax.figure.savefig(new_image_file_name, dpi=300, transparent=True, bbox_inches='tight')

    def progress_bar_updated(self, value, draw=True):
        # update the current suggested correction to the last fixation of the list
        self.current_fixation = value

        # update current suggestion to the progress bar
        if self.current_fixation is not None:
            self.ui.label_progress.setText(
                f"{self.current_fixation}/{len(self.fixations)-1}"
            )
            self.ui.progress_bar.setValue(self.current_fixation)

        if draw:

            if self.ui.canvas.background is None:
                self.draw_canvas()
                return

            self.quick_draw_canvas(all_fixations=False)

    def aoi_height_changed(self, value):
        self.aoi_height = value
        self.find_aoi()
        self.quick_draw_canvas()

    def aoi_width_changed(self, value):
        self.aoi_width = value
        self.find_aoi()
        self.quick_draw_canvas()

    def select_fixation_color(self):
        color = QColorDialog.getColor(initial=QColor(self.fixation_color))
        if color.isValid():
            self.fixation_color = str(color.name())
        else:
            self.fixation_color = "red"

        self.quick_draw_canvas(all_fixations=False)

    def select_current_fixation_color(self):
        color = QColorDialog.getColor(initial=QColor(self.current_fixation_color))
        if color.isValid():
            self.current_fixation_color = str(color.name())
        else:
            self.current_fixation_color = "magenta"

        self.quick_draw_canvas(all_fixations=False)

    def select_suggested_fixation_color(self):
        color = QColorDialog.getColor(initial=QColor(self.suggested_fixation_color))
        if color.isValid():
            self.suggested_fixation_color = str(color.name())
        else:
            self.suggested_fixation_color = "blue"

        self.quick_draw_canvas(all_fixations=False)

    def select_remaining_fixation_color(self):
        color = QColorDialog.getColor(initial=QColor(self.remaining_fixation_color))
        if color.isValid():
            self.remaining_fixation_color = str(color.name())
        else:
            self.remaining_fixation_color = "grey"

        self.quick_draw_canvas(all_fixations=False)

    def select_saccade_color(self):
        color = QColorDialog.getColor(initial=QColor(self.saccade_color))
        if color.isValid():
            self.saccade_color = str(color.name())
        else:
            self.saccade_color = "blue"

        self.quick_draw_canvas(all_fixations=False)

    def select_aoi_color(self):
        color = QColorDialog.getColor(initial=QColor(self.aoi_color))
        if color.isValid():
            self.aoi_color = str(color.name())
        else:
            self.aoi_color = "black"

        self.quick_draw_canvas(all_fixations=False)

    def colorblind_assist(self):
        if self.colorblind_assist_status == False:
            self.fixation_color = "#00ff00"
            self.current_fixation_color = "#ff00ff"
            self.saccade_color = "#0000ff"
            self.aoi_color = "black"
            self.colorblind_assist_status = True
            self.quick_draw_canvas(all_fixations=False)
        else:
            self.fixation_color = "red"
            self.saccade_color = "blue"
            self.aoi_color = "black"
            self.colorblind_assist_status = False
            self.quick_draw_canvas(all_fixations=False)

    def saccade_opacity_changed(self, value):
        self.saccade_opacity = float(value / 10)
        self.quick_draw_canvas(all_fixations=False)

    def saccade_width_changed(self, value):
        self.saccade_line_size = value
        self.draw_canvas()

    def fixation_opacity_changed(self, value):
        self.fixation_opacity = float(value / 10)
        self.quick_draw_canvas(all_fixations=False)

    def fixation_size_changed(self, value):
        self.fixation_size = value * 6
        self.draw_canvas()
    
def main():
    if platform.system() == "Windows":
        import ctypes
        myappid = 'ThisCanBeAnything' # arbitrary string

        # This helps Windows manage and group windows of this application together
        # And helps us maintain the taskbar icon
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    window = Fix8()
    window.fix8.exec_()

if __name__ == "__main__":
    main()