

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolBar
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


class QtCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=12, height=8, dpi=100):
        self.figure, self.ax = plt.subplots(ncols=1, nrows=1, figsize=(width, height))
        self.figure.tight_layout()
        self.figure.patch.set_facecolor('#5e6169')

        self.background = None

        FigureCanvasQTAgg.__init__(self, self.figure)
        self.setParent(parent)

        FigureCanvasQTAgg.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

        self.initialize()

    def initialize(self):
        #img = mpimg.imread("./.images/fix8_landing.png")
        img = mpimg.imread("./.images/fix8-landing-logo.png")
        self.ax.imshow(img, interpolation="hanning")
        self.draw()

    def clear(self):
        self.ax.clear()


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