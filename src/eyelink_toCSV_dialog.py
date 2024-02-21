from PyQt5.QtWidgets import QApplication, QDialog, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, QLabel, QFileDialog

class EyelinkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ascii_file_line_edit = QLineEdit(self)
        self.ascii_file_line_edit.setReadOnly(True)
        self.runtime_folder_line_edit = QLineEdit(self)
        self.runtime_folder_line_edit.setReadOnly(True)
        self.save_folder_line_edit = QLineEdit(self)
        self.save_folder_line_edit.setReadOnly(True)

        self.setWindowTitle("Eyelink Experiment Converter")
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        ascii_browse_button = QPushButton("Browse", self)
        ascii_browse_button.clicked.connect(self.select_ascii_file)

        runtime_folder_browse_button = QPushButton("Browse", self)
        runtime_folder_browse_button.clicked.connect(self.select_runtime_folder)
        
        save_folder_browse_button = QPushButton("Browse", self)
        save_folder_browse_button.clicked.connect(self.select_save_folder)

        layout = QFormLayout(self)
        layout.addRow("Select ASCII File:", self.ascii_file_line_edit)
        layout.addWidget(ascii_browse_button)
        layout.addRow("Select Runtime Folder:", self.runtime_folder_line_edit)
        layout.addWidget(runtime_folder_browse_button)
        layout.addRow("Select Save Folder:", self.save_folder_line_edit)
        layout.addWidget(save_folder_browse_button)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def select_ascii_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select ASCII file", "", "ASCII Files (*.asc)")
        if file_name:
            self.ascii_file_line_edit.setText(file_name)

    def select_runtime_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Select Runtime Folder")
        if folder_name:
            self.runtime_folder_line_edit.setText(folder_name)

    def select_save_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if folder_name:
            self.save_folder_line_edit.setText(folder_name)

    def getInputs(self):
        return self.ascii_file_line_edit.text(), self.runtime_folder_line_edit.text(), self.save_folder_line_edit.text()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    dialog = EyelinkDialog()
    if dialog.exec():
        ascii_file, runtime_folder, save_folder = dialog.getInputs()
        print("ASCII File:", ascii_file)
        print("Runtime Folder:", runtime_folder)
        print("Save Folder:", save_folder)
    sys.exit(0)
