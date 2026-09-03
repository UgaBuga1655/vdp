from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QPushButton, QDialogButtonBox,\
    QLineEdit, QColorDialog, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from data import Data, CustomBlock
# from db_config import settings

class EditCustomBlockDialog(QDialog):
    def __init__(self, custom_block: CustomBlock, db: Data):
        super().__init__()
        self.setWindowTitle(custom_block.print_full_time())
        self.custom_block = custom_block
        self.db = db
        self.classrooms = self.db.all_classrooms()
        self.collisions = self.db.potential_collisions_at_block(custom_block, exclude_self=True, get_classrooms=True, get_teachers=True, get_students=True)

        self.sen_students = []
        for subclass in self.custom_block.subclasses:
            self.sen_students.extend([s for s in subclass.students if s.sen])
        self.sen_students.sort(key=lambda s: (s.class_.order, s.subclass.full_name(), s.name))

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

        mandatory = QCheckBox('Obowiązkowy')
        self.name_row.addWidget(mandatory)
        mandatory.setChecked(custom_block.mandatory)
        mandatory.toggled.connect(self.set_mandatory)

        self.duties = QGridLayout()
        self.main_layout.addLayout(self.duties)
        for duty in custom_block.events:
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
            student_select.addItem(f'({student.subclass.full_name()}) {student.name}', student)
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

    
    def update_text(self, text):
        self.db.update_custom_block_text(self.custom_block, text)

    def set_color(self):
        color = QColorDialog.getColor(QColor(self.custom_block.color))
        if color.isValid():
            # self.setBrush(color)
            self.db.update_custom_block_color(self.custom_block, color.name())
            self.color_btn.setStyleSheet(f'background-color: {color.name()}')

    def set_mandatory(self, mandatory):
        self.db.update_custom_block_mandatory(self.custom_block, mandatory)


    def delete_duty(self, duty, widgets):
        def func():
            self.db.delete_duty(duty)
            for widget in widgets:
                widget.deleteLater()
        return func