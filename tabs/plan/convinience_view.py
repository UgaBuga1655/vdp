from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt5 import QtCore

cell_style = 'border: 1px solid black;'

class AvailabilityCell(QWidget):
    def __init__(self, row, col, color):
        super().__init__()
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(cell_style)
        self.setMouseTracking(True)
        self.mouseMoveEvent= self.moved
        self.row = row
        self.col = col
        self.available = False
        self.mousePressEvent=self.clicked
        self.color = color

    def set_highlight(self, highlight):
        self.setStyleSheet(cell_style + f'background: {"pink" if highlight else "white"}')
    
    def show_true_color(self):
        self.setStyleSheet(cell_style + f'background: {self.color if self.available else "white"}')


    def clicked(self, event):
        parent: AvFrame = self.parent()
        parent.change_availability = not parent.change_availability
        if parent.change_availability:
            parent.availability_mode = not self.available
            parent.start_highlight(self.row, self.col)
        else:
            parent.set_availability(self.row, self.col)

    def moved(self, event):
        if self.parent().change_availability:
            self.parent().highlight_to(self.row, self.col)
        
class AvFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.change_availability = False
        self.availability = QGridLayout()
        self.availability.setSpacing(0)
        headers = 'Godzina: Poniedziałek: Wtorek: Środa: Czwartek: Piątek:'.split()
        for col, head in enumerate(headers):
            cell = QLabel(head)
            cell.setStyleSheet(cell_style)
            self.availability.addWidget(cell, 0, col)

        for n in range(8,16):
            cell_1 = QLabel(f'{n}:00-{n}:30')
            cell_2 = QLabel(f'{n}:30-{n+1}:00')
            cell_1.setStyleSheet(cell_style)
            cell_2.setStyleSheet(cell_style)
            row = (n-8)*2+1
            self.availability.addWidget(cell_1, row, 0)
            self.availability.addWidget(cell_2, row+1, 0)

        for col in range(1,6):
            for row in range(1,17):
                cell = AvailabilityCell(row, col)
                self.availability.addWidget(cell, row, col)

        self.setLayout(self.availability)

    
    def start_highlight(self, row, col):
        self.s_row = row
        self.s_col = col

    def highlight_to(self, e_row, e_col):
        s_row = min(self.s_row, e_row)
        e_row = max(self.s_row, e_row)
        s_col = min(self.s_col, e_col)
        e_col = max(self.s_col, e_col)
        for row in range(1,17):
            for col in range(1,6):
                if s_row <= row and row <= e_row and \
                   s_col <= col and col <= e_col:
                    self.availability.itemAtPosition(row, col).widget().set_highlight(self.availability_mode)
                else:
                    self.availability.itemAtPosition(row, col).widget().show_true_color()

    def set_availability(self, e_row, e_col):
        s_row = min(self.s_row, e_row)
        e_row = max(self.s_row, e_row)
        s_col = min(self.s_col, e_col)
        e_col = max(self.s_col, e_col)
        for row in range(1,17):
            for col in range(1,6):
                if s_row <= row and row <= e_row and \
                    s_col <= col and col <= e_col:
                    self.availability.itemAtPosition(row, col).widget().available = self.availability_mode
                self.availability.itemAtPosition(row, col).widget().show_true_color()
        self.parent().parent().save_av()

