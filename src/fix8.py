# Fix8
#
# Authors: Naser Al Madi <nsalmadi@colby.edu>
#          Brett Torra
#          Agnes Li
#          Najam Tariq
#          Ricky Peng
#
#
# URL: <https://github.com/nalmadi/fix8>
#
#
# The algorithms were implemented by:
#          Jon Carr
# URL: <https://github.com/jwcarr/drift>
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
    QComboBox,
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
    QButtonGroup,
    QLineEdit,
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

from PIL import Image
import pandas as pd

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
        self.save_correction_action = QAction(
            QIcon("./.images/save.png"), "Save Correction", self
        )

        self.next_fixation_action = QAction("Next Fixation", self)
        self.previous_fixation_action = QAction("Previous Fixation", self)
        self.accept_and_next_action = QAction("Accept suggestion and next", self)
        self.delete_fixation_action = QAction("Delete Fixation", self)

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
        
        self.warp_auto_action.triggered.connect(self.warp_auto)
        self.warp_semi_action.triggered.connect(self.warp_semi)
        self.manual_correction_action.triggered.connect(self.manual_correction)

        # add actions to menu
        self.file_menu.addAction(self.new_file_action)
        self.file_menu.addAction(self.save_correction_action)

        self.edit_menu.addAction(self.next_fixation_action)
        self.edit_menu.addAction(self.previous_fixation_action)
        self.edit_menu.addAction(self.accept_and_next_action)
        self.edit_menu.addAction(self.delete_fixation_action)

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
        self.suggested_corrections, self.single_suggestion = (
            None,
            None,
        )  # single suggestion is the current suggestion

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
        self.saccade_color = "blue"
        self.aoi_color = "yellow"
        self.colorblind_assist_status = False

        # fields related to duration filters
        self.lesser_value = 0
        self.greater_value = 0

    def warp_auto(self):
        fixation_XY = copy.deepcopy(self.fixations)
        fixation_XY = fixation_XY[:, 0:2]
        fixation_XY = np.array(fixation_XY)
        line_Y = self.find_lines_y(self.aoi)
        line_Y = np.array(line_Y)
        word_XY = self.find_word_centers(self.aoi)
        word_XY = np.array(word_XY)

        self.suggested_corrections = copy.deepcopy(self.fixations)

        # select warp as an algorithm
        self.suggested_corrections[:, 0:2] = da.warp(fixation_XY, word_XY)
        self.status_text = self.algorithm + " Algorithm Selected"
        self.statusBar.showMessage(self.status_text)
        self.relevant_buttons("algorithm_selected")

        # correct all
        self.correct_all_fixations()

        # update progress bar to end
        self.progress_bar.setValue(self.progress_bar.maximum())

    def warp_semi(self):
        fixation_XY = copy.deepcopy(self.fixations)
        fixation_XY = fixation_XY[:, 0:2]
        fixation_XY = np.array(fixation_XY)
        line_Y = self.find_lines_y(self.aoi)
        line_Y = np.array(line_Y)
        word_XY = self.find_word_centers(self.aoi)
        word_XY = np.array(word_XY)

        self.suggested_corrections = copy.deepcopy(self.fixations)

        # select warp as an algorithm
        self.suggested_corrections[:, 0:2] = da.warp(fixation_XY, word_XY)
        self.status_text = self.algorithm + " Algorithm Selected"
        self.statusBar.showMessage(self.status_text)
        self.relevant_buttons("algorithm_selected")

        # show suggestion
        self.checkbox_show_suggestion.setChecked(True)

        # update progress bar to end
        self.progress_bar.setValue(self.progress_bar.minimum())

    def manual_correction(self):

        self.suggested_corrections = copy.deepcopy(self.fixations)
        self.checkbox_show_suggestion.setEnabled(False)

        # show suggestion
        self.checkbox_show_suggestion.setChecked(False)

    """get the selected fixation that the user picks, with the selection inside a specific diameter range (epsilon),
    selected_fixation is an index, not the actual scatter point"""

    def get_selected_fixation(self, event):
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

    """when released the fixation, update the corrected fixations"""

    def button_release_callback(self, event):
        if self.selected_fixation is not None:
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

            self.fixations[self.selected_fixation][0] = self.xy[self.selected_fixation][
                0
            ]
            self.fixations[self.selected_fixation][1] = self.xy[self.selected_fixation][
                1
            ]

            if self.algorithm != "manual" and self.algorithm is not None:
                # run correction
                fixation_XY = np.array([self.fixations[self.selected_fixation]])
                fixation_XY = fixation_XY[:, 0:2]
                line_Y = self.find_lines_y(self.aoi)
                line_Y = np.array(line_Y)

                word_XY = self.find_word_centers(self.aoi)
                word_XY = np.array(word_XY)

                if self.algorithm == "attach":
                    updated_correction = da.attach(copy.deepcopy(fixation_XY), line_Y)[
                        0
                    ]
                elif self.algorithm == "chain":
                    updated_correction = da.chain(copy.deepcopy(fixation_XY), line_Y)[0]
                # elif self.algorithm == 'cluster':
                #     updated_correction = da.cluster(copy.deepcopy(fixation_XY), line_Y)[0]
                elif self.algorithm == "merge":
                    self.suupdated_correction = da.merge(
                        copy.deepcopy(fixation_XY), line_Y
                    )[0]
                elif self.algorithm == "regress":
                    updated_correction = da.regress(copy.deepcopy(fixation_XY), line_Y)[
                        0
                    ]
                elif self.algorithm == "segment":
                    updated_correction = da.segment(copy.deepcopy(fixation_XY), line_Y)[
                        0
                    ]
                # elif self.algorithm == 'split':
                #     updated_correction = da.split(copy.deepcopy(fixation_XY), line_Y)[0]
                elif self.algorithm == "stretch":
                    updated_correction = da.stretch(copy.deepcopy(fixation_XY), line_Y)[
                        0
                    ]
                elif self.algorithm == "warp":
                    updated_correction = da.warp(copy.deepcopy(fixation_XY), word_XY)[0]

                self.suggested_corrections[self.selected_fixation, :2] = updated_correction
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
        if e.key() == 16777251 and self.button_confirm_suggestion.isEnabled():
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

    """open trial folder, display it to trial list window with list of JSON trials"""

    def open_trial_folder(self):
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

    ######################## from EMTK #################################

    def find_background_color(self, img):
        """Private function that identifies the background color of the image
        Parameters
        ----------
        img : PIL.Image
            a PIL (pillow fork) Image object
        Returns
        -------
        str
            the color of the background of the image
        """

        img = img.convert("L")  # Convert to grayscale
        threshold = 80
        img = img.point(
            lambda x: 0 if x < threshold else 255, "1"
        )  # Apply threshold and convert to black and white

        width, height = img.size

        color_result = []
        box_size = min(width, height) // 20

        # Move a tiny rectangle box to obtain most common color
        for x, y in zip(range(0, width, box_size), range(0, height, box_size)):
            box = (x, y, x + box_size, y + box_size)
            minimum, maximum = img.crop(box).getextrema()
            color_result.append(minimum)
            color_result.append(maximum)

        # Analyze and determine the background color
        if color_result.count(255) > color_result.count(0):
            bg_color = "white"
        else:
            bg_color = "black"

        return bg_color

    def EMTK_find_aoi(
        self,
        image=None,
        image_path=None,
        img=None,
        level="sub-line",
        margin_height=4,
        margin_width=7,
    ):
        """Find Area of Interest in the given image and store the aoi attributes in a Pandas Dataframe
        Parameters
        ----------
        image : str
            filename for the image, e.g. "vehicle_java.jpg"
        image_path : str
            path for all images, e.g. "emip_dataset/stimuli/"
        img : PIL.Image, optional
            PIL.Image object if user chooses to input an PIL image object
        level : str, optional
            level of detection in AOIs, "line" for each line as an AOI or "sub-line" for each token as an AOI
        margin_height : int, optional
            marginal height when finding AOIs, use smaller number for tight text layout
        margin_width : int, optional
            marginal width when finding AOIs, use smaller number for tight text layout
        Returns
        -------
        pandas.DataFrame
            a pandas DataFrame of area of interest detected by the method
        """

        if img is None:
            if image is None or image_path is None:
                return
            # img = Image.open(image_path + image).convert('1')
            img = Image.open(image_path + image)
            img = img.convert("L")  # Convert to grayscale
            threshold = 80
            img = img.point(
                lambda x: 0 if x < threshold else 255, "1"
            )  # Apply threshold and convert to black and white

        else:
            img = img.convert("L")  # Convert to grayscale
            threshold = 80
            img = img.point(
                lambda x: 0 if x < threshold else 255, "1"
            )  # Apply threshold and convert to black and white

        width, height = img.size

        # Detect the background color
        bg_color = self.find_background_color(img)
        # print("bg_color: ", bg_color)

        left, right = 0, width

        vertical_result, upper_bounds, lower_bounds = [], [], []

        # Move the detecting rectangle from the top to the bottom of the image
        for upper in range(height - margin_height):
            lower = upper + margin_height

            box = (left, upper, right, lower)
            minimum, maximum = img.crop(box).getextrema()

            if upper > 1:
                if bg_color == "black":
                    if vertical_result[-1][3] == 0 and maximum == 255:
                        # Rectangle detects white color for the first time in a while -> Start of one line
                        upper_bounds.append(upper)
                    if vertical_result[-1][3] == 255 and maximum == 0:
                        # Rectangle detects black color for the first time in a while -> End of one line
                        lower_bounds.append(lower)
                elif bg_color == "white":
                    if vertical_result[-1][2] == 255 and minimum == 0:
                        # Rectangle detects black color for the first time in a while -> Start of one line
                        upper_bounds.append(upper)
                    if vertical_result[-1][2] == 0 and minimum == 255:
                        # Rectangle detects white color for the first time in a while -> End of one line
                        lower_bounds.append(lower)

            # Storing all detection result
            vertical_result.append([upper, lower, minimum, maximum])

        final_result = []

        line_count = 1

        # Iterate through each line of code from detection
        for upper_bound, lower_bound in list(zip(upper_bounds, lower_bounds)):
            # Reset all temporary result for the next line
            horizontal_result, left_bounds, right_bounds = [], [], []

            # Move the detecting rectangle from the left to the right of the image
            for left in range(width - margin_width):
                right = left + margin_width

                box = (left, upper_bound, right, lower_bound)
                minimum, maximum = img.crop(box).getextrema()

                if left > 1:
                    if bg_color == "black":
                        if horizontal_result[-1][3] == 0 and maximum == 255:
                            # Rectangle detects black color for the first time in a while -> Start of one word
                            left_bounds.append(left)
                        if horizontal_result[-1][3] == 255 and maximum == 0:
                            # Rectangle detects white color for the first time in a while -> End of one word
                            right_bounds.append(right)
                    elif bg_color == "white":
                        if horizontal_result[-1][2] == 255 and minimum == 0:
                            # Rectangle detects black color for the first time in a while -> Start of one word
                            left_bounds.append(left)
                        if horizontal_result[-1][2] == 0 and minimum == 255:
                            # Rectangle detects white color for the first time in a while -> End of one word
                            right_bounds.append(right)

                # Storing all detection result
                horizontal_result.append([left, right, minimum, maximum])

            if level == "sub-line":
                part_count = 1

                for left, right in list(zip(left_bounds, right_bounds)):
                    final_result.append(
                        [
                            "sub-line",
                            f"line {line_count} part {part_count}",
                            left,
                            upper_bound,
                            right,
                            lower_bound,
                        ]
                    )
                    part_count += 1

            elif level == "line":
                final_result.append(
                    [
                        "line",
                        f"line {line_count}",
                        left_bounds[0],
                        upper_bound,
                        right_bounds[-1],
                        lower_bound,
                    ]
                )

            line_count += 1

        # Format pandas dataframe
        columns = ["kind", "name", "x", "y", "width", "height", "image"]
        aoi = pd.DataFrame(columns=columns)

        for entry in final_result:
            kind, name, x, y, x0, y0 = entry
            width = x0 - x
            height = y0 - y
            image = image

            # For better visualization
            x += margin_width / 2
            width -= margin_width

            value = [kind, name, x, y, width, height, image]
            dic = dict(zip(columns, value))

            aoi = aoi.append(dic, ignore_index=True)

        return aoi, bg_color

    ######################## end from EMTK #################################

    """find the areas of interest (aoi) for the selected stimulus"""

    def find_aoi(self):
        if self.file_path != "":
            self.aoi, self.background_color = self.EMTK_find_aoi(
                self.file_name,
                self.file_path.replace(self.file_name, ""),
                margin_height=self.aoi_height,
                margin_width=self.aoi_width,
            )

    """draw the found aois to the canvas"""

    def draw_aoi(self):
        color = self.aoi_color if self.background_color == "black" else "black"
        self.patches = []

        for row in self.aoi.iterrows():
            # ---
            """Credit: Dr. Naser Al Madi and Ricky Peng"""
            xcord = row[1]["x"]
            ycord = row[1]["y"]
            height = row[1]["height"]
            width = row[1]["width"]
            # ---

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

    """clear the aois from the canvas"""

    def clear_aoi(self):
        if self.patches is not None:
            for patch in self.patches:
                patch.remove()
            self.canvas.draw()

    """when the show aoi button is pressed, show or hide aois based on checkbox"""

    def show_aoi(self, state):
        if self.checkbox_show_aoi.isCheckable():
            if state == Qt.Checked:
                self.draw_aoi()
            elif state == Qt.Unchecked:
                self.clear_aoi()

    """find all the fixations of the trial that was double clicked
        parameters:
        trial_path - the trial file path of the trial clicked on"""

    def find_fixations(self, trial_path):
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

    """Credit: Dr. Naser Al Madi and Ricky Peng"""

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

    """draw the fixations to the canvas
        parameters:
        fixations - 0 is default since the corrected fixations are the main thing to be shown,
        1 the original fixations is manually chosen (not currently needed as this isn't in option in algorithms)"""

    def draw_fixations(self, fixations=0):
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

    """if the user clicks the show fixations checkbox, show or hide the fixations
        parameters:
        state - the checkbox being checked or unchecked"""

    def show_fixations(self, state):
        if self.folder_path != "":
            if self.checkbox_show_fixations.isCheckable():
                if state == Qt.Checked:
                    self.draw_fixations()
                elif state == Qt.Unchecked:
                    self.clear_fixations()

    """if the user clicks saccades, show or hide them"""

    def show_saccades(self, state):
        if self.folder_path != "":
            if self.checkbox_show_saccades.isCheckable():
                if state == Qt.Checked:
                    self.draw_saccades()
                elif state == Qt.Unchecked:
                    self.clear_saccades()

    """draw the scatter plot to the canvas"""

    def draw_saccades(self):
        fixations = self.fixations
        x = fixations[0 : self.current_fixation + 1, 0]
        y = fixations[0 : self.current_fixation + 1, 1]
        duration = fixations[0 : self.current_fixation + 1, 2]
        self.saccades = self.canvas.ax.plot(
            x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1
        )
        self.canvas.draw()

    """remove the saccades from the canvas (this does not erase the data, just visuals)"""

    def clear_saccades(self):
        if self.saccades != None:
            self.canvas.ax.lines.clear()  # <-- if this line crashes the tool

            # for line in self.canvas.ax.lines:  #<-- use this instead
            #    line.remove()

            self.saccades = None
            # self.canvas.draw()

    """clear the fixations from the canvas"""

    def clear_fixations(self):
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
                colors = np.array(list_colors + [self.aoi_color])
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

            self.single_suggestion = self.canvas.ax.scatter(
                x,
                y,
                s=30 * (duration / 50) ** 1.8,
                alpha=self.fixation_opacity,
                c="blue",
            )

        # draw whatever was updated
        self.canvas.draw()

    """when the user selects an algorithm from the drop down menu,
        make it the current algorithm to use for automated and semi automated use
        parameters:
        algorithm - the selected correction algorithm"""

    def get_algorithm_picked(self, algorithm):
        self.algorithm = algorithm
        self.algorithm = self.algorithm.lower()

        # write metadata
        self.metadata += (
            "selected,algorithm " + str(algorithm) + "," + str(time.time()) + "\n"
        )

        # run correction
        fixation_XY = copy.deepcopy(self.fixations)
        fixation_XY = fixation_XY[:, 0:2]
        fixation_XY = np.array(fixation_XY)
        line_Y = self.find_lines_y(self.aoi)
        line_Y = np.array(line_Y)

        word_XY = self.find_word_centers(self.aoi)
        word_XY = np.array(word_XY)

        self.suggested_corrections = copy.deepcopy(self.fixations)
        # print(self.corrected_fixations)

        if len(self.fixations) > 0:
            if self.algorithm == "attach":
                self.suggested_corrections[:, 0:2] = da.attach(
                    copy.deepcopy(fixation_XY), line_Y
                )
                self.status_text = self.algorithm + " Algorithm Selected"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("algorithm_selected")
                # self.update_suggestion()  # update the current suggestion as well
            elif self.algorithm == "chain":
                self.suggested_corrections[:, 0:2] = da.chain(
                    copy.deepcopy(fixation_XY), line_Y
                )
                self.status_text = self.algorithm + " Algorithm Selected"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("algorithm_selected")
                # self.update_suggestion()
            # elif self.algorithm == 'cluster':
            #     self.suggested_corrections[:, 0:2] = da.cluster(copy.deepcopy(fixation_XY), line_Y)
            #     self.relevant_buttons("algorithm_selected")
            # self.update_suggestion()
            elif self.algorithm == "merge":
                self.suggested_corrections[:, 0:2] = da.merge(
                    copy.deepcopy(fixation_XY), line_Y
                )
                self.status_text = self.algorithm + " Algorithm Selected"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("algorithm_selected")
                # self.update_suggestion()
            elif self.algorithm == "regress":
                self.suggested_corrections[:, 0:2] = da.regress(
                    copy.deepcopy(fixation_XY), line_Y
                )
                self.status_text = self.algorithm + " Algorithm Selected"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("algorithm_selected")
                # self.update_suggestion()
            elif self.algorithm == "segment":
                self.suggested_corrections[:, 0:2] = da.segment(
                    copy.deepcopy(fixation_XY), line_Y
                )
                self.status_text = self.algorithm + " Algorithm Selected"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("algorithm_selected")
                # self.update_suggestion()
            # elif self.algorithm == 'split':
            #     self.suggested_corrections[:, 0:2] = da.split(copy.deepcopy(fixation_XY), line_Y)
            #     self.relevant_buttons("algorithm_selected")
            # self.update_suggestion()
            elif self.algorithm == "stretch":
                self.suggested_corrections[:, 0:2] = da.stretch(
                    copy.deepcopy(fixation_XY), line_Y
                )
                self.status_text = self.algorithm + " Algorithm Selected"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("algorithm_selected")
                # self.update_suggestion()
            elif self.algorithm == "warp":
                self.suggested_corrections[:, 0:2] = da.warp(fixation_XY, word_XY)
                self.status_text = self.algorithm + " Algorithm Selected"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("algorithm_selected")
                # self.update_suggestion()
            else:
                self.status_text = "No Selected Algorithm"
                self.statusBar.showMessage(self.status_text)
                self.relevant_buttons("no_selected_algorithm")
                self.algorithm = None
                # self.update_suggestion()
            self.checkbox_show_suggestion.setChecked(True)

            # reset progress bar when algorithm is selected, saving the user one manual step
            self.progress_bar.setValue(self.progress_bar.minimum())

    """if the user presses the correct all fixations button,
    make the corrected fixations the suggested ones from the correction algorithm"""

    def correct_all_fixations(self):
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
        if self.current_fixation == 0:
            self.current_fixation = len(self.fixations)
        self.current_fixation -= 1

        self.draw_canvas(self.fixations)
        self.progress_bar_updated(self.current_fixation, draw=False)

        # if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
        #    self.update_suggestion()

    """when the next fixation button is clicked, call this function and find the suggested correction for this fixation"""

    def next_fixation(self):
        # if self.suggested_corrections is not None:
        if self.current_fixation == len(self.fixations) - 1:
            self.current_fixation = -1
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

    """ when the confirm button is clicked, the suggested correction replaces the current fixation"""

    def confirm_suggestion(self):
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


    def save_corrections(self):
        """save a JSON object of the corrections to a file"""

        qfd = QFileDialog()
        default_file_name = self.trial_path.replace('.json', '') + '_CORRECTED_json'
        new_correction_file_path, _ = qfd.getSaveFileName(self, "Save correction", default_file_name)

        if len(self.fixations) > 0:
            list = self.fixations.tolist()

            corrected_fixations = {}
            for i in range(len(self.fixations)):
                corrected_fixations[i + 1] = list[i]

            with open(f"{new_correction_file_path.replace('.json', '') + '_CORRECTED.json'}", "w") as f:
                json.dump(corrected_fixations, f)

            # TODO: write a function for adding things to metadata and another function to save metadata file
                
            self.duration = (time.time() - self.timer_start)
            today = date.today()

            headers = "event,event details,timestamp\n"

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

            metadata_file_name = new_correction_file_path + '_metadata.csv'
            metadata_file_path = Path(f"{metadata_file_name}")

            with open(metadata_file_path, "w", newline="") as meta_file:
                    meta_file.write(headers)
                    meta_file.write(self.metadata)
                    self.metadata = ""

            self.status_text = "Corrections Saved to" + " " + metadata_file_name
            self.statusBar.showMessage(self.status_text)

        else:
            qmb = QMessageBox()
            qmb.setWindowTitle("Save Error")
            qmb.setText("No Corrections Made")
            qmb.exec_()

    # progress bar updated in tool
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

    """Activates when the lesser value filter changes"""

    def lesser_value_changed(self, value):
        self.lesser_value = value

    def lesser_value_confirmed(self):
        # set lesser_value to value of the greater value filter
        self.lesser_value = self.input_lesser.text()

        # writing a log in metadata
        self.metadata += (
            "filter,removed fixations less than "
            + self.lesser_value
            + ","
            + str(time.time())
            + "\n"
        )

        self.fixations = self.fixations[self.fixations[:, 2] > int(self.lesser_value)]
        self.current_fixation = 0
        if self.algorithm != "manual" and self.suggested_corrections is not None:
            if self.current_fixation == len(self.fixations):
                # off by one error, since deleting fixation moves current onto the next fixation
                self.current_fixation -= 1
            self.suggested_corrections = self.suggested_corrections[
                self.suggested_corrections[:, 2] > int(self.lesser_value)
            ]

        temp = self.current_fixation
        self.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(temp)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)

    """Activates when the greater value filter changes"""

    def greater_value_changed(self, value):
        self.greater_value = value

    def greater_value_confirmed(self):
        # set greater_value to value of the greater value filter
        self.greater_value = self.input_greater.text()

        # writing a log in metadata
        self.metadata += (
            "filter,removed fixations greater than "
            + self.greater_value
            + ","
            + str(time.time())
            + "\n"
        )

        self.fixations = self.fixations[self.fixations[:, 2] < int(self.greater_value)]
        self.current_fixation = 0
        if self.algorithm != "manual" and self.suggested_corrections is not None:
            if self.current_fixation == len(self.fixations):
                # off by one error, since deleting fixation moves current onto the next fixation
                self.current_fixation -= 1

            self.suggested_corrections = self.suggested_corrections[
                self.suggested_corrections[:, 2] < int(self.greater_value)
            ]

        temp = self.current_fixation
        self.progress_bar.setMaximum(len(self.fixations) - 1)
        self.progress_bar_updated(temp)

        self.draw_canvas(self.fixations, draw_all=True)
        self.progress_bar_updated(self.current_fixation, draw=False)

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

    """initalize the tool window"""

    def init_UI(self):
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
        self.greater_inputs = QHBoxLayout()
        self.input_greater = QLineEdit()
        self.input_greater.textChanged.connect(self.greater_value_changed)
        self.input_greater.setEnabled(False)
        self.input_greater.setText("1000")
        self.button_greater = QPushButton("Remove Fixations >")
        self.button_greater.setEnabled(False)
        self.button_greater.clicked.connect(self.greater_value_confirmed)
        self.greater_inputs.addWidget(self.input_greater)
        self.greater_inputs.addWidget(self.button_greater)

        self.lesser_inputs = QHBoxLayout()
        self.input_lesser = QLineEdit()
        self.input_lesser.textChanged.connect(self.lesser_value_changed)
        self.input_lesser.setEnabled(False)
        self.input_lesser.setText("50")
        self.button_lesser = QPushButton("Remove Fixations <")
        self.button_lesser.setEnabled(False)
        self.button_lesser.clicked.connect(self.lesser_value_confirmed)
        self.lesser_inputs.addWidget(self.input_lesser)
        self.lesser_inputs.addWidget(self.button_lesser)

        widget_list = [self.trial_list]

        for w in widget_list:
            self.left_side.addWidget(w)

        self.left_side.addLayout(self.greater_inputs)
        self.left_side.addLayout(self.lesser_inputs)
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
        self.semi_automation = QVBoxLayout()

        self.label_semi_automation = QLabel("Semi-Automation")
        self.label_semi_automation.setAlignment(Qt.AlignCenter)
        self.semi_automation.addWidget(self.label_semi_automation)

        self.semi_automation_second_row = QHBoxLayout()

        # self.button_next_fixation = QPushButton("Next Fixation", self)
        # #self.button_next_fixation.setEnabled(False)
        # self.button_next_fixation.clicked.connect(self.next_fixation)

        # self.button_previous_fixation = QPushButton("Previous Fixation", self)
        # self.button_previous_fixation.setEnabled(False)
        # self.button_previous_fixation.clicked.connect(self.previous_fixation)

        # self.semi_automation_second_row.addWidget(self.button_previous_fixation)
        # self.semi_automation_second_row.addWidget(self.button_next_fixation)

        self.semi_automation.addLayout(self.semi_automation_second_row)

        self.button_confirm_suggestion = QPushButton("Accept Suggestion and Next", self)
        self.button_confirm_suggestion.setEnabled(False)
        self.button_confirm_suggestion.clicked.connect(self.confirm_suggestion)
        self.semi_automation.addWidget(self.button_confirm_suggestion)

        self.button_undo_suggestion = QPushButton("Undo Correction", self)
        self.button_undo_suggestion.setEnabled(False)
        self.button_undo_suggestion.clicked.connect(self.undo_suggestion)
        self.semi_automation.addWidget(self.button_undo_suggestion)

        self.button1 = QPushButton()
        self.semi_automation.addWidget(self.button1)
        retain = self.button1.sizePolicy()
        retain.setRetainSizeWhenHidden(True)
        self.button1.setSizePolicy(retain)
        self.button1.hide()

        self.frame = QFrame()
        self.frame.setStyleSheet(
            " QFrame {border: 2px solid black; margin: 0px; padding: 0px;}"
        )
        self.label_semi_automation.setStyleSheet("QLabel { border: 0px }")
        self.frame.setLayout(self.semi_automation)
        self.below_canvas.addWidget(self.frame)
        # ---

        # --- section for automated tools
        self.automation = QVBoxLayout()

        self.label_automation = QLabel("Automation")
        self.label_automation.setAlignment(Qt.AlignCenter)
        self.automation.addWidget(self.label_automation)

        self.button_correct_all_fixations = QPushButton("Correct All Fixations", self)
        self.button_correct_all_fixations.setEnabled(False)
        self.button_correct_all_fixations.clicked.connect(self.correct_all_fixations)

        self.dropdown_select_algorithm = QComboBox()
        self.dropdown_select_algorithm.setEditable(True)
        self.dropdown_select_algorithm.addItem("Manual Correction")
        self.dropdown_select_algorithm.addItem("Attach")
        self.dropdown_select_algorithm.addItem("Chain")
        # self.dropdown_select_algorithm.addItem('Cluster')
        self.dropdown_select_algorithm.addItem("Merge")
        self.dropdown_select_algorithm.addItem("Regress")
        self.dropdown_select_algorithm.addItem("Segment")
        # self.dropdown_select_algorithm.addItem('Split')
        self.dropdown_select_algorithm.addItem("Stretch")
        # self.dropdown_select_algorithm.addItem('Compare')
        self.dropdown_select_algorithm.addItem("Warp")
        # self.dropdown_select_algorithm.addItem('Time Warp')
        # self.dropdown_select_algorithm.addItem('Slice')
        self.dropdown_select_algorithm.lineEdit().setAlignment(Qt.AlignCenter)
        self.dropdown_select_algorithm.lineEdit().setReadOnly(True)
        self.dropdown_select_algorithm.setEnabled(False)
        self.dropdown_select_algorithm.currentTextChanged.connect(
            self.get_algorithm_picked
        )

        self.automation.addWidget(self.dropdown_select_algorithm)
        self.automation.addWidget(self.button_correct_all_fixations)

        # buttons to fill in space
        self.button2 = QPushButton()
        self.automation.addWidget(self.button2)
        retain = self.button2.sizePolicy()
        retain.setRetainSizeWhenHidden(True)
        self.button2.setSizePolicy(retain)
        self.button2.hide()

        self.button3 = QPushButton()
        self.automation.addWidget(self.button3)
        retain = self.button3.sizePolicy()
        retain.setRetainSizeWhenHidden(True)
        self.button3.setSizePolicy(retain)
        self.button3.hide()

        self.frame2 = QFrame()
        self.frame2.setStyleSheet(
            " QFrame {border: 2px solid black; margin: 0px; padding: 0px;}"
        )
        self.label_automation.setStyleSheet("QLabel { border: 0px }")
        self.frame2.setLayout(self.automation)
        self.below_canvas.addWidget(self.frame2)
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
        self.layer_fixation_color = QHBoxLayout()
        self.button_saccade_color = QPushButton("Select Saccade Color")
        self.button_saccade_color.clicked.connect(self.select_saccade_color)
        self.button_fixation_color.setEnabled(False)
        self.button_saccade_color.setEnabled(False)

        self.button_coloblind_assist = QPushButton("Colorblind Assist")
        self.button_coloblind_assist.clicked.connect(self.colorblind_assist)
        self.button_coloblind_assist.setEnabled(False)

        self.layer_fixation_color.addWidget(self.button_fixation_color)
        self.layer_fixation_color.addWidget(self.button_saccade_color)
        self.layer_fixation_color.addWidget(self.button_coloblind_assist)

        self.filters.addLayout(self.layer_fixation_color)
        # --

        self.right_side.addLayout(self.below_canvas)

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
        self.dropdown_select_algorithm.setEditable(False)
        self.dropdown_select_algorithm.setEnabled(False)
        self.button_next_fixation.setEnabled(False)
        self.button_correct_all_fixations.setEnabled(False)
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
            self.button_correct_all_fixations.setEnabled(False)
            self.button_confirm_suggestion.setEnabled(False)

            self.checkbox_show_fixations.setCheckable(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setEnabled(False)
            self.input_lesser.setEnabled(False)
            self.input_greater.setEnabled(False)
            self.button_lesser.setEnabled(False)
            self.button_greater.setEnabled(False)

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
            self.toggle_aoi_width.setEnabled(False)
            self.toggle_aoi_height.setEnabled(False)
            self.button_coloblind_assist.setEnabled(False)
            self.toggle_fixation_opacity.setEnabled(False)
            self.toggle_saccade_opacity.setEnabled(False)

            self.dropdown_select_algorithm.setEnabled(False)
        elif feature == "trial_clicked":
            # self.button_save_corrections.setEnabled(True)
            self.save_correction_action.setEnabled(True)
            self.edit_menu.setEnabled(True)
            self.filters_menu.setEnabled(True)
            self.correction_menu.setEnabled(True)

            self.button_previous_fixation.setEnabled(True)
            self.button_next_fixation.setEnabled(True)
            self.button_correct_all_fixations.setEnabled(False)
            self.button_confirm_suggestion.setEnabled(False)

            self.dropdown_select_algorithm.setEnabled(True)
            self.dropdown_select_algorithm.setCurrentIndex(0)

            self.checkbox_show_aoi.setCheckable(True)
            self.checkbox_show_aoi.setEnabled(True)

            self.checkbox_show_fixations.setCheckable(True)
            self.checkbox_show_fixations.setEnabled(True)

            self.checkbox_show_saccades.setCheckable(True)
            self.checkbox_show_saccades.setEnabled(True)

            self.input_lesser.setEnabled(True)
            self.input_greater.setEnabled(True)
            self.button_lesser.setEnabled(True)
            self.button_greater.setEnabled(True)

            self.toggle_aoi_width.setEnabled(True)
            self.toggle_aoi_height.setEnabled(True)

            self.button_fixation_color.setEnabled(True)
            self.button_saccade_color.setEnabled(True)
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
            self.button_correct_all_fixations.setEnabled(False)
            self.button_confirm_suggestion.setEnabled(False)
            self.button_undo_suggestion.setEnabled(False)
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setChecked(
                False
            )  # the no algorithm selection updates the suggestions
            # which clears them in the function itself
            self.checkbox_show_suggestion.setEnabled(False)
        elif feature == "algorithm_selected":
            self.button_previous_fixation.setEnabled(True)
            self.button_next_fixation.setEnabled(True)
            self.button_correct_all_fixations.setEnabled(True)
            self.button_confirm_suggestion.setEnabled(True)
            self.button_undo_suggestion.setEnabled(True)
            self.checkbox_show_suggestion.setCheckable(True)
            self.checkbox_show_suggestion.setEnabled(True)


if __name__ == "__main__":
    fix8 = QApplication([])
    window = Fix8()
    # apply_stylesheet(fix8, 'my_theme.xml')
    fix8.exec_()
