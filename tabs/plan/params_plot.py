from PyQt5.QtWidgets import QWidget, QTabWidget, QStackedWidget, QVBoxLayout, QComboBox
from data import Data
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy import array

class FigureWidget(FigureCanvas):
    def __init__(self, figure=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        # super().__init__(figure)

class ParamReport(QWidget):
    def __init__(self, parent = ..., flags = ...):
        super().__init__()
        self.db: Data = parent.db
        main_layout = QVBoxLayout(self)

        # setup layout
        self.selection = QComboBox()
        main_layout.addWidget(self.selection)
        self.plot_field = QStackedWidget()
        main_layout.addWidget(self.plot_field)
        self.setWindowTitle('Parametry uzupełniania')

        # load data
        all_params, best_params = self.db.last_params()
        param_names = self.db.settings().scoring_names

        # params of best in generation
        canvas = FigureWidget(self)
        self.plot_field.addWidget(canvas)
        self.selection.addItem('Parametry najlepszych rozwiązań')
        canvas.ax.legend(param_names)
        for param in best_params:
            param = array(param)
            canvas.ax.plot((param - param.min()) / (param.max() - param.min()))

        # box plot for each param
        for name, param in zip(param_names, all_params):
            canvas = FigureWidget(self)
            canvas.ax.boxplot(param)
            self.plot_field.addWidget(canvas)
            self.selection.addItem(name)

        
        self.selection.currentIndexChanged.connect(self.plot_field.setCurrentIndex)

