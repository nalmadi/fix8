from PyQt5.QtWidgets import QApplication, QLineEdit, QDialogButtonBox, QFormLayout, QDialog
from PyQt5.QtGui import QIntValidator, QDoubleValidator


class GenerateFixationsSkipDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # approximate_letter_width, lam_value, k_value

        self.approximate_letter_width = QLineEdit(self)
        self.lam_value = QLineEdit(self)
        self.k_value = QLineEdit(self)

        # set validators
        self.approximate_letter_width.setValidator(QIntValidator(10, 1000))
        #self.lam_value.setValidator(QDoubleValidator(0.1, 100))
        #self.k_value.setValidator(QDoubleValidator(0.1, 100.00, 2))

        # default values
        self.approximate_letter_width.setText('30')
        self.lam_value.setText('0.2926')
        self.k_value.setText('0.99')

        self.setWindowTitle("Generate Fixations with Skip") 
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("Approximate letter width (pixels)", self.approximate_letter_width)
        layout.addRow("Exponential distribution Lambda", self.lam_value)
        layout.addRow("Exponential distribution constant K", self.k_value)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return int(self.approximate_letter_width.text()), float(self.lam_value.text()), float(self.k_value.text())

if __name__ == '__main__':

    import sys
    app = QApplication(sys.argv)
    dialog = GenerateFixationsSkipDialog()
    if dialog.exec():
        print(dialog.getInputs())
    exit(0)