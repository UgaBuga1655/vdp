from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QPushButton, QLineEdit, QWidget, QHBoxLayout,\
      QSpinBox, QCheckBox, QMessageBox, QComboBox, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from data import Data, Classroom

class ClassroomTreeWidget(QTreeWidget):
    redraw_table = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.db: Data = parent.db
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QTreeWidget.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.header().hide()
        self.load_data()


    def load_data(self, db=None):
        if db:
            self.db = db
        self.clear()
        add_group_widget = QWidget(self)
        row = QHBoxLayout()
        add_group_widget.setLayout(row)

        self.add_group_edit = QLineEdit(add_group_widget)
        self.add_group_edit.setMaximumWidth(200)
        self.add_group_edit.setPlaceholderText('Dodaj grupę sal')
        self.add_group_edit.returnPressed.connect(self.create_classroom_group)
        row.addWidget(self.add_group_edit)

        btn = QPushButton('+', add_group_widget)
        btn.setMaximumWidth(20)
        btn.clicked.connect(self.create_classroom_group)
        row.addWidget(btn)

        row.addStretch()

        add_item = QTreeWidgetItem(self, [])
        self.setItemWidget(add_item, 0, add_group_widget)

        for group in self.db.all_classrooms_groups():
            self.add_group(group)
   

    def add_group(self, group):
        count = self.topLevelItemCount()
        index = max(0, count-1)
        group_item = QTreeWidgetItem([])

        group_widget = QWidget(self)
        row = QHBoxLayout()
        row.setContentsMargins(0,0,0,0)
        group_widget.setLayout(row)

        name_edit = QLineEdit(group_widget)
        name_edit.setText(group.name)
        name_edit.setMaximumWidth(200)
        name_edit.editingFinished.connect(self.update_group_name(group, name_edit))
        row.addWidget(name_edit)

        btn = QPushButton('X')
        btn.setFixedWidth(20)
        btn.clicked.connect(self.delete_group(group_item, group))
        row.addWidget(btn)

        row.addStretch()

        self.insertTopLevelItem(index, group_item)
        self.setItemWidget(group_item, 0, group_widget)
        new_classroom_item = QTreeWidgetItem(group_item, [])

        new_classroom_widget = QWidget(self)
        row = QHBoxLayout()
        row.setContentsMargins(0,0,0,0)
        new_classroom_widget.setLayout(row)

        new_classroom_edit = QLineEdit(new_classroom_widget)
        new_classroom_edit.setPlaceholderText('Dodaj salę')
        new_classroom_edit.setMaximumWidth(100)
        new_classroom_edit.returnPressed.connect(self.create_classroom(group, group_item, new_classroom_edit))
        row.addWidget(new_classroom_edit)

        btn = QPushButton('+')
        btn.setMaximumWidth(20)
        btn.clicked.connect(self.create_classroom(group, group_item, new_classroom_edit))
        row.addWidget(btn)

        row.addStretch()

        self.setItemWidget(new_classroom_item, 0, new_classroom_widget)
        for classroom in group.classrooms:
            self.add_classroom(group_item, classroom)
        group_item.setExpanded(True)
        return new_classroom_edit

    def create_classroom_group(self):
        group_name = self.add_group_edit.text().strip()
        if not group_name:
            return
        group = self.db.create_classroom_group(group_name)
        new_classroom_edit = self.add_group(group)
        new_classroom_edit.setFocus()
        self.add_group_edit.clear()
        self.redraw_table.emit()

    def update_group_name(self, group, name_edit):
        def func():
            self.db.update_classroom_group_name(group, name_edit.text())
            self.redraw_table.emit()
        return func

    def delete_group(self,item, group):
        def func():
            n_of_classrooms = len(group.classrooms)
            n_of_lessons = 0
            if n_of_classrooms:
                for classroom in group.classrooms:
                    n_of_lessons += len(classroom.lessons)
                    n_of_lessons += len(classroom.duties)
                match n_of_classrooms:
                    case 1:
                        classrooms = 'jest 1 sala, w której'
                    case _ if n_of_classrooms%10 in [2,3,4] and (n_of_classrooms<10 or n_of_classrooms>20):
                        classrooms = f'są {n_of_classrooms} sale, w których'
                    case _:
                        classrooms = f'jest {n_of_classrooms} sal, w których'
                match n_of_lessons:
                    case 0:
                        lessons = 'nie odbywa się żadna lekcja ani dyżur'
                    case 1:
                        lessons = 'odbywa się 1 lekcja lub dyżur'
                    case _ if n_of_lessons%10 in [2,3,4] and (n_of_lessons<10 or n_of_lessons>20):
                        lessons = f'odbywają się {n_of_lessons} lekcje lub dyżury'
                    case _:
                        lessons = f'odbywa się {n_of_lessons} lekcji lub dyżurów'
                message = f'W grupie "{group.name}" {classrooms} {lessons}. Czy na pewno chcesz ją usunąć?'
                if QMessageBox.question(self, 'Uwaga', message) != QMessageBox.StandardButton.Yes:
                    return

            self.db.delete_classroom_group(group)
            self.removeItemWidget(item, 0)
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            self.redraw_table.emit()
        return func


    def add_classroom(self, group_item: QTreeWidgetItem, classroom: Classroom):
        count = group_item.childCount()
        index = max(0, count -1)
        classroom_item = QTreeWidgetItem([])
        group_item.insertChild(index, classroom_item)

        classroom_widget = QWidget(self)
        row = QHBoxLayout()
        classroom_widget.setLayout(row)
        row.setContentsMargins(0,0,0,0)

        name_edit = QLineEdit(classroom.name, classroom_widget)
        name_edit.setMaximumWidth(100)
        name_edit.editingFinished.connect(self.update_classroom_name(classroom, name_edit))
        row.addWidget(name_edit)

        capacity = QSpinBox()
        capacity.setRange(1, 999999)
        capacity.setValue(classroom.capacity)
        capacity.valueChanged.connect(self.set_capacity(classroom))
        row.addWidget(capacity)

        row.addWidget(QLabel('Lekcje:'))
        self.allow_lessons = QComboBox(classroom_widget)

        self.allow_lessons.addItem('Wszystkie', 'all')
        self.allow_lessons.addItem('Przypisane', 'selected')
        self.allow_lessons.addItem('Żadne', 'none')
        index = ['all', 'selected', 'none'].index(classroom.allow_lessons)
        self.allow_lessons.setCurrentIndex(index)
        self.allow_lessons.currentIndexChanged.connect(self.set_allow_lessons(classroom))
        row.addWidget(self.allow_lessons)

        del_btn = QPushButton('X', classroom_widget)
        del_btn.setMaximumWidth(20)
        del_btn.clicked.connect(self.delete_classroom(classroom_item, classroom))
        row.addWidget(del_btn)

        row.addStretch()
        self.setItemWidget(classroom_item, 0, classroom_widget)
        return capacity

    def create_classroom(self, group, group_item: QTreeWidgetItem, line:QLineEdit):
        def func():
            name = line.text().strip()
            if not name:
                self.add_group_edit.setFocus()
                return
            classroom = self.db.create_classroom(group, name)
            capacity = self.add_classroom(group_item, classroom)
            capacity.selectAll()
            capacity.setFocus()
            capacity.lineEdit().returnPressed.connect(line.setFocus)
            line.clear()
        return func
    
    def set_capacity(self, classroom):
        def func(capacity):
            self.db.update_classroom_capacity(classroom, capacity)
        return func

    def set_allow_lessons(self, classroom):
        def func():
            allow = self.allow_lessons.currentData()
            self.db.update_classroom_allow_lessons(classroom, allow)
        return func
    
    def update_classroom_name(self, classroom, name_edit):
        def func():
            self.db.update_classroom_name(classroom, name_edit.text())
        return func
 
    def delete_classroom(self, classroom_item: QTreeWidgetItem, classroom):
        def func():
            n_of_lessons = len(classroom.lessons)
            n_of_duties = len(classroom.duties)
            if n_of_lessons + n_of_duties:
                match n_of_lessons:
                    case 1:
                        lessons = 'odbywa się 1 lekcja'
                    case _ if n_of_lessons%10 in [2,3,4] and (n_of_lessons<10 or n_of_lessons>20):
                        lessons = f'odbywają się {n_of_lessons} lekcje'
                    case _:
                        lessons = f'odbywa się {n_of_lessons} lekcji'
                
                match n_of_duties:
                    case 1:
                        duties = '1 dyżur'
                    case _ if n_of_duties%10 in [2,3,4] and (n_of_duties<10 or n_of_duties>20):
                        duties = f'{n_of_duties} dyżury'
                    case _:
                        duties = f'{n_of_duties} dyżurów'
                
                message = f'W sali "{classroom.name}" {lessons} i {duties}. Czy na pewno chcesz ją usunąć?'
                if QMessageBox.question(self, 'Uwaga', message) != QMessageBox.StandardButton.Yes:
                    return

            self.db.delete_classroom(classroom)
            self.removeItemWidget(classroom_item, 0)
            classroom_item.parent().removeChild(classroom_item)
        return func
 
   

