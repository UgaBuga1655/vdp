from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QPushButton, QLineEdit, QWidget, QHBoxLayout, QSpinBox, QCheckBox
from PyQt5.QtCore import Qt
from data import Data, Classroom

class ClassroomTreeWidget(QTreeWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.db: Data = parent.db
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        # self.root = QTreeWidgetItem(self, ['Groups'])
        self.load_data()

    def load_data(self):
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

    def create_classroom(self, group, group_item: QTreeWidgetItem, line:QLineEdit):
        def func():
            name = line.text()
            if not name:
                return
            classroom = self.db.create_classroom(group, name)
            self.add_classroom(group_item, classroom)
            line.clear()
        # del_btn.clicked.connect(self.delete_classroom(classroom_item, classroom))
        # self.setItemWidget(classro
        return func
    
    def delete_classroom(self, classroom_item: QTreeWidgetItem, classroom):
        def func():
            self.db.delete_classroom(classroom)
            for n in range(1):
                self.removeItemWidget(classroom_item, n)
            classroom_item.parent().removeChild(classroom_item)
            # del classroom_item
        return func
    
    def add_group(self, group):
        count = self.topLevelItemCount()
        index = max(0, count-1)
        group_item = QTreeWidgetItem([group.name])
        self.insertTopLevelItem(index, group_item)
        add_classroom_item = QTreeWidgetItem(group_item, [])

        widget = QWidget(self)
        row = QHBoxLayout()
        row.setContentsMargins(0,0,0,0)
        widget.setLayout(row)

        new_classroom_edit = QLineEdit(widget)
        new_classroom_edit.setPlaceholderText('Dodaj salę')
        new_classroom_edit.setMaximumWidth(100)
        new_classroom_edit.returnPressed.connect(self.create_classroom(group, group_item, new_classroom_edit))
        row.addWidget(new_classroom_edit)

        btn = QPushButton('+')
        btn.setMaximumWidth(20)
        btn.clicked.connect(self.create_classroom(group, group_item, new_classroom_edit))
        row.addWidget(btn)

        row.addStretch()

        self.setItemWidget(add_classroom_item, 0, widget)
        for classroom in group.classrooms:
            self.add_classroom(group_item, classroom)
        group_item.setExpanded(True)

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
        name_edit.textEdited.connect(self.update_classroom_name(classroom))
        row.addWidget(name_edit)

        capacity = QSpinBox()
        capacity.setMinimum(1)
        capacity.setValue(classroom.capacity)
        capacity.valueChanged.connect(self.set_capacity(classroom))
        row.addWidget(capacity)

        allow_lessons = QCheckBox('Przypisuj lekcje', classroom_widget)
        allow_lessons.setChecked(classroom.allow_lessons)
        allow_lessons.toggled.connect(self.set_allow_lessons(classroom))
        row.addWidget(allow_lessons)

        del_btn = QPushButton('X', classroom_widget)
        del_btn.setMaximumWidth(20)
        del_btn.clicked.connect(self.delete_classroom(classroom_item, classroom))
        row.addWidget(del_btn)

        row.addStretch()
        self.setItemWidget(classroom_item, 0, classroom_widget)

    def create_classroom_group(self):
        group_name = self.add_group_edit.text()
        group = self.db.create_classroom_group(group_name)
        self.add_group(group)
        self.add_group_edit.clear()
        
    def set_capacity(self, classroom):
        def func(capacity):
            self.db.update_classroom_capacity(classroom, capacity)
        return func

    def set_allow_lessons(self, classroom):
        def func(allow):
            self.db.update_classroom_allow_lessons(classroom, allow)
        return func
    
    def update_classroom_name(self, classroom):
        def func(name):
            self.db.update_classroom_name(classroom, name)
        return func
