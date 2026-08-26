from turtle import st

from sqlalchemy.orm import sessionmaker, scoped_session, load_only
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, or_, and_, literal
from PyQt5.QtCore import pyqtSignal, QObject
from string import ascii_lowercase
from typing import List
from functions import shorten_name
from db_config import Base
from models import *
from itertools import combinations


class Data(QObject):
    update_block = pyqtSignal(Block)
    redraw_plan = pyqtSignal()
    teachers_changed = pyqtSignal()
    classrooms_changed = pyqtSignal()

    def changes_les_g_or_feas(func):
        def my_inner(self: 'Data', *args, **kwargs):
            # print(func)
            self.clear_les_g_and_feas()
            return func(self, *args, **kwargs)
        return my_inner
    
    def changes_bl_g(func):
        def inner(self: 'Data', *args, **kwargs):
            self.clear_bl_g()
            return func(self, *args, **kwargs)
        return inner


    def __init__(self, filename="planer.vdp"):
        super().__init__()
        engine = create_engine('sqlite:///' + filename)
        Base.metadata.create_all(engine)
        self.session_factory = sessionmaker(bind=engine)
        self.session = self.session_factory()
        # self.init_distances()
        if not self.session.query(Metadata).count():
            settings = Metadata()
            self.session.add(settings)
        if not self.session.query(Results).count():
            results = Results()
            self.session.add(results)
        for subject in self.session.query(Subject):
            for day in range(5):
                if getattr(subject, f'for{day+1}') is None:
                    setattr(subject, f'for{day+1}', 0)
                if getattr(subject, f'inconv{day+1}') is None:
                    setattr(subject, f'inconv{day+1}', 0)
        #     subject.basic = subject.class_ is None
        #     if subject.teacher and subject.teacher not in subject.teachers:
        #         print(subject.id, subject.teacher_id)
        #         subject.teachers.append(subject.teacher)
        # self.clear_all_lesson_blocks(leave_locked=True)
        self.session.commit()

    def save_solution(self, solution):
        # print(solution[63])
        for lesson in self.session.query(Lesson).filter_by(block_locked=False):
            if lesson.id in solution.keys():
                # print(f'jest {lesson.id}')
                block_id, classroom_id = solution[lesson.id]
                lesson.block = self.session.query(Block).filter_by(id=block_id).first()
                lesson.classroom = self.session.query(Classroom).filter_by(id=classroom_id).first()
                # print(f'{lesson}: {solution[lesson]}')
                # lesson.block = self.session.query(LessonBlockDB).filter_by(id=solution[lesson]).first()
            else:
                # print(f'nie ma {lesson.id}')
                lesson.block, lesson.classroom = None, None
            # self.session.add(lesson)
            # print(lesson.id,lesson.block_id)
        self.session.commit()
        self.redraw_plan.emit()

    def get_scoped_session(self):
        Session = scoped_session(session_factory=self.session_factory)
        return Session()
        
    def table_names(self):
        return Base.metadata.tables.keys()

    # teachers
    def create_teacher(self, name, availability = [0]*5):
        teacher = Teacher(name=name, av=availability)
        try:
            self.session.add(teacher)
            self.session.commit()
            self.teachers_changed.emit()
            return teacher
        except IntegrityError:
            self.session.rollback()
            raise IntegrityError('Taki nauczyciel już istnieje', '', '')
        
    def read_teacher_av(self, t: Teacher):
        return [t.av1, t.av2, t.av3, t.av4, t.av5]

    @changes_les_g_or_feas    
    def update_teacher_av(self, t: Teacher, av):
        t.av1, t.av2, t.av3, t.av4, t.av5 = av
        for subject in t.subjects:
            for lesson in subject.lessons:
                if not lesson.block:
                    continue
                self.update_block.emit(lesson.block)
        self.session.commit()

    def update_teacher_name(self, t: Teacher, name):
        t.name = name
        self.session.commit()
        self.teachers_changed.emit()

    def all_teachers(self):
        return self.session.query(Teacher).order_by(Teacher.name).all()

    @changes_les_g_or_feas
    def delete_teacher(self, t):
        self.session.delete(t)
        self.session.commit()
        self.teachers_changed.emit()


    # subclasses
    def all_subclasses(self) -> List[Subclass]:
        return self.session.query(Subclass).join(Class).order_by(Class.order).order_by(Subclass.class_id).all()
    
    def copy_subjects_to_subclass(self, origin: Subclass|Class, target: Subclass|Class):
        if type(origin) != type(target):
            return

        target_names = [s.name for s in target.subjects]
        subject: Subject
        for subject in origin.subjects:
            if subject.name in target_names:
                continue
            copy = Subject(teacher=subject.teacher, name=subject.name, basic=subject.basic, short_name=subject.short_name, color=subject.color)
            self.session.add(copy)
            target.subjects.append(copy)
            for lesson in subject.lessons:
                self.create_lesson(lesson.length, copy)
        self.session.commit()

     
    def copy_subject_to_subclass(self, subject: Subject, target: Subclass|Class):
        if type(subject.parent()) != type(target):
            return

        target_names = [s.name for s in target.subjects]
        
        if subject.name in target_names:
            return
        copy = Subject(teacher=subject.teacher, name=subject.name, basic=subject.basic, short_name=subject.short_name, color=subject.color)
        self.session.add(copy)
        target.subjects.append(copy)
        for lesson in subject.lessons:
            self.create_lesson(lesson.length, copy)
        self.session.commit()


    def move_subject(self, subject: Subject, target: Class | Subclass, clear_students = True):
        subject.class_ = None
        subject.subclass = None
        if clear_students:
            subject.students = []
        if isinstance(target, Subclass):
            subject.subclass = target
        else:
            subject.class_ = target
        self.session.commit()



    # classes
    def all_classes(self, session=None) -> List[Class]:
        if not session:
            session = self.session
        return session.query(Class).order_by(Class.order).all()

    def create_class(self, name: str, n_of_subclasses=1) -> Class:
        classes = self.all_classes()
        order = classes[-1].order + 1 if classes else 1
        new_class = Class(name=name, order=order)
        self.session.add(new_class)
        self.session.commit()
        for _ in range(n_of_subclasses):
            self.create_subclass(new_class, redraw=False)
        self.redraw_plan.emit()
        return new_class
    
    def reorder_classes(self, new_order: List[Class]):
        for order, class_ in enumerate(new_order):
            class_.order = order
        self.session.commit()
        self.redraw_plan.emit()

    def update_class_name(self, class_: Class, name: str) -> None:
        class_.name = name
        self.session.commit()
    
    def delete_class(self, class_: Class) -> None:
        for subclass in class_.subclasses:
            self.delete_subclass(subclass, redraw=False)
        for subject in class_.subjects:
            self.delete_subject(subject)
        for block in class_.blocks:
            self.delete_block(block)
        self.session.delete(class_)
        self.session.commit()
        self.redraw_plan.emit()
    
    def create_subclass(self, class_: Class, redraw=True) -> Subclass:
        names = [s.name for s in class_.subclasses]
        name = ascii_lowercase[len(names)]
        subclass = Subclass(name=name, class_id=class_.id)
        if len(class_.subclasses):
            last_subclass = class_.subclasses[-1]
            for custom_block in self.all_custom_blocks():
                if last_subclass in custom_block.subclasses:
                    custom_block.subclasses.append(subclass)
        self.session.add(subclass)
        self.session.commit()
        if redraw:
            self.redraw_plan.emit()
        return subclass

    
    def delete_subclass(self, subclass: Subclass, redraw=True) -> None:
        class_: Class = subclass.class_
        for student in subclass.students:
            self.delete_student(student)
        for block in subclass.blocks:
            self.delete_block(block)
        for subject in subclass.subjects:
            self.delete_subject(subject)
        for custom_block in subclass.custom_blocks:
            custom_block.subclasses.remove(subclass)
        self.session.delete(subclass)
        self.session.commit()
        for name, subclass in zip(ascii_lowercase, class_.subclasses):
            subclass.name = name
        # if only one subclass left, move its blocks to class
        if len(class_.subclasses)==1:
            for block in class_.subclasses[0].blocks:
                block.subclass=None
                block.class_=class_
        self.session.commit()
        self.redraw_plan.emit()


    # students
    def create_student(self, name, subclass:Subclass):
        student = Student(name=name, subclass=subclass, class_id=subclass.class_id)
        self.session.add(student)
        self.session.commit()
        return student
    
    def student_count(self) -> int:
        return self.session.query(Student).count()

    @changes_les_g_or_feas
    def delete_student(self, student):
        self.session.delete(student)
        self.session.commit()

    def update_student_name(self, student, name):
        student.name = name
        self.session.commit()

    @changes_les_g_or_feas
    def remove_subject_from_student(self, subject: Subject, student: Student):
        student.subjects.remove(subject)
        for lesson in subject.lessons:
            if not lesson.block:
                continue
            self.update_block.emit(lesson.block)

        self.session.commit()

    @changes_les_g_or_feas
    def add_subject_to_student(self, subject: Subject, student: Student):
        if subject in student.subjects:
            return
        student.subjects.append(subject)
        for lesson in subject.lessons:
            if not lesson.block:
                continue
            self.update_block.emit(lesson.block)
        self.session.commit()

    def student_exists(self, name):
        student = self.session.query(Student).filter_by(name=name).first()
        return student.subclass.full_name() if student else None
    
    def move_student(self, student: Student, target_subclass: Subclass):
        if target_subclass.class_id != student.class_id:
            return
        student.subclass = target_subclass
        old_subject: Subject
        for old_subject in student.subjects:
            if old_subject.class_id or old_subject.subclass == target_subclass:
                continue

            self.remove_subject_from_student(old_subject, student)
            for new_subject in target_subclass.subjects:
                if new_subject.name == old_subject.name:
                    self.add_subject_to_student(new_subject, student)
                    break

        self.session.commit()


    # subjects
    def get_matching_subject(self, name):
        return self.session.query(Subject).filter(Subject.name.ilike(name)).first()
       

    def create_subject(self, name, basic, my_sub_class, color=None, teachers=None, short_name=None) -> Subject:
        if teachers is None:
            teachers = []
        # copy values if subject with same name exists or load deafaults
        if not (color and teacher and short_name):
            same_name_subject = self.get_matching_subject(name)
            if same_name_subject:
                color = same_name_subject.color
                teachers = same_name_subject.teachers
                short_name = same_name_subject.short_name
            else:
                color = '#c0c0c0'
                teachers = []
                short_name = shorten_name(name)
        subject = Subject(name=name, basic=basic, color=color, short_name=short_name, teachers=teachers)
        self.session.add(subject)
        my_sub_class.subjects.append(subject)
        self.session.commit()
        return subject
    
    def update_subject_target_block_length(self, subject: Subject, length: int):
        subject.target_block_length = length
        self.session.commit()

    # @changes_les_g_or_feas
    # def update_subject_teacher(self, subject: Subject, teacher: Teacher) -> None:
    #     if subject.teacher == teacher:
    #         return
    #     self.clear_les_g_and_feas()
    #     subject.teacher = teacher
    #     for lesson in subject.lessons:
    #         if lesson.block is None:
    #             continue
    #         self.update_block.emit(lesson.block)
    #     self.session.commit()

    def add_teacher_to_subject(self, subject: Subject, teacher: Teacher) -> None:
        if teacher in subject.teachers:
            return
        subject.teachers.append(teacher)
        for lesson in subject.lessons:
            if lesson.block is None:
                continue
            self.update_block.emit(lesson.block)
        self.clear_les_g_and_feas()
        self.session.commit()

    def remove_teacher_from_subject(self, subject: Subject, teacher: Teacher) -> None:
        if teacher not in subject.teachers:
            return
        subject.teachers.remove(teacher)
        for lesson in subject.lessons:
            if lesson.block is None:
                continue
            self.update_block.emit(lesson.block)
        self.clear_les_g_and_feas()
        self.session.commit()

    def update_subject_name(self, subject: Subject, name: str) -> None:
        subject.name = name
        self.session.commit()

    def update_subject_short_name(self, subject: Subject, short_name: str) -> None:
        subject.short_name = short_name
        self.session.commit()

    def update_subject_color(self, subject: Subject, color: str) -> None:
        subject.color = color
        self.session.commit()

    def update_subject_is_basic(self, subject: Subject, basic: bool) -> None:
        subject.basic = basic
        for lesson in subject.lessons:
            if lesson.block:
                self.update_block.emit(lesson.block)
        self.session.commit()

    def update_subject_is_project(self, subject: Subject, project: bool) -> None:
        subject.is_a_project = project
        self.session.commit()

    @changes_les_g_or_feas
    def update_subject_convinience(self, subject: Subject, forb, conv):
        for i in range(5):
            setattr(subject, f'for{i+1}',forb[i])
            setattr(subject, f'inconv{i+1}',conv[i])
        for lesson in subject.lessons:
            if lesson.block:
                self.update_block.emit(lesson.block)

    def is_subject_forbidden(self, subject, block):
        mask_start = int(block.start//6)
        mask_end = int((block.start+block.length-0.5)//6) + 1
        mask = 0
        for shift in range(mask_start, mask_end):
            mask |=  1 << shift
        return mask & subject.__getattribute__(f'for{block.day+1}') 

    def is_subject_inconvinient(self, subject, block):
        mask_start = int(block.start//6)
        mask_end = int((block.start+block.length-0.5)//6) + 1
        mask = 0
        for shift in range(mask_start, mask_end):
            mask |=  1 << shift
        return mask & subject.__getattribute__(f'inconv{block.day+1}')

    @changes_les_g_or_feas
    def update_subject_classroom(self, subject: Subject, classroom: Classroom | None) -> None:
        subject.required_classroom = classroom
        for lesson in subject.lessons:
            if lesson.block:
                self.update_block.emit(lesson.block)
        self.session.commit()

    @changes_les_g_or_feas
    def delete_subject(self, subject: Subject) -> None:
        for lesson in subject.lessons:
            self.session.delete(lesson)
            if lesson.block:
                self.update_block.emit(lesson.block)
        self.session.delete(subject)
        self.session.commit()
    

    # lessons
    @changes_les_g_or_feas
    def create_lesson(self, length: int, subject: Subject) -> Lesson:
        lesson = Lesson(length=length, subject=subject)
        self.session.add(lesson)
        self.session.commit()
        return lesson
    
    def all_lessons(self) -> List[Lesson]:
        return self.session.query(Lesson).all()
    
    def pin_all_lessons(self, locked=True) -> None:
        for block in self.all_lesson_blocks():
            for lesson in block.events:
                lesson.block_locked = locked
            self.update_block.emit(block)
        self.session.commit()

    def pin_lessons_without_classrooms(self, pinned=True) -> None:
        for block in self.all_lesson_blocks():
            for lesson in block.events:
                if lesson.classroom:
                    continue
                lesson.block_locked = pinned
            self.update_block.emit(block)
        self.session.commit()
    
    def update_lesson_classroom(self, lesson: Lesson, classroom: Classroom) -> None:
        lesson.classroom = classroom
        self.session.commit()
        if lesson.block:
            self.update_block.emit(lesson.block)

    def update_event_classroom(self, event, classroom):
        event.classroom = classroom
        self.session.commit()
        if event.block:
            self.update_block.emit(event.block)

    @changes_les_g_or_feas
    def update_lesson_pinned(self, lesson: Lesson, locked: bool) -> None:
        lesson.block_locked = locked
        self.session.commit()
        self.update_block.emit(lesson.block)
    
    @changes_les_g_or_feas
    def delete_lesson(self, lesson: Lesson) -> None:
        if lesson.block:
            self.update_block.emit(lesson.block)
        self.session.delete(lesson)
        self.session.commit()

    @changes_bl_g
    def create_block(self, day:int, start:int, length:int, class_) -> LessonBlockDB:
        if isinstance(class_, Class):
            block = LessonBlockDB(day=day, start=start, length=length, class_=class_)
        else:
            block = LessonBlockDB(day=day, start=start, length=length, subclass=class_)
        self.session.add(block)
        self.session.commit()
        return block
    
    def copy_block_down(self, block: LessonBlockDB) -> LessonBlockDB:
        new_block = LessonBlockDB(
            day=block.day, 
            start=block.start+block.length+1, 
            length=block.length, 
            class_=block.class_,
            subclass=block.subclass,
            color=block.color,
            text=block.text
        )
        self.session.add(new_block)
        self.session.commit()
        self.update_block.emit(new_block)


    def all_lesson_blocks(self) -> List[LessonBlockDB]:
        return self.session.query(LessonBlockDB).all()
    
    def clear_all_lesson_blocks(self, leave_locked=False):
        for lesson in self.session.query(Lesson).all():
            if lesson.block_locked and leave_locked:
                continue
            self.remove_lesson_from_block(lesson)
        self.session.commit()
    
    def lesson_block_collides_with(self, block:Block, blocks: List[Block]):
        # get all other blocks during the same day
        for block_2 in blocks:
            if block.start <= block_2.start < block.start+block.length \
              or block_2.start <= block.start < block_2.start + block_2.length:
                yield block

    @changes_bl_g
    def delete_block(self, block: Block):
        for lesson in block.events:
            if isinstance(lesson, Lesson):
                lesson.classroom = None
            else:
                self.session.delete(lesson)
        
        self.session.delete(block)
        self.session.commit()
    
    def overlapping_blocks(self, block: Block):
        is_custom_block = isinstance(block, CustomBlock)
        return self.session.query(LessonBlockDB).filter_by(day=block.day)\
                .filter(or_(
                    Block.start.between(block.start, block.start+block.length-is_custom_block),
                    and_(Block.start <= block.start, block.start <= Block.start+Block.length-is_custom_block)
                )).all()
    
    def overlapping_custom_blocks(self, block: Block):
        return self.session.query(CustomBlock).filter_by(day=block.day)\
                .filter(or_(
                    CustomBlock.start.between(block.start, block.start+block.length-1),
                    and_(CustomBlock.start <= block.start, block.start < CustomBlock.start+CustomBlock.length)
                )).all()
    
    def overlapping_duties(self, block, exclude_self = False):
        return self.session.query(TeacherDuty).join(Block).filter(Block.day==block.day)\
                .filter(or_(not exclude_self, Block.id != block.id))\
                .filter(or_(
                    Block.start.between(block.start, block.start+block.length-1),
                    and_(Block.start <= block.start, block.start < Block.start+Block.length)
                )).all()
    
    def overlapping_lessons(self, block, exclude_self = False):
        return self.session.query(Lesson).join(Block).filter(Block.day==block.day)\
                .filter(or_(not exclude_self, Block.id != block.id))\
                .filter(or_(
                    Block.start.between(block.start, block.start+block.length),
                    and_(Block.start <= block.start, block.start <= Block.start+Block.length)
                )).all()
    
    @changes_bl_g
    def update_block_start(self, block: Block, start: int):
        pre_overlapping = set(self.overlapping_blocks(block) + self.overlapping_custom_blocks(block))
        block.start = start
        self.session.commit()
        post_overlapping = set(self.overlapping_blocks(block) + self.overlapping_custom_blocks(block))
        to_remove = pre_overlapping - post_overlapping
        # collisions = self.block_collisions(block)
        return to_remove

    def add_lesson_to_block(self, lesson: Lesson, block: Block, lock=True):
        if not lesson :
            return False
        
        if not block:
            self.remove_lesson_from_block(lesson)
            return
        old_block = lesson.block
        
        lesson.block = block
        block.events.append(lesson)
        if lesson.block_locked or lock:
            self.clear_les_g_and_feas()
        lesson.block_locked = lock
        self.session.commit()
        self.update_block.emit(block)
        if old_block:
            self.update_block.emit(old_block)
            
    def place_lesson_id_mode(self, lesson_id: int, block_id: int, classroom_id: int, lock=True):
        if not lesson_id :
            return False
        lesson = self.session.query(Lesson).filter_by(id=lesson_id).first()
        block = self.session.query(Block).filter_by(id=block_id).first()
        classroom = self.session.query(Classroom).filter_by(id=classroom_id).first()
        if not block:
            self.remove_lesson_from_block(lesson)
            return
        # old_block = lesson.block
        block.lessons.append(lesson)
        lesson.block = block
        lesson.classroom = classroom
        self.session.commit()
        self.update_block.emit(block)
        
        # lesson.block_locked = lock
        # self.update_block.emit(block)
        # if old_block:
        #     self.update_block.emit(old_block)

    def swap_lessons(self, source:Block, block:Block):
        source.events, block.events = block.events, source.events
        lesson: Lesson
        for lesson in source.events + block.events:
            if lesson.block_locked:
                self.clear_les_g_and_feas()
                break
        self.session.commit()
        self.update_block.emit(source)
        self.update_block.emit(block)

    def remove_lesson_from_block(self, lesson: Lesson):
        lesson.classroom = None
        block = lesson.block
        lesson.block = None
        if lesson.block_locked:
            self.clear_les_g_and_feas()
        lesson.block_locked = False
        if block:
            self.update_block.emit(block)
        self.session.commit()

    def all_custom_blocks(self) -> List[CustomBlock]:
        return self.session.query(CustomBlock).all()

    def create_custom_block(self, day:int, start:int, length: int, subclasses: List[Subclass]):
        block = CustomBlock(day=day, start=start, length=length, subclasses=subclasses, color='#c0c0c0', text='')
        self.session.add(block)
        self.session.commit()
        return block
    
    def update_custom_block_color(self, block, color):
        block.color = color
        self.session.commit()
        if block:
            self.update_block.emit(block)

    def update_custom_block_text(self, block: CustomBlock, text):
        block.text = text
        self.session.commit()
        if block:
            self.update_block.emit(block)

    def delete_unplaceable_custom_blocks(self):
        for custom_block in self.all_custom_blocks():
            orders = [scl.class_.order for scl in custom_block.subclasses]
            orders.sort()
            for i in range(0, len(orders)-1):
                if orders[i+1] - orders[i] > 1:
                    self.session.delete(custom_block)
                    self.session.commit()
                    break
    
    def all_blocks(self):
        blocks = self.all_lesson_blocks()
        blocks.extend(self.all_custom_blocks())
        return blocks
    

    # classrooms
    def all_classrooms(self) -> List[Classroom]:
        return self.session.query(Classroom).all()

    @changes_bl_g
    def create_classroom(self, group: ClassroomGroup, name: str) -> Classroom:
        classroom = Classroom(name=name, capacity=15, group=group)
        self.session.add(classroom)
        self.session.commit()
        self.classrooms_changed.emit()
        return classroom

    @changes_bl_g
    def update_classroom_capacity(self, classroom: Classroom, capacity: int) -> None:
        classroom.capacity = capacity
        self.session.commit()

    def update_classroom_allow_lessons(self, classroom: Classroom, allow: str) -> None:
        classroom.allow_lessons = allow
        if allow == 'none':
            for subject in classroom.subjects:
                self.update_subject_classroom(subject, None)
        self.session.commit()

    def update_classroom_name(self, classroom: Classroom, name: str) -> None:
        classroom.name = name
        self.session.commit()
        for lesson in classroom.events:
            if lesson.block:
                self.update_block.emit(lesson.block)
        self.classrooms_changed.emit()

    def delete_classroom(self, classroom: Classroom) -> None:
        for event in classroom.events:
            self.update_event_classroom(lesson, None)
        self.session.delete(classroom)
        self.session.commit()

        self.classrooms_changed.emit()

    # CLASSROOM GROUPS
    def create_classroom_group(self, name):
        groups = self.session.query(ClassroomGroup).all()
        group = ClassroomGroup(name=name)
        self.session.add(group)
        for other_group in groups:
            dist1 = Distance(start = group, end = other_group, distance = 1)
            dist2 = Distance(end = group, start = other_group, distance = 1)
            self.session.add(dist1)
            self.session.add(dist2)
        self.session.commit()
        return group

    def all_classrooms_groups(self) -> List[ClassroomGroup]:
        return self.session.query(ClassroomGroup).all()
    
    def update_classroom_group_name(self, group: ClassroomGroup, name: str) -> None:
        group.name = name
        self.session.commit()

    def delete_classroom_group(self, group: ClassroomGroup) -> None:
        for classroom in group.classrooms:
            self.delete_classroom(classroom)
        for dist in group.distances_from:
            self.session.delete(dist)
        for dist in group.distances_to:
            self.session.delete(dist)
        self.session.delete(group)
        self.session.commit()

    # DISTANCES

    def init_distances(self):
        for c1, c2 in combinations(self.session.query(ClassroomGroup).all(), 2):
            dist = Distance(start = c1, end=c2, distance = 1)
            self.session.add(dist)
            dist = Distance(start = c2, end=c1, distance = 1)
            self.session.add(dist)
        self.session.commit()

    def get_distance(self, start, end):
        return 0 if start==end else \
            self.session.query(Distance).filter_by(start=start, end=end).first().distance
    
    def set_distance(self, start, end, distance):
        if start == end:
            return
        self.session.query(Distance).filter_by(start=start, end=end).first().distance = distance
        if self.session.query(Metadata).first().symmetrical_distances:
            self.session.query(Distance).filter_by(start=end, end=start).first().distance = distance
        self.session.commit()

    def set_distances_symmetrical(self, symmetrical):
        self.session.query(Metadata).first().symmetrical_distances = symmetrical
        self.session.commit()
        if not symmetrical:
            return
        for c1, c2 in combinations(self.session.query(ClassroomGroup).all(), 2):
            dist = self.get_distance(c2, c1)
            self.set_distance(c1, c2, dist)

    # def get_collisions_for_classroom_at_block(self, classroom: Classroom, block: LessonBlockDB) -> List[Lesson]:
    #     return self.session.query(Lesson).filter_by(classroom=classroom)\
    #                .join(Lesson.block).filter(LessonBlockDB.day == block.day)\
    #                .filter(or_(
    #                     LessonBlockDB.start.between(block.start, block.start+block.length-1),
    #                     and_(LessonBlockDB.start <= block.start, block.start < LessonBlockDB.start+LessonBlockDB.length)
    #                 )).all() \
    #         if classroom else []

    # def get_duty_collisions_for_classroom_at_block(self, teacher: Teacher, block: LessonBlockDB|CustomBlock) -> List[TeacherDuty]:
    #     if not teacher:
    #         return []
    #     return self.session.query(TeacherDuty).filter_by(teacher=teacher) \
    #                     .join(TeacherDuty.block).filter(CustomBlock.day == block.day) \
    #                     .filter(or_(
    #                     CustomBlock.start.between(block.start, block.start+block.length-1), 
    #                     and_(CustomBlock.start <= block.start, block.start < CustomBlock.start+CustomBlock.length)
    #                 )).all()
 

   
    def get_lesson_collisions_for_teacher_at_block(self, teacher: Teacher, block: Block, session=None) -> int:
        if not session:
            session = self.session
        if not teacher:
            return 0
        lesson_count = self.session.query(Lesson).filter_by(block_locked=True)\
                    .join(Lesson.subject).join(Subject.teachers).filter(Teacher.id == teacher.id) \
                    .join(Lesson.block).filter(Block.day == block.day) \
                    .filter(or_(
                        Block.start.between(block.start, block.start+block.length), 
                        and_(Block.start <= block.start, block.start <= Block.start+Block.length)
                    )).count()
        duties_count = self.session.query(TeacherDuty).filter_by(teacher=teacher)\
                    .join(TeacherDuty.block).filter(Block.day==block.day) \
                    .filter(or_(
                        Block.start.between(block.start, block.start+block.length), 
                        and_(Block.start <= block.start, block.start <= Block.start+Block.length)
                    )).count()
        # print(duties_count)
        if lesson_count:
            print('l', lesson_count)
        if duties_count:
            print('d', duties_count)
        return lesson_count + duties_count
    

    # def get_duty_collisions_for_teacher_at_block(self, teacher: Teacher, block: LessonBlockDB|CustomBlock) -> List[TeacherDuty]:
    #     if not teacher:
    #         return []
    #     return self.session.query(TeacherDuty).filter_by(teacher=teacher) \
    #                     .join(TeacherDuty.block).filter(CustomBlock.day == block.day) \
    #                     .filter(or_(
    #                     CustomBlock.start.between(block.start, block.start+block.length-1), 
    #                     and_(CustomBlock.start <= block.start, block.start < CustomBlock.start+CustomBlock.length)
    #                 )).all()
    
    def get_collisions_for_students_at_block(self, students: List[Student], block: Block, session=None) -> List[Lesson]:
        if not session:
            session = self.session
        student_ids = [s.id for s in students]
        return session.query(Lesson).filter_by(block_locked=True) \
                    .join(Lesson.subject).filter(Subject.students.any(Student.id.in_(student_ids)))\
                    .join(Lesson.block).filter(Block.day == block.day)\
                    .filter(or_(
                        Block.start.between(block.start, block.start+block.length),
                        and_(Block.start <= block.start, block.start <= Block.start+Block.length)
                    )).all()
    
    def is_teacher_available(self, teacher: Teacher, block: Block) -> bool:
        if teacher is None:
            return True
        mask_start = int(block.start//6)
        mask_end = int((block.start+block.length-0.5)//6) + 1
        mask = 0
        for shift in range(mask_start, mask_end):
            mask |=  1 << shift
        return not(mask & ~teacher.__getattribute__(f'av{block.day+1}'))
    
    # def potential_clasroom_collisions(self, events: List[Lesson|TeacherDuty]):
    #     collisions = {cr: [] for cr in self.all_classrooms()}
    #     for event in events:
    #         if event.classroom:
    #             collisions[event.classroom].append(event.name_and_time())
    #     return collisions

    # def potential_clasroom_collisions_at_block(self, block):
    #     events = []
    #     for bl in self.overlapping_blocks(block):
    #         if bl == block:
    #             continue
    #         events.extend(bl.lessons)
        
    #     for bl in self.overlapping_custom_blocks(block):
    #         if bl == block:
    #             continue
    #         events.extend(bl.duties)

    #     return self.potential_clasroom_collisions(events)
    
    def potential_collisions_at_block(self, block: Block|CustomBlock, exclude_self = False, get_subjects = False, get_classrooms = False, get_teachers = False):
        if isinstance(block, CustomBlock) and get_subjects:
            raise ValueError('Custom block do not have subjects')
        # get all subjects
        items = []

        if get_subjects:
            if block.subclass:
                subjects = [s for s in block.subclass.subjects]
            else:
                subjects = [s for s in block.class_.subjects]
                for subclass in block.class_.subclasses:
                    subjects.extend(subclass.subjects)
            items.extend(subjects)

        if get_classrooms: 
            items.extend(self.all_classrooms())

        if get_teachers:
            items.extend(self.all_teachers())

        collisions = {item: [] for item in items}


        events = []
        # for bl in self.overlapping_blocks(block):
        #     if exclude_self and bl == block:
        #         continue
        #     events.extend(bl.events)
        
        # for bl in self.overlapping_custom_blocks(block):
        #     if exclude_self and bl == block:
        #         continue
        #     events.extend(bl.duties)

        
        events.extend(self.overlapping_duties(block, exclude_self=exclude_self))
        events.extend(self.overlapping_lessons(block, exclude_self=exclude_self))
        

        event: TeacherDuty | Lesson
        for event in events:
            # find busy teachers
            for teacher in event.teachers:
                for subject in teacher.subjects:
                    if subject in collisions:
                        collisions[subject].append(event.collision_text(teacher.name))
                if teacher in collisions:
                    collisions[teacher].append(event.collision_text(teacher.name))

            # find busy students
            if get_subjects and not isinstance(event, TeacherDuty):
                for subject in subjects:
                    if len(set(subject.students).intersection(event.subject.students)):
                        collisions[subject].append(f'Niektórzy uczniowie mają {event.name_and_time()}')

            
            # find occupied classrooms
            if get_classrooms:
                if event.classroom and not (isinstance(event, TeacherDuty)):
                    collisions[event.classroom].append(event.name_and_time())
                if event.classroom and not event.classroom.allow_lessons:
                    collisions[event.classroom].append(f'W {classroom.name} nie mogą odbywać się lekcje')

        # positive subject requirements
        if get_subjects:
            available_classrooms = {cr for cr in self.all_classrooms() if not collisions[cr]}
            subject: Subject
            for subject in subjects:
                # teacher
                for teacher in subject.teachers:
                    if not self.is_teacher_available(teacher, block):
                        collisions[subject].append(f'{teacher.name} nie jest dostępny w tych godzinach')

                # is required classroom available
                if subject.required_classroom:
                    collisions[subject].extend([
                        f'{subject.required_classroom.name} jest zajęte przez {les}'
                        for les in collisions[subject.required_classroom]
                    ])

                # forbidden time
                if self.is_subject_forbidden(subject, block):
                    collisions[subject].append('Nie może odbywać się w tym czasie')
                
                # is there an available classroom with enough capacity
                n_of_students = len(subject.students)
                if not len([cr for cr in available_classrooms
                            if cr.capacity >= n_of_students]) and not collisions[subject]:
                    collisions[subject].append('Żadna odpowiednio duża sala nie jest dostępna')

                # is the block long enough
                if block.length*5 not in [l.length for l in subject.lessons]:
                    collisions[subject].append(f'Żadna lekcja nie ma odpowiedniej długości')

        if get_teachers:
            for teacher in self.all_teachers():
                if not self.is_teacher_available(teacher, block):
                    collisions[teacher].append(f'{teacher.name} nie jest dostępny w tych godzinach')

        return collisions
        

    
    def block_collisions(self, block: Block):
        # if not isinstance(block, LessonBlockDB):
            # return {}
        is_lesson_block = isinstance(block, LessonBlockDB)
        colliding_blocks = self.overlapping_blocks(block)
        
        colliding_custom_blocks = self.overlapping_custom_blocks(block)
        
        collisions = {bl: [] for bl in colliding_blocks + colliding_custom_blocks}
        collisions[None] = []
        colliding_lessons = []
        for bl in colliding_blocks:
            colliding_lessons.extend(bl.events)

        events = block.events
        for event in events:
            teachers = set(event.teachers)  
            students = set(event.students)
            if isinstance(event, Lesson):
                required_classroom = event.subject.required_classroom
                if required_classroom and event.classroom and event.classroom != required_classroom:
                    collisions[None].append(([
                        f'{event.get_name()} musi odbywać się w {required_classroom.name}',
                        ''
                    ]))
                if self.is_subject_forbidden(event.subject, block):
                    collisions[None].append(([
                        f'{event.get_name()} nie może odbywać się w tym czasie',
                        ''
                    ]))
            for teacher in teachers:
                if not self.is_teacher_available(teacher, block):
                    collisions[None].append((
                        f'{event.get_name()}: {teacher.name} nie jest dostępny w tych godzinach',
                        ''
                    ))

            col_les: Event
            for col_les in colliding_lessons:
                if col_les == event:
                    continue
                # teachers
                for teacher in teachers:
                    if teacher is None:
                        continue
                    if teacher not in col_les.teachers:
                        continue
                    collisions[col_les.block].append((
                        f'{event.get_name()}: {teacher.name} prowadzi {col_les.name_and_time()}',
                        f'{col_les.get_name()}: {teacher.name} prowadzi {event.name_and_time()}'\
                        if is_lesson_block else \
                        f'{col_les.get_name()}: {event.collision_text()}',
                    ))
                if isinstance(col_les, TeacherDuty) and isinstance(event, TeacherDuty):
                    continue
                # classrooms
                if event.classroom and col_les.classroom == event.classroom:
                    collisions[col_les.block].append((
                        f'{event.get_name()}: {event.classroom.name} jest zajęte przez {col_les.name_and_time()}',
                        f'{col_les.get_name()}: {event.classroom.name} jest zajęte przez {event.name_and_time()}'\
                        if is_lesson_block else \
                        f'{col_les.get_name()}: {event.collision_text()}',
                    ))
                # students
                # # don't bother when classes are different
                # if not is_lesson_block or col_les.subject.absolute_class() != event.subject.absolute_class():
                #     continue
                if len(students.intersection(col_les.students)):
                    collisions[col_les.block].append(( 
                      f'{event.get_name()}: Niektórzy uczniowie mają {col_les.name_and_time()}',
                      f'{col_les.subject.get_name()}: Niektórzy uczniowie mają {event.name_and_time()}'
                    ))
            for col_bl in colliding_custom_blocks:
                for duty in col_bl.events:
                    if duty == event:
                        continue
                    if duty.teacher in event.teachers:
                        collisions[col_bl].append((
                            f'{event.get_name()}: {duty.collision_text()}',
                            f'{duty.get_name()}: {teacher.name} prowadzi {event.name_and_time()}' \
                            if is_lesson_block else \
                            f'{duty.get_name()}: {event.collision_text()}',
                        ))
                    if is_lesson_block and event.classroom and duty.classroom == event.classroom:
                        collisions[col_bl].append((
                            f'{event.get_name()}: W {event.classroom.name} trwa dyżur {duty.teacher.name if duty.teacher else "---"}',
                            f'{duty.get_name()}: W {event.classroom.name} trwa {event.name_and_time()}' \
                            if is_lesson_block else \
                            f'{duty.get_name()}: {event.collision_text()}',
                        ))

        
        return collisions

        
    def classroom_fit_collisions(self, classroom, subject):
        collisions = []
        # classroom is to small
        if classroom.capacity < len(subject.students):
            collisions.append('Sala jest za mała.')

        # other classroom is required
        if subject.required_classroom and subject.required_classroom!=classroom:
            collisions.append(f'{subject.name} musi odbywać się w {subject.required_classroom.name}')
        
        return collisions
    
    # DUTIES
    def new_duty(self, block: CustomBlock):
        duty = TeacherDuty()
        duty.block = block
        self.session.add(duty)
        self.session.commit()
        return duty
    
    def update_duty_teacher(self, duty: TeacherDuty, teacher: Teacher):
        duty.teacher = teacher
        self.session.commit()
        self.update_block.emit(duty.block)
    
    def update_duty_classroom(self, duty: TeacherDuty, classroom: Classroom):
        duty.classroom = classroom
        self.session.commit()
        self.update_block.emit(duty.block)

    def delete_duty(self, duty: TeacherDuty):
        self.session.delete(duty)
        self.session.commit()
        self.update_block.emit(duty.block)
    
    # SETTINGS
    def settings(self):
        return self.session.query(Metadata).first()
    
    def update_settings(self, **kwargs):
        self.session.query(Metadata).first().update(**kwargs)
        self.session.commit()

    def last_params(self):
        return self.session.query().with_entities(Results.all_params, Results.best_params).first()

    def stats(self):
        return self.session.query().with_entities(Results.stats).first()
    
    def pop_exists(self) -> bool:
        return len(self.stats()) != 0
    
    def save_results(self, best_result, population, bl_g,for_bl, les_g, feas, inconv, best_params, all_params, stats):
        stat_size = self.settings().stat_size
        if stat_size < len(all_params[0]):
            best_params = [p[-stat_size:] for p in best_params]
            all_params = [p[-stat_size:] for p in all_params]
        if stat_size < len(stats[0]):
            stats = [s[-stat_size:] for s in stats]
        self.session.query(Results).first().update(
            best_result=best_result,
            population=population,
            bl_g=bl_g,
            for_bl=for_bl,
            les_g=les_g,
            feas=feas,
            inconv=inconv,
            best_params=best_params,
            all_params=all_params,
            stats=stats
            )
        self.session.commit()

    def forget_results(self):
        for res in self.session.query(Results).all():
            self.session.delete(res)
        self.session.add(Results())
        self.session.commit()

    def clear_les_g_and_feas(self):
        res = self.session.query(Results).options(load_only(Results.les_g, Results.feas)).first()
        res.les_g, res.feas = None, None
        self.session.commit()

    def clear_bl_g(self):
        res = self.session.query(Results).options(load_only(Results.bl_g, Results.for_bl)).first()
        res.bl_g, res.for_bl = None, None
        self.session.commit()

    def harden_blocks(self):
        # group lessons in blocks
        for subject in self.session.query(Subject).filter(Subject.target_block_length>1):
            lessons = [l.length for l in subject.lessons]
            lessons.sort()
            for lesson in subject.lessons[::-1]:
                self.delete_lesson(lesson)
            while len(lessons)>=subject.target_block_length:
                self.create_lesson(
                    sum(lessons[:subject.target_block_length])+5*(subject.target_block_length-1),
                    subject
                    )
                lessons = lessons[subject.target_block_length:]
            if sum(lessons):
                self.create_lesson(sum(lessons)+5*(len(lessons)-1), subject)
            self.update_subject_target_block_length(subject, 1)

        # make longer blocks
        for l_block in self.session.query(LessonBlockDB):
            if self.session.query(LessonBlockDB).filter_by(
                subclass=l_block.subclass,
                class_=l_block.class_,
                start=l_block.start+l_block.length+1,
                length=l_block.length,
                day=l_block.day
            ).count():
                self.create_block(l_block.day, l_block.start, l_block.length*2+1, l_block.parent())
        self.redraw_plan.emit()
            
            