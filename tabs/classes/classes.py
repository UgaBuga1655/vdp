from PyQt5.QtWidgets import QWidget, QHBoxLayout, QInputDialog, QPushButton, \
    QComboBox, QMessageBox, QVBoxLayout, QCheckBox, QGridLayout, QLabel, \
    QLineEdit, QScrollArea, QFileDialog

from PyQt5.QtCore import Qt
from data import Data, Class, Subclass, Student, Subject
from sqlalchemy.exc import IntegrityError
from pathlib import Path
from csv import reader

from models import student
from .reorder_classes_dialog import ReorderClassesDialog
from .subject_label import SubjectLabel
from .new_subject_label import NewSubjectLabel
from .colorwidget import Color
from .name_label import NameLabel
from .subjects import SubjectsWindow
from .subject_label import CopySubjectsDialog
from .class_import import *

class ClassesWidget(QWidget):
    def __init__(self,parent):
        super().__init__(parent=parent)
        self.db: Data = parent.db
        self.subjects = {}

        main_layout = QVBoxLayout()

        layout= QHBoxLayout()
        self.list = QComboBox(self)
        self.list.currentTextChanged.connect(self.load_class)
        layout.addWidget(self.list)

        btn = QPushButton('Dodaj klasę')
        btn.clicked.connect(self.new_class)
        layout.addWidget(btn)

        new_subclass_btn = QPushButton('Dodaj podklasę')
        new_subclass_btn.clicked.connect(self.new_subclass)
        layout.addWidget(new_subclass_btn)

        layout.addStretch()


        export_class_btn = QPushButton('Eksport do csv')
        export_class_btn.clicked.connect(self.export_class)
        layout.addWidget(export_class_btn)
        
        import_class_btn = QPushButton('Import z csv')
        import_class_btn.clicked.connect(self.import_class)
        layout.addWidget(import_class_btn)
        
        delete_class_btn = QPushButton('Usuń klasę')
        delete_class_btn.clicked.connect(self.delete_class)
        layout.addWidget(delete_class_btn)

        rename_btn = QPushButton('Zmień nazwę')
        rename_btn.clicked.connect(self.rename_class)
        layout.addWidget(rename_btn)

        reorder_btn = QPushButton('Zmień kolejność')
        reorder_btn.clicked.connect(self.reorder_classes)
        layout.addWidget(reorder_btn)

        main_layout.addLayout(layout)

        container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        container.setLayout(self.container_layout)

    
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        self.load_data(self.db)

    def new_class(self):
        class_name, ok = QInputDialog.getText(self, 'Dodaj Klasę', 'Klasa:')
        if ok and class_name:
            try:
                my_class = self.db.create_class(class_name)
                self.list.addItem(my_class.name, my_class)
                self.list.setCurrentText(my_class.name)
            except IntegrityError:
                QMessageBox.warning(self, 'Uwaga', 'Taka klasa już istnieje')


    def new_subclass(self):
        curr_class = self.list.currentData()
        if not curr_class:
            return False
        subclass = self.db.create_subclass(curr_class)
        self.load_class()
        return subclass
    
    def rename_class(self):
        class_ = self.list.currentData()
        name, ok = QInputDialog.getText(self, 'Zmień nazwę klasy', 'Nowa nazwa:', text=class_.name)
        if ok and name:
            try:
                self.db.update_class_name(class_, name)
                index = self.list.currentIndex()
                self.list.setItemText(index, name)
            except IntegrityError:
                QMessageBox.warning(self, 'Uwaga', 'Taka klasa już istnieje')
    
    def reorder_classes(self):
        btn = QMessageBox.question(self, 'Uwaga', 'Jesteś pewien? To może spowodować usunięcie części własnych bloków.')
        if btn != QMessageBox.StandardButton.Yes:
            return
        dialog = ReorderClassesDialog(self)
        ok = dialog.exec()
        if not ok:
            return
        
        new_order = [
            dialog.class_list.item(i).data(Qt.UserRole)
            for i in range(dialog.class_list.count())
        ]

        self.db.reorder_classes(new_order)
        
        # for i in range(dialog.class_list.count()):
        #     class_ = dialog.class_list.item(i).data(Qt.UserRole)
        #     self.db.update_class_order(class_, i)

        self.db.delete_unplaceable_custom_blocks()
        
        self.load_data(self.db)

    def remove_subclass(self, subclass):
        def func():
            my_class: Class = self.list.currentData()
            if not my_class:
                return False
            if len(my_class.subclasses) == 1:
                QMessageBox.information(self, 'Uwaga', 'Nie możesz usunąć jedynej podklasy')
                return False
            if QMessageBox.question(self, 'Uwaga', f'Czy na pewno chcesz usunąć: {subclass.name.upper()}') != QMessageBox.StandardButton.Yes:
                return False
            
            self.db.delete_subclass(subclass)
            
            self.load_class() 
        return func

    def load_data(self, db):
        opened_class = self.list.currentText()
        self.db = db
        self.list.clear()
        for cl in self.db.all_classes():    
            self.list.addItem(cl.name, cl)
        try:
            self.list.setCurrentText(opened_class)
        except:
            pass


    def load_class(self):
        #clear widget
        for i in range(self.container_layout.count()):
            self.container_layout.itemAt(i).widget().deleteLater()

        frame = QWidget() 
        frame_layout = QVBoxLayout()
        frame.setLayout(frame_layout)
        self.container_layout.addWidget(frame)
        #classes data
        my_class: Class = self.list.currentData()
        if not my_class:
            return False
        subclass: Subclass
        extra_subs = sorted(my_class.subjects, key=lambda x: x.get_name(0,0,0))
        self.labels = {s: [] for s in extra_subs}
        for subclass in my_class.subclasses:
            scrollarea = QScrollArea()
            subclass_widget = QWidget()
            scrollarea.setWidget(subclass_widget)
            scrollarea.setMinimumHeight(200//len(my_class.subclasses))
            subclass_layout = QVBoxLayout()
            subclass_widget.setLayout(subclass_layout)
            student_list = QGridLayout()
            subclass_layout.addLayout(student_list)
            student_list.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            student_list.setContentsMargins(0, 0, 0, 0)
            student_list.setSpacing(0)
            scrollarea.setWidgetResizable(True)

            #subclass name
            name_row = QHBoxLayout()
            frame_layout.addLayout(name_row)
            name_row.addWidget(QLabel(subclass.name.upper()))
            name_row.addStretch()
            remove_subclass_btn = QPushButton('Usuń podklasę')
            remove_subclass_btn.clicked.connect(self.remove_subclass(subclass))
            name_row.addWidget(remove_subclass_btn)
            

            #headers
            student_header = QLabel('Uczeń')
            student_header.setStyleSheet('font-weight: bold;')
            student_list.addWidget(student_header, 1, 0, Qt.AlignCenter)
            col = 1
            basic_subs = sorted(subclass.subjects, key=lambda x: x.get_name(0,0,0))

            self.subjects[subclass] = []
            self.subjects[subclass].extend(extra_subs)
            self.subjects[subclass].append(my_class)
            self.subjects[subclass].extend(basic_subs)
            self.subjects[subclass].append(subclass)

            for sub in basic_subs:
                self.labels[sub] = []

            for subject in self.subjects[subclass]:
                if isinstance(subject, Subject):
                    checkbox = QCheckBox()
                    checkbox.clicked.connect(self.toggle_all_checkboxes(subject))
                    student_list.addWidget(checkbox, 1, col, Qt.AlignCenter)
                    label = SubjectLabel(subject)
                    label.delete.connect(self.delete_subject)
                    label.edit.connect(self.edit_subject)
                    label.copy.connect(self.copy_subject)
                    student_list.addWidget(label, 0, col)
                    self.labels[subject].append(label)
                else:
                    label = NewSubjectLabel('+')
                    student_list.addWidget(label, 0, col, Qt.AlignBottom)
                    label.clicked.connect(self.new_subject(subject))
                col += 1

            #load students
            student: Student
            for student in sorted(subclass.students, key=lambda s: s.name):
                self.add_student_to_list(student, student_list)

            new_student_row = QHBoxLayout()
            subclass_layout.addLayout(new_student_row)
            new_name = QLineEdit()
            new_name.setPlaceholderText('Imię i nazwisko')
            new_name.setObjectName(f'new_name_{subclass.name}')
            new_name.setMaximumWidth(143)
            new_name.returnPressed.connect(self.new_student(subclass, student_list))
            new_student_row.addWidget(new_name)
            add_student_btn = QPushButton("Dodaj ucznia")
            add_student_btn.clicked.connect(self.new_student(subclass, student_list))
            new_student_row.addWidget(add_student_btn)
            new_student_row.addStretch()

            subclass_layout.addStretch()
            
            frame_layout.addWidget(scrollarea)

    def add_student_to_list(self, student, student_list: QGridLayout): 
        n = student_list.rowCount()
        #checkbox
        label = NameLabel(student)
        label.setMargin(5)
        label.setMinimumWidth(150)
        label.delete.connect(self.delete_student)
        label.update_name.connect(self.db.update_student_name)
        student_list.addWidget(label,n, 0)

        #subjects
        for i, subject in enumerate(self.subjects[student.subclass]):
            if not isinstance(subject, Subject):
                continue
            student_list.addWidget(Color(subject.color, brighten=n%2), n, i+1)
            checkbox = QCheckBox()
            checkbox.subject = subject
            if subject in student.subjects:
                checkbox.setChecked(True)
            # checkbox.setStyleSheet(f'background-color: {subject.color}')
            checkbox.toggled.connect(self.set_student_subject(student, subject))
            student_list.addWidget(checkbox, n, i+1, Qt.AlignCenter)

    def new_student(self, subclass, student_list):
        def func():
            new_name_box = self.findChild(QLineEdit, f'new_name_{subclass.name}')
            new_name = new_name_box.text()
            if not new_name:
                return
            class_name = self.db.student_exists(new_name)
            if class_name:
                QMessageBox.warning(self, 'Uwaga', f'Taki uczeń już istnieje! ({class_name})')
                return
            student = self.db.create_student(new_name, subclass)

            self.add_student_to_list(student, student_list)
            new_name_box.clear()
        return func

    def toggle_all_checkboxes(self, subject):
        def func(new_state):
            curr_widget:QWidget = self.sender().parent()
            checkboxes: list[QCheckBox] = curr_widget.findChildren(QCheckBox)
            # new_state = checkboxes[0].isChecked()
            for checkbox in checkboxes:
                if hasattr(checkbox, 'subject') and checkbox.subject == subject:
                    checkbox.setChecked(new_state)
        return func

    def set_student_subject(self, student, subject):
        def func(add):
            if add:
                self.db.add_subject_to_student(subject, student)
            else:
                self.db.remove_subject_from_student(subject, student)
        return func

    def delete_student(self, student: Student):
        if QMessageBox.question(self, 'Uwaga', f'Czy na pewno chesz usunąć: {student.name}') != QMessageBox.StandardButton.Yes:
            return False
        self.db.delete_student(student)
        self.load_class()

    def delete_subject(self, subject):
        if QMessageBox.question(self, 'Uwaga', f'Czy na pewno chesz usunąć: {subject.get_name(0,0,0)}') != QMessageBox.StandardButton.Yes:
            return False
        self.db.delete_subject(subject)
        self.load_class()
    
    def edit_subject(self, subject):
        if not subject:
            return
        subject_window = SubjectsWindow(self, self.db, subject)
        setattr(self, f'subject_{subject.id}', subject_window)
        subject_window.show()
        label: SubjectLabel
        for label in self.labels[subject]:
            subject_window.short_name_updated.connect(label.setText)
            subject_window.teacher_changed.connect(label.setToolTip)
        subject_window.color_changed.connect(self.load_class)

    def copy_subject(self, subject):
        if subject.subclass:
            targets = self.db.all_subclasses()
        else:
            targets = self.db.all_classes()
        dialog = CopySubjectsDialog(self, targets)
        ok = dialog.exec()
        if not ok:
            return
        target = dialog.target_list.currentData()
        self.db.copy_subject_to_subclass(subject, target)



        
    def new_subject(self, sub_class):
        def func():
            basic = isinstance(sub_class, Subclass)
            subject_name, ok = QInputDialog.getText(self, f"Dodaj Przedmiot {'Podstawowy' if basic else 'Wspólny'}", 'Przedmiot:')
            if ok and subject_name:
                subject = self.db.create_subject(subject_name, basic, sub_class)
            self.load_class()
        return func

    def delete_class(self):
        my_class: Class = self.list.currentData()
        if QMessageBox.question(self, 'Uwaga', f'Czy na pewno chcesz usunąć klasę: {my_class.name}') == QMessageBox.StandardButton.Yes:
            self.db.delete_class(my_class)
        self.load_data(self.db)

    def export_class(self):
        class_ = self.list.currentData()
        filename, _ = QFileDialog.getSaveFileName(self, 
                                                caption=f'Exportuj {class_.name}', 
                                                directory=f'{class_.name}.csv')
        class_.to_csv(filename=filename)

    def import_class(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Wybierz plik', '', f'Pliki csv (*.csv)')
        if not filename:
            return
        class_name = Path(filename)
        class_name = class_name.name.split('.')[0]
        class_names = {class_.name for class_ in self.db.all_classes()}
        while class_name in class_names:
            class_name += '_copy'

        format_dialog = ImportFormatDialog(self, filename)
        ok = format_dialog.exec()
        if not ok:
            return

        name_cols = format_dialog.n_of_name_cols.value()
        n_of_subclasses = format_dialog.n_of_subclasses.value()

        class_ = self.db.create_class(class_name)
        for _ in range(n_of_subclasses-1):
            self.db.create_subclass(class_)

        self.list.addItem(class_.name, class_)

        with open(filename) as csvfile:
            csvreader = reader(csvfile)
            students = []
            # student_names = []
            subject_names = set()
            for row in csvreader:
                name = ' '.join(row[:name_cols])
                students.append((name, row[name_cols:]))
                for subject_name in row[name_cols:]:
                    subject_names.add(subject_name)
        subject_names = list(subject_names)
        subject_names.sort()

        import_dialog = ImportDialog(self, students, subject_names, class_)
        ok = import_dialog.exec()
        if not ok:
            self.db.delete_class(class_)

            self.load_data(self.db)
            return
        

            
                    
                