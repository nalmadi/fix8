from PyQt5.QtWidgets import QApplication, QLineEdit, QDialogButtonBox, QFormLayout, QDialog, QComboBox


class OutlierMetricsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)



        # Dropdown for metric
        self.select_metrics = QComboBox(self)
        self.select_metrics.addItem("First Fixation Duration")
        self.select_metrics.addItem("Single Fixation Duration")
        self.select_metrics.addItem("Gaze Duration")
        self.select_metrics.addItem("Total Time")

        # select standard deviation threshold for each metric
        self.selected_std = QLineEdit(self)

        # default value
        self.selected_std.setText('2.5')

        self.setWindowTitle("Outlier Metrics Filter") 
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("Select Metric to filter outliers", self.select_metrics)
        layout.addRow("Select Standard Deviation", self.selected_std)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.select_metrics.currentText() , self.selected_std.text())

if __name__ == '__main__':

    import sys
    app = QApplication(sys.argv)
    dialog = OutlierMetricsDialog()
    if dialog.exec():
        print(dialog.getInputs())
    exit(0)