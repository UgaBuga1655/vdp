from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QVBoxLayout, QSizePolicy, QFrame
from PyQt5.QtCore import Qt

from data import Data

class CellWidget(QFrame):
    def __init__(self, parent, color, widget):
        super().__init__(parent)
        self.setStyleSheet(f'background-color: {color};')
        # self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)
        # self.setLayout(main_layout)
        main_layout.addWidget(widget)
        # widget.setStyleSheet("")

class DistanceTable(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # self.move(QCursor.pos() + QPoint(10,10))
        self.inner_table = QWidget(self)
        self.outer_grid = QGridLayout()
        self.setLayout(self.outer_grid)
        self.outer_grid.addWidget(self.inner_table, 0, 0)
        # self.load_data(parent.db)


    def load_data(self, db):
        self.db: Data = db
        self.inner_table.deleteLater()
        self.inner_table = QWidget(self)
        self.outer_grid.addWidget(self.inner_table, 0, 0)

        inner_grid = QGridLayout()
        inner_grid.setSpacing(0)
        inner_grid.setContentsMargins(0,0,0,0)
        self.inner_table.setLayout(inner_grid)
        groups = self.db.all_classrooms_groups()
        for i, group in enumerate(groups):
            # labels
            # label = QLabel(group.name)
            color = 'lightgray' if (i+1)%2 else 'white'
            cell = CellWidget(self.inner_table, color, QLabel(group.name))
            cell2 = CellWidget(self.inner_table, color, QLabel(group.name))
            inner_grid.addWidget(cell, 0, i+1)
            inner_grid.addWidget(cell2, i+1, 0)
  
        for row in range(1, len(groups)+1):
            for col in range(1, len(groups)+1):
                start = groups[row-1]
                end = groups[col-1]
                widget = QSpinBox()
                widget.setRange(0, 999)
                widget.setValue(self.db.get_distance(start, end))
                widget.valueChanged.connect(self.set_distance(start, end))
                widget.setStyleSheet("""
                    QSpinBox {
                        border: 1px solid #aaa;
                        padding-right: 0px;   /* remove space where arrows were */
                        qproperty-alignment: AlignCenter;
                    }
                    QSpinBox::up-button, QSpinBox::down-button {
                        width: 0;
                        height: 0;
                        border: none;
                    }
                """)
                if row == col:
                    widget.setDisabled(True)
                color = 'lightgray' if max(row, col)%2 else 'white'
                cell = CellWidget(self.inner_table, color, widget)
                inner_grid.addWidget(cell, row, col)
                    # inner_grid.addWidgetQLabel(groups))


    def set_distance(self, start, end):
        def func(dist):
            self.db.set_distance(start, end, dist)
        return func
