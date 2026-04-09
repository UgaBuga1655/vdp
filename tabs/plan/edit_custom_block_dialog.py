from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QPushButton, QDialogButtonBox,\
    QLineEdit, QColorDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from data import Data, CustomBlock
from db_config import settings

class EditCustomBlockDialog(QDialog):
    def __init__(self, custom_block: CustomBlock, db: Data):
        super().__init__()
        self.setWindowTitle(custom_block.print_full_time())
        self.custom_block = custom_block
        self.db = db
        self.classrooms = self.db.all_classrooms()
        self.classroom_collisions = self.db.potential_collisions_at_block(custom_block, exclude_self=True, get_classrooms=True, get_teachers=True)
      
 
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        self.name_row = QHBoxLayout()
        self.main_layout.addLayout(self.name_row)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(20, 20)
        self.color_btn.setStyleSheet(f'background-color: {self.custom_block.color}')
        self.color_btn.clicked.connect(self.set_color)
        self.name_row.addWidget(self.color_btn)

        text_edit = QLineEdit(custom_block.text)
        self.name_row.addWidget(text_edit)
        text_edit.textChanged.connect(self.update_text)

        self.duties = QGridLayout()
        self.main_layout.addLayout(self.duties)
        for duty in custom_block.duties:
            self.place_duty(duty)
            
        row = QHBoxLayout()
        self.main_layout.addLayout(row)
        new_button = QPushButton('+')
        new_button.clicked.connect(self.add_duty)
        row.addWidget(new_button)
        row.addStretch()

        buttonBox = QDialogButtonBox()
        row.addWidget(buttonBox)

        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
       

    def add_duty(self):
        duty = self.db.new_duty(self.custom_block)
        self.place_duty(duty)


    def place_duty(self, duty):
        row = self.duties.rowCount()

        classroom_select = QComboBox()
        classroom_select.addItem('---', None)
        for i, classroom in enumerate(self.classrooms):
            classroom_select.addItem(classroom.name, classroom)

            collision = '\n'.join(self.classroom_collisions[classroom])
            if not collision:
                continue
            classroom_select.setItemData(i+1, collision, Qt.ToolTipRole)
            if not settings.allow_creating_conflicts:
                classroom_select.setItemData(i+1, 0, Qt.UserRole - 1)
            else:
                classroom_select.setItemData(i+1, QColor('red'), Qt.BackgroundRole)
        classroom_select.currentIndexChanged.connect(
            self.update_duty_classroom(duty, classroom_select)
        )
        self.duties.addWidget(classroom_select, row, 0)
        if duty.classroom:
            classroom_select.setCurrentText(duty.classroom.name)

        teacher_select = QComboBox()
        teacher_select.addItem('---', None)
        for i, teacher in enumerate(self.db.all_teachers()):
            teacher_select.addItem(teacher.name, teacher)
            collision = '\n'.join(self.classroom_collisions[teacher])
            if not collision:
                continue
            teacher_select.setItemData(i+1, collision, Qt.ToolTipRole)
            if not settings.allow_creating_conflicts:
                teacher_select.setItemData(i+1, 0, Qt.UserRole - 1)
            else:
                teacher_select.setItemData(i+1, QColor('red'), Qt.BackgroundRole)
        teacher_select.currentIndexChanged.connect(
            self.update_duty_teacher(duty, teacher_select)
        )
        self.duties.addWidget(teacher_select, row, 1)
        if duty.teacher:
            teacher_select.setCurrentText(duty.teacher.name)

        del_btn = QPushButton('X')
        del_btn.setFixedWidth(20)
        del_btn.clicked.connect(self.delete_duty(duty,
            [teacher_select, classroom_select, del_btn]))
        self.duties.addWidget(del_btn, row, 2)


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
    
    def update_text(self, text):
        self.db.update_custom_block_text(self.custom_block, text)

    def set_color(self):
        color = QColorDialog.getColor(QColor(self.custom_block.color))
        if color.isValid():
            # self.setBrush(color)
            self.db.update_custom_block_color(self.custom_block, color.name())
            self.color_btn.setStyleSheet(f'background-color: {color.name()}')


    def delete_duty(self, duty, widgets):
        def func():
            self.db.delete_duty(duty)
            for widget in widgets:
                widget.deleteLater()
        return func