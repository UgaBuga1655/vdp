from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, or_, and_, literal
from PyQt5.QtCore import pyqtSignal, QObject
from string import ascii_lowercase
from typing import List
from functions import shorten_name
from db_config import Base
from models import *


class Data(QObject):
    update_custom_block = pyqtSignal(CustomBlock)
    update_block = pyqtSignal(LessonBlockDB)
    redraw_plan = pyqtSignal()


    def __init__(self, filename="planer.vdp"):
        super().__init__()
        engine = create_engine('sqlite:///' + filename)
        Base.metadata.create_all(engine)
        self.session_factory = sessionmaker(bind=engine)
        self.session = self.session_factory()

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
            return teacher
        except IntegrityError:
            self.session.rollback()
            raise IntegrityError('Taki nauczyciel już istnieje', '', '')
        
    def read_teacher_av(self, t: Teacher):
        return [t.av1, t.av2, t.av3, t.av4, t.av5]
        
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

    def all_teachers(self):
        return self.session.query(Teacher).order_by(Teacher.name).all()

    def delete_teacher(self, t):
        self.session.delete(t)
        self.session.commit()


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

    def move_subject(self, subject: Subject, target: Class | Subclass):
        subject.my_class = None
        subject.subclass = None
        if isinstance(target, Subclass):
            subject.subclass = target
        else:
            subject.my_class = target
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
    
    def delete_class(self, my_class: Class) -> None:
        for subclass in my_class.subclasses:
            self.delete_subclass(subclass, redraw=False)
        for subject in my_class.subjects:
            self.delete_subject(subject)
        for block in my_class.blocks:
            self.delete_block(block)
        self.session.delete(my_class)
        self.session.commit()
        self.redraw_plan.emit()
    
    def create_subclass(self, my_class: Class, redraw=True) -> Subclass:
        names = [s.name for s in my_class.subclasses]
        name = ascii_lowercase[len(names)]
        subclass = Subclass(name=name, class_id=my_class.id)
        if len(my_class.subclasses):
            last_subclass = my_class.subclasses[-1]
            for custom_block in self.all_custom_blocks():
                if last_subclass in custom_block.subclasses:
                    custom_block.subclasses.append(subclass)
        self.session.add(subclass)
        self.session.commit()
        if redraw:
            self.redraw_plan.emit()
        return subclass

    
    def delete_subclass(self, subclass: Subclass, redraw=True) -> None:
        my_class: Class = subclass.my_class
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
        for name, subclass in zip(ascii_lowercase, my_class.subclasses):
            subclass.name = name
        # if only one subclass left, move its blocks to class
        if len(my_class.subclasses)==1:
            for block in my_class.subclasses[0].blocks:
                block.subclass=None
                block.my_class=my_class
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

    def delete_student(self, student):
        self.session.delete(student)
        self.session.commit()

    def update_student_name(self, student, name):
        student.name = name
        self.session.commit()

    def remove_subject_from_student(self, subject: Subject, student: Student):
        student.subjects.remove(subject)
        for lesson in subject.lessons:
            if not lesson.block:
                continue
            self.update_block.emit(lesson.block)

        self.session.commit()

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


    # subjects
    def get_matching_subject(self, name):
        return self.session.query(Subject).filter(
            or_(Subject.name.contains(name), 
                literal(name).like('%' + Subject.name + '%'))).first()

    def create_subject(self, name, basic, my_sub_class, color=None, teacher=None, short_name=None) -> Subject:
        # copy values if subject with same name exists or load deafaults
        if not (color or teacher or short_name):
            same_name_subject = self.get_matching_subject(name)
            if same_name_subject:
                color = same_name_subject.color
                teacher = same_name_subject.teacher
                short_name = same_name_subject.short_name
            else:
                color = '#c0c0c0'
                teacher = None
                short_name = shorten_name(name)
        subject = Subject(name=name, basic=basic, color=color, short_name=short_name, teacher=teacher)
        self.session.add(subject)
        my_sub_class.subjects.append(subject)
        self.session.commit()
        return subject
    
    def read_subjects_of_student(self, student: Student) -> List[Subject]:
        return student.subjects
    
    def update_subject_teacher(self, subject: Subject, teacher: Teacher) -> None:
        subject.teacher = teacher
        for lesson in subject.lessons:
            if lesson.block is None:
                continue
            self.update_block.emit(lesson.block)
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
        self.session.commit()

    def update_subject_classroom(self, subject: Subject, classroom: Classroom) -> None:
        subject.required_classroom = classroom
        for lesson in subject.lessons:
            if lesson.block:
                self.update_block.emit(lesson.block)
        self.session.commit()

    def delete_subject(self, subject: Subject) -> None:
        for lesson in subject.lessons:
            self.session.delete(lesson)
            if lesson.block:
                self.update_block.emit(lesson.block)
        self.session.delete(subject)
        self.session.commit()
    

    # lessons
    def create_lesson(self, length: int, subject: Subject) -> Lesson:
        lesson = Lesson(length=length, subject=subject)
        self.session.add(lesson)
        self.session.commit()
        return lesson
    
    def all_lessons(self) -> List[Lesson]:
        return self.session.query(Lesson).all()
    
    def pin_all_lessons(self, locked=True) -> None:
        for block in self.all_lesson_blocks():
            for lesson in block.lessons:
                lesson.block_locked = locked
            self.update_block.emit(block)
        self.session.commit()

    def pin_lessons_without_classrooms(self, pinned=True) -> None:
        for block in self.all_lesson_blocks():
            for lesson in block.lessons:
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

    def update_lesson_pinned(self, lesson: Lesson, locked: bool) -> None:
        lesson.block_locked = locked
        self.session.commit()
        self.update_block.emit(lesson.block)
    
    def delete_lesson(self, lesson: Lesson) -> None:
        if lesson.block:
            self.update_block.emit(lesson.block)
        self.session.delete(lesson)
        self.session.commit()

    def create_block(self, day:int, start:int, length:int, my_class) -> LessonBlockDB:
        if isinstance(my_class, Class):
            block = LessonBlockDB(day=day, start=start, length=length, my_class=my_class)
        else:
            block = LessonBlockDB(day=day, start=start, length=length, subclass=my_class)
        self.session.add(block)
        self.session.commit()
        return block

    def all_lesson_blocks(self) -> List[LessonBlockDB]:
        return self.session.query(LessonBlockDB).all()
    
    def clear_all_lesson_blocks(self, leave_locked=False):
        for lesson in self.session.query(Lesson).all():
            if lesson.block_locked and leave_locked:
                continue
            self.remove_lesson_from_block(lesson)
        self.session.commit()
    
    def lesson_block_collides_with(self, block:LessonBlockDB, blocks: List[LessonBlockDB]):
        # get all other blocks during the same day
        for block_2 in blocks:
            if block.start <= block_2.start < block.start+block.length \
              or block_2.start <= block.start < block_2.start + block_2.length:
                yield block

    
    def delete_block(self, block):
        if hasattr(block, 'lessons'):
            for lesson in block.lessons:
                lesson.classroom = None
        self.session.delete(block)
        self.session.commit()
    
    def overlapping_blocks(self, block: LessonBlockDB):
        is_custom_block = isinstance(block, CustomBlock)
        return self.session.query(LessonBlockDB).filter_by(day=block.day)\
                .filter(or_(
                    LessonBlockDB.start.between(block.start, block.start+block.length-is_custom_block),
                    and_(LessonBlockDB.start <= block.start, block.start <= LessonBlockDB.start+LessonBlockDB.length-is_custom_block)
                )).all()
    
    def overlapping_custom_blocks(self, block: LessonBlockDB):
        return self.session.query(CustomBlock).filter_by(day=block.day)\
                .filter(or_(
                    CustomBlock.start.between(block.start, block.start+block.length-1),
                    and_(CustomBlock.start <= block.start, block.start < CustomBlock.start+CustomBlock.length)
                )).all()
    
    def update_block_start(self, block: LessonBlockDB, start: int):
        pre_overlapping = set(self.overlapping_blocks(block) + self.overlapping_custom_blocks(block))
        block.start = start
        self.session.commit()
        post_overlapping = set(self.overlapping_blocks(block) + self.overlapping_custom_blocks(block))
        to_remove = pre_overlapping - post_overlapping
        # collisions = self.block_collisions(block)
        return to_remove

    def add_lesson_to_block(self, lesson: Lesson, block: LessonBlockDB, lock=True):
        if not lesson :
            return False
        
        if not block:
            self.remove_lesson_from_block(lesson)
            return
        old_block = lesson.block
        
        lesson.block = block
        block.lessons.append(lesson)
        lesson.block_locked = lock
        self.session.commit()
        self.update_block.emit(block)
        if old_block:
            self.update_block.emit(old_block)
            
    def place_lesson_id_mode(self, lesson_id: int, block_id: int, classroom_id: int, lock=True):
        if not lesson_id :
            return False
        lesson = self.session.query(Lesson).filter_by(id=lesson_id).first()
        block = self.session.query(LessonBlockDB).filter_by(id=block_id).first()
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

    def swap_lessons(self, source, block):
        source.lessons, block.lessons = block.lessons, source.lessons
        self.session.commit()
        self.update_block.emit(source)
        self.update_block.emit(block)

    def remove_lesson_from_block(self, lesson: Lesson):
        lesson.classroom = None
        block = lesson.block
        lesson.block = None
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
            self.update_custom_block.emit(block)

    def update_custom_block_text(self, block: CustomBlock, text):
        block.text = text
        self.session.commit()
        if block:
            self.update_custom_block.emit(block)

    def delete_unplaceable_custom_blocks(self):
        for custom_block in self.all_custom_blocks():
            orders = [scl.my_class.order for scl in custom_block.subclasses]
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
    
    def create_classroom(self, name: str) -> Classroom:
        classroom = Classroom(name=name, capacity=15)
        self.session.add(classroom)
        self.session.commit()
        return classroom

    def update_classroom_capacity(self, classroom: Classroom, capacity: int) -> None:
        classroom.capacity = capacity
        self.session.commit()

    def delete_classroom(self, classroom: Classroom) -> None:
        self.session.delete(classroom)
        self.session.commit()

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
 

   
    def get_lesson_collisions_for_teacher_at_block(self, teacher: Teacher, block: LessonBlockDB|CustomBlock, session=None) -> List[Lesson]:
        if not session:
            session = self.session
        if not teacher:
            return []
        return self.session.query(Lesson) \
                    .join(Lesson.subject).filter_by(teacher=teacher) \
                    .join(Lesson.block).filter(LessonBlockDB.day == block.day) \
                    .filter(or_(
                        LessonBlockDB.start.between(block.start, block.start+block.length), 
                        and_(LessonBlockDB.start <= block.start, block.start <= LessonBlockDB.start+LessonBlockDB.length)
                    )).all()
    

    # def get_duty_collisions_for_teacher_at_block(self, teacher: Teacher, block: LessonBlockDB|CustomBlock) -> List[TeacherDuty]:
    #     if not teacher:
    #         return []
    #     return self.session.query(TeacherDuty).filter_by(teacher=teacher) \
    #                     .join(TeacherDuty.block).filter(CustomBlock.day == block.day) \
    #                     .filter(or_(
    #                     CustomBlock.start.between(block.start, block.start+block.length-1), 
    #                     and_(CustomBlock.start <= block.start, block.start < CustomBlock.start+CustomBlock.length)
    #                 )).all()
    
    def get_collisions_for_students_at_block(self, students: List[Student], block: LessonBlockDB, session=None) -> List[Lesson]:
        if not session:
            session = self.session
        student_ids = [s.id for s in students]
        return session.query(Lesson) \
                    .join(Lesson.subject).filter(Subject.students.any(Student.id.in_(student_ids)))\
                    .join(Lesson.block).filter(LessonBlockDB.day == block.day)\
                    .filter(or_(
                        LessonBlockDB.start.between(block.start, block.start+block.length),
                        and_(LessonBlockDB.start <= block.start, block.start <= LessonBlockDB.start+LessonBlockDB.length)
                    )).all()
    
    def is_teacher_available(self, teacher: Teacher, block: LessonBlockDB) -> bool:
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
    
    def potential_collisions_at_block(self, block: LessonBlockDB|CustomBlock, exclude_self = False, get_subjects = False, get_classrooms = False, get_teachers = False):
        if isinstance(block, CustomBlock) and get_subjects:
            raise ValueError('Custom block do not have subjects')
        # get all subjects
        items = []

        if get_subjects:
            if block.subclass:
                subjects = [s for s in block.subclass.subjects]
            else:
                subjects = [s for s in block.my_class.subjects]
                for subclass in block.my_class.subclasses:
                    subjects.extend(subclass.subjects)
            items.extend(subjects)

        if get_classrooms: 
            items.extend(self.all_classrooms())

        if get_teachers:
            items.extend(self.all_teachers())

        collisions = {item: [] for item in items}


        events = []
        for bl in self.overlapping_blocks(block):
            if exclude_self and bl == block:
                continue
            events.extend(bl.lessons)
        
        for bl in self.overlapping_custom_blocks(block):
            if exclude_self and bl == block:
                continue
            events.extend(bl.duties)

        

        event: TeacherDuty | Lesson
        for event in events:
            # find busy teachers
            teacher = event.teacher
            if teacher:
                for subject in teacher.subjects:
                    if subject in collisions:
                        collisions[subject].append(event.collision_text())
                if teacher in collisions:
                    collisions[teacher].append(event.collision_text())

            # find busy students
            if get_subjects and not isinstance(event, TeacherDuty):
                for subject in subjects:
                    if len(set(subject.students).intersection(event.subject.students)):
                        collisions[subject].append(f'Niektórzy uczniowie mają {event.name_and_time()}')

            
            # find occupied classrooms
            if get_classrooms:
                if event.classroom and not (isinstance(event, TeacherDuty) and isinstance(block, CustomBlock)):
                    collisions[event.classroom].append(event.name_and_time())

        # positive subject requirements
        if get_subjects:
            available_classrooms = {cr for cr in self.all_classrooms() if not collisions[cr]}
            subject: Subject
            for subject in subjects:
                # teacher
                if not self.is_teacher_available(subject.teacher, block):
                    collisions[subject].append(f'{subject.teacher.name} nie jest dostępny w tych godzinach')

                # is required classroom available
                if subject.required_classroom:
                    collisions[subject].extend([
                        f'{subject.required_classroom.name} jest zajęte przez {les}'
                        for les in collisions[subject.required_classroom]
                    ])
                
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
        

    
    def block_collisions(self, block: LessonBlockDB|CustomBlock):
        # if not isinstance(block, LessonBlockDB):
            # return {}
        is_lesson_block = isinstance(block, LessonBlockDB)
        colliding_blocks = self.overlapping_blocks(block)
        
        colliding_custom_blocks = self.overlapping_custom_blocks(block)
        
        collisions = {bl: [] for bl in colliding_blocks + colliding_custom_blocks}
        collisions[None] = []
        colliding_lessons = []
        for bl in colliding_blocks:
            colliding_lessons.extend(bl.lessons)

        events = block.lessons if is_lesson_block else block.duties
        event: Lesson
        for event in events:
            if is_lesson_block:
                teacher = event.subject.teacher  
                students = set(event.subject.students)
                required_classroom = event.subject.required_classroom
                if required_classroom and event.classroom and event.classroom != required_classroom:
                    collisions[None].append(([
                        f'{event.get_name()} musi odbywać się w {required_classroom.name}',
                        ''
                    ]))
            else:
                teacher = event.teacher
                students = set()

            if teacher and not self.is_teacher_available(teacher, block):
                collisions[None].append((
                    f'{event.get_name()}: {teacher.name} nie jest dostępny w tych godzinach',
                    ''
                ))

            col_les: Lesson
            for col_les in colliding_lessons:
                if col_les == event:
                    continue
                # teachers
                if teacher and col_les.subject.teacher == teacher:
                    collisions[col_les.block].append((
                        f'{event.get_name()}: {teacher.name} prowadzi {col_les.name_and_time()}',
                        f'{col_les.get_name()}: {teacher.name} prowadzi {event.name_and_time()}'\
                        if is_lesson_block else \
                        f'{col_les.get_name()}: {event.collision_text()}',
                    ))
                # classrooms
                if event.classroom and col_les.classroom == event.classroom:
                    collisions[col_les.block].append((
                        f'{event.get_name()}: {event.classroom.name} jest zajęte przez {col_les.name_and_time()}',
                        f'{col_les.get_name()}: {event.classroom.name} jest zajęte przez {event.name_and_time()}'\
                        if is_lesson_block else \
                        f'{col_les.get_name()}: {event.collision_text()}',
                    ))
                # students
                # don't bother when classes are different
                if not is_lesson_block or col_les.subject.absolute_class() != event.subject.absolute_class():
                    continue
                if len(students.intersection(col_les.subject.students)):
                    collisions[col_les.block].append(( 
                      f'{event.get_name()}: Niektórzy uczniowie mają {col_les.name_and_time()}',
                      f'{col_les.subject.get_name()}: Niektórzy uczniowie mają {event.name_and_time()}'
                    ))
            for col_bl in colliding_custom_blocks:
                for duty in col_bl.duties:
                    if duty == event:
                        continue
                    if duty.teacher == teacher:
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
    
    def update_duty_classroom(self, duty: TeacherDuty, classroom: Classroom):
        duty.classroom = classroom
        self.session.commit()

    def delete_duty(self, duty: TeacherDuty):
        self.session.delete(duty)
        self.session.commit()
    
