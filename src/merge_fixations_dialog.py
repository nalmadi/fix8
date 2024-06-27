from PyQt5.QtWidgets import QApplication, QLineEdit, QDialogButtonBox, QFormLayout, QDialog


class MergeFixationsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.duration_threshold = QLineEdit(self)
        self.visual_angle_pixels = QLineEdit(self)

        # default values
        self.duration_threshold.setText('50')
        self.visual_angle_pixels.setText('20')

        self.setWindowTitle("Merge Fixations") 
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("Fixation duration bellow (ms)", self.duration_threshold)
        layout.addRow("will be merged with other fixations within (pixels)", self.visual_angle_pixels)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.duration_threshold.text(), self.visual_angle_pixels.text())

if __name__ == '__main__':

    import sys
    app = QApplication(sys.argv)
    dialog = MergeFixationsDialog()
    if dialog.exec():
        print(dialog.getInputs())
    exit(0)