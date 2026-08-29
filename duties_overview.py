from PyQt5.QtWidgets import QWidget, QTreeWidget, QComboBox, QLabel, QHBoxLayout, QTreeWidgetItem, QGridLayout, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from data import Data, LessonBlockDB, CustomBlock
from functions import display_hour, delete_layout

day_names = ['Poniedziałek','Wtorek','Środa','Czwartek','Piątek']

class UnscrollabeComboBox(QComboBox):
    def wheelEvent(self, e):
        e.ignore()

class DutiesOverview(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.db: Data = parent.db
        self.frame_layout = QHBoxLayout()
        self.main_widget = QWidget()

        self.setLayout(self.frame_layout)

    def update_duty_teacher(self, duty, combo: QComboBox):
        def func():
            teacher = combo.currentData()
            self.db.update_duty_teacher(duty, teacher)
        return func

    def classes_name(self, duty, total_sub_classes):
        if isinstance(duty.block, LessonBlockDB):
            class_name = duty.block.parent().full_name()
        else:
            if len(duty.block.subclasses) == total_sub_classes:
                class_name = 'Wszyscy'
            else:
                names = [cl.full_name() for cl in duty.block.subclasses]
                names.sort()
                class_name = '/'.join(names)

        return class_name

    def load(self):
        self.main_widget.deleteLater()
        self.main_widget = QWidget()
        self.frame_layout.addWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        bundle = self.db.bundled_duties()
        self.setWindowTitle('Zarządzanie dyżurami')
        total_sub_classes = len(self.db.all_subclasses())
        for day_name, day in zip(day_names, bundle):
            column = QVBoxLayout()
            self.main_layout.addLayout(column)
            tree = QTreeWidget()
            tree.setHeaderLabel(day_name)
            column.addWidget(tree)
            for row in day:
                if not len(row):
                    continue
                lens = {}
                for duty in row:
                    if duty.block.length in lens:
                        lens[duty.block.length].append(duty)
                    else:
                        lens[duty.block.length] = [duty]
                lens = list(lens.items())
                lens.sort()
                for _, duties in lens:
                    start = duties[0].block.start
                    end = start + duties[0].block.length
                    time = f'{display_hour(start)} - {display_hour(end)}'
                    row_item = QTreeWidgetItem([])
                    tree.addTopLevelItem(row_item)
                    duties.sort(key=lambda d: (d.classroom.name, self.classes_name(d, total_sub_classes)))
                    widget = QWidget()
                    grid = QGridLayout()
                    widget.setLayout(grid)
                    grid.addWidget(QLabel(f'<b>{time}</b>'), 0, 0, 1, 2)
                    for i, duty in enumerate(duties):
                        class_name = self.classes_name(duty, total_sub_classes)
                        grid.addWidget(QLabel(f'{duty.classroom.name}, {class_name}: '), i+1, 0)
                        combobox = UnscrollabeComboBox()
                        combobox.addItem('---', None)
                        combobox.setFocusPolicy(Qt.NoFocus)
                        collisions = self.db.potential_collisions_at_block(duty.block, exclude_self=False, get_teachers=True)
                        for it, teacher in enumerate(self.db.all_teachers()):
                            
                            combobox.addItem(teacher.name, teacher)
                            collision = '\n'.join(collisions[teacher])
                            if not collision:
                                continue
                            combobox.setItemData(it+1, collision, Qt.ToolTipRole)
                            if not self.db.settings().allow_conflicts:
                                combobox.setItemData(it+1, 0, Qt.UserRole - 1)
                            else:
                                combobox.setItemData(it+1, QColor('red'), Qt.BackgroundRole)

                        if duty.teacher:
                            combobox.setCurrentText(duty.teacher.name)
                        combobox.currentIndexChanged.connect(self.update_duty_teacher(duty, combobox))
                        grid.addWidget(combobox, i+1, 2)
                    
                    tree.setItemWidget(row_item, 0, widget)

