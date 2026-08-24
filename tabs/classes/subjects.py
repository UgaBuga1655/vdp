from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QDialog, QDialogButtonBox, \
      QPushButton, QLabel, QDialogButtonBox, QMessageBox, QCheckBox, QColorDialog, QLineEdit, QSpinBox
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QCursor

from data import Data, Class, Subclass, Subject
from .convinience_view import ConvinienceDialog

class AddLessonDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setWindowTitle('Podaj długość')
        layout = QVBoxLayout(self)
        self.combobox = QComboBox()
        layout.addWidget(self.combobox)
        self.combobox.addItems(['30', '45', '60', '90'])
        self.combobox.setEditable(True)
        buttonBox = QDialogButtonBox()
        layout.addWidget(buttonBox)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

class AddTeacherDialog(QDialog):
    def __init__(self, parent, teachers):
        super().__init__(parent=parent)
        self.setWindowTitle('Dodaj Nauczyciela')
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.teacher = QComboBox()
        layout.addWidget(self.teacher)
        for teacher in teachers:
            self.teacher.addItem(teacher.name, teacher)

        buttonBox = QDialogButtonBox()
        layout.addWidget(buttonBox)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

class CopySubjectsDialog(QDialog):
    def __init__(self, parent, targets):
        super().__init__(parent=parent)
        self.setWindowFlag(Qt.Tool)
        self.setWindowTitle('Kopiuj Lekcje')
        layout = QVBoxLayout(self)
        self.target_list = QComboBox()
        layout.addWidget(self.target_list)
        for target in targets:
            self.target_list.addItem(target.full_name(), target)
        buttonBox = QDialogButtonBox()
        layout.addWidget(buttonBox)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        

