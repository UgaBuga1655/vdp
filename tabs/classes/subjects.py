from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QDialog, QDialogButtonBox, \
      QPushButton, QLabel, QDialogButtonBox, QMessageBox, QCheckBox, QColorDialog, QLineEdit
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QCursor

from data import Data, Class, Subclass

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


class CopySubjectsDialog(QDialog):
    def __init__(self, parent, targets):
        super().__init__(parent=parent)
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
    
    def __init__(self,parent, db, subject):
        super().__init__()
        self.db: Data = db
        self.subject = subject
        layout= QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle('Przedmiot')
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.move(QCursor.pos() + QPoint(10,10))

        top_row = QHBoxLayout()
        layout.addLayout(top_row)
        full_name = QLineEdit(subject.name, self)
        top_row.addWidget(full_name)
        full_name.textEdited.connect(self.set_name)



        # display options row
        display_options_row = QHBoxLayout()
        layout.addLayout(display_options_row)
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
        self.display_r_checkbox = QCheckBox('Rozszerzony')
        self.display_r_checkbox.clicked.connect(self.update_subject_is_basic)
        display_options_row.addWidget(self.display_r_checkbox)
        display_options_row.addStretch()



        # subject info row
        teacher_row = QHBoxLayout()
        layout.addLayout(teacher_row)
        teacher_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # teachers
        teacher_row.addWidget(QLabel('Nauczyciel:'))
        self.teacher_list = QComboBox()
        self.teacher_list.addItem('')
        for t in self.db.read_all_teachers():
            self.teacher_list.addItem(t.name, t)
        self.teacher_list.currentTextChanged.connect(self.set_teacher)
        self.teacher_list.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        teacher_row.addWidget(self.teacher_list)

        # required classroom
        teacher_row.addWidget(QLabel('Wymagana sala:'))
        self.classroom_list = QComboBox()
        for classroom in self.db.all_classrooms():
            self.classroom_list.addItem(classroom.name, classroom)
        self.classroom_list.currentTextChanged.connect(self.set_classroom)
        teacher_row.addWidget(self.classroom_list)

        # lessons
        lesson_row = QHBoxLayout()
        layout.addLayout(lesson_row)
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
        layout.addWidget(buttonBox)
        if subject:
            self.load_subject(subject)


    def load_subject(self, subject):
        # teacher
        teacher = subject.teacher
        teacher_name = teacher.name if teacher else ''
        self.teacher_list.setCurrentText(teacher_name)

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
        self.display_r_checkbox.setCheckable(subject.my_class is not None)
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

    def set_teacher(self):
        teacher = self.teacher_list.currentData()
        subject = self.subject
        if not (subject and teacher):
            return False
        self.db.update_subject_teacher(subject, teacher)

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
        self.short_name_updated.emit(short_name)
        self.db.update_subject_short_name(self.subject, short_name)

    def set_name(self, name):
        self.db.update_subject_name(self.subject, name)

    def update_subject_is_basic(self):
        basic = not self.display_r_checkbox.isChecked()
        self.db.update_subject_is_basic(self.subject, basic)

    def set_classroom(self):
        classroom = self.classroom_list.currentData()
        self.db.update_subject_classroom(self.subject, classroom)


