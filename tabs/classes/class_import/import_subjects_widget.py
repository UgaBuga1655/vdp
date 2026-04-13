from turtle import color

from PyQt5.QtWidgets import QWidget, QButtonGroup, QPushButton, QLineEdit,\
      QComboBox, QVBoxLayout, QGridLayout, QScrollArea, QSizePolicy, QLabel, QColorDialog
from PyQt5.QtGui import QColor
from typing import List

from functions import shorten_name
from data import Data
from models import teacher

class ImportSubjectsWidget(QWidget):
    def __init__(self, parent, subject_names: List[str], class_):
        super().__init__(parent)
        self.subjects = dict()
        self.db: Data = parent.db
        
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        scroll_area = QScrollArea()
        main_layout.addWidget(scroll_area)
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        scroll_area.setWidget(container)


        self.grid = QGridLayout()
        container.setLayout(self.grid)
        for row, name in enumerate(subject_names):
            split_name = name.split()
            if len(split_name[-1]) <= 2:
                split_name.pop()
            stripped_name = ' '.join(split_name)
            basic = name[-1]!='R'
            subject = self.db.create_subject(name=stripped_name, basic=basic, my_sub_class=class_)
            self.subjects[name] = subject
            col = 0

            # original name
            label = QLabel(name)
            self.grid.addWidget(label, row, col)
            col+=1

            # parent
            button_group = QButtonGroup(self)
            button_group.setExclusive(True)
        
            common = QPushButton('Wspólny', self)
            common.setCheckable(True)
            button_group.addButton(common)
            common.setChecked(True)
            common.setFixedWidth(60)
            self.grid.addWidget(common, row, col)
            col+=1
            common.clicked.connect(self.set_subject_parent(subject, class_))

            for subclass in class_.subclasses:
                subclass_name = subclass.name.upper()
                btn = QPushButton(subclass_name, self)
                btn.setCheckable(True)
                btn.clicked.connect(self.set_subject_parent(subject, subclass))
                
                button_group.addButton(btn)
                btn.setFixedWidth(20)
                self.grid.addWidget(btn, row, col)
                col+=1
                if name[-1] == subclass_name:
                    btn.setChecked(True)
                    self.db.move_subject(subject, subclass)

            for btn in button_group.buttons():
                btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                btn.adjustSize()
                # btn.setFixedWidth(btn.width()+10)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f0f0;
                    }
                    QPushButton:checked {
                        background-color: #e0e0e0;
                        border: 1px solid #888;
                        border-radius: 2px;
                    }
                """)

            # new name
            
            line_edit = QLineEdit(subject.name)
            line_edit.textChanged.connect(self.set_subject_name(subject))
            self.grid.addWidget(line_edit, row, col)
            col+=1


            # short name
            short_edit = QLineEdit(subject.short_name)
            short_edit.textEdited.connect(self.set_subject_short_name(subject))
            self.grid.addWidget(short_edit, row, col)
            col += 1

            # color
            color_btn = QPushButton()
            color_btn.setStyleSheet(f'background-color: {subject.color}')
            color_btn.setFixedSize(20, 20)
            color_btn.clicked.connect(self.set_subject_color(subject, color_btn))
            self.grid.addWidget(color_btn, row, col)
            col += 1

            # teacher
            teacher_list = QComboBox()
            for teacher in self.db.all_teachers():
                teacher_list.addItem(teacher.name, teacher)
            if subject.teacher:
                teacher_list.setCurrentText(subject.teacher.name)
            teacher_list.currentTextChanged.connect(self.set_subject_teacher(subject))
            self.grid.addWidget(teacher_list, row, col)
            col += 1
            


            


    def set_subject_parent(self, subject, parent):
        def func():
            self.db.move_subject(subject, parent)
        return func

    def set_subject_name(self, subject):
        def func(new_name):
            self.db.update_subject_name(subject, new_name)
        return func
    
    def set_subject_short_name(self, subject):
        def func(new_name):
            self.db.update_subject_short_name(subject, new_name)
        return func
    
    def set_subject_color(self, subject, btn):
        def func():
            color = QColorDialog.getColor(QColor(subject.color))
            if not color.isValid():
                return
            color = color.name()
            self.db.update_subject_color(subject, color)
            btn.setStyleSheet(f'background-color: {color}')
        return func
    
    def set_subject_teacher(self, subject):
        def func():
            teacher = self.sender().currentData()
            self.db.update_subject_teacher(subject, teacher)
        return func
    