class SubjectsWindow(QWidget):
    short_name_updated = pyqtSignal(str)
    color_changed = pyqtSignal(QColor)
    teacher_changed = pyqtSignal(str)
    
    def __init__(self, parent, db: Data, subject: Subject):
        super().__init__()
        self.setWindowFlag(Qt.Tool)
        self.db: Data = db
        self.subject = subject
        main_layout= QVBoxLayout()
        self.setLayout(main_layout)
        self.setWindowTitle('Przedmiot')
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.move(QCursor.pos() + QPoint(10,10))
        self.allow_conflicts = self.db.settings().allow_conflicts
        self.convinience_dialog = None

        top_row = QHBoxLayout()
        main_layout.addLayout(top_row)
        full_name = QLineEdit(subject.name, self)
        top_row.addWidget(full_name)
        full_name.textEdited.connect(self.set_name)



        # display options row
        display_options_row = QHBoxLayout()
        main_layout.addLayout(display_options_row)
        display_options_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # color
        display_options_row.addWidget(QLabel('Kolor:'))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(20,20)
        self.color_button.clicked.connect(self.pick_color)
        display_options_row.addWidget(self.color_button)

        # short name
        display_options_row.addWidget(QLabel('Skrót:'))
        self.short_name = QLineEdit()
        self.short_name.setFixedWidth(100)
        self.short_name.textEdited.connect(self.set_short_name)
        display_options_row.addWidget(self.short_name)

        # display R
        self.display_r_checkbox = QCheckBox('R')
        self.display_r_checkbox.clicked.connect(self.update_subject_is_basic)
        display_options_row.addWidget(self.display_r_checkbox)
        display_options_row.addStretch()



        # subject info row
        subject_info_row = QHBoxLayout()
        main_layout.addLayout(subject_info_row)
        subject_info_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # teachers
        subject_info_row.addWidget(QLabel('Nauczyciele:'))
        self.teachers_row = QHBoxLayout()
        subject_info_row.addLayout(self.teachers_row)
        self.add_teacher_btn = QPushButton('+')
        self.add_teacher_btn.setFixedWidth(20)
        self.add_teacher_btn.clicked.connect(self.add_teacher)
        self.teachers_row.addWidget(self.add_teacher_btn)
        self.teachers_row.addStretch()
        # teacher_list = QComboBox()
        # self.teacher_list.addItem('')
        # for t in self.db.all_teachers():
        #     self.teacher_list.addItem(t.name, t)
        # self.teacher_list.currentTextChanged.connect(self.set_teacher)
        # self.teacher_list.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # teacher_row.addWidget(self.teacher_list)

        planning_info_row = QHBoxLayout()
        main_layout.addLayout(planning_info_row)

        # target block length
        planning_info_row.addWidget(QLabel('Docelowo lekcji w bloku:'))
        bl_len = QSpinBox()
        bl_len.setValue(subject.target_block_length)
        bl_len.setMinimum(1)
        bl_len.valueChanged.connect(self.set_target_block_length)
        planning_info_row.addWidget(bl_len)

        convinience_btn = QPushButton('Rozłożenie lekcji')
        planning_info_row.addWidget(convinience_btn)
        convinience_btn.clicked.connect(self.edit_convinience)


        # required classroom
        planning_info_row.addWidget(QLabel('Wymagana sala:'))
        self.classroom_list = QComboBox()
        self.classroom_list.addItem('---', None)
        n_of_students = len(subject.students)
        for i, classroom in enumerate(self.db.all_classrooms()):
            self.classroom_list.addItem(classroom.name, classroom)

            collisions = []
            if not classroom.allow_lessons:
                collisions.append(f'W {classroom.name} nie mogą odbywać się lekcje')
            if n_of_students > classroom.capacity:
                collisions.append(f'W {classroom.name} zmieści się tylko {classroom.capacity} uczniów, a na {subject.name} zapisanych jest {n_of_students}')

            collisions = "\n".join(collisions)
            if not collisions:
                continue
            self.classroom_list.setItemData(i+1 ,collisions, Qt.ToolTipRole)
            if not self.allow_conflicts:
                self.classroom_list.setItemData(i+1, 0, Qt.UserRole - 1)
            else:
                self.classroom_list.setItemData(i+1, QColor('red'), Qt.BackgroundRole)

        self.classroom_list.currentTextChanged.connect(self.set_classroom)
        planning_info_row.addWidget(self.classroom_list)

        # lessons
        lesson_row = QHBoxLayout()
        main_layout.addLayout(lesson_row)
        lesson_row.addWidget(QLabel('Lekcje:'))
        self.lessons = QHBoxLayout()
        self.lessons.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lesson_row.addLayout(self.lessons)
        add_lesson_btn = QPushButton('+')
        add_lesson_btn.clicked.connect(self.add_lesson)
        lesson_row.addWidget(add_lesson_btn)
        lesson_row.addStretch()

        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.close)
        main_layout.addWidget(buttonBox)
        if subject:
            self.load_subject(subject)


    def load_subject(self, subject: Subject):
        # teacher
        teachers = subject.teachers
        teachers
        for teacher in teachers:
            teacher_btn = QPushButton(teacher.name)
            self.teachers_row.insertWidget(0, teacher_btn)
            teacher_btn.clicked.connect(self.remove_teacher(teacher, teacher_btn))

        # classroom
        classroom = subject.required_classroom
        classroom_name = classroom.name if classroom else ''
        self.classroom_list.setCurrentText(classroom_name)

        # color
        self.color_button.setStyleSheet(f'background-color: {subject.color}')

        # short name
        self.short_name.setText(subject.short_name)

        # display r
        if isinstance(subject.parent(), Class):
            self.display_r_checkbox.show()
        else:
            self.display_r_checkbox.hide()
        self.display_r_checkbox.setCheckable(True)
        self.display_r_checkbox.blockSignals(True)
        self.display_r_checkbox.setChecked(not subject.basic)
        self.display_r_checkbox.setCheckable(subject.class_ is not None)
        self.display_r_checkbox.blockSignals(False)
        
        # lessons
        for n in range(self.lessons.count()):
            self.lessons.itemAt(n).widget().deleteLater()
        for lesson in subject.lessons:
            suffix = f' ({lesson.block.print_full_time()})' if lesson.block else ''
            btn = QPushButton(str(lesson.length) + suffix)
            btn.lesson = lesson
            self.lessons.addWidget(btn)
            btn.clicked.connect(self.remove_lesson)

    def edit_convinience(self):
       conv_dialog = ConvinienceDialog(self.subject, self)
       ok = conv_dialog.exec()


    def add_teacher(self):
        teachers = self.db.all_teachers()
        for teacher in self.subject.teachers:
            teachers.remove(teacher)
        dialog = AddTeacherDialog(self, teachers)
        ok = dialog.exec()
        if not ok:
            return
        teacher = dialog.teacher.currentData()
        self.db.add_teacher_to_subject(self.subject, teacher)
        btn = QPushButton(teacher.name)
        btn.clicked.connect(self.remove_teacher(teacher, btn))
        self.teachers_row.insertWidget(0, btn)

    def remove_teacher(self, teacher, btn: QPushButton):
        def func():
            self.db.remove_teacher_from_subject(self.subject, teacher)
            btn.deleteLater()
        return func
            
        
    def add_lesson(self):
        dialog = AddLessonDialog(self)
        ok = dialog.exec()
        if not ok:
            return False
        length = dialog.combobox.currentText()
        try:
            length = int(length)
        except:
            QMessageBox.warning(self, 'Błąd', 'Podaj liczbę!')
            return False
        lesson = self.db.create_lesson(length, self.subject)
        btn = QPushButton(str(length))
        btn.lesson = lesson
        self.lessons.addWidget(btn)
        btn.clicked.connect(self.remove_lesson)

    def remove_lesson(self):
        btn: QPushButton = self.sender()
        self.db.delete_lesson(btn.lesson)
        btn.deleteLater()

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.subject.color))
        if color.isValid():
            self.color_button.setStyleSheet(f'background-color: {color.name()}')
            self.db.update_subject_color(self.subject, color.name())
            self.color_changed.emit(color)

    def set_short_name(self, short_name):
        self.db.update_subject_short_name(self.subject, short_name)
        if not self.subject.basic:
            short_name += ' R'
        self.short_name_updated.emit(short_name)

    def set_name(self, name):
        self.db.update_subject_name(self.subject, name)

    def update_subject_is_basic(self):
        basic = not self.display_r_checkbox.isChecked()
        self.db.update_subject_is_basic(self.subject, basic)
        self.short_name_updated.emit(
            self.subject.short_name + '' if self.subject.basic else ' R'
        )

    def set_classroom(self):
        classroom = self.classroom_list.currentData()
        self.db.update_subject_classroom(self.subject, classroom)

    def set_target_block_length(self, length: int):
        self.db.update_subject_target_block_length(self.subject, length)


