

from qt_material import QtStyleTools, list_themes
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QSpinBox,
    QStatusBar,
    QAction,
    QTableWidget, 
    QTableWidgetItem,
    QSpacerItem
)

from . import canvas_resources
from . import driftAlgorithms as drift
from . import correction

class Ui_Main_Window(QMainWindow, QtStyleTools):
    def __init__(self, fix8):
        super().__init__()
        self.fix8 = fix8
        self.setWindowTitle("Fix8")
        self.setWindowIcon(QIcon("src/.images/icon.ico"))
        self.init_UI()
        self.apply_stylesheet(self, 'src/my_theme.xml')
    


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
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        
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



        # section for trial statistics panel
        self.trial_statistics = QVBoxLayout()

        # add a qtablewidget for trial statistics
        self.statistics_table = QTableWidget(self)

        self.statistics_table.setColumnCount(2)
        self.statistics_table.setRowCount(5)
        # remove horizontal and vertical headers
        self.statistics_table.verticalHeader().setVisible(False)
        self.statistics_table.horizontalHeader().setVisible(False)

        self.statistics_table.setItem(0, 0, QTableWidgetItem("Trial duration"))
        self.statistics_table.setItem(1, 0, QTableWidgetItem("Max fixation duration"))
        self.statistics_table.setItem(2, 0, QTableWidgetItem("Min fixation duration"))
        self.statistics_table.setItem(3, 0, QTableWidgetItem("Number of AOIs"))
        self.statistics_table.setItem(4, 0, QTableWidgetItem("Number of regressions"))
        #self.statistics_table.setItem(5, 0, QTableWidgetItem("Current x, y, duration"))

        self.statistics_table.setItem(0, 1, QTableWidgetItem("0"))
        self.statistics_table.setItem(1, 1, QTableWidgetItem("0"))
        self.statistics_table.setItem(2, 1, QTableWidgetItem("0"))
        self.statistics_table.setItem(3, 1, QTableWidgetItem("0"))
        self.statistics_table.setItem(4, 1, QTableWidgetItem("-"))
        #self.statistics_table.setItem(5, 1, QTableWidgetItem("0"))

        # expand the first column horizontally to show the text
        self.statistics_table.horizontalHeader().setSectionResizeMode(0, 1)
        self.statistics_table.horizontalHeader().setSectionResizeMode(1, 1)

        # add the table to the layout
        self.trial_statistics.addWidget(self.statistics_table)

        self.statistics_table.setHidden(True)
        self.left_side.addLayout(self.trial_statistics)
        

        # --- section for visualization panel
        self.visualization_panel = QHBoxLayout()
        self.filters = QVBoxLayout()

        self.label_filters = QLabel("Visualization")
        self.label_filters.setAlignment(Qt.AlignCenter)
        self.filters.addWidget(self.label_filters)
        self.filters.addSpacerItem(QSpacerItem(20, 10))
        
        # ---------------------------------------------------------------------

        # Fixations
        self.fixation_layer_top = QHBoxLayout()
        self.checkbox_show_fixations = QCheckBox("Show Fixations")
        self.checkbox_show_fixations.setEnabled(False)
        self.fixation_layer_top.addWidget(self.checkbox_show_fixations)

        self.fixation_opacity_layer = QHBoxLayout()
        self.toggle_fixation_opacity = QSpinBox()
        self.toggle_fixation_opacity.setMaximum(10)
        self.toggle_fixation_opacity.setValue(4)
        self.toggle_fixation_opacity.setMinimum(1)
        self.fixation_opacity_text = QLabel("Opacity")
        self.toggle_fixation_opacity.setEnabled(False)

        self.fixation_opacity_layer.addWidget(self.toggle_fixation_opacity)
        self.fixation_opacity_layer.addWidget(self.fixation_opacity_text)

        self.fixation_layer_top.addLayout(self.fixation_opacity_layer)
        # self.fixation_layer.addWidget(self.fixation_opacity_text)

        self.filters.addLayout(self.fixation_layer_top)

        # layer for fixation size customization 
        self.fixation_layer_middle = QHBoxLayout()
        self.checkbox_show_order = QCheckBox("Fixation order")
        self.checkbox_show_order.setEnabled(False)
        self.fixation_layer_middle.addWidget(self.checkbox_show_order)

        self.fixation_size_layer = QHBoxLayout()
        self.fixation_size_box = QSpinBox()
        self.fixation_size_box.setMinimum(1)
        self.fixation_size_box.setMaximum(30)
        self.fixation_size_box.setValue(5)
        self.fixation_size_box.setEnabled(False)
        self.fixation_size_text = QLabel("Size")
        self.fixation_size_layer.addWidget(self.fixation_size_box)
        self.fixation_size_layer.addWidget(self.fixation_size_text)
        self.fixation_layer_middle.addLayout(self.fixation_size_layer)

        self.filters.addLayout(self.fixation_layer_middle)

        self.fixation_layer_bottom = QHBoxLayout()
        self.button_fixation_color = QPushButton("Fixation Color")
        self.button_current_fixation_color = QPushButton("Current Fix. Color")
        self.button_fixation_color.setEnabled(False)
        self.button_current_fixation_color.setEnabled(False)
        
        self.fixation_layer_bottom.addWidget(self.button_fixation_color)
        self.fixation_layer_bottom.addWidget(self.button_current_fixation_color)

        self.filters.addLayout(self.fixation_layer_bottom)

        # -- 4th layer
        self.suggestion_4th_layer = QHBoxLayout()
        self.checkbox_show_all_fixations = QCheckBox("Show Remaining Fix.")
        self.checkbox_show_all_fixations.setEnabled(False)
        self.suggestion_4th_layer.addWidget(self.checkbox_show_all_fixations)

        self.button_remaining_fixation_color = QPushButton("Next Fix. Color")
        self.button_remaining_fixation_color.setEnabled(False)
        self.suggestion_4th_layer.addWidget(self.button_remaining_fixation_color)
        self.filters.addLayout(self.suggestion_4th_layer)

        self.filters.addSpacerItem(QSpacerItem(20, 10))
        fixation_line_separator = QFrame(self)
        fixation_line_separator.setFrameShape(QFrame.HLine)
        fixation_line_separator.setFrameShadow(QFrame.Sunken)
        self.filters.addWidget(fixation_line_separator)
        self.filters.addSpacerItem(QSpacerItem(20, 10))
        
        # ---------------------------------------------------------------------
        # Suggestion
        self.suggestion_layer_top = QHBoxLayout()
        self.checkbox_show_suggestion = QCheckBox("Show Suggestion")
        self.checkbox_show_suggestion.setEnabled(False)
        # self.checkbox_show_suggestion.stateChanged.connect(self.show_suggestion)
        self.suggestion_layer_top.addWidget(self.checkbox_show_suggestion)

        
        self.button_suggested_fixation_color = QPushButton("Suggestion Color")
        self.button_suggested_fixation_color.setEnabled(False)
        self.suggestion_layer_top.addWidget(self.button_suggested_fixation_color)
        self.filters.addLayout(self.suggestion_layer_top)
        

        self.filters.addSpacerItem(QSpacerItem(20, 10))
        suggestion_line_separator = QFrame(self)
        suggestion_line_separator.setFrameShape(QFrame.HLine)
        suggestion_line_separator.setFrameShadow(QFrame.Sunken)
        self.filters.addWidget(suggestion_line_separator)
        self.filters.addSpacerItem(QSpacerItem(20, 10))

        # ---------------------------------------------------------------------
        # Saccades
        self.saccade_layer_top = QHBoxLayout()
        self.checkbox_show_saccades = QCheckBox("Show Saccades")
        self.checkbox_show_saccades.setEnabled(False)
        self.saccade_layer_top.addWidget(self.checkbox_show_saccades)
        
        self.saccade_opacity_layer = QHBoxLayout()
        self.toggle_saccade_opacity = QSpinBox()
        self.toggle_saccade_opacity.setMaximum(10)
        self.toggle_saccade_opacity.setValue(4)
        self.toggle_saccade_opacity.setMinimum(1)
        self.toggle_saccade_opacity.setEnabled(False)
        self.saccade_opacity_text = QLabel("Opacity")
        self.saccade_opacity_layer.addWidget(self.toggle_saccade_opacity)
        self.saccade_opacity_layer.addWidget(self.saccade_opacity_text)
        self.saccade_layer_top.addLayout(self.saccade_opacity_layer)

        self.filters.addLayout(self.saccade_layer_top)

        
        self.saccade_layer_middle = QHBoxLayout()
        self.button_saccade_color = QPushButton("Saccade Color")
        self.button_saccade_color.setEnabled(False)
        self.saccade_layer_middle.addWidget(self.button_saccade_color)
        
        self.saccade_size_layer = QHBoxLayout()
        self.saccade_size_box = QSpinBox()
        self.saccade_size_box.setMinimum(1)
        self.saccade_size_box.setMaximum(30)
        self.saccade_size_box.setValue(1)
        self.saccade_size_box.setEnabled(False)
        self.saccade_size_text = QLabel("Width")
        self.saccade_size_layer.addWidget(self.saccade_size_box)
        self.saccade_size_layer.addWidget(self.saccade_size_text)
        self.saccade_layer_middle.addLayout(self.saccade_size_layer)

        self.filters.addLayout(self.saccade_layer_middle)
        
        







        # ---

        self.visualization_frame = QFrame()
        self.visualization_frame.setLayout(self.filters)
        self.visualization_panel.addWidget(self.visualization_frame)

        # --




        self.filters.addSpacerItem(QSpacerItem(20, 10))
        saccade_line_separator = QFrame(self)
        saccade_line_separator.setFrameShape(QFrame.HLine)
        saccade_line_separator.setFrameShadow(QFrame.Sunken)
        self.filters.addWidget(saccade_line_separator)
        self.filters.addSpacerItem(QSpacerItem(20, 10))
        
        # self.colorblind_button_layer.addWidget(self.button_coloblind_assist)
        # self.button_coloblind_assist = QPushButton("Colorblind Assist")
        # self.button_coloblind_assist.setEnabled(False)

        #self.layer_fixation_color = QHBoxLayout()
        #self.layer_fixation_color.addWidget(self.button_fixation_color)
        

        #self.second_layer_fixation_color = QHBoxLayout()
        #self.second_layer_fixation_color.addWidget(self.button_current_fixation_color)
        #self.second_layer_fixation_color.addWidget(self.button_suggested_fixation_color)

        #self.colorblind_button_layer = QHBoxLayout()
        
        
        #self.filters.addLayout(self.layer_fixation_color)
        #self.filters.addLayout(self.second_layer_fixation_color)

        # ---------------------------------------------------------------------
        # AOI 
        self.aoi_layer_top = QHBoxLayout()

        
        self.checkbox_show_aoi = QCheckBox("Show AOIs")
        self.checkbox_show_aoi.setEnabled(False)

        self.aoi_width_layer = QHBoxLayout()
        self.toggle_aoi_width = QSpinBox()
        self.toggle_aoi_width.setMaximum(50)
        self.toggle_aoi_width.setMinimum(1)
        self.toggle_aoi_width.setValue(7)
        self.aoi_width_text = QLabel("Width")
        self.aoi_width_layer.addWidget(self.toggle_aoi_width)
        self.aoi_width_layer.addWidget(self.aoi_width_text)
        self.toggle_aoi_width.setEnabled(False)

        self.aoi_layer_top.addWidget(self.checkbox_show_aoi)
        self.aoi_layer_top.addLayout(self.aoi_width_layer)

        self.aoi_layer_bottom = QHBoxLayout()
        self.button_aoi_color = QPushButton("AOIs Color")
        self.button_aoi_color.setEnabled(False)
        self.aoi_layer_bottom.addWidget(self.button_aoi_color)
        
        self.aoi_height_layer = QHBoxLayout()
        self.toggle_aoi_height = QSpinBox()
        self.toggle_aoi_height.setMaximum(100)
        self.toggle_aoi_height.setMinimum(1)
        self.toggle_aoi_height.setValue(4)
        self.aoi_height_text = QLabel("Height")
        self.toggle_aoi_height.setEnabled(False)
        self.aoi_height_layer.addWidget(self.toggle_aoi_height)
        self.aoi_height_layer.addWidget(self.aoi_height_text)

        self.aoi_layer_bottom.addLayout(self.aoi_height_layer)

        self.filters.addLayout(self.aoi_layer_top)
        self.filters.addLayout(self.aoi_layer_bottom)



        #self.filters.addLayout(self.colorblind_button_layer)

        self.left_side.addLayout(self.visualization_panel)


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
        self.new_file_action = QAction(QIcon("src/.images/open.png"), "Open Trial Folder", self)
        self.open_image_action = QAction("Open Image", self)
        self.open_trial_action = QAction("Open Trial", self)
        self.open_aoi_action = QAction("Open AOI", self)
        self.save_correction_json_action = QAction("Save Json", self)
        self.save_correction_CSV_action = QAction("Save CSV", self)
        self.save_aoi_csv_action = QAction("Save AOI file", self)
        self.undo_correction_action = QAction("Undo", self)
        self.next_fixation_action = QAction("Next", self)
        self.previous_fixation_action = QAction("Previous", self)
        self.assign_above_action = QAction("Assign Above", self)
        self.assign_below_action = QAction("Assign Below", self)
        self.accept_and_next_action = QAction("Accept suggestion", self)
        self.delete_fixation_action = QAction("Delete Fixation", self)

        self.trial_list_action = QAction("Show/Hide Trial List", self)
        self.trial_summary_action = QAction("Show/Hide Trial Summary", self)
        self.visualization_panel_action = QAction("Show/Hide Visualization Panel", self)
        self.hide_side_panel_action = QAction("Show/Hide Side Panel", self)

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
        self.outlier_metrics_filter_action = QAction("Outlier Metrics Filter", self)
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
        self.slice_auto_action = QAction("Slice", self)
        
        self.warp_attach_auto_action = QAction("Warp+Attach", self)
        self.warp_chain_auto_action = QAction("Warp+Chain", self)
        self.war_regress_auto_action = QAction("Warp+Regress", self)
        self.warp_stretch_auto_action = QAction("Warp+Stretch", self)

        self.warp_semi_action = QAction("Warp", self)
        self.attach_semi_action = QAction("Attach", self)
        self.chain_semi_action = QAction("Chain", self)
        self.cluster_semi_action = QAction("Cluster", self)
        self.merge_semi_action = QAction("Merge", self)
        self.regress_semi_action = QAction("Regress", self)
        self.segment_semi_action = QAction("Segment", self)
        self.stretch_semi_action = QAction("Stretch", self)
        self.slice_semi_action = QAction("Slice", self)

        self.warp_attach_semi_action = QAction("Warp+Attach", self)
        self.warp_chain_semi_action = QAction("Warp+Chain", self)
        self.war_regress_semi_action = QAction("Warp+Regress", self)
        self.warp_stretch_semi_action = QAction("Warp+Stretch", self)

        self.fixation_report_action = QAction("Fixation Report", self)
        self.saccade_report_action = QAction("Saccade Report", self)
        self.aoi_report_action = QAction("AOI Report", self)
        self.aoi_metrics_report_action = QAction("AOI Metrics Report", self)

        self.ascii_to_csv_converter_action = QAction("ASCII to CSV (one trial)", self)
        self.json_to_csv_converter_action = QAction("JSON to CSV (one trial)", self)
        self.csv_to_json_converter_action = QAction("CSV to JSON (one trial)", self)
        self.eyelink_experiment_to_csv_converter_action = QAction("Eyelink Experiment to CSV", self)

        self.assign_line_1_action = QAction("Assign to Line 1", self)
        self.assign_line_2_action = QAction("Assign to Line 2", self)
        self.assign_line_3_action = QAction("Assign to Line 3", self)
        self.assign_line_4_action = QAction("Assign to Line 4", self)
        self.assign_line_5_action = QAction("Assign to Line 5", self)
        self.assign_line_6_action = QAction("Assign to Line 6", self)
        self.assign_line_7_action = QAction("Assign to Line 7", self)
        self.assign_line_8_action = QAction("Assign to Line 8", self)
        self.assign_line_9_action = QAction("Assign to Line 9", self)

        # add shortcuts
        self.new_file_action.setShortcut("Ctrl+O")
        self.save_correction_CSV_action.setShortcut("Ctrl+S")
        self.next_fixation_action.setShortcut("right")
        self.previous_fixation_action.setShortcut("left")
        self.assign_above_action.setShortcut("a")
        self.assign_below_action.setShortcut("z")
        self.undo_correction_action.setShortcut("Ctrl+Z")
        self.accept_and_next_action.setShortcut("space")
        self.delete_fixation_action.setShortcut("backspace")

        # add shortcuts for numbers from 1 to 9
        self.assign_line_1_action.setShortcut("1")
        self.assign_line_2_action.setShortcut("2")
        self.assign_line_3_action.setShortcut("3")
        self.assign_line_4_action.setShortcut("4")
        self.assign_line_5_action.setShortcut("5")
        self.assign_line_6_action.setShortcut("6")
        self.assign_line_7_action.setShortcut("7")
        self.assign_line_8_action.setShortcut("8")
        self.assign_line_9_action.setShortcut("9")        

        # enable/disable
        self.save_correction_json_action.setEnabled(False)
        self.save_correction_CSV_action.setEnabled(False)
        self.open_trial_action.setEnabled(False)
        self.open_aoi_action.setEnabled(False)
        self.save_aoi_csv_action.setEnabled(False)
        
        self.edit_menu.setEnabled(False)
        self.generate_menu.setEnabled(False)
        self.filters_menu.setEnabled(False)
        self.correction_menu.setEnabled(False)
        self.analyses_menu.setEnabled(False)

        # add actions to menu
        self.file_menu.addAction(self.new_file_action)
        self.file_menu.addAction(self.open_image_action)
        self.file_menu.addAction(self.open_trial_action)
        self.file_menu.addAction(self.open_aoi_action)
        self.file_menu.addAction(self.save_correction_json_action)
        self.file_menu.addAction(self.save_aoi_csv_action)
        self.file_menu.addAction(self.save_correction_CSV_action)

        self.edit_menu.addAction(self.next_fixation_action)
        self.edit_menu.addAction(self.previous_fixation_action)
        self.edit_menu.addAction(self.assign_above_action)
        self.edit_menu.addAction(self.assign_below_action)
        self.edit_menu.addAction(self.accept_and_next_action)
        self.edit_menu.addAction(self.undo_correction_action)
        self.edit_menu.addAction(self.delete_fixation_action)
        self.edit_menu.addAction(self.assign_line_1_action)
        self.edit_menu.addAction(self.assign_line_2_action)
        self.edit_menu.addAction(self.assign_line_3_action)
        self.edit_menu.addAction(self.assign_line_4_action)
        self.edit_menu.addAction(self.assign_line_5_action)
        self.edit_menu.addAction(self.assign_line_6_action)
        self.edit_menu.addAction(self.assign_line_7_action)
        self.edit_menu.addAction(self.assign_line_8_action)
        self.edit_menu.addAction(self.assign_line_9_action)

        self.view_menu.addAction(self.trial_list_action)
        self.view_menu.addAction(self.trial_summary_action)
        self.view_menu.addAction(self.visualization_panel_action)
        self.view_menu.addAction(self.hide_side_panel_action)

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
        self.filters_menu.addAction(self.outlier_metrics_filter_action)
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
        self.automated_correction_menu.addAction(self.slice_auto_action)
        self.automated_correction_menu.addAction(self.warp_attach_auto_action)
        self.automated_correction_menu.addAction(self.warp_chain_auto_action)
        self.automated_correction_menu.addAction(self.war_regress_auto_action)
        self.automated_correction_menu.addAction(self.warp_stretch_auto_action)

        self.semi_auto_correction_menu.addAction(self.warp_semi_action)
        self.semi_auto_correction_menu.addAction(self.attach_semi_action)
        self.semi_auto_correction_menu.addAction(self.chain_semi_action)
        self.semi_auto_correction_menu.addAction(self.cluster_semi_action)
        self.semi_auto_correction_menu.addAction(self.merge_semi_action)
        self.semi_auto_correction_menu.addAction(self.regress_semi_action)
        self.semi_auto_correction_menu.addAction(self.segment_semi_action)
        self.semi_auto_correction_menu.addAction(self.stretch_semi_action)
        self.semi_auto_correction_menu.addAction(self.slice_semi_action)
        self.semi_auto_correction_menu.addAction(self.warp_attach_semi_action)
        self.semi_auto_correction_menu.addAction(self.warp_chain_semi_action)
        self.semi_auto_correction_menu.addAction(self.war_regress_semi_action)
        self.semi_auto_correction_menu.addAction(self.warp_stretch_semi_action)

        self.analyses_menu.addAction(self.fixation_report_action)
        self.analyses_menu.addAction(self.saccade_report_action)
        self.analyses_menu.addAction(self.aoi_report_action)
        self.analyses_menu.addAction(self.aoi_metrics_report_action)

        self.converters_menu.addAction(self.ascii_to_csv_converter_action)
        self.converters_menu.addAction(self.json_to_csv_converter_action)
        self.converters_menu.addAction(self.csv_to_json_converter_action)
        self.converters_menu.addAction(self.eyelink_experiment_to_csv_converter_action)

        # add menu item called "Style" to the menu bar
        self.menu_style = self.menuBar().addMenu("Appearance")

        action = QAction('Default', self)
        action.triggered.connect(lambda _, theme='Default': self.apply_stylesheet(self, 'src/my_theme.xml'))
        self.menu_style.addAction(action)

        # add sub menu to the menu item "Style" for Dark
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

        
        self.color_blind_action = QAction('Colorblind Assist', self)
        self.menu_style.addAction(self.color_blind_action)
        self.color_blind_action.triggered.connect(self.fix8.colorblind_assist)

        self.lock_x_axis_action = QAction('Lock X Axis', self)
        self.correction_menu.addAction(self.lock_x_axis_action)
        self.lock_x_axis_action.triggered.connect(self.fix8.lock_x_axis)

        self.canvas.mpl_connect("button_press_event", self.fix8.button_press_callback)
        self.canvas.mpl_connect("button_release_event", self.fix8.button_release_callback)
        self.canvas.mpl_connect("motion_notify_event", self.fix8.motion_notify_callback)

        self.trial_list.itemDoubleClicked.connect(self.fix8.trial_double_clicked)
        self.button_previous_fixation.clicked.connect(self.fix8.previous_fixation)
        self.button_next_fixation.clicked.connect(self.fix8.next_fixation)
        self.progress_bar.valueChanged.connect(self.fix8.progress_bar_updated)
        self.checkbox_show_aoi.stateChanged.connect(self.fix8.quick_draw_canvas)
        self.toggle_aoi_width.valueChanged.connect(self.fix8.aoi_width_changed)
        self.toggle_aoi_width.valueChanged.connect(self.set_canvas_focus)
        self.toggle_aoi_height.valueChanged.connect(self.fix8.aoi_height_changed)
        self.toggle_aoi_height.valueChanged.connect(self.set_canvas_focus)
        self.checkbox_show_fixations.stateChanged.connect(self.fix8.quick_draw_canvas)
        self.checkbox_show_all_fixations.stateChanged.connect(self.fix8.quick_draw_canvas)
        self.toggle_fixation_opacity.valueChanged.connect(self.fix8.fixation_opacity_changed)
        self.toggle_fixation_opacity.valueChanged.connect(self.set_canvas_focus)


        self.checkbox_show_saccades.stateChanged.connect(self.fix8.quick_draw_canvas)
        self.toggle_saccade_opacity.valueChanged.connect(self.fix8.saccade_opacity_changed)
        self.toggle_saccade_opacity.valueChanged.connect(self.set_canvas_focus)
        self.fixation_size_box.valueChanged.connect(self.fix8.fixation_size_changed)
        self.fixation_size_box.valueChanged.connect(self.set_canvas_focus)
        self.saccade_size_box.valueChanged.connect(self.fix8.saccade_width_changed)
        self.saccade_size_box.valueChanged.connect(self.set_canvas_focus)
        self.button_fixation_color.clicked.connect(self.fix8.select_fixation_color)
        self.button_saccade_color.clicked.connect(self.fix8.select_saccade_color)
        self.button_aoi_color.clicked.connect(self.fix8.select_aoi_color)
        self.button_current_fixation_color.clicked.connect(self.fix8.select_current_fixation_color)
        self.button_suggested_fixation_color.clicked.connect(self.fix8.select_suggested_fixation_color)
        self.button_remaining_fixation_color.clicked.connect(self.fix8.select_remaining_fixation_color)
        #self.button_coloblind_assist.clicked.connect(self.fix8.colorblind_assist)
        # connect functions
        self.new_file_action.triggered.connect(self.fix8.open_trial_folder)
        self.open_image_action.triggered.connect(self.fix8.open_image)
        self.open_trial_action.triggered.connect(self.fix8.open_trial)
        self.open_aoi_action.triggered.connect(self.fix8.open_aoi)
        self.save_correction_json_action.triggered.connect(self.fix8.save_corrections_json)
        self.save_correction_CSV_action.triggered.connect(self.fix8.save_corrections_csv)
        self.save_aoi_csv_action.triggered.connect(self.fix8.save_aoi_csv)
        self.next_fixation_action.triggered.connect(self.fix8.next_fixation)
        self.previous_fixation_action.triggered.connect(self.fix8.previous_fixation)
        self.assign_above_action.triggered.connect(self.fix8.assign_fixation_above)
        self.assign_below_action.triggered.connect(self.fix8.assign_fixation_below)
        self.accept_and_next_action.triggered.connect(self.fix8.confirm_suggestion)
        self.delete_fixation_action.triggered.connect(self.fix8.remove_fixation)
        self.undo_correction_action.triggered.connect(self.fix8.undo)

        self.trial_list_action.triggered.connect(self.show_hide_trial_list)
        self.trial_summary_action.triggered.connect(self.show_hide_trial_summary)
        self.visualization_panel_action.triggered.connect(self.show_hide_visualization_panel)
        self.hide_side_panel_action.triggered.connect(self.show_hide_side_panel)

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
        self.outlier_metrics_filter_action.triggered.connect(self.fix8.outlier_metrics_filter)
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
        self.slice_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('slice', drift.slice, 'auto'))
        self.warp_attach_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+attach', correction.warp_regs, 'auto', drift.attach))
        self.warp_chain_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+chain', correction.warp_regs, 'auto', drift.chain))
        self.war_regress_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+regress', correction.warp_regs, 'auto', drift.regress))
        self.warp_stretch_auto_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+stretch', correction.warp_regs, 'auto', drift.stretch))

        self.warp_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('warp', drift.warp, 'semi'))
        self.attach_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('attach', drift.attach, 'semi'))
        self.chain_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('chain', drift.chain, 'semi'))
        self.cluster_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('cluster', drift.cluster, 'semi'))
        self.merge_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('merge', drift.merge, 'semi'))
        self.regress_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('regress', drift.regress, 'semi'))
        self.segment_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('segment', drift.segment, 'semi'))
        self.stretch_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('stretch', drift.stretch, 'semi'))
        self.slice_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('slice', drift.slice, 'semi'))
        self.warp_attach_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+attach', correction.warp_regs, 'semi', drift.attach))
        self.warp_chain_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+chain', correction.warp_regs, 'semi', drift.chain))
        self.war_regress_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+regress', correction.warp_regs, 'semi', drift.regress))
        self.warp_stretch_semi_action.triggered.connect(lambda: self.fix8.run_algorithm('warp+stretch', correction.warp_regs, 'semi', drift.stretch))

        self.manual_correction_action.triggered.connect(self.fix8.manual_correction)

        self.fixation_report_action.triggered.connect(self.fix8.calculate_fixation_report)
        self.saccade_report_action.triggered.connect(self.fix8.calculate_saccade_report)
        self.aoi_report_action.triggered.connect(self.fix8.calculate_aoi_report)
        self.aoi_metrics_report_action.triggered.connect(self.fix8.calculate_aoi_metrics)

        self.ascii_to_csv_converter_action.triggered.connect(self.fix8.ascii_to_csv_converter)
        self.json_to_csv_converter_action.triggered.connect(self.fix8.json_to_csv_converter)
        self.csv_to_json_converter_action.triggered.connect(self.fix8.csv_to_json_converter)
        self.eyelink_experiment_to_csv_converter_action.triggered.connect(self.fix8.eyelink_experiment_to_csv_converter)

        self.assign_line_1_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(1))
        self.assign_line_2_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(2))
        self.assign_line_3_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(3))
        self.assign_line_4_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(4))
        self.assign_line_5_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(5))
        self.assign_line_6_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(6))
        self.assign_line_7_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(7))
        self.assign_line_8_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(8))
        self.assign_line_9_action.triggered.connect(lambda: self.fix8.assign_fixation_to_line(9))
        

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
            self.checkbox_show_all_fixations.setChecked(False)

            self.checkbox_show_saccades.setCheckable(False)
            self.checkbox_show_saccades.setChecked(False)
            self.checkbox_show_saccades.setEnabled(False)
            self.progress_bar.setEnabled(False)
            self.progress_bar.setValue(self.progress_bar.minimum())
            self.button_fixation_color.setEnabled(False)
            self.button_saccade_color.setEnabled(False)
            self.button_aoi_color.setEnabled(False)
            self.button_suggested_fixation_color.setEnabled(False)
            self.button_current_fixation_color.setEnabled(False)
            self.button_remaining_fixation_color.setEnabled(False)
            
            self.toggle_aoi_width.setEnabled(False)
            self.toggle_aoi_height.setEnabled(False)
            #self.button_coloblind_assist.setEnabled(False)
            self.toggle_fixation_opacity.setEnabled(False)
            self.toggle_saccade_opacity.setEnabled(False)
            self.fixation_size_box.setEnabled(False)
            self.saccade_size_box.setEnabled(False)

        elif feature == "trial_clicked":
            self.save_correction_json_action.setEnabled(True)
            self.save_correction_CSV_action.setEnabled(True)
            self.save_aoi_csv_action.setEnabled(True)
            self.open_trial_action.setEnabled(True)
            self.open_aoi_action.setEnabled(True)

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

            self.checkbox_show_all_fixations.setEnabled(True)

            self.toggle_aoi_width.setEnabled(True)
            self.toggle_aoi_height.setEnabled(True)
            self.button_fixation_color.setEnabled(True)
            self.button_saccade_color.setEnabled(True)
            self.button_aoi_color.setEnabled(True)
            self.button_suggested_fixation_color.setEnabled(False)
            self.button_current_fixation_color.setEnabled(True)
            self.button_remaining_fixation_color.setEnabled(True)
            self.toggle_fixation_opacity.setEnabled(True)
            self.toggle_saccade_opacity.setEnabled(True)
            self.fixation_size_box.setEnabled(True)
            self.saccade_size_box.setEnabled(True)
            #self.button_coloblind_assist.setEnabled(True)

            # IMPORTANT: here, set checked to false first so it activates suggestion removal since the removal
            # happens in the checkbox connected method,
            # then make in uncheckable so it won't activate by accident anymore; there is no helper
            # function for removing suggestions
            self.checkbox_show_suggestion.setChecked(False)
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setEnabled(False)
            self.checkbox_show_all_fixations.setChecked(False)

            self.progress_bar.setValue(self.progress_bar.minimum())
            self.progress_bar.setEnabled(True)
        elif feature == "no_selected_algorithm":
            self.checkbox_show_suggestion.setCheckable(False)
            self.checkbox_show_suggestion.setChecked(False)  # the no algorithm selection updates the suggestions
            # which clears them in the function itself
            self.checkbox_show_suggestion.setEnabled(False)
            self.checkbox_show_all_fixations.setChecked(False)
        elif feature == "algorithm_selected":
            self.button_previous_fixation.setEnabled(True)
            self.button_next_fixation.setEnabled(True)
            self.button_suggested_fixation_color.setEnabled(True)
            self.button_remaining_fixation_color.setEnabled(True)

    
    def show_hide_side_panel(self):
        if not self.trial_list.isHidden() or not self.visualization_frame.isHidden():
            self.hide_side_panel()
        else:
            self.show_side_panel()

        if self.fix8.image_file_path is not None:
            self.fix8.draw_canvas()

    def hide_side_panel(self):
        self.trial_list.setHidden(True)
        self.visualization_frame.setHidden(True)
        self.statistics_table.setHidden(True)

    def show_side_panel(self):
        self.trial_list.setHidden(False)
        self.visualization_frame.setHidden(False)
        #self.statistics_table.setHidden(False)

    def show_hide_trial_list(self):
        self.trial_list.setHidden(not self.trial_list.isHidden())
        if self.fix8.image_file_path is not None:
            self.fix8.draw_canvas()

    def show_hide_trial_summary(self):
        self.statistics_table.setHidden(not self.statistics_table.isHidden())
        if self.fix8.image_file_path is not None:
            self.fix8.draw_canvas()

    def show_hide_visualization_panel(self):
        self.visualization_frame.setHidden(not self.visualization_frame.isHidden())
        if self.fix8.image_file_path is not None:
            self.fix8.draw_canvas()
    
    def resizeEvent(self, event):
        # This method is called when the window is resized
        if self.fix8.image_file_path is not None:
            self.fix8.draw_canvas()

    def set_canvas_focus(self):
        self.canvas.setFocus()
    