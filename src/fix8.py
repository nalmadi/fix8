from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import QColor
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
from matplotlib.animation import FuncAnimation
from datetime import date
import csv
from pathlib import Path

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
        self.folder_path, self.trial_path, self.trial_data, self.trial_name = None, None, None, None

        # fields relating to fixations
        self.original_fixations, self.corrected_fixations, self.scatter, self.saccades = None, None, None, None
        self.current_fixation = -1

        # fields relating to AOIs
        self.patches, self.aoi, self.background_color = None, None, None

        # fields relating to the correction algorithm
        self.algorithm = 'original'
        self.suggested_corrections, self.single_suggestion = None, None

        # keeps track of how many times file was saved so duplicates can be saved instead of overriding previous save file
        self.file_saved = 0
        self.b = 0 # beginning time of trial
        self.duration = 0
        self.user = ''
        
        self.saccade_opacity = 0.4

        # fields relating to the drag and drop system
        self.selected_fixation = None
        self.epsilon = 11
        self.xy = None
        self.canvas.mpl_connect('button_press_event', self.button_press_callback)
        self.canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        
        # fields relating to color filters
        self.fixation_color = 'red'
        self.saccade_color = 'blue' 
               
        # fields related to filters
        self.lesser_value = 0
        self.greater_value = 0

    '''get the selected fixation that the user picks, with the selection inside a specific diameter range (epsilon),
    selected_fixation is an index, not the actual scatter point'''
    def get_selected_fixation(self, event):
        if self.scatter is not None:
            self.xy = np.asarray(self.scatter.get_offsets())
            xyt = self.canvas.ax.transData.transform(self.xy)
            xt, yt = xyt[:, 0], xyt[:, 1]

            d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
            self.selected_fixation = d.argmin()
            print(self.selected_fixation)

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
            if self.algorithm != 'original':
                fixation_XY = np.array([self.corrected_fixations[self.selected_fixation]])
                line_Y = self.find_lines_y(self.aoi)
                updated_correction = da.attach(copy.deepcopy(fixation_XY), line_Y)[0]
                self.suggested_corrections[self.selected_fixation] = updated_correction
                self.update_suggestion()
            if self.checkbox_show_saccades.isChecked():
                self.clear_saccades()
                self.show_saccades(Qt.Checked)
            else:
                self.show_saccades(Qt.Unchecked)
        if event.button != 1:
            return
        # self.selected_fixation = None
        self.canvas.draw_idle()


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
        if e.key() == 16777219:
            # print(self.corrected_fixations[0], "selected fixation\n", self.selected_fixation)    
            if(self.corrected_fixations is not None and self.selected_fixation is not None):
                if self.selected_fixation < len(self.corrected_fixations):
                    print("delete:", self.current_fixation)
                    # print("able to delete")
                    self.corrected_fixations = np.delete(self.corrected_fixations, self.selected_fixation, 0) # delete the row of selected fixation
                    if self.current_fixation == 0:
                        self.current_fixation = len(self.corrected_fixations)
                        self.current_fixation -= 1
                        temp = self.current_fixation
                    else:
                        self.current_fixation-=1
                        temp = self.current_fixation
                    self.progress_bar.setMaximum(len(self.corrected_fixations) - 1)
                    self.progress_bar_updated(temp)
                    if self.suggested_corrections is not None:
                        self.suggested_corrections = np.delete(self.suggested_corrections, self.selected_fixation, 0) # delete the row of selected fixation
                    self.selected_fixation = None
                    fixations = self.corrected_fixations
                    saccades = self.saccades
                    
                    x = fixations[0:self.current_fixation+1,0]
                    y = fixations[0:self.current_fixation+1,1]
                    duration = fixations[0:self.current_fixation+1,2]
                    
                    # get rid of the data before updating it
                    self.clear_fixations()
                    self.clear_saccades()
                    
                    # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
                    # do the same for saccades
                    if self.checkbox_show_fixations.isCheckable():
                        if self.checkbox_show_fixations.isChecked():
                            self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
                    if self.checkbox_show_saccades.isCheckable():
                        if self.checkbox_show_saccades.isChecked():
                            self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

                    if self.algorithm != 'original':
                        if self.current_fixation == len(self.corrected_fixations):
                            # off by one error
                            self.current_fixation-=1
                        self.update_suggestion()
                    # draw whatever was updated
                    self.canvas.draw()
                    
                

    '''opens the stimulus, displays it to the canvas, and grabs the aois of the image'''
    def open_stimulus(self):
        # if self.scatter is None:
            # self.checkbox_show_fixations.setEnabled(False)
        # open the file, grab the file name and file type
        qfd = QFileDialog()
        self.file = qfd.getOpenFileName(self, 'Open File', 'c:\\')

        # make sure a file is chosen, if cancelled don't do anything
        if self.file[0] != '':
            self.file_path = self.file[0]
            self.file_name = self.file_path.split('/')[-1]
            fileType = self.file_name.split('.')[-1]

            # make sure the file is a png type
            if fileType.lower() != 'png' and fileType.lower() != 'jpg' and fileType.lower() != 'jpeg':
                qmb = QMessageBox()
                qmb.setWindowTitle("Stimulus File Error")
                qmb.setText("Not a PNG; please choose a PNG, JPG or JPEG file")
                qmb.exec_()
            else:
                # draw the image to the canvas
                self.canvas.clear()
                image = mpimg.imread(self.file[0])
                self.canvas.ax.imshow(image)
                self.canvas.ax.set_title(str(self.file_name.split('.')[0]))
                self.canvas.draw()

                self.find_aoi()

                self.relevant_buttons("opened_stimulus")



    '''open trial folder, display it to trial list window with list of JSON trials'''
    def open_trial_folder(self):

        qfd = QFileDialog()
        self.folder_path = qfd.getExistingDirectory(self, 'Select Folder')

        # --- make sure a folder was actually chosen, otherwise just cancel ---
        if self.folder_path != '':

            # clear the data since a new folder was open, no trial is chosen at this point
            self.trial_list.clear()
            self.clear_fixations()
            self.clear_saccades()

            # when open a new folder, block off all the relevant buttons that shouldn't be accesible until a trial is clicked
            self.relevant_buttons("opened_folder")

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
        # reset times saved if a DIFFERENT trial was selected
        self.trial_name = item.text()
        if self.trials[item.text()] != self.trial_path:
            self.file_saved = 0
        self.trial_path = self.trials[item.text()]
        self.current_fixation = 0 # resets the current suggestion since the user is restarting the trial


        self.find_fixations(self.trial_path)
        
        # set the progress bar to the amount of fixations found
        self.progress_bar.setMaximum(len(self.original_fixations) - 1)
        self.b = time.time()
        if self.current_fixation is not None:
            if self.current_fixation == -1:
                self.label_progress.setText(f"0/{len(self.original_fixations)}")
            else:
                self.label_progress.setText(f"{self.current_fixation}/{len(self.original_fixations)}")
        self.corrected_fixations = copy.deepcopy(self.original_fixations) # corrected fixations will be the current fixations on the screen and in the data
        self.checkbox_show_fixations.setChecked(True)
        if self.checkbox_show_fixations.isChecked() == True:
            self.clear_fixations()
            self.draw_fixations()

        if self.checkbox_show_saccades.isChecked() == True:
            self.clear_saccades()
            self.draw_saccades()

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
        if self.patches is not None:
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
                self.relevant_buttons("trial_clicked")
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

    def find_word_centers(self, aois):
        ''' returns a list of word centers '''
        results = []
        
        for index, row in aois.iterrows():
            x, y, height, width = row['x'], row['y'], row['height'], row['width']
            
            center = [int(x + width // 2), int(y + height // 2)]
            
            if center not in results:
                results.append(center)
                
        return results

    '''draw the fixations to the canvas
        parameters:
        fixations - 0 is default since the corrected fixations are the main thing to be shown,
        1 the original fixations is manually chosen (not currently needed as this isn't in option in algorithms)'''
    def draw_fixations(self, fixations = 0):
        if fixations == 0: # default fixations to use
            fixations = self.corrected_fixations
        elif fixations == 1:
            fixations = self.original_fixations
        x = fixations[:, 0]
        y = fixations[:, 1]
        duration = fixations[:, 2]
        self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
        self.canvas.draw()

    '''if the user clicks the show fixations checkbox, show or hide the fixations
        parameters:
        state - the checkbox being checked or unchecked'''
    def show_fixations(self, state):
        if self.folder_path != '':
            if self.checkbox_show_fixations.isCheckable():
                if state == Qt.Checked:
                    self.draw_fixations()
                elif state == Qt.Unchecked:
                    self.clear_fixations()

    '''if the user clicks saccades, show or hide them'''
    def show_saccades(self, state):
        if self.folder_path != '':
            if self.checkbox_show_saccades.isCheckable():
                if state == Qt.Checked:
                    self.draw_saccades()
                elif state == Qt.Unchecked:
                    self.clear_saccades()

    '''draw the scatter plot to the canvas'''
    def draw_saccades(self):
        x = self.corrected_fixations[:, 0]
        y = self.corrected_fixations[:, 1]
        self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)
        self.canvas.draw()

    '''remove the saccades from the canvas (this does not erase the data, just visuals)'''
    def clear_saccades(self):
        if self.saccades != None:
            self.canvas.ax.lines.clear()
            self.saccades = None
            self.canvas.draw()

    '''clear the fixations from the canvas'''
    def clear_fixations(self):
        if self.scatter != None:
            self.scatter.remove()
            self.scatter = None
            self.canvas.draw()

    '''when the user selects an algorithm from the drop down menu,
        make it the current algorithm to use for automated and semi automated use
        parameters:
        algorithm - the selected correction algorithm'''
    def get_algorithm_picked(self,algorithm):
        self.algorithm = algorithm
        self.algorithm = self.algorithm.lower()

        # run correction
        fixation_XY = self.corrected_fixations
        line_Y = self.find_lines_y(self.aoi)
        word_XY = self.find_word_centers(self.aoi)

        if self.algorithm == 'attach':
            self.suggested_corrections = da.attach(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()  # update the suggested corrections to the new algorithm, and the current suggestion aswell
        elif self.algorithm == 'chain':
            self.suggested_corrections = da.chain(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'cluster':
            self.suggested_corrections = da.cluster(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'merge':
            self.suggested_corrections = da.merge(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'regress':
            self.suggested_corrections = da.regress(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'segment':
            self.suggested_corrections = da.segment(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'split':
            self.suggested_corrections = da.split(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'stretch':
            self.suggested_corrections = da.stretch(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'compare':
            self.suggested_corrections = da.compare(copy.deepcopy(fixation_XY), word_XY)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'warp':
            self.suggested_corrections = da.warp(copy.deepcopy(fixation_XY), word_XY)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'time warp':
            self.suggested_corrections = da.time_warp(copy.deepcopy(fixation_XY), word_XY)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        elif self.algorithm == 'slice':
            self.suggested_corrections = da.slice(copy.deepcopy(fixation_XY), line_Y)
            self.relevant_buttons("algorithm_selected")
            self.update_suggestion()
        else:
            self.relevant_buttons("no_selected_algorithm")
            self.algorithm = None
            self.update_suggestion()

    '''if the user presses the correct all fixations button,
    make the corrected fixations the suggested ones from the correction algorithm'''
    def correct_all_fixations(self):
        if self.suggested_corrections is not None:
            self.corrected_fixations = copy.deepcopy(self.suggested_corrections)
            self.clear_fixations()
            self.clear_saccades()
            if self.checkbox_show_fixations.isChecked():
                self.draw_fixations()
            if self.checkbox_show_saccades.isChecked():
                self.draw_saccades()

    def previous_fixation(self):
        if self.suggested_corrections is not None:
            if self.current_fixation == 0:
                self.current_fixation = len(self.suggested_corrections)
            self.current_fixation -= 1
            print("previous:", self.current_fixation)

            fixations = self.corrected_fixations
            saccades = self.saccades
            x = fixations[0:self.current_fixation + 1, 0]
            y = fixations[0:self.current_fixation + 1, 1]
            duration = fixations[0:self.current_fixation + 1, 2]
            # print(fixations[1, 0])

            # get rid of the data before updating it
            self.clear_fixations()
            self.clear_saccades()

            
            # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
            # do the same for saccades
            if self.checkbox_show_fixations.isCheckable():
                if self.checkbox_show_fixations.isChecked():
                    self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
            if self.checkbox_show_saccades.isCheckable():
                if self.checkbox_show_saccades.isChecked():
                    self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

            # draw whatever was updated
            self.canvas.draw()

            if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
                self.update_suggestion()
                self.update_suggestion()

    '''when the next fixation button is clicked, call this function and find the suggested correction for this fixation'''
    def next_fixation(self):
        if self.suggested_corrections is not None:
            if self.current_fixation == len(self.suggested_corrections) - 1:
                self.current_fixation = -1
            self.current_fixation += 1

            fixations = self.corrected_fixations
            saccades = self.saccades
            x = fixations[0:self.current_fixation + 1, 0]
            y = fixations[0:self.current_fixation + 1, 1]
            duration = fixations[0:self.current_fixation + 1, 2]
            # print(fixations[1, 0])

            # get rid of the data before updating it
            self.clear_fixations()
            self.clear_saccades()

            
            # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
            # do the same for saccades
            if self.checkbox_show_fixations.isCheckable():
                if self.checkbox_show_fixations.isChecked():
                    self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
            if self.checkbox_show_saccades.isCheckable():
                if self.checkbox_show_saccades.isChecked():
                    self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

            # draw whatever was updated
            self.canvas.draw()

            if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
                self.update_suggestion()
                self.update_suggestion()
            

    def show_suggestion(self,state):
        if self.checkbox_show_suggestion.isCheckable():
            self.update_suggestion()

    def update_suggestion(self):
        if self.current_fixation != -1:
            x = self.suggested_corrections[self.current_fixation][0]
            y = self.suggested_corrections[self.current_fixation][1]
            duration = self.suggested_corrections[self.current_fixation][2]

            # remove and replace the last suggestion for the current suggestion
            if self.single_suggestion != None:
                self.single_suggestion.remove()
                self.single_suggestion = None
                self.canvas.draw()
            self.single_suggestion = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = 'blue')

            # if checkbox is checked draw the suggestion, else remove it
            if self.checkbox_show_suggestion.isChecked():
                self.canvas.draw()
            else:
                if self.single_suggestion != None:
                    self.single_suggestion.remove()
                    self.single_suggestion = None
                    self.canvas.draw()

    def back_to_beginning(self):
        self.current_fixation = 1
        self.update_suggestion()

    ''' when the confirm button is clicked, the suggested correction replaces the current fixation'''
    def confirm_suggestion(self):
        x = self.suggested_corrections[self.current_fixation][0]
        y = self.suggested_corrections[self.current_fixation][1]
        self.corrected_fixations[self.current_fixation][0] = x
        self.corrected_fixations[self.current_fixation][1] = y
        self.next_fixation()
        
        fixations = self.corrected_fixations
        saccades = self.saccades
        x = fixations[0:self.current_fixation + 1, 0]
        y = fixations[0:self.current_fixation + 1, 1]
        duration = fixations[0:self.current_fixation + 1, 2]
        # print(fixations[1, 0])

        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()

        
        # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
        # do the same for saccades
        if self.checkbox_show_fixations.isCheckable():
            if self.checkbox_show_fixations.isChecked():
                self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
        if self.checkbox_show_saccades.isCheckable():
            if self.checkbox_show_saccades.isChecked():
                self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

        # draw whatever was updated
        self.canvas.draw()

        if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
            self.update_suggestion()
            self.update_suggestion()
        # if self.checkbox_show_fixations.isCheckable():
        #     if self.checkbox_show_fixations.isChecked():
        #         self.clear_fixations()
        #         self.draw_fixations()
        # if self.checkbox_show_saccades.isCheckable():
        #     if self.checkbox_show_saccades.isChecked():
        #         self.clear_saccades()
        #         self.draw_saccades()

    '''save a JSON object of the corrections to a file'''
    def save_corrections(self):
        if self.corrected_fixations is not None:
            list = self.corrected_fixations.tolist()
            corrected_fixations = {}
            for i in range(len(self.corrected_fixations)):
                corrected_fixations[i + 1] = list[i]
            with open(f"{self.trial_path.replace('.json', '_CORRECTED' + '.json')}", 'w') as f:
                json.dump(corrected_fixations, f)
            self.file_saved += 1
            self.duration = time.time() - self.b  # store in a file called metadata which includes the file name they were correcting, the image, and the duration
            today = date.today()
            # print("Today's date:", today)
            # current_session_metadata = {"Date": None,
            #                             "Trial Name": None,
            #                             "Image": None,
            #                             "Duration": None
            #                             }
            # current_session_metadata["Date"] = str(today)
            # current_session_metadata["Trial Name"] = str(self.trial_name)
            # current_session_metadata["Image"] = str(self.file_path)
            # current_session_metadata["Duration"] = str(self.duration)
            # l_metadata = []
            # l_metadata.append(current_session_metadata)

            headers = ["Date", "Trial Name", "File Path", "Duration"]
            l_metadata = [str(today), str(self.trial_name), str(self.file_path), str(self.duration)]
            path = Path(f"{self.trial_path.replace(self.trial_path.split('/')[-1], 'metadata.csv')}").is_file()
            
            if(path == False):       
                with open(f"{self.trial_path.replace(self.trial_path.split('/')[-1], 'metadata.csv')}", 'w', newline='') as wr:
                    writer = csv.writer(wr)
                    writer.writerow(headers)
                    writer.writerow(l_metadata)
            else:
                with open(f"{self.trial_path.replace(self.trial_path.split('/')[-1], 'metadata.csv')}", 'a',newline='') as wr:
                    writer = csv.writer(wr)
                    writer.writerow(l_metadata)               
        else:
            qmb = QMessageBox()
            qmb.setWindowTitle("Save Error")
            qmb.setText("No Corrections Made")
            qmb.exec_()


    # progress bar updated in tool
    def progress_bar_updated(self, value):
        # update the current suggested correction to the last fixation of the list
        self.current_fixation = value
        print("progress:", self.current_fixation)
        # update current suggestion to the progress bar
        if self.current_fixation is not None:
            self.label_progress.setText(f"{self.current_fixation}/{len(self.corrected_fixations)}")
        
        fixations = self.corrected_fixations
        saccades = self.saccades
        x = fixations[0:value + 1, 0]
        y = fixations[0:value + 1, 1]
        duration = fixations[0:value + 1, 2]
        # print(fixations[1, 0])

        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()
        
        # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
        # do the same for saccades
        if self.checkbox_show_fixations.isCheckable():
            if self.checkbox_show_fixations.isChecked():
                self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
        if self.checkbox_show_saccades.isCheckable():
            if self.checkbox_show_saccades.isChecked():
                self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

        # draw whatever was updated
        self.canvas.draw()

        if self.dropdown_select_algorithm.currentText() != "Select Correction Algorithm":
            self.update_suggestion()
            
    
    '''Activates when the lesser value filter changes'''
    def lesser_value_changed(self,value):
        self.lesser_value = value
            

    def lesser_value_confirmed(self):
        
        print("getting rid of all fixations less than", self.lesser_value)
        
        self.corrected_fixations = self.corrected_fixations[self.corrected_fixations[:, 2] > int(self.lesser_value)]
        self.current_fixation = 0
        if self.algorithm != 'original':
            if self.current_fixation == len(self.corrected_fixations):
                # off by one error, since deleting fixation moves current onto the next fixation
                self.current_fixation-=1
            self.suggested_corrections = self.suggested_corrections[self.suggested_corrections[:, 2] > int(self.lesser_value)]
            
        temp = self.current_fixation
        self.progress_bar.setMaximum(len(self.corrected_fixations) - 1)
        self.progress_bar_updated(temp)
        fixations = self.corrected_fixations
        saccades = self.saccades
        x = fixations[:,0]
        y = fixations[:,1]
        duration = fixations[:,2]
        
        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()
        
        # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
        # do the same for saccades
        if self.checkbox_show_fixations.isCheckable():
            if self.checkbox_show_fixations.isChecked():
                self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
        if self.checkbox_show_saccades.isCheckable():
            if self.checkbox_show_saccades.isChecked():
                self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

        # draw whatever was updated
        self.canvas.draw()       

    '''Activates when the greater value filter changes'''
    def greater_value_changed(self,value):
        self.greater_value = value
        
    def greater_value_confirmed(self):
        
        print("getting rid of all fixations greater than", self.greater_value)
        
        self.corrected_fixations = self.corrected_fixations[self.corrected_fixations[:, 2] < int(self.greater_value)]
        self.current_fixation = 0
        if self.algorithm != 'original':
            if self.current_fixation == len(self.corrected_fixations):
                # off by one error, since deleting fixation moves current onto the next fixation
                self.current_fixation-=1
            print(self.suggested_corrections[:,2])
            self.suggested_corrections = self.suggested_corrections[self.suggested_corrections[:, 2] < int(self.greater_value)]
        temp = self.current_fixation
        self.progress_bar.setMaximum(len(self.corrected_fixations) - 1)
        self.progress_bar_updated(temp)
        fixations = self.corrected_fixations
        saccades = self.saccades
        x = fixations[:,0]
        y = fixations[:,1]
        duration = fixations[:,2]
        
        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()
        
        # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
        # do the same for saccades
        if self.checkbox_show_fixations.isCheckable():
            if self.checkbox_show_fixations.isChecked():
                self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
        if self.checkbox_show_saccades.isCheckable():
            if self.checkbox_show_saccades.isChecked():
                self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

        # draw whatever was updated
        self.canvas.draw()       
        
    def select_fixation_color(self):
        
        color = QColorDialog.getColor()
        self.fixation_color = str(color.name())
        
        fixations = self.corrected_fixations
        saccades = self.saccades
        x = fixations[:,0]
        y = fixations[:,1]
        duration = fixations[:,2]
        
        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()
        
        # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
        # do the same for saccades
        if self.checkbox_show_fixations.isCheckable():
            if self.checkbox_show_fixations.isChecked():
                self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
        if self.checkbox_show_saccades.isCheckable():
            if self.checkbox_show_saccades.isChecked():
                self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

        # draw whatever was updated
        self.canvas.draw()
        
    def select_saccade_color(self):
        color = QColorDialog.getColor()
        self.saccade_color = str(color.name())  
        
        fixations = self.corrected_fixations
        saccades = self.saccades
        x = fixations[:,0]
        y = fixations[:,1]
        duration = fixations[:,2]
        
        # get rid of the data before updating it
        self.clear_fixations()
        self.clear_saccades()
        
        # update the scatter based on the progress bar, redraw the canvas if checkbox is clicked
        # do the same for saccades
        if self.checkbox_show_fixations.isCheckable():
            if self.checkbox_show_fixations.isChecked():
                self.scatter = self.canvas.ax.scatter(x,y,s=30 * (duration/50)**1.8, alpha = 0.4, c = self.fixation_color)
        if self.checkbox_show_saccades.isCheckable():
            if self.checkbox_show_saccades.isChecked():
                self.saccades = self.canvas.ax.plot(x, y, alpha=self.saccade_opacity, c=self.saccade_color, linewidth=1)

        # draw whatever was updated
        self.canvas.draw()
        
    '''initalize the tool window'''
    def init_UI(self): 

        # wrapper layout
        self.wrapper_layout = QHBoxLayout()

        # --- left side
        self.left_side = QVBoxLayout()

        self.button_open_stimulus = QPushButton("Open Stimulus", self)
        self.button_open_stimulus.clicked.connect(self.open_stimulus)

        self.button_open_folder = QPushButton("Open Folder", self)
        self.button_open_folder.setEnabled(False)
        self.button_open_folder.clicked.connect(self.open_trial_folder)

        self.button_save_corrections = QPushButton("Save Corrrections", self)
        self.button_save_corrections.setEnabled(False)
        self.button_save_corrections.clicked.connect(self.save_corrections)

        self.trial_list = QListWidget()
        self.trial_list.itemDoubleClicked.connect(self.trial_double_clicked)
        
        # section for fixation size filters
        self.greater_inputs = QHBoxLayout()
        self.input_greater = QLineEdit()
        self.input_greater.textChanged.connect(self.greater_value_changed)
        self.input_greater.setEnabled(False)
        self.button_greater = QPushButton("Remove Fixations >")
        self.button_greater.setEnabled(False)
        self.button_greater.clicked.connect(self.greater_value_confirmed)
        self.greater_inputs.addWidget(self.input_greater)
        self.greater_inputs.addWidget(self.button_greater)
        
        self.lesser_inputs = QHBoxLayout()
        self.input_lesser = QLineEdit()
        self.input_lesser.textChanged.connect(self.lesser_value_changed)
        self.input_lesser.setEnabled(False)
        self.button_lesser = QPushButton("Remove Fixations <")
        self.button_lesser.setEnabled(False)
        self.button_lesser.clicked.connect(self.lesser_value_confirmed)
        self.lesser_inputs.addWidget(self.input_lesser)
        self.lesser_inputs.addWidget(self.button_lesser)
        

        widget_list = [self.button_open_stimulus, self.button_open_folder, self.button_save_corrections,
                        self.trial_list]
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

        self.toolbar = NavigationToolBar(self.canvas, self)
        self.toolbar.setStyleSheet("QToolBar { border: 0px }")
        self.toolbar.setEnabled(False)
        self.progress_tools.addWidget(self.toolbar)

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

        self.button_next_fixation = QPushButton("Next Fixation", self)
        self.button_next_fixation.setEnabled(False)
        self.button_next_fixation.clicked.connect(self.next_fixation)

        self.button_previous_fixation = QPushButton("Previous Fixation", self)
        self.button_previous_fixation.setEnabled(False)
        self.button_previous_fixation.clicked.connect(self.previous_fixation)

        self.semi_automation_second_row.addWidget(self.button_previous_fixation)
        self.semi_automation_second_row.addWidget(self.button_next_fixation)

        self.semi_automation.addLayout(self.semi_automation_second_row)

        self.button_confirm_suggestion = QPushButton("Accept Suggestion and Next", self)
        self.button_confirm_suggestion.setEnabled(False)
        self.button_confirm_suggestion.clicked.connect(self.confirm_suggestion)
        self.semi_automation.addWidget(self.button_confirm_suggestion)

        self.button1 = QPushButton()
        self.semi_automation.addWidget(self.button1)
        retain = self.button1.sizePolicy()
        retain.setRetainSizeWhenHidden(True)
        self.button1.setSizePolicy(retain)
        self.button1.hide()

        self.frame = QFrame()
        self.frame.setStyleSheet(" QFrame {border: 2px solid black; margin: 0px; padding: 0px;}")
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
        self.dropdown_select_algorithm.addItem('Select Correction Algorithm')
        self.dropdown_select_algorithm.addItem('Attach')
        self.dropdown_select_algorithm.addItem('Chain')
        self.dropdown_select_algorithm.addItem('Cluster')
        self.dropdown_select_algorithm.addItem('Merge')
        self.dropdown_select_algorithm.addItem('Regress')
        self.dropdown_select_algorithm.addItem('Segment')
        self.dropdown_select_algorithm.addItem('Split')
        self.dropdown_select_algorithm.addItem('Stretch')
        self.dropdown_select_algorithm.addItem('Compare')
        self.dropdown_select_algorithm.addItem('Warp')
        self.dropdown_select_algorithm.addItem('Time Warp')
        self.dropdown_select_algorithm.addItem('Slice')
        self.dropdown_select_algorithm.lineEdit().setAlignment(Qt.AlignCenter)
        self.dropdown_select_algorithm.lineEdit().setReadOnly(True)
        self.dropdown_select_algorithm.setEnabled(False)
        self.dropdown_select_algorithm.currentTextChanged.connect(self.get_algorithm_picked)

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
        self.frame2.setStyleSheet(" QFrame {border: 2px solid black; margin: 0px; padding: 0px;}")
        self.label_automation.setStyleSheet("QLabel { border: 0px }")
        self.frame2.setLayout(self.automation)
        self.below_canvas.addWidget(self.frame2)
        # ---


        # --- section for filters
        self.filters = QVBoxLayout()

        self.label_filters = QLabel("Visualization")
        self.label_filters.setAlignment(Qt.AlignCenter)
        self.filters.addWidget(self.label_filters)

        self.checkbox_show_aoi = QCheckBox("Show AOIs")
        self.checkbox_show_aoi.setEnabled(False)
        self.checkbox_show_aoi.stateChanged.connect(self.show_aoi)
        self.filters.addWidget(self.checkbox_show_aoi)

        self.checkbox_show_fixations = QCheckBox("Show Fixations")
        self.checkbox_show_fixations.setEnabled(False)
        self.checkbox_show_fixations.stateChanged.connect(self.show_fixations)
        self.filters.addWidget(self.checkbox_show_fixations)

        self.checkbox_show_saccades = QCheckBox("Show Saccades")
        self.checkbox_show_saccades.setEnabled(False)
        self.checkbox_show_saccades.stateChanged.connect(self.show_saccades)
        self.filters.addWidget(self.checkbox_show_saccades)
        

        self.checkbox_show_suggestion = QCheckBox("Show Suggested Correction")
        self.checkbox_show_suggestion.setEnabled(False)
        self.checkbox_show_suggestion.stateChanged.connect(self.show_suggestion)
        self.filters.addWidget(self.checkbox_show_suggestion)
        self.frame3 = QFrame()
        self.frame3.setStyleSheet(" QFrame {border: 2px solid black; margin: 0px; padding: 0px;}")
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
        
        self.layer_fixation_color.addWidget(self.button_fixation_color)
        self.layer_fixation_color.addWidget(self.button_saccade_color)
        
        self.filters.addLayout(self.layer_fixation_color)
        # --

        self.right_side.addLayout(self.below_canvas)

        # add both sides to overall wrapper layout
        self.wrapper_layout.addLayout(self.left_side)
        self.wrapper_layout.addLayout(self.right_side)
        self.wrapper_layout.setStretch(0,1)
        self.wrapper_layout.setStretch(1,3)

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
        self.checkbox_show_suggestion.setChecked(False)
        self.checkbox_show_suggestion.setCheckable(False)

        widget = QWidget()
        widget.setLayout(self.wrapper_layout)
        self.setCentralWidget(widget)
        self.showMaximized()

    def relevant_buttons(self, feature):
        if feature == "opened_stimulus":
            self.button_open_folder.setEnabled(True)
            self.checkbox_show_aoi.setCheckable(True)
            self.checkbox_show_aoi.setChecked(False)
            self.checkbox_show_aoi.setEnabled(True)
            self.toolbar.setEnabled(True)
            self.checkbox_show_fixations.setCheckable(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setCheckable(True)
            self.checkbox_show_saccades.setCheckable(False)
            self.checkbox_show_saccades.setChecked(False)
            self.checkbox_show_saccades.setCheckable(True)
        elif feature == "opened_folder":
            self.button_save_corrections.setEnabled(False)
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

            # IMPORTANT: here, set checked to false first so it activates suggestion removal since the removal happens in the checkbox connected method,
            # then make in uncheckable so it won't activate by accident anymore; there is no helper function for removing suggestions, so clearing suggestions isn't called anywhere in the code
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

            self.dropdown_select_algorithm.setEnabled(False)
        elif feature == "trial_clicked":
            self.button_save_corrections.setEnabled(True)

            self.button_previous_fixation.setEnabled(False)
            self.button_next_fixation.setEnabled(False)
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
            
            self.button_fixation_color.setEnabled(True)
            self.button_saccade_color.setEnabled(True)

            # IMPORTANT: here, set checked to false first so it activates suggestion removal since the removal happens in the checkbox connected method,
            # then make in uncheckable so it won't activate by accident anymore; there is no helper function for removing suggestions
            self.checkbox_show_suggestion.setChecked(False)
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setEnabled(False)
            
            self.progress_bar.setValue(self.progress_bar.minimum())
            self.progress_bar.setEnabled(True)
        elif feature == "no_selected_algorithm":
            self.button_previous_fixation.setEnabled(False)
            self.button_next_fixation.setEnabled(False)
            self.button_correct_all_fixations.setEnabled(False)
            self.button_confirm_suggestion.setEnabled(False)
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setChecked(False) # the no algorithm selection updates the suggestions which clears them in the function itself
            self.checkbox_show_suggestion.setEnabled(False)
        elif feature == "algorithm_selected":
            self.button_previous_fixation.setEnabled(True)
            self.button_next_fixation.setEnabled(True)
            self.button_correct_all_fixations.setEnabled(True)
            self.button_confirm_suggestion.setEnabled(True)
            self.checkbox_show_suggestion.setCheckable(True)
            self.checkbox_show_suggestion.setEnabled(True)

if __name__ == '__main__':
    fix8 = QApplication([])
    window = Fix8()
    fix8.exec_()
