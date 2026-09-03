from typing import List

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QGridLayout, \
    QLabel, QWidget, QPushButton, QColorDialog, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QCursor
from data import Data, Block
from models.lesson import Lesson
from .add_lesson_dialog import AddLessonToBlockDialog


class EditLessonBlockDialog(QDialog):
    def __init__(self, parent_block):
        super().__init__()

        self.db: 'Data' = parent_block.db
        self.block: Block = parent_block.block
        self.setWindowTitle(self.block.print_full_time())
        self.lessons = self.block.events
        self.collisions = self.db.potential_collisions_at_block(self.block, exclude_self=True, get_classrooms=True, get_teachers=True, get_students=True)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(QLabel('Lekcje'))

        self.lesson_grid = QGridLayout()
        self.main_layout.addLayout(self.lesson_grid)
        # print(self.collisions)

        add_btn = QPushButton('+')
        self.main_layout.addWidget(add_btn)
        add_btn.clicked.connect(self.add_lesson)

        self.main_layout.addWidget(QLabel('Dyżury'))

        self.name_row = QHBoxLayout()
        self.main_layout.addLayout(self.name_row)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(20, 20)
        self.color_btn.setStyleSheet(f'background-color: {self.block.color}')
        self.color_btn.clicked.connect(self.set_color)
        self.name_row.addWidget(self.color_btn)

        text_edit = QLineEdit(self.block.text)
        self.name_row.addWidget(text_edit)
        text_edit.textChanged.connect(self.update_text)
        self.duties = QGridLayout()
        self.main_layout.addLayout(self.duties)

        new_button = QPushButton('+')
        new_button.clicked.connect(self.add_duty)
        self.main_layout.addWidget(new_button)

        buttonBox = QDialogButtonBox()
        self.main_layout.addWidget(buttonBox)

        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

        self.sen_students = [s for s in self.block.parent().students if s.sen]
        self.sen_students.sort(key=lambda s: s.name)
        self.load_lessons()
        # buttonBox.rejected.connect(self.reject)
        self.move(QCursor.pos() + QPoint(10,10))

    
    def update_lesson_classroom(self, lesson):
        def func():
            classroom = self.sender().currentData()
            self.db.update_lesson_classroom(lesson, classroom)
            for row in range(self.lesson_grid.rowCount()):
                item = self.lesson_grid.itemAtPosition(row, 2)
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
        for event in self.lessons:
            if isinstance(event, Lesson):
                self.place_lesson(event)
            else:
                self.place_duty(event)
            

    def place_lesson(self, lesson: Lesson):
        row = self.lesson_grid.rowCount()
        del_btn = QPushButton('X')
        del_btn.setFixedSize(20,20)
        self.lesson_grid.addWidget(del_btn, row, 0)
        label = QLabel(lesson.subject.get_name())
        label.setToolTip(lesson.teacher.name if lesson.teacher else '')
        self.lesson_grid.addWidget(label, row, 1)
        combobox = QComboBox()
        combobox.lesson = lesson
        combobox.currentTextChanged.connect(self.update_lesson_classroom(lesson))
        self.update_classroom_list(combobox)
        self.lesson_grid.addWidget(combobox,row , 2) 
        pinned = QPushButton('📌')
        pinned.setFixedSize(20,20)
        pinned.setCheckable(True)
        pinned.setChecked(lesson.block_locked)
        pinned.toggled.connect(self.update_lesson_pinned(lesson))
        self.lesson_grid.addWidget(pinned, row, 3)

        del_btn.clicked.connect(self.remove_lesson(lesson, [del_btn, label, combobox, pinned]))


    def remove_lesson(self, lesson, widgets: List[QWidget]):
        def func():
            self.db.remove_lesson_from_block(lesson)
            for widget in widgets:
                widget.deleteLater()
                widget.setParent(None)
            self.main_layout.update()
            self.adjustSize()
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



    def place_duty(self, duty):
        row = self.duties.rowCount()

        del_btn = QPushButton('X')
        del_btn.setFixedWidth(20)
        self.duties.addWidget(del_btn, row, 0)
        
        teacher_select = QComboBox()
        teacher_select.addItem('---', None)
        for i, teacher in enumerate(self.db.all_teachers()):
            teacher_select.addItem(teacher.name, teacher)
            collision = '\n'.join(self.collisions[teacher])
            if not collision:
                continue
            teacher_select.setItemData(i+1, collision, Qt.ToolTipRole)
            if not self.db.settings().allow_conflicts:
                teacher_select.setItemData(i+1, 0, Qt.UserRole - 1)
            else:
                teacher_select.setItemData(i+1, QColor('red'), Qt.BackgroundRole)
        teacher_select.currentIndexChanged.connect(
            self.update_duty_teacher(duty, teacher_select)
        )
        self.duties.addWidget(teacher_select, row, 1)
        if duty.teacher:
            teacher_select.setCurrentText(duty.teacher.name)


        teacher_pinned = QPushButton('📌')
        teacher_pinned.setFixedSize(20,20)
        teacher_pinned.setCheckable(True)
        teacher_pinned.setChecked(duty.teacher_pinned)
        teacher_pinned.toggled.connect(self.update_duty_teacher_pinned(duty))
        self.duties.addWidget(teacher_pinned, row, 2)


        classroom_select = QComboBox()
        classroom_select.addItem('---', None)
        for i, classroom in enumerate(self.db.all_classrooms()):
            classroom_select.addItem(classroom.name, classroom)

            collision = '\n'.join(self.collisions[classroom])
            if not collision:
                continue
            classroom_select.setItemData(i+1, collision, Qt.ToolTipRole)
            if not self.db.settings().allow_conflicts:
                classroom_select.setItemData(i+1, 0, Qt.UserRole - 1)
            else:
                classroom_select.setItemData(i+1, QColor('red'), Qt.BackgroundRole)
        classroom_select.currentIndexChanged.connect(
            self.update_duty_classroom(duty, classroom_select)
        )
        self.duties.addWidget(classroom_select, row, 3)
        if duty.classroom:
            classroom_select.setCurrentText(duty.classroom.name)

        student_select = QComboBox()
        student_select.addItem('---', None)
        for i, student in enumerate(self.sen_students):
            student_select.addItem(student.name, student)
            collision = '\n'.join(list(set(self.collisions[student])))
            if not collision:
                continue
            student_select.setItemData(i+1, collision, Qt.ToolTipRole)
            if self.db.settings().allow_conflicts:
                student_select.setItemData(i+1, QColor('red'), Qt.BackgroundRole)
            else:
                student_select.setItemData(i+1, 0, Qt.UserRole - 1)


        self.duties.addWidget(student_select, row, 4)
        if duty.student:
            student_select.setCurrentText(student.name)
        student_select.currentIndexChanged.connect(
            self.update_duty_student(duty, student_select)
        )

        
        classroom_pinned = QPushButton('📌')
        classroom_pinned.setFixedSize(20,20)
        classroom_pinned.setCheckable(True)
        classroom_pinned.setChecked(duty.classroom_pinned)
        classroom_pinned.toggled.connect(self.update_duty_classroom_pinned(duty))
        self.duties.addWidget(classroom_pinned, row, 5)

        del_btn.clicked.connect(self.delete_duty(duty,
        [teacher_select, classroom_select, del_btn, teacher_pinned, classroom_pinned]))

    def update_duty_classroom(self, duty, select):
        def func():
            classroom = select.currentData()
            self.db.update_duty_classroom(duty, classroom)
        return func
    
    def update_duty_teacher(self, duty, select):
        def func():
            teacher = select.currentData()
            self.db.update_duty_teacher(duty, teacher)
        return func

    def update_duty_teacher_pinned(self, duty):
        def func(checked):
            self.db.update_duty_teacher_pinned(duty, checked)
        return func
    
    def update_duty_classroom_pinned(self, duty):
        def func(checked):
            self.db.update_duty_classroom_pinned(duty, checked)
        return func

    def update_duty_student(self, duty, select):
        def func():
            self.db.update_duty_student(duty, select.currentData())
        return func

    def add_duty(self):
        duty = self.db.new_duty(self.block)
        self.place_duty(duty) 
    
    def delete_duty(self, duty, widgets):
        def func():
            self.db.delete_duty(duty)
            for widget in widgets:
                widget.deleteLater()
                widget.setParent(None)
            self.main_layout.update()
            self.adjustSize()
        return func


    def update_text(self, text):
        self.db.update_custom_block_text(self.block, text)

    def set_color(self):
        color = QColorDialog.getColor(QColor(self.block.color))
        if color.isValid():
            # self.setBrush(color)
            self.db.update_custom_block_color(self.block, color.name())
            self.color_btn.setStyleSheet(f'background-color: {color.name()}')