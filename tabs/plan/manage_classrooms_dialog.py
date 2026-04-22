from typing import List

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QGridLayout, QLabel, QWidget, QPushButton
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QCursor
from data import Data, LessonBlockDB
# from db_config import settings
from models.lesson import Lesson
from .add_lesson_dialog import AddLessonToBlockDialog


class EditLessonBlockDialog(QDialog):
    def __init__(self, parent_block):
        super().__init__()

        self.db: 'Data' = parent_block.db
        self.block: LessonBlockDB = parent_block.block
        self.setWindowTitle(self.block.print_full_time())
        self.lessons = self.block.lessons
        self.collisions = self.db.potential_collisions_at_block(self.block, exclude_self=True, get_classrooms=True)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_grid = QGridLayout()
        self.main_layout.addLayout(self.main_grid)
        # print(self.collisions)

        add_btn = QPushButton('+')
        self.main_layout.addWidget(add_btn)
        add_btn.clicked.connect(self.add_lesson)

        buttonBox = QDialogButtonBox()
        self.main_layout.addWidget(buttonBox)

        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        self.load_lessons()
        # buttonBox.rejected.connect(self.reject)
        self.move(QCursor.pos() + QPoint(10,10))
    
    def update_lesson_classroom(self, lesson):
        def func():
            classroom = self.sender().currentData()
            self.db.update_lesson_classroom(lesson, classroom)
            for row in range(self.main_grid.rowCount()):
                item = self.main_grid.itemAtPosition(row, 2)
                if item:
                    combobox = item.widget()
                    self.update_classroom_list(combobox)
        return func
    
    def update_lesson_pinned(self, lesson):
        def func(locked):
            self.db.update_lesson_pinned(lesson, locked)
        return func
    
    def update_classroom_list(self, list: QComboBox):
        lesson = list.lesson
        list.blockSignals(True)
        list.clear()
        for i, classroom in enumerate(self.db.all_classrooms()):
            list.addItem(classroom.name, classroom)
            collisions = '\n'.join(self.db.classroom_fit_collisions(classroom, lesson.subject) + self.collisions[classroom])
            if collisions:
                list.setItemData(i, collisions, Qt.ToolTipRole)
                if not self.db.settings().allow_conflicts:
                    list.setItemData(i, 0, Qt.UserRole - 1)
                else:
                    list.setItemData(i, QColor('red'), Qt.BackgroundRole)
        list.insertItem(0, '')
        if lesson.classroom:
            list.setCurrentText(lesson.classroom.name)
        else:
            list.setCurrentIndex(0)
        list.blockSignals(False)
            
    def load_lessons(self):
        for lesson in self.lessons:
            self.place_lesson(lesson)
            

    def place_lesson(self, lesson: Lesson):
        row = self.main_grid.rowCount()
        del_btn = QPushButton('X')
        del_btn.setFixedSize(20,20)
        self.main_grid.addWidget(del_btn, row, 0)
        label = QLabel(lesson.subject.get_name())
        label.setToolTip(lesson.teacher.name)
        self.main_grid.addWidget(label, row, 1)
        combobox = QComboBox()
        combobox.lesson = lesson
        combobox.currentTextChanged.connect(self.update_lesson_classroom(lesson))
        self.update_classroom_list(combobox)
        self.main_grid.addWidget(combobox,row , 2) 
        pinned = QPushButton('📌')
        pinned.setFixedSize(20,20)
        pinned.setCheckable(True)
        pinned.setChecked(lesson.block_locked)
        pinned.toggled.connect(self.update_lesson_pinned(lesson))
        self.main_grid.addWidget(pinned, row, 3)

        del_btn.clicked.connect(self.remove_lesson(lesson, [del_btn, label, combobox, pinned]))

    def remove_lesson(self, lesson, widgets: List[QWidget]):
        def func():
            self.db.remove_lesson_from_block(lesson)
            for widget in widgets:
                widget.deleteLater()
        return func
    
    def add_lesson(self):
        dialog = AddLessonToBlockDialog(self)
        ok = dialog.exec()
        if not ok:
            return False
        subject = dialog.subject_list.currentData()
        lesson = dialog.lesson_list.currentData()
        classroom = dialog.classroom_list.currentData()
        if subject and lesson and classroom:
            self.db.update_lesson_classroom(lesson, classroom)
            self.db.add_lesson_to_block(lesson, self.block)
        if lesson:
            self.place_lesson(lesson)


