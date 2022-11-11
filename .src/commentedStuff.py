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

# # --- show Saccades checkbox ---
# self.checkbox_showSaccades = QCheckBox("Show Saccades", self)
# self.checkbox_showSaccades.setChecked(False)
# self.checkbox_showSaccades.setCheckable(False)
# self.checkbox_showSaccades.stateChanged.connect(self.showSaccades)
# self.belowCanvas.addWidget(self.checkbox_showSaccades)
