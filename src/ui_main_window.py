

from qt_material import QtStyleTools, list_themes
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
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QStatusBar,
    QAction,
)

import canvas_resources
import driftAlgorithms as drift


class Ui_Main_Window(QMainWindow, QtStyleTools):
    def __init__(self, fix8):
        super().__init__()
        self.fix8 = fix8
        self.setWindowTitle("Fix8")
        self.setWindowIcon(QIcon("./.images/icon.ico"))
        self.init_UI()
        self.apply_stylesheet(self, 'my_theme.xml')


    def init_UI(self):
        """initalize the tool window"""
        # wrapper layout
        self.wrapper_layout = QHBoxLayout()

        # --- left side
        self.left_side = QVBoxLayout()

        self.trial_list = QListWidget()
        
        #self.trial_list.setHidden(True)

        self.left_side.addWidget(self.trial_list)
        
        # ---

        # --- canvas
        self.right_side = QVBoxLayout()

        self.canvas = canvas_resources.QtCanvas(self, width=12, height=8, dpi=200)
        self.right_side.addWidget(self.canvas)

        self.progress_tools = QHBoxLayout()

        # initialize status bar
        self.status_text = "Beginning..."
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(self.status_text)

        self.canvas_toolbar = canvas_resources.Toolbar(self.canvas, self)
        #self.toolbar.setStyleSheet("QToolBar { border: 0px }")
        #self.toolbar.setEnabled(False)
        self.progress_tools.addWidget(self.canvas_toolbar)

        self.button_previous_fixation = QPushButton("Back", self)
        self.button_previous_fixation.setEnabled(False)
        
        self.progress_tools.addWidget(self.button_previous_fixation)

        self.button_next_fixation = QPushButton("Next", self)
        self.button_next_fixation.setEnabled(True)
        
        self.progress_tools.addWidget(self.button_next_fixation)

        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setEnabled(False)
        
        self.progress_tools.addWidget(self.progress_bar)

        self.label_progress = QLabel("0/0")
        self.progress_tools.addWidget(self.label_progress)

        self.right_side.addLayout(self.progress_tools)

        self.below_canvas = QHBoxLayout()

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
        
        self.toggle_aoi_width = QSpinBox()
        self.toggle_aoi_width.setMaximum(50)
        self.toggle_aoi_width.setMinimum(1)
        self.toggle_aoi_width.setValue(7)
        self.toggle_aoi_height = QSpinBox()
        self.toggle_aoi_height.setMaximum(100)
        self.toggle_aoi_height.setMinimum(1)
        self.toggle_aoi_height.setValue(4)
        
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
        
        self.toggle_fixation_opacity = QSpinBox()
        self.toggle_fixation_opacity.setMaximum(10)
        self.toggle_fixation_opacity.setValue(4)
        self.toggle_fixation_opacity.setMinimum(1)
        
        self.fixation_opacity_text = QLabel("Fixation Opacity")
        self.fixation_layer.addWidget(self.checkbox_show_fixations)
        self.fixation_layer.addWidget(self.toggle_fixation_opacity)
        self.fixation_layer.addWidget(self.fixation_opacity_text)

        self.filters.addLayout(self.fixation_layer)

        self.saccade_layer = QHBoxLayout()
        self.checkbox_show_saccades = QCheckBox("Show Saccades")
        self.checkbox_show_saccades.setEnabled(False)
        
        self.toggle_saccade_opacity = QSpinBox()
        self.toggle_saccade_opacity.setMaximum(10)
        self.toggle_saccade_opacity.setValue(4)
        self.toggle_saccade_opacity.setMinimum(1)
        
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

        # layer for fixation size customization 
        self.fixation_size_layer = QHBoxLayout()

        self.fixation_size_bar = QSlider(Qt.Horizontal)
        self.fixation_size_bar.setMinimum(1)
        self.fixation_size_bar.setMaximum(30)
        self.fixation_size_bar.setValue(5)
        self.fixation_size_bar.setEnabled(False)
        

        
        self.fixation_size_text = QLabel("Fixation Size")
        self.fixation_size_layer.addWidget(self.fixation_size_bar)
        self.fixation_size_layer.addWidget(self.fixation_size_text)

        self.filters.addLayout(self.fixation_size_layer)
        # ---

        self.visualization_frame = QFrame()
        # self.frame3.setStyleSheet(
        #     " QFrame {border: 2px solid black; margin: 0px; padding: 0px;}"
        # )
        # self.label_filters.setStyleSheet("QLabel { border: 0px }")
        self.visualization_frame.setLayout(self.filters)
        self.below_canvas.addWidget(self.visualization_frame)
        #self.frame3.setHidden(True)
        # --
        self.button_fixation_color = QPushButton("Fixation Color")
        
        
        self.button_saccade_color = QPushButton("Saccade Color")
        

        self.button_current_fixation_color = QPushButton("Current Fix. Color")
        

        self.button_suggested_fixation_color = QPushButton("Suggestion Color")
        

        self.button_coloblind_assist = QPushButton("Colorblind Assist")
        

        self.button_fixation_color.setEnabled(False)
        self.button_saccade_color.setEnabled(False)
        self.button_current_fixation_color.setEnabled(False)
        self.button_suggested_fixation_color.setEnabled(False)
        self.button_coloblind_assist.setEnabled(False)

        self.layer_fixation_color = QHBoxLayout()
        self.layer_fixation_color.addWidget(self.button_fixation_color)
        self.layer_fixation_color.addWidget(self.button_saccade_color)

        

        self.second_layer_fixation_color = QHBoxLayout()
        self.second_layer_fixation_color.addWidget(self.button_current_fixation_color)
        self.second_layer_fixation_color.addWidget(self.button_suggested_fixation_color)

        self.third_layer_fixation_color = QHBoxLayout()

        
        self.third_layer_fixation_color.addWidget(self.button_coloblind_assist)

        self.filters.addLayout(self.layer_fixation_color)
        self.filters.addLayout(self.second_layer_fixation_color)
        self.filters.addLayout(self.third_layer_fixation_color)

        self.left_side.addLayout(self.below_canvas)
        # --

        #self.right_side.addLayout(self.below_canvas)

        # add both sides to overall wrapper layout
        self.wrapper_layout.addLayout(self.left_side)
        self.wrapper_layout.addLayout(self.right_side)
        self.wrapper_layout.setStretch(0, 1)
        self.wrapper_layout.setStretch(1, 3)

        # initial button states
        self.canvas_toolbar.setEnabled(False)
        self.checkbox_show_aoi.setChecked(False)
        self.checkbox_show_aoi.setCheckable(False)
        self.checkbox_show_fixations.setChecked(False)
        self.checkbox_show_fixations.setCheckable(False)


        #self.button_next_fixation.setEnabled(False)
        self.checkbox_show_suggestion.setChecked(False)
        self.checkbox_show_suggestion.setCheckable(False)

        widget = QWidget()
        widget.setLayout(self.wrapper_layout)
        self.setCentralWidget(widget)
        self.showMaximized()

        # styling menu bar
        self.menuBar().setStyleSheet("QMenuBar {font-size: 14px; color: black; padding: 2px; margin: 0px; border-radius: 4px;}")
        # add menues
        self.file_menu = self.menuBar().addMenu("File")
        self.edit_menu = self.menuBar().addMenu("Edit")
        self.view_menu = self.menuBar().addMenu("View")

        self.generate_menu = self.menuBar().addMenu("Generate")
        self.synthetic_data_menu = self.generate_menu.addMenu("Synthetic Data")
        self.distortions_menu = self.generate_menu.addMenu("Distortions")

        self.filters_menu = self.menuBar().addMenu("Filters")

        self.correction_menu = self.menuBar().addMenu("Correction")
        self.automated_correction_menu = self.correction_menu.addMenu("Automatic")
        self.semi_auto_correction_menu = self.correction_menu.addMenu("Assisted")

        self.analyses_menu = self.menuBar().addMenu("Analyses")
        self.converters_menu = self.menuBar().addMenu("Converters")

        # add actions
        self.new_file_action = QAction(QIcon("./.images/open.png"), "Open Folder", self)
        self.open_image_action = QAction("Open Image", self)
        self.save_correction_json_action = QAction("Save json", self)
        self.save_correction_CSV_action = QAction("Save CSV", self)

        self.undo_correction_action = QAction("Undo", self)
        self.next_fixation_action = QAction("Next Fixation", self)
        self.previous_fixation_action = QAction("Previous Fixation", self)
        self.accept_and_next_action = QAction("Accept suggestion", self)
        self.delete_fixation_action = QAction("Delete Fixation", self)

        self.trial_list_action = QAction("Show/Hide Trial List", self)
        self.trial_summary_action = QAction("Show/Hide Trial Summary", self)
        self.visualization_panel_action = QAction("Show/Hide Visualization Panel", self)
        self.hude_side_panel_action = QAction("Show/Hide Side Panel", self)

        self.generate_fixations_action = QAction("Generate Fixations", self)
        self.generate_fixations_skip_action = QAction("Generate Fixations (Skip)", self)
        self.generat_within_line_regression_action = QAction("Generate Within Line Regression", self)
        self.generate_between_line_regression_action = QAction("Generate Between Line Regression", self)
        self.generate_noise_action = QAction("Generate Noise", self)
        self.generate_slope_action = QAction("Generate Slope", self)
        self.generate_offset_action = QAction("Generate Offset", self)
        self.generate_shift_action = QAction("Generate Shift", self)

        self.lowpass_duration_filter_action = QAction("Filters less than", self)
        self.highpass_duration_filter_action = QAction("Filters greater than", self)
        self.outlier_duration_filter_action = QAction("Outlier Filter", self)
        self.merge_fixations_filter_action = QAction("Merge Fixations", self)
        self.outside_screen_filter_action = QAction("Outside Screen", self)

        self.manual_correction_action = QAction("Manual", self)
        self.warp_auto_action = QAction("Warp", self)
        self.attach_auto_action = QAction("Attach", self)
        self.chain_auto_action = QAction("Chain", self)
        self.cluster_auto_action = QAction("Cluster", self)
        self.merge_auto_action = QAction("Merge", self)
        self.regress_auto_action = QAction("Regress", self)
        self.segment_auto_action = QAction("Segment", self)
        self.stretch_auto_action = QAction("Stretch", self)

        self.warp_semi_action = QAction("Warp", self)
        self.attach_semi_action = QAction("Attach", self)
        self.chain_semi_action = QAction("Chain", self)
        self.cluster_semi_action = QAction("Cluster", self)
        self.merge_semi_action = QAction("Merge", self)
        self.regress_semi_action = QAction("Regress", self)
        self.segment_semi_action = QAction("Segment", self)
        self.stretch_semi_action = QAction("Stretch", self)

        self.ascii_to_csv_converter_action = QAction("ASCII to CSV (one trial)", self)
        self.eyelink_experiment_to_csv_converter_action = QAction("Eyelink Experiment to CSV", self)

        # add shortcuts
        self.new_file_action.setShortcut("Ctrl+O")
        self.save_correction_CSV_action.setShortcut("Ctrl+S")

        self.next_fixation_action.setShortcut("a")
        self.previous_fixation_action.setShortcut("z")
        self.undo_correction_action.setShortcut("Ctrl+Z")
        self.accept_and_next_action.setShortcut("space")
        self.delete_fixation_action.setShortcut("backspace")

        # enable/disable
        self.save_correction_json_action.setEnabled(False)
        self.save_correction_CSV_action.setEnabled(False)
        self.edit_menu.setEnabled(False)
        self.generate_menu.setEnabled(False)
        self.filters_menu.setEnabled(False)
        self.correction_menu.setEnabled(False)
        self.analyses_menu.setEnabled(False)

        # add actions to menu
        self.file_menu.addAction(self.new_file_action)
        self.file_menu.addAction(self.open_image_action)
        self.file_menu.addAction(self.save_correction_json_action)
        self.file_menu.addAction(self.save_correction_CSV_action)

        self.edit_menu.addAction(self.next_fixation_action)
        self.edit_menu.addAction(self.previous_fixation_action)
        self.edit_menu.addAction(self.accept_and_next_action)
        self.edit_menu.addAction(self.undo_correction_action)
        self.edit_menu.addAction(self.delete_fixation_action)

        self.view_menu.addAction(self.trial_list_action)
        self.view_menu.addAction(self.trial_summary_action)
        self.view_menu.addAction(self.visualization_panel_action)
        self.view_menu.addAction(self.hude_side_panel_action)

        # Generate
        self.synthetic_data_menu.addAction(self.generate_fixations_action)
        self.synthetic_data_menu.addAction(self.generate_fixations_skip_action)
        self.synthetic_data_menu.addAction(self.generat_within_line_regression_action)
        self.synthetic_data_menu.addAction(self.generate_between_line_regression_action)
        self.distortions_menu.addAction(self.generate_noise_action)
        self.distortions_menu.addAction(self.generate_slope_action)
        self.distortions_menu.addAction(self.generate_offset_action)
        self.distortions_menu.addAction(self.generate_shift_action)        
        
        self.filters_menu.addAction(self.lowpass_duration_filter_action)
        self.filters_menu.addAction(self.highpass_duration_filter_action)
        self.filters_menu.addAction(self.outlier_duration_filter_action)
        self.filters_menu.addAction(self.merge_fixations_filter_action)
        self.filters_menu.addAction(self.outside_screen_filter_action)

        self.correction_menu.addAction(self.manual_correction_action)
        self.automated_correction_menu.addAction(self.warp_auto_action)
        self.automated_correction_menu.addAction(self.attach_auto_action)
        self.automated_correction_menu.addAction(self.chain_auto_action)
        self.automated_correction_menu.addAction(self.cluster_auto_action)
        self.automated_correction_menu.addAction(self.merge_auto_action)
        self.automated_correction_menu.addAction(self.regress_auto_action)
        self.automated_correction_menu.addAction(self.segment_auto_action)
        self.automated_correction_menu.addAction(self.stretch_auto_action)

        self.semi_auto_correction_menu.addAction(self.warp_semi_action)
        self.semi_auto_correction_menu.addAction(self.attach_semi_action)
        self.semi_auto_correction_menu.addAction(self.chain_semi_action)
        self.semi_auto_correction_menu.addAction(self.cluster_semi_action)
        self.semi_auto_correction_menu.addAction(self.merge_semi_action)
        self.semi_auto_correction_menu.addAction(self.regress_semi_action)
        self.semi_auto_correction_menu.addAction(self.segment_semi_action)
        self.semi_auto_correction_menu.addAction(self.stretch_semi_action)

        self.converters_menu.addAction(self.ascii_to_csv_converter_action)
        self.converters_menu.addAction(self.eyelink_experiment_to_csv_converter_action)

        # add menue item called "Style" to the menu bar
        self.menu_style = self.menuBar().addMenu("Appearance")

        action = QAction('Default', self)
        action.triggered.connect(lambda _, theme='Default': self.apply_stylesheet(self, 'my_theme.xml'))
        self.menu_style.addAction(action)

        # add sub menue to the menue item "Style" for Dark
        self.dark_menue_style = self.menu_style.addMenu("Dark")
        self.light_menue_style = self.menu_style.addMenu("Light")

        # add actions to the menu item "Style"
        for theme in list_themes():
            action = QAction(theme.replace('.xml', '').replace('_', ' '), self)
            action.triggered.connect(lambda _, theme=theme: self.apply_stylesheet(self, theme))

            if 'dark' in theme.lower():
                self.dark_menue_style.addAction(action)
            else:
                self.light_menue_style.addAction(action)

        self.canvas.mpl_connect("button_press_event", self.fix8.button_press_callback)
        self.canvas.mpl_connect("button_release_event", self.fix8.button_release_callback)
        self.canvas.mpl_connect("motion_notify_event", self.fix8.motion_notify_callback)

        self.trial_list.itemDoubleClicked.connect(self.fix8.trial_double_clicked)
        self.button_previous_fixation.clicked.connect(self.fix8.previous_fixation)
        self.button_next_fixation.clicked.connect(self.fix8.next_fixation)
        self.progress_bar.valueChanged.connect(self.fix8.progress_bar_updated)
        self.checkbox_show_aoi.stateChanged.connect(self.fix8.quick_draw_canvas)
        self.toggle_aoi_width.valueChanged.connect(self.fix8.aoi_width_changed)
        self.toggle_aoi_height.valueChanged.connect(self.fix8.aoi_height_changed)
        self.checkbox_show_fixations.stateChanged.connect(self.fix8.quick_draw_canvas)
        self.toggle_fixation_opacity.valueChanged.connect(self.fix8.fixation_opacity_changed)
        self.checkbox_show_saccades.stateChanged.connect(self.fix8.quick_draw_canvas)
        self.toggle_saccade_opacity.valueChanged.connect(self.fix8.saccade_opacity_changed)
        self.fixation_size_bar.valueChanged.connect(self.fix8.fixation_size_changed)
        self.button_fixation_color.clicked.connect(self.fix8.select_fixation_color)
        self.button_saccade_color.clicked.connect(self.fix8.select_saccade_color)
        self.button_current_fixation_color.clicked.connect(self.fix8.select_current_fixation_color)
        self.button_suggested_fixation_color.clicked.connect(self.fix8.select_suggested_fixation_color)
        self.button_coloblind_assist.clicked.connect(self.fix8.colorblind_assist)
        # connect functions
        self.new_file_action.triggered.connect(self.fix8.open_trial_folder)
        self.open_image_action.triggered.connect(self.fix8.open_image)
        self.save_correction_json_action.triggered.connect(self.fix8.save_corrections_json)
        self.save_correction_CSV_action.triggered.connect(self.fix8.save_corrections_csv)

        self.next_fixation_action.triggered.connect(self.fix8.next_fixation)
        self.previous_fixation_action.triggered.connect(self.fix8.previous_fixation)
        self.accept_and_next_action.triggered.connect(self.fix8.confirm_suggestion)
        self.delete_fixation_action.triggered.connect(self.fix8.remove_fixation)
        self.undo_correction_action.triggered.connect(self.fix8.undo)

        self.trial_list_action.triggered.connect(self.show_hide_trial_list)
        self.trial_summary_action.triggered.connect(self.show_hide_trial_summary)
        self.visualization_panel_action.triggered.connect(self.show_hide_visualization_panel)
        self.hude_side_panel_action.triggered.connect(self.show_hide_side_panel)

        self.generate_fixations_action.triggered.connect(self.fix8.generate_fixations)
        self.generate_fixations_skip_action.triggered.connect(self.fix8.generate_fixations_skip)
        self.generat_within_line_regression_action.triggered.connect(self.fix8.generate_within_line_regression)
        self.generate_between_line_regression_action.triggered.connect(self.fix8.generate_between_line_regression)
        self.generate_noise_action.triggered.connect(self.fix8.generate_noise)
        self.generate_slope_action.triggered.connect(self.fix8.generate_slope)
        self.generate_offset_action.triggered.connect(self.fix8.generate_offset)
        self.generate_shift_action.triggered.connect(self.fix8.generate_shift)

        self.lowpass_duration_filter_action.triggered.connect(self.fix8.lowpass_duration_filter)
        self.highpass_duration_filter_action.triggered.connect(self.fix8.highpass_duration_filter)
        self.outlier_duration_filter_action.triggered.connect(self.fix8.outlier_duration_filter)
        self.merge_fixations_filter_action.triggered.connect(self.fix8.merge_fixations)
        self.outside_screen_filter_action.triggered.connect(self.fix8.outside_screen_filter)

        self.warp_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('warp', drift.warp, 'auto'))
        self.attach_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('attach', drift.attach, 'auto'))
        self.chain_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('chain', drift.chain, 'auto'))
        self.cluster_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('cluster', drift.cluster, 'auto'))
        self.merge_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('merge', drift.merge, 'auto'))
        self.regress_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('regress', drift.regress, 'auto'))
        self.segment_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('segment', drift.segment, 'auto'))
        self.stretch_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('stretch', drift.stretch, 'auto'))

        self.warp_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('warp', drift.warp, 'semi'))
        self.attach_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('attach', drift.attach, 'semi'))
        self.chain_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('chain', drift.chain, 'semi'))
        self.cluster_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('cluster', drift.cluster, 'semi'))
        self.merge_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('merge', drift.merge, 'semi'))
        self.regress_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('regress', drift.regress, 'semi'))
        self.segment_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('segment', drift.segment, 'semi'))
        self.stretch_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('stretch', drift.stretch, 'semi'))
        self.manual_correction_action.triggered.connect(self.fix8.manual_correction)

        self.ascii_to_csv_converter_action.triggered.connect(self.fix8.ascii_to_csv_converter)
        self.eyelink_experiment_to_csv_converter_action.triggered.connect(self.fix8.eyelink_experiment_to_csv_converter)

    def relevant_buttons(self, feature):
        if feature == "opened_stimulus":
            self.checkbox_show_aoi.setCheckable(True)
            self.checkbox_show_aoi.setChecked(False)
            self.checkbox_show_aoi.setEnabled(True)
            self.toggle_aoi_width.setEnabled(True)
            self.toggle_aoi_height.setEnabled(True)
            self.canvas_toolbar.setEnabled(True)
            self.checkbox_show_fixations.setCheckable(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setCheckable(True)
            self.checkbox_show_saccades.setCheckable(False)
            self.checkbox_show_saccades.setChecked(False)
            self.checkbox_show_saccades.setCheckable(True)
        elif feature == "opened_folder":
            self.button_previous_fixation.setEnabled(False)
            self.button_next_fixation.setEnabled(False)


            self.checkbox_show_fixations.setCheckable(False)
            self.checkbox_show_fixations.setChecked(False)
            self.checkbox_show_fixations.setEnabled(False)

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
            self.fixation_size_bar.setEnabled(False)

        elif feature == "trial_clicked":
            self.save_correction_json_action.setEnabled(True)
            self.save_correction_CSV_action.setEnabled(True)
            self.edit_menu.setEnabled(True)
            self.filters_menu.setEnabled(True)
            self.generate_menu.setEnabled(True)
            self.correction_menu.setEnabled(True)
            self.analyses_menu.setEnabled(True)

            self.button_previous_fixation.setEnabled(True)
            self.button_next_fixation.setEnabled(True)
            self.checkbox_show_aoi.setCheckable(True)
            self.checkbox_show_aoi.setEnabled(True)

            self.checkbox_show_fixations.setCheckable(True)
            self.checkbox_show_fixations.setEnabled(True)

            self.checkbox_show_saccades.setCheckable(True)
            self.checkbox_show_saccades.setEnabled(True)

            self.toggle_aoi_width.setEnabled(True)
            self.toggle_aoi_height.setEnabled(True)
            self.button_fixation_color.setEnabled(True)
            self.button_saccade_color.setEnabled(True)
            self.button_suggested_fixation_color.setEnabled(False)
            self.button_current_fixation_color.setEnabled(True)
            self.toggle_fixation_opacity.setEnabled(True)
            self.toggle_saccade_opacity.setEnabled(True)
            self.fixation_size_bar.setEnabled(True)
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

    
    def show_hide_side_panel(self):
        if not self.trial_list.isHidden() or not self.visualization_frame.isHidden():
            self.hide_side_panel()
        else:
            self.show_side_panel()

    def hide_side_panel(self):
        self.trial_list.setHidden(True)
        self.visualization_frame.setHidden(True)

    def show_side_panel(self):
        self.trial_list.setHidden(False)
        self.visualization_frame.setHidden(False)

    def show_hide_trial_list(self):
        self.trial_list.setHidden(not self.trial_list.isHidden())

    def show_hide_trial_summary(self):
        pass

    def show_hide_visualization_panel(self):
        self.visualization_frame.setHidden(not self.visualization_frame.isHidden())