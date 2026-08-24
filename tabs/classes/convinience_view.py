from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QDialogButtonBox
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QCursor
from data import Subject, Teacher, Data

cell_style = 'border: 1px solid black;'
unavailable_style = 'border: 5px solid black;'

class UncheckableBtn(QPushButton):
    color_unset = QtCore.pyqtSignal(bool)
    def __init__(self, parent, color):
        super().__init__('', parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.color = color
        self.setStyleSheet(f'background-color: {color}')


    def mousePressEvent(self, event):
        if self.isChecked():
            self.setAutoExclusive(False)
            self.setChecked(False)
            self.setAutoExclusive(True)
            self.color_unset.emit(False)
        else: 
            super().mousePressEvent(event)


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
        self.setStyleSheet((cell_style if self.available else unavailable_style) + f'background: {highlight}')


    def set_color(self, color):
        self.color = color

    def show_true_color(self):
        self.setStyleSheet((cell_style if self.available else unavailable_style) + f'background: {self.color}')
        # self.setStyleSheet(cell_style + f'background: {self.color if self.available else "black"}')


    def clicked(self, event):
        parent: AvFrame = self.parent()
        if not parent.highlight_started:
            parent.start_highlight(self.row, self.col)
        else:
            parent.set_color(self.row, self.col)

    def moved(self, event):
        if self.parent().highlight_started:
            self.parent().highlight_to(self.row, self.col)
        
class AvFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.highlight_started = False
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
                cell = AvailabilityCell(row, col, '#00ff00')
                self.availability.addWidget(cell, row, col)

        self.setLayout(self.availability)
        self.color = None

    
    def start_highlight(self, row, col):
        self.s_row = row
        self.s_col = col
        self.highlight_started = True

    def highlight_to(self, e_row, e_col):
        if self.color is None:
            return
        s_row = min(self.s_row, e_row)
        e_row = max(self.s_row, e_row)
        s_col = min(self.s_col, e_col)
        e_col = max(self.s_col, e_col)
        for row in range(1,17):
            for col in range(1,6):
                if s_row <= row and row <= e_row and \
                   s_col <= col and col <= e_col:
                    self.availability.itemAtPosition(row, col).widget().set_highlight(self.color)
                else:
                    self.availability.itemAtPosition(row, col).widget().show_true_color()

    def set_color(self, e_row, e_col):
        if self.color is None:
            return
        self.highlight_started = False
        s_row = min(self.s_row, e_row)
        e_row = max(self.s_row, e_row)
        s_col = min(self.s_col, e_col)
        e_col = max(self.s_col, e_col)
        for row in range(1,17):
            for col in range(1,6):
                if s_row <= row and row <= e_row and \
                    s_col <= col and col <= e_col:
                    self.availability.itemAtPosition(row, col).widget().color = self.color
                self.availability.itemAtPosition(row, col).widget().show_true_color()
        # self.parent().parent().save_av()

class ConvinienceDialog(QDialog):
    def __init__(self, subject: Subject, parent):
        super().__init__(parent)
        self.subject = subject
        self.db: Data = parent.db
        self.setWindowTitle('Przedmiot')
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.move(QCursor.pos() + QPoint(10,10))
        self.allow_conflicts = self.db.settings().allow_conflicts
        self.setMinimumWidth(600)

        # self.color = None

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        colors = QWidget()
        color_row = QGridLayout()
        colors.setLayout(color_row)
        red_btn = UncheckableBtn(colors, '#ff0000')
        red_btn.clicked.connect(lambda _: self.set_color('#ff0000'))
        red_btn.color_unset.connect(lambda _: self.set_color(None))
        color_row.addWidget(red_btn,1,0)
        color_row.addWidget(QLabel('Nie umieszczać'),0,0)

        yellow_btn = UncheckableBtn(colors, "#f7f307")
        yellow_btn.clicked.connect(lambda _: self.set_color('#f7f307'))
        yellow_btn.color_unset.connect(lambda _: self.set_color(None))
        color_row.addWidget(yellow_btn,1,1)
        color_row.addWidget(QLabel('W ostateczności'), 0,1)
        
        green_btn = UncheckableBtn(colors, '#00ff00')
        green_btn.clicked.connect(lambda _: self.set_color('#00ff00'))
        green_btn.color_unset.connect(lambda _: self.set_color(None))
        color_row.addWidget(green_btn,1,2)
        color_row.addWidget(QLabel('Umieszczać'),0,2)
        main_layout.addWidget(colors)

        self.table = AvFrame()
        main_layout.addWidget(self.table)

        btn_box = QDialogButtonBox()
        btn_box.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # self.buttons.accepted.connect(self.accept)
        btn_box.accepted.connect(self.save_convinience)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)
        self.load()

    def set_color(self, color):
        self.table.color = color 
        self.table.highlight_started = False
        for row in range(1,17):
            for col in range(1,6):
                cell: AvailabilityCell = self.table.availability.itemAtPosition(row, col).widget()
                cell.show_true_color()
        # if color is not None:
        #     self.table.highlight_started = True

    def load(self):
        av = [(1<<17)-1]*5
        for teacher in self.subject.teachers:
            teacher_av = self.db.read_teacher_av(teacher)
            for day, t_av in enumerate(teacher_av):
                av[day] &= t_av
        for row in range(1,17):
            for col in range(1,6):
                cell: AvailabilityCell = self.table.availability.itemAtPosition(row, col).widget()
                cell.available = av[col-1]>>row-1 & 1
                if getattr(self.subject, f'for{col}') & 1<<row-1:
                    cell.color = '#ff0000'
                elif getattr(self.subject, f'inconv{col}') & 1<<row-1:
                    cell.color = '#f7f307'
                cell.show_true_color()


    def save_convinience(self):
        forbidden = [0]*5
        inconvinient = [0]*5
        for col in range(1,6):
            for row in range(1,17):
                cell: AvailabilityCell = self.table.availability.itemAtPosition(row, col).widget()
                color = cell.color
                if color == '#ff0000':
                    forbidden[col-1] |= 1<<row-1
                elif color == '#f7f307':
                    inconvinient[col-1] |= 1<<row-1

        self.db.update_subject_convinience(self.subject, forbidden, inconvinient)
        self.accept()
        






