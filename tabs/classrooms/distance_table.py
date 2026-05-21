from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QVBoxLayout, QCheckBox, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from vertical_label import VerticalLabel

from data import Data

class CellWidget(QFrame):
    def __init__(self, parent, color, widget):
        super().__init__(parent)
        self.setStyleSheet(f'background-color: {color};')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(widget)

class DistanceTable(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.outer_layout = QVBoxLayout(self)
        label = QLabel('Odległości między grupami sal', alignment=Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        label.setFont(font)
        self.outer_layout.addWidget(label)
        self.inner_table = QWidget(self)
        self.outer_layout.addWidget(self.inner_table)
        self.symmetrical = QCheckBox('Takie same w obie strony')
        self.symmetrical.clicked.connect(self.load_content)
        self.outer_layout.addWidget(self.symmetrical, alignment=Qt.AlignmentFlag.AlignCenter)
        self.outer_layout.addStretch()


    def load_data(self, db):
        try:
            self.symmetrical.toggled.disconnect()
        except:
            pass
        self.db: Data = db
        self.symmetrical.toggled.connect(self.db.set_distances_symmetrical)
        self.load_content()

    def load_content(self):
        self.inner_table.deleteLater()
        self.inner_table = QWidget(self)
        self.outer_layout.insertWidget(0, self.inner_table)
        inner_grid = QGridLayout(self.inner_table)
        inner_grid.setSpacing(0)
        inner_grid.setContentsMargins(0,0,0,0)
        self.inner_table.setLayout(inner_grid)
        groups = self.db.all_classrooms_groups()
        inner_grid.addWidget(QLabel('Do', alignment=Qt.AlignmentFlag.AlignCenter), 0, 2, 1, len(groups))
        left_label = VerticalLabel('Od', Qt.AlignmentFlag.AlignCenter)
        inner_grid.addWidget(left_label, 2, 0, len(groups), 1)

        sym = self.db.settings().symmetrical_distances
        self.disabled_spinboxes = dict()
        for row, start in enumerate(groups):

            color = 'lightgray' if (row)%2 else 'white'
            top = CellWidget(self.inner_table, color, VerticalLabel(start.name))
            left = CellWidget(self.inner_table, color, QLabel(start.name))
            inner_grid.addWidget(top, 1, row+2)
            inner_grid.addWidget(left, row+2, 1)
            for col, end in enumerate(groups):
                spin = QSpinBox()
                spin.setRange(0, 999)
                spin.setValue(self.db.get_distance(start, end))
                spin.valueChanged.connect(self.set_distance(start, end))
                spin.setStyleSheet("""
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
                    spin.setDisabled(True)
                if sym:
                    if row < col:
                        spin.setDisabled(True)
                        self.disabled_spinboxes[(row, col)] = spin
                    else:
                        spin.valueChanged.connect(self.update_disabled_spin(row, col))

                color = 'lightgray' if max(row, col)%2 else 'white'
                cell = CellWidget(self.inner_table, color, spin)
                inner_grid.addWidget(cell, row+2, col+2)

        self.symmetrical.blockSignals(True)
        self.symmetrical.setChecked(sym)
        self.symmetrical.blockSignals(False)

    def update_disabled_spin(self, row, col):
        def func(val):
            self.disabled_spinboxes[(col, row)].setValue(val)
        return func
        
    def set_distance(self, start, end):
        def func(dist):
            self.db.set_distance(start, end, dist)
        return func